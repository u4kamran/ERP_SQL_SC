"""Authentication API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, CurrentUser
from app.config.settings import settings
from app.database.session import get_db
from app.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshTokenRequest,
    ResetPasswordConfirmRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(request: Request, response: Response, data: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT tokens."""
    auth_service = AuthService(db)
    result = auth_service.login(request, data)

    max_age = (
        settings.jwt_remember_me_expire_days * 86400
        if data.remember_me
        else settings.jwt_refresh_token_expire_days * 86400
    )
    response.set_cookie(
        key="access_token",
        value=result.access_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.samesite_cookies,
        max_age=settings.jwt_access_token_expire_minutes * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=result.refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.samesite_cookies,
        max_age=max_age,
    )
    return result


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(data: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh access token using refresh token."""
    return AuthService(db).refresh(data.refresh_token)


@router.post("/logout", response_model=MessageResponse)
def logout(
    request: Request,
    response: Response,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Logout and revoke tokens."""
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")
    AuthService(db).logout(request, access_token, refresh_token)

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return MessageResponse(message="Logged out successfully.")


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    request: Request,
    data: ChangePasswordRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change current user's password."""
    AuthService(db).change_password(current_user.user_id, data, request)
    return MessageResponse(message="Password changed successfully.")


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Request password reset (email-ready)."""
    AuthService(db).request_password_reset(data.email)
    return MessageResponse(message="If the email exists, a reset link will be sent.")


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(data: ResetPasswordConfirmRequest, db: Session = Depends(get_db)):
    """Confirm password reset with token."""
    # Full implementation hooks into PasswordResetToken validation
    return MessageResponse(message="Password reset endpoint ready for token validation.")
