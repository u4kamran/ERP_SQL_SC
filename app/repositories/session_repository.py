"""Session data access repository."""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.session import RefreshToken, RevokedToken, UserSession


class SessionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_session(self, session: UserSession) -> UserSession:
        self.db.add(session)
        self.db.flush()
        return session

    def get_session(self, session_id: uuid.UUID) -> Optional[UserSession]:
        return self.db.get(UserSession, session_id)

    def get_active_sessions(self, user_id: int) -> List[UserSession]:
        stmt = (
            select(UserSession)
            .where(
                UserSession.UserId == user_id,
                UserSession.IsRevoked == False,  # noqa: E712
                UserSession.IsDeleted == False,  # noqa: E712
                UserSession.ExpiresAt > datetime.utcnow(),
            )
            .order_by(UserSession.LastActivityDate.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def revoke_session(self, session_id: uuid.UUID, reason: str = "User logout"):
        session = self.get_session(session_id)
        if session:
            session.IsRevoked = True
            session.RevokedDate = datetime.utcnow()
            session.RevokedReason = reason
            session.IsActive = False
            self.db.flush()

    def revoke_all_user_sessions(self, user_id: int, except_session_id: Optional[uuid.UUID] = None, reason: str = "Force logout"):
        sessions = self.get_active_sessions(user_id)
        for s in sessions:
            if except_session_id and s.SessionId == except_session_id:
                continue
            self.revoke_session(s.SessionId, reason)

    def create_refresh_token(self, token: RefreshToken) -> RefreshToken:
        self.db.add(token)
        self.db.flush()
        return token

    def get_refresh_token_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        stmt = select(RefreshToken).where(
            RefreshToken.TokenHash == token_hash,
            RefreshToken.IsRevoked == False,  # noqa: E712
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def revoke_refresh_token(self, token_id: int):
        token = self.db.get(RefreshToken, token_id)
        if token:
            token.IsRevoked = True
            token.RevokedDate = datetime.utcnow()
            self.db.flush()

    def is_token_revoked(self, jti: str) -> bool:
        stmt = select(RevokedToken).where(RevokedToken.Jti == jti, RevokedToken.IsDeleted == False)  # noqa: E712
        return self.db.execute(stmt).scalar_one_or_none() is not None

    def revoke_jti(self, jti: str, token_type: str, user_id: Optional[int], expires_at: datetime, reason: str = ""):
        if not self.is_token_revoked(jti):
            self.db.add(
                RevokedToken(
                    Jti=jti,
                    TokenType=token_type,
                    UserId=user_id,
                    ExpiresAt=expires_at,
                    RevokedDate=datetime.utcnow(),
                    RevokedReason=reason,
                )
            )
            self.db.flush()

    def update_last_activity(self, session_id: uuid.UUID):
        session = self.get_session(session_id)
        if session:
            session.LastActivityDate = datetime.utcnow()
            self.db.flush()
