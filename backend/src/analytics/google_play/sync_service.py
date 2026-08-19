from typing import List, Dict, Any
import uuid
import pymongo # type: ignore
from datetime import datetime, timezone
from pymongo.database import Database # type: ignore

from .client import GooglePlayStorageClient
from .filenames import parse_filename
from .parser import parse_play_report
from .validator import validate_schema, validate_row
from .normalizer import normalize_row
from src.database.models import utc_now, generate_uuid

def run_sync(db: Database, apps: List[Dict[str, str]], bucket_name: str, 
             auth_mode: str = "cloud_run_service_identity") -> Dict[str, Any]:
    
    run_id = generate_uuid()
    client = GooglePlayStorageClient(bucket_name=bucket_name, auth_mode=auth_mode)
    
    # 1. Create sync run record
    sync_run = {
        "_id": run_id,
        "status": "running",
        "started_at": utc_now(),
        "counters": {
            "files_discovered": 0,
            "files_processed": 0,
            "rows_inserted": 0
        }
    }
    db["analytics_sync_runs"].insert_one(sync_run)
    
    for app in apps:
        app_code = app["app_code"]
        package_name = app["package_name"]
        prefix = f"stats/installs/installs_{package_name}_"
        
        try:
            blobs = client.list_objects(prefix=prefix)
            sync_run["counters"]["files_discovered"] += len(blobs)
            
            for blob in blobs:
                # 7. Parse and validate filename
                try:
                    file_info = parse_filename(blob.name)
                except Exception:
                    continue # Skip invalid
                
                # Check if already processed
                existing_file = db["analytics_source_files"].find_one({
                    "bucket_name": bucket_name,
                    "object_name": blob.name,
                    "generation": str(blob.generation)
                })
                
                if existing_file:
                    continue
                
                # Download and parse
                content = blob.download_as_bytes()
                headers, normalized_headers, rows, encoding, fingerprint = parse_play_report(content)
                
                # Validate schema
                validate_schema(normalized_headers)
                
                # Process rows
                metrics_to_insert = []
                for row in rows:
                    validate_row(row, package_name, file_info["report_month"])
                    norm_row = normalize_row(row, package_name, row["date"], file_info["dimension"])
                    norm_row["_id"] = generate_uuid()
                    norm_row["app_code"] = app_code
                    norm_row["package_name"] = package_name
                    norm_row["source_file_id"] = blob.name
                    norm_row["source_generation"] = str(blob.generation)
                    metrics_to_insert.append(norm_row)
                    
                if metrics_to_insert:
                    db["play_install_metrics"].insert_many(metrics_to_insert)
                    sync_run["counters"]["rows_inserted"] += len(metrics_to_insert)
                
                # Record source file
                db["analytics_source_files"].insert_one({
                    "_id": generate_uuid(),
                    "bucket_name": bucket_name,
                    "object_name": blob.name,
                    "generation": str(blob.generation),
                    "package_name": package_name,
                    "app_code": app_code,
                    "report_month": file_info["report_month"],
                    "dimension_type": file_info["dimension"],
                    "ingestion_status": "success",
                    "updated_at": utc_now()
                })
                
                sync_run["counters"]["files_processed"] += 1
                
        except Exception as e:
            print(f"Error syncing {app_code}: {e}")
            
    # Update sync run status
    db["analytics_sync_runs"].update_one(
        {"_id": run_id},
        {"$set": {
            "status": "success",
            "completed_at": utc_now(),
            "counters": sync_run["counters"]
        }}
    )
    
    return {"run_id": run_id, "status": "success"}
