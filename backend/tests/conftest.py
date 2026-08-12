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
