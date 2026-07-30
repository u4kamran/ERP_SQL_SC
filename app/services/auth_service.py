"""Authentication business logic service."""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, Request, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.models.session import RefreshToken, UserSession
from app.models.user import PasswordResetToken, User
from app.repositories.audit_repository import AuditRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository
from app.schemas import ChangePasswordRequest, LoginRequest, TokenResponse
from app.security.jwt import create_access_token, create_refresh_token, decode_token
from app.security.password import hash_password, validate_password_policy, verify_password
from app.utils import generate_secure_token, get_client_ip, hash_token, parse_user_agent


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.session_repo = SessionRepository(db)
        self.audit_repo = AuditRepository(db)

    def login(self, request: Request, login_data: LoginRequest) -> TokenResponse:
        ip = get_client_ip(request)
        ua_string = request.headers.get("User-Agent", "")
        ua_info = parse_user_agent(ua_string)
        username = login_data.username.strip()

        user = self.user_repo.get_by_username(username)
        if not user:
            self._log_failed_login(username, "Invalid credentials", ip, ua_string, ua_info)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password.")

        if not user.IsActive:
            self._log_failed_login(username, "Account inactive", ip, ua_string, ua_info, user.UserId)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive.")

        if user.IsDeleted:
            self._log_failed_login(username, "Account deleted", ip, ua_string, ua_info, user.UserId)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled.")

        if user.is_locked:
            self._log_failed_login(username, "Account locked", ip, ua_string, ua_info, user.UserId)
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account is locked until {user.LockoutEndDate.isoformat()}.",
            )

        if not verify_password(login_data.password, user.PasswordHash):
            user.FailedLoginAttempts += 1
            if user.FailedLoginAttempts >= settings.max_failed_login_attempts:
                user.LockoutEndDate = datetime.utcnow() + timedelta(minutes=settings.account_lockout_minutes)
            self.user_repo.update(user)
            self.db.commit()
            self._log_failed_login(username, "Invalid credentials", ip, ua_string, ua_info, user.UserId)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password.")

        if user.PasswordExpiryDate and user.PasswordExpiryDate < datetime.utcnow() and not user.MustChangePassword:
            user.MustChangePassword = True

        user.FailedLoginAttempts = 0
        user.LockoutEndDate = None
        user.LastLoginDate = datetime.utcnow()
        user.LastLoginIp = ip
        self.user_repo.update(user)

        roles = [r.RoleCode for r in self.user_repo.get_user_roles(user.UserId)]
        permissions = self.user_repo.get_user_permissions(user.UserId)

        active_sessions = self.session_repo.get_active_sessions(user.UserId)
        if len(active_sessions) >= settings.max_concurrent_sessions:
            oldest = active_sessions[-1]
            self.session_repo.revoke_session(oldest.SessionId, "Max concurrent sessions exceeded")

        session_id = uuid.uuid4()
        refresh_days = settings.jwt_remember_me_expire_days if login_data.remember_me else settings.jwt_refresh_token_expire_days
        expires_at = datetime.utcnow() + timedelta(days=refresh_days)

        refresh_token_raw, refresh_jti, refresh_exp = create_refresh_token(
            user.UserId, str(session_id), login_data.remember_me
        )
        refresh_hash = hash_token(refresh_token_raw)

        session = UserSession(
            SessionId=session_id,
            UserId=user.UserId,
            RefreshTokenHash=refresh_hash,
            IpAddress=ip,
            UserAgent=ua_string,
            Browser=ua_info["browser"],
            Device=ua_info["device"],
            OperatingSystem=ua_info["os"],
            IsRememberMe=login_data.remember_me,
            ExpiresAt=expires_at,
            LastActivityDate=datetime.utcnow(),
        )
        self.session_repo.create_session(session)

        self.session_repo.create_refresh_token(
            RefreshToken(
                UserId=user.UserId,
                SessionId=session_id,
                TokenHash=refresh_hash,
                ExpiresAt=refresh_exp.replace(tzinfo=None),
            )
        )

        access_token, access_jti, access_exp = create_access_token(
            user.UserId, user.Username, roles, permissions, str(session_id)
        )

        self.audit_repo.log_login(
            username=username,
            status="SUCCESS",
            user_id=user.UserId,
            ip_address=ip,
            user_agent=ua_string,
            browser=ua_info["browser"],
            device=ua_info["device"],
            os=ua_info["os"],
            session_id=session_id,
        )
        self.audit_repo.log_audit(
            action="LOGIN",
            user_id=user.UserId,
            username=username,
            ip_address=ip,
            user_agent=ua_string,
        )
        self.db.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_raw,
            expires_in=settings.jwt_access_token_expire_minutes * 60,
            must_change_password=user.MustChangePassword,
        )

    def refresh(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token)
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type.")

        jti = payload.get("jti")
        if self.session_repo.is_token_revoked(jti):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked.")

        token_hash = hash_token(refresh_token)
        stored = self.session_repo.get_refresh_token_by_hash(token_hash)
        if not stored or stored.ExpiresAt < datetime.utcnow():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired.")

        user_id = int(payload["sub"])
        user = self.user_repo.get_by_id(user_id)
        if not user or not user.IsActive:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive.")

        session_id = uuid.UUID(payload["session_id"])
        session = self.session_repo.get_session(session_id)
        if not session or session.IsRevoked:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired.")

        roles = [r.RoleCode for r in self.user_repo.get_user_roles(user.UserId)]
        permissions = self.user_repo.get_user_permissions(user.UserId)

        access_token, _, _ = create_access_token(
            user.UserId, user.Username, roles, permissions, str(session_id)
        )
        self.session_repo.update_last_activity(session_id)
        self.db.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.jwt_access_token_expire_minutes * 60,
            must_change_password=user.MustChangePassword,
        )

    def logout(self, request: Request, access_token: Optional[str], refresh_token: Optional[str]):
        ip = get_client_ip(request)
        user_id = None
        username = None

        if access_token:
            try:
                payload = decode_token(access_token)
                user_id = int(payload.get("sub", 0))
                jti = payload.get("jti")
                exp = payload.get("exp")
                if jti and exp:
                    self.session_repo.revoke_jti(
                        jti, "access", user_id,
                        datetime.utcfromtimestamp(exp), "Logout"
                    )
                session_id = payload.get("session_id")
                if session_id:
                    self.session_repo.revoke_session(uuid.UUID(session_id), "User logout")
            except JWTError:
                pass

        if refresh_token:
            try:
                payload = decode_token(refresh_token)
                jti = payload.get("jti")
                exp = payload.get("exp")
                user_id = int(payload.get("sub", 0))
                if jti and exp:
                    self.session_repo.revoke_jti(
                        jti, "refresh", user_id,
                        datetime.utcfromtimestamp(exp), "Logout"
                    )
                token_hash = hash_token(refresh_token)
                stored = self.session_repo.get_refresh_token_by_hash(token_hash)
                if stored:
                    self.session_repo.revoke_refresh_token(stored.RefreshTokenId)
            except JWTError:
                pass

        if user_id:
            user = self.user_repo.get_by_id(user_id)
            username = user.Username if user else None

        self.audit_repo.log_audit(
            action="LOGOUT", user_id=user_id, username=username, ip_address=ip
        )
        self.db.commit()

    def change_password(self, user_id: int, data: ChangePasswordRequest, request: Request):
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        if not verify_password(data.current_password, user.PasswordHash):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect.")

        valid, errors = validate_password_policy(data.new_password)
        if not valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="; ".join(errors))

        history = self.user_repo.get_password_history(user_id, settings.password_history_count)
        for h in history:
            if verify_password(data.new_password, h.PasswordHash):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot reuse any of the last {settings.password_history_count} passwords.",
                )

        self.user_repo.add_password_history(user_id, user.PasswordHash)
        user.PasswordHash = hash_password(data.new_password)
        user.PasswordChangedDate = datetime.utcnow()
        user.PasswordExpiryDate = datetime.utcnow() + timedelta(days=settings.password_expiry_days)
        user.MustChangePassword = False
        self.user_repo.update(user)

        self.audit_repo.log_audit(
            action="PASSWORD_CHANGE",
            user_id=user_id,
            username=user.Username,
            ip_address=get_client_ip(request),
        )
        self.db.commit()

    def request_password_reset(self, email: str) -> str:
        user = self.user_repo.get_by_email(email)
        if not user:
            return "If the email exists, a reset link will be sent."

        token = generate_secure_token()
        token_hash = hash_token(token)
        reset = PasswordResetToken(
            UserId=user.UserId,
            TokenHash=token_hash,
            ExpiresAt=datetime.utcnow() + timedelta(hours=settings.password_reset_token_expire_hours),
        )
        self.db.add(reset)
        self.audit_repo.log_audit(action="PASSWORD_RESET_REQUEST", user_id=user.UserId, username=user.Username)
        self.db.commit()

        if settings.smtp_enabled:
            pass  # Email sending hook for future implementation

        return token  # Returned for dev/testing; in production only email is sent

    def _log_failed_login(self, username, reason, ip, ua_string, ua_info, user_id=None):
        self.audit_repo.log_login(
            username=username,
            status="FAILED",
            user_id=user_id,
            failure_reason=reason,
            ip_address=ip,
            user_agent=ua_string,
            browser=ua_info["browser"],
            device=ua_info["device"],
            os=ua_info["os"],
        )
        self.db.commit()
