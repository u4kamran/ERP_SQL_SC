"""User profile API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_current_user, require_permission
from app.database.session import get_db
from app.models.user import UserPreference
from app.repositories.user_repository import UserRepository
from app.schemas import MessageResponse, PreferenceUpdate, ProfileResponse, ProfileUpdate, UserUpdate
from app.services.user_service import UserService
from app.services.user_menu_rights_service import get_session_menu_info
from app.utils.auth_flags import is_super_admin

router = APIRouter()


@router.get("/", response_model=ProfileResponse)
def get_profile(
    current_user: CurrentUser = Depends(require_permission("auth.profile.view")),
    db: Session = Depends(get_db),
):
    user = UserRepository(db).get_by_id(current_user.user_id)
    user_repo = UserRepository(db)
    roles = [r.RoleCode for r in user_repo.get_user_roles(user.UserId)]
    permissions = user_repo.get_user_permissions(user.UserId)
    prefs_stmt = select(UserPreference).where(
        UserPreference.UserId == current_user.user_id,
        UserPreference.IsDeleted == False,  # noqa: E712
    )
    prefs = {p.PreferenceKey: p.PreferenceValue for p in db.execute(prefs_stmt).scalars()}
    menu_info = get_session_menu_info(db, user.UserId)

    return ProfileResponse(
        user_id=user.UserId,
        username=user.Username,
        email=user.Email,
        first_name=user.FirstName,
        last_name=user.LastName,
        phone_number=user.PhoneNumber,
        profile_image_url=user.ProfileImageUrl,
        roles=roles,
        permissions=permissions,
        is_super_admin=is_super_admin(roles, permissions),
        preferences=prefs,
        menu_access_enforced=menu_info.enforced,
        allowed_menu_paths=menu_info.allowed_paths,
        allowed_menu_codes=menu_info.allowed_menu_codes,
    )


@router.put("/", response_model=MessageResponse)
def update_profile(
    data: ProfileUpdate,
    current_user: CurrentUser = Depends(require_permission("auth.profile.update")),
    db: Session = Depends(get_db),
):
    UserService(db).update_user(
        current_user.user_id,
        UserUpdate(
            first_name=data.first_name,
            last_name=data.last_name,
            phone_number=data.phone_number,
        ),
        current_user.user_id,
    )
    return MessageResponse(message="Profile updated successfully.")


@router.put("/preferences", response_model=MessageResponse)
def update_preferences(
    data: PreferenceUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pref_map = {
        "theme": data.theme,
        "language": data.language,
        "timezone": data.timezone,
    }
    for key, value in pref_map.items():
        if value is not None:
            existing = db.execute(
                select(UserPreference).where(
                    UserPreference.UserId == current_user.user_id,
                    UserPreference.PreferenceKey == key,
                )
            ).scalar_one_or_none()
            if existing:
                existing.PreferenceValue = value
            else:
                db.add(UserPreference(
                    UserId=current_user.user_id,
                    PreferenceKey=key,
                    PreferenceValue=value,
                    CreatedBy=current_user.user_id,
                ))
    db.commit()
    return MessageResponse(message="Preferences updated.")
