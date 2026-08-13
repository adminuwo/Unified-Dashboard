"""
One-time script to create the super admin user in MongoDB.
Run from the backend/ directory:
    python create_super_admin.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

import bcrypt
from pymongo import MongoClient
from datetime import datetime, timezone

MONGODB_URL = os.getenv("MONGODB_URL", "")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "unified_service_db")

# ─── Credentials ──────────────────────────────────────────────────────────────
ADMIN_USERNAME = "superadmin"
ADMIN_PASSWORD = "SuperAdmin@123"
# ──────────────────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")

def main():
    client = MongoClient(MONGODB_URL, tlsAllowInvalidCertificates=True)
    db = client[MONGODB_DB_NAME]

    existing = db["admin_users"].find_one({"username": ADMIN_USERNAME})
    if existing:
        print(f"[INFO] Super admin '{ADMIN_USERNAME}' already exists. No changes made.")
        return

    admin_doc = {
        "username": ADMIN_USERNAME,
        "password_hash": hash_password(ADMIN_PASSWORD),
        "is_active": True,
        "role": "super_admin",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    db["admin_users"].insert_one(admin_doc)
    print(f"[SUCCESS] Super admin created!")
    print(f"  Username : {ADMIN_USERNAME}")
    print(f"  Password : {ADMIN_PASSWORD}")

if __name__ == "__main__":
    main()
