"""Audit service wrapper."""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.audit import AuditLog, LoginHistory
from app.repositories.audit_repository import AuditRepository


class AuditService:
    def __init__(self, db: Session):
        self.repo = AuditRepository(db)

    def get_audit_logs(self, skip: int = 0, limit: int = 50, user_id: Optional[int] = None) -> List[AuditLog]:
        return self.repo.get_audit_logs(skip, limit, user_id)

    def get_login_history(self, user_id: int, skip: int = 0, limit: int = 20) -> List[LoginHistory]:
        return self.repo.get_login_history(user_id, skip, limit)
