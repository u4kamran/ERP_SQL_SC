"""FastAPI dependencies for authentication and authorization."""

from typing import List, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository
from app.security.jwt import decode_token

security_scheme = HTTPBearer(auto_error=False)


class CurrentUser:
    def __init__(self, user_id: int, username: str, roles: List[str], permissions: List[str], session_id: str):
        self.user_id = user_id
        self.username = username
        self.roles = roles
        self.permissions = permissions
        self.session_id = session_id

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions or "auth.admin.full" in self.permissions

    def has_role(self, role: str) -> bool:
        return role in self.roles


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> CurrentUser:
    token = None
    if credentials:
        token = credentials.credentials
    elif "access_token" in request.cookies:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")

    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.")

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type.")

    jti = payload.get("jti")
    session_repo = SessionRepository(db)
    if jti and session_repo.is_token_revoked(jti):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked.")

    user_id = int(payload["sub"])
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    if not user or not user.IsActive or user.IsDeleted:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive.")

    return CurrentUser(
        user_id=user_id,
        username=payload.get("username", user.Username),
        roles=payload.get("roles", []),
        permissions=payload.get("permissions", []),
        session_id=payload.get("session_id", ""),
    )


def require_permission(permission: str):
    async def _checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not current_user.has_permission(permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")
        return current_user
    return _checker


def require_any_permission(*permissions: str):
    async def _checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not any(current_user.has_permission(permission) for permission in permissions):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")
        return current_user
    return _checker


def require_report_delivery(
    *view_permissions: str,
    action_permission: str | None = None,
    action_permissions: tuple[str, ...] | None = None,
    denied_detail: str,
):
    """
    Require report View (any of view_permissions) AND any delivery action permission.
    auth.admin.full already bypasses via CurrentUser.has_permission.
    """
    actions = tuple(action_permissions or ())
    if action_permission:
        actions = actions + (action_permission,)
    if not actions:
        raise ValueError("action_permission or action_permissions is required")

    async def _checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not any(current_user.has_permission(permission) for permission in view_permissions):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")
        if not any(current_user.has_permission(permission) for permission in actions):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=denied_detail)
        return current_user

    return _checker


def require_role(role: str):
    async def _checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not current_user.has_role(role) and "SUPER_ADMIN" not in current_user.roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role.")
        return current_user
    return _checker
