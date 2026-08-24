import os
import pytest  # type: ignore
from fastapi.testclient import TestClient  # type: ignore
import mongomock  # type: ignore

os.environ["ENVIRONMENT"] = "testing"
from src.config.settings import settings
settings.ENVIRONMENT = "testing"

from src.database.connection import get_db, init_db
from src.main import app



@pytest.fixture(scope="function")
def db_session():
    """Create fresh in-memory MongoDB database for each test function."""
    client = mongomock.MongoClient()
    db = client["test_unified_service_db"]
    init_db(db)
    yield db


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


from src.auth.service import hash_password


@pytest.fixture(scope="function")
def admin_headers(client, db_session):
    """Fixture providing valid admin JWT authorization header."""
    if not db_session["admin_users"].find_one({"username": "super.admin@unified.com"}):
        from src.modules.auth.service import hash_password
        db_session["admin_users"].insert_one({
            "_id": "super_admin_test_id",
            "username": "super.admin@unified.com",
            "password_hash": hash_password("@xQn!W&Wg-ufSWn)93Qg_0S2"),
            "role": "super_admin",
            "name": "Super Admin",
            "is_active": True
        })
    res = client.post("/api/admin/login", json={
        "username": "super.admin@unified.com",
        "password": "@xQn!W&Wg-ufSWn)93Qg_0S2"
    })
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
