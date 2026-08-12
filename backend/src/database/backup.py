import os
import json
from datetime import datetime, timezone
from src.database.connection import get_db


def create_database_backup():
    """Create timestamped JSON backup snapshot of all MongoDB collections."""
    db = get_db().__next__()
    now_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    backups_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backups"))
    os.makedirs(backups_dir, exist_ok=True)

    backup_filepath = os.path.join(backups_dir, f"backup_snapshot_{now_str}.json")

    collections_to_backup = [
        "users",
        "admin_users",
        "application_keys",
        "chat_tracking",
        "app_downloads",
        "logs",
        "payments",
        "subscriptions"
    ]

    backup_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database_name": db.name,
        "collections": {}
    }

    for col in collections_to_backup:
        docs = list(db[col].find())
        # Clean ObjectId or non-serializable fields if any
        serializable_docs = []
        for doc in docs:
            d = dict(doc)
            if "_id" in d and not isinstance(d["_id"], str):
                d["_id"] = str(d["_id"])
            serializable_docs.append(d)

        backup_data["collections"][col] = serializable_docs

    with open(backup_filepath, "w", encoding="utf-8") as f:
        json.dump(backup_data, f, indent=2, default=str)

    print(f"[backup] Database backup created successfully at: {backup_filepath}")
    return backup_filepath


if __name__ == "__main__":
    create_database_backup()
