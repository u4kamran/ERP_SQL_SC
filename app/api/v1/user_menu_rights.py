"""System Administration — User Menu Rights API."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, require_permission
from app.database.session import get_db
from app.models.user import User
from app.schemas.user_menu_rights import (
    UserMenuRightsResponse,
    UserMenuRightsSaveRequest,
    UserMenuRightsSaveResponse,
)
from app.services.user_menu_rights_service import (
    build_user_menu_rights_form,
    ensure_user_menu_tables,
    save_user_menu_rights,
    sync_menus_from_site_links,
)

router = APIRouter()


def _get_user_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if not user or user.IsDeleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return user


@router.post("/sync-menus")
def sync_menus(
    current_user: CurrentUser = Depends(require_permission("auth.roles.manage")),
    db: Session = Depends(get_db),
):
    ensure_user_menu_tables(db)
    count = sync_menus_from_site_links(db, actor_user_id=current_user.user_id)
    return {"message": f"Synced {count} menu rows from application menu registry."}


@router.get("/users")
def list_users_for_menu_rights(
    current_user: CurrentUser = Depends(require_permission("auth.roles.manage")),
    db: Session = Depends(get_db),
):
    """Compact user list for the rights form dropdown."""
    users = db.execute(
        select(User).where(
            User.IsDeleted == False,  # noqa: E712
        ).order_by(User.Username)
    ).scalars().all()
    return [
        {
            "user_id": u.UserId,
            "username": u.Username,
            "full_name": u.full_name,
            "is_active": bool(u.IsActive),
        }
        for u in users
    ]


@router.get("/users/{user_id}", response_model=UserMenuRightsResponse)
def get_user_menu_rights(
    user_id: int,
    current_user: CurrentUser = Depends(require_permission("auth.roles.manage")),
    db: Session = Depends(get_db),
):
    user = _get_user_or_404(db, user_id)
    try:
        return build_user_menu_rights_form(db, user)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not load menu rights: {exc}",
        ) from exc


@router.put("/users/{user_id}", response_model=UserMenuRightsSaveResponse)
def put_user_menu_rights(
    user_id: int,
    body: UserMenuRightsSaveRequest,
    current_user: CurrentUser = Depends(require_permission("auth.roles.manage")),
    db: Session = Depends(get_db),
):
    user = _get_user_or_404(db, user_id)
    try:
        saved = save_user_menu_rights(
            db,
            user=user,
            rights=body.rights,
            actor_user_id=current_user.user_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save menu rights: {exc}",
        ) from exc

    return UserMenuRightsSaveResponse(
        user_id=user_id,
        saved_count=saved,
        message=(
            f"Saved menu rights for {user.Username}. "
            "User must log in again to refresh the menu."
        ),
    )
