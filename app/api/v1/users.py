"""User management API endpoints."""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, require_permission
from app.database.session import get_db
from app.repositories.user_repository import UserRepository
from app.schemas import (
    AdminResetPasswordRequest,
    MessageResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.services.user_service import UserService

router = APIRouter()


def _to_user_response(user, roles: List) -> UserResponse:
    return UserResponse(
        UserId=user.UserId,
        Username=user.Username,
        Email=user.Email,
        FirstName=user.FirstName,
        LastName=user.LastName,
        PhoneNumber=user.PhoneNumber,
        IsActive=user.IsActive,
        MustChangePassword=user.MustChangePassword,
        LastLoginDate=user.LastLoginDate,
        roles=[r.RoleCode for r in roles],
        role_ids=[r.RoleId for r in roles],
    )


@router.get("/", response_model=List[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 50,
    current_user: CurrentUser = Depends(require_permission("auth.users.view")),
    db: Session = Depends(get_db),
):
    repo = UserRepository(db)
    users = UserService(db).list_users(skip, limit)
    return [_to_user_response(u, repo.get_user_roles(u.UserId)) for u in users]


@router.post("/", response_model=UserResponse, status_code=201)
def create_user(
    data: UserCreate,
    current_user: CurrentUser = Depends(require_permission("auth.users.create")),
    db: Session = Depends(get_db),
):
    user = UserService(db).create_user(data, current_user.user_id)
    roles = UserRepository(db).get_user_roles(user.UserId)
    return _to_user_response(user, roles)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    current_user: CurrentUser = Depends(require_permission("auth.users.view")),
    db: Session = Depends(get_db),
):
    user = UserService(db).get_user(user_id)
    roles = UserRepository(db).get_user_roles(user.UserId)
    return _to_user_response(user, roles)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UserUpdate,
    current_user: CurrentUser = Depends(require_permission("auth.users.update")),
    db: Session = Depends(get_db),
):
    user = UserService(db).update_user(user_id, data, current_user.user_id)
    roles = UserRepository(db).get_user_roles(user.UserId)
    return _to_user_response(user, roles)


@router.post("/{user_id}/reset-password", response_model=MessageResponse)
def admin_reset_password(
    user_id: int,
    data: AdminResetPasswordRequest,
    current_user: CurrentUser = Depends(require_permission("auth.users.update")),
    db: Session = Depends(get_db),
):
    UserService(db).admin_reset_password(
        user_id, data.new_password, current_user.user_id, data.must_change_password
    )
    return MessageResponse(message="Password reset successfully.")


@router.delete("/{user_id}", response_model=MessageResponse)
def delete_user(
    user_id: int,
    current_user: CurrentUser = Depends(require_permission("auth.users.delete")),
    db: Session = Depends(get_db),
):
    UserService(db).soft_delete_user(user_id, current_user.user_id)
    return MessageResponse(message="User deactivated successfully.")
