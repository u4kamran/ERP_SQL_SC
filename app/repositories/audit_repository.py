"""Audit and login history repository."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit import AuditLog, LoginHistory


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def log_login(
        self,
        username: str,
        status: str,
        user_id: Optional[int] = None,
        failure_reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        browser: Optional[str] = None,
        device: Optional[str] = None,
        os: Optional[str] = None,
        session_id=None,
    ) -> LoginHistory:
        entry = LoginHistory(
            UserId=user_id,
            Username=username,
            LoginStatus=status,
            FailureReason=failure_reason,
            IpAddress=ip_address,
            UserAgent=user_agent,
            Browser=browser,
            Device=device,
            OperatingSystem=os,
            SessionId=session_id,
        )
        self.db.add(entry)
        self.db.flush()
        return entry

    def log_audit(
        self,
        action: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        old_values: Optional[str] = None,
        new_values: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "SUCCESS",
        error_message: Optional[str] = None,
    ) -> AuditLog:
        entry = AuditLog(
            UserId=user_id,
            Username=username,
            Action=action,
            EntityType=entity_type,
            EntityId=entity_id,
            OldValues=old_values,
            NewValues=new_values,
            IpAddress=ip_address,
            UserAgent=user_agent,
            Status=status,
            ErrorMessage=error_message,
        )
        self.db.add(entry)
        self.db.flush()
        return entry

    def get_audit_logs(self, skip: int = 0, limit: int = 50, user_id: Optional[int] = None) -> List[AuditLog]:
        stmt = select(AuditLog).where(AuditLog.IsDeleted == False)  # noqa: E712
        if user_id:
            stmt = stmt.where(AuditLog.UserId == user_id)
        stmt = stmt.order_by(AuditLog.CreatedDate.desc()).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def get_login_history(self, user_id: int, skip: int = 0, limit: int = 20) -> List[LoginHistory]:
        stmt = (
            select(LoginHistory)
            .where(LoginHistory.UserId == user_id, LoginHistory.IsDeleted == False)  # noqa: E712
            .order_by(LoginHistory.CreatedDate.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())
