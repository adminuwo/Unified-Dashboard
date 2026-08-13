from fastapi import APIRouter, Depends, status  # type: ignore
from pymongo.database import Database  # type: ignore

from src.database.connection import get_db
from src.database.models import ApplicationKey
from src.middleware.authentication import get_current_application
from src.logs.schemas import LogCreate, LogResponse
from src.logs import service

router = APIRouter(prefix="/logs", tags=["Logs"])


@router.post("/", response_model=LogResponse, status_code=status.HTTP_201_CREATED)
def submit_log(
    data: LogCreate,
    db: Database = Depends(get_db),
    app: ApplicationKey = Depends(get_current_application)
):
    """Record an application log entry with automatic data redaction."""
    log_entry = service.create_log_entry(db, app.id, data)
    return log_entry
