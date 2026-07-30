"""Audit log API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, require_permission
from app.database.session import get_db
from app.schemas import AuditLogResponse
from app.services.audit_service import AuditService

router = APIRouter()


@router.get("/", response_model=List[AuditLogResponse])
def list_audit_logs(
    skip: int = 0,
    limit: int = 50,
    user_id: Optional[int] = None,
    current_user: CurrentUser = Depends(require_permission("auth.audit.view")),
    db: Session = Depends(get_db),
):
    logs = AuditService(db).get_audit_logs(skip, limit, user_id)
    return [AuditLogResponse.model_validate(log) for log in logs]
