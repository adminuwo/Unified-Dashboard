import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from pymongo.database import Database  # type: ignore


class AuthRepository:
    """MongoDB Repository layer for users, sessions, and applications collections."""

    def __init__(self, db: Database):
        self.db = db
        self.users_col = db["users"]
        self.sessions_col = db["sessions"]
        self.applications_col = db["applications"]
        self.password_resets_col = db["password_resets"]


    # ------------------ USERS COLLECTION ------------------

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        return self.users_col.find_one({"email": email.strip().lower()})

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self.users_col.find_one({"_id": user_id})

    def create_user(
        self,
        email: str,
        password_hash: str,
        name: str = "User",
        is_verified: bool = True,
        is_active: bool = True,
        connected_apps: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        user_doc = {
            "_id": str(uuid.uuid4()),
            "email": email.strip().lower(),
            "password_hash": password_hash,
            "name": name,
            "is_active": is_active,
            "is_verified": is_verified,
            "connected_apps": connected_apps or [],
            "created_at": now,
            "updated_at": now,
            "last_login": None,
        }
        self.users_col.insert_one(user_doc)
        return user_doc

    def update_last_login(self, user_id: str, application_id: Optional[str] = None) -> None:
        now = datetime.now(timezone.utc)
        update_doc: Dict[str, Any] = {"$set": {"last_login": now, "updated_at": now}}
        if application_id:
            update_doc["$addToSet"] = {"connected_apps": application_id}
            
        self.users_col.update_one(
            {"_id": user_id},
            update_doc
        )

    def update_user_password(self, user_id: str, new_password_hash: str) -> None:
        now = datetime.now(timezone.utc)
        self.users_col.update_one(
            {"_id": user_id},
            {"$set": {"password_hash": new_password_hash, "updated_at": now}}
        )

    # ------------------ PASSWORD RESETS COLLECTION ------------------

    def save_password_reset(self, email: str, otp_hash: str, expires_at: datetime) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        clean_email = email.strip().lower()
        # Invalidate previous unused reset tokens for this email
        self.password_resets_col.update_many(
            {"email": clean_email, "is_used": False},
            {"$set": {"is_used": True, "updated_at": now}}
        )

        reset_doc = {
            "_id": str(uuid.uuid4()),
            "email": clean_email,
            "otp_hash": otp_hash,
            "expires_at": expires_at,
            "is_used": False,
            "created_at": now,
        }
        self.password_resets_col.insert_one(reset_doc)
        return reset_doc

    def get_active_password_reset(self, email: str) -> Optional[Dict[str, Any]]:
        clean_email = email.strip().lower()
        return self.password_resets_col.find_one(
            {"email": clean_email, "is_used": False},
            sort=[("created_at", -1)]
        )

    def mark_password_reset_used(self, reset_id: str) -> None:
        now = datetime.now(timezone.utc)
        self.password_resets_col.update_one(
            {"_id": reset_id},
            {"$set": {"is_used": True, "updated_at": now}}
        )

    # ------------------ SESSIONS COLLECTION ------------------


    def create_session(
        self,
        user_id: str,
        refresh_token_hash: str,
        device: str = "Unknown Device",
        ip_address: str = "127.0.0.1",
        expires_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        session_doc = {
            "_id": str(uuid.uuid4()),
            "user_id": user_id,
            "refresh_token_hash": refresh_token_hash,
            "device": device,
            "ip_address": ip_address,
            "expires_at": expires_at or (now + timedelta(days=7)),
            "created_at": now,
        }
        self.sessions_col.insert_one(session_doc)
        return session_doc

    def find_session_by_hash(self, refresh_token_hash: str) -> Optional[Dict[str, Any]]:
        return self.sessions_col.find_one({"refresh_token_hash": refresh_token_hash})

    def delete_session_by_id(self, session_id: str) -> None:
        self.sessions_col.delete_one({"_id": session_id})

    def delete_session_by_hash(self, refresh_token_hash: str) -> None:
        self.sessions_col.delete_one({"refresh_token_hash": refresh_token_hash})

    def delete_all_user_sessions(self, user_id: str) -> int:
        res = self.sessions_col.delete_many({"user_id": user_id})
        return res.deleted_count

    # ------------------ APPLICATIONS COLLECTION (Future-ready) ------------------

    def create_application(
        self,
        app_code: str,
        name: str,
        redirect_url: str = "",
        api_key_hash: str = ""
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        app_doc = {
            "_id": str(uuid.uuid4()),
            "app_code": app_code.lower().strip(),
            "name": name,
            "redirect_url": redirect_url,
            "api_key_hash": api_key_hash,
            "is_active": True,
            "created_at": now
        }
        self.applications_col.update_one(
            {"app_code": app_code.lower().strip()},
            {"$set": app_doc},
            upsert=True
        )
        return app_doc

    def get_application_by_code(self, app_code: str) -> Optional[Dict[str, Any]]:
        return self.applications_col.find_one({"app_code": app_code.lower().strip()})
