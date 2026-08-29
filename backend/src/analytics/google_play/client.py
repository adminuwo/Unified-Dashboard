from typing import List
from google.cloud import storage
from google.oauth2 import service_account
from google.auth import default

class GooglePlayStorageClient:
    def __init__(self, bucket_name: str, auth_mode: str = "cloud_run_service_identity", 
                 service_account_email: str = None, secret_resource_name: str = None):
        self.bucket_name = bucket_name
        self.auth_mode = auth_mode
        self.service_account_email = service_account_email
        self.secret_resource_name = secret_resource_name
        self._storage_client = None

    def _get_client(self) -> storage.Client:
        if self._storage_client is None:
            import json
            import os
            from src.config.settings import settings

            # 1. Try to load from GOOGLE_PLAY_SERVICE_ACCOUNT_JSON or GCP_SERVICE_ACCOUNT_JSON settings
            raw_json = settings.GOOGLE_PLAY_SERVICE_ACCOUNT_JSON or settings.GCP_SERVICE_ACCOUNT_JSON
            if raw_json:
                try:
                    info = json.loads(raw_json.strip())
                    self._storage_client = storage.Client.from_service_account_info(info)
                    return self._storage_client
                except Exception as e:
                    print(f"Failed to load GCS client from service account JSON: {e}")

            # 2. Try to load from local key file path if configured/exists
            key_path = "gcp-key.json"
            if os.path.exists(key_path):
                try:
                    self._storage_client = storage.Client.from_service_account_json(key_path)
                    return self._storage_client
                except Exception as e:
                    print(f"Failed to load GCS client from key file {key_path}: {e}")

            # 3. Fallback to Application Default Credentials (ADC)
            credentials, project = default()
            self._storage_client = storage.Client(credentials=credentials)
        return self._storage_client

    def list_objects(self, prefix: str) -> List[storage.Blob]:
        client = self._get_client()
        bucket = client.bucket(self.bucket_name)
        return list(bucket.list_blobs(prefix=prefix))

    def download_object(self, object_name: str) -> bytes:
        client = self._get_client()
        bucket = client.bucket(self.bucket_name)
        blob = bucket.blob(object_name)
        return blob.download_as_bytes()
