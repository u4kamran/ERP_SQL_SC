"""Permission API endpoints."""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, require_any_permission
from app.database.session import get_db
from app.models.permission import Permission
from app.schemas import PermissionResponse

router = APIRouter()


@router.get("/", response_model=List[PermissionResponse])
def list_permissions(
    current_user: CurrentUser = Depends(
        require_any_permission("auth.permissions.view", "auth.roles.manage")
    ),
    db: Session = Depends(get_db),
):
    stmt = select(Permission).where(
        Permission.IsDeleted == False,  # noqa: E712
        Permission.IsActive == True,  # noqa: E712
    ).order_by(Permission.PermissionCode)
    permissions = db.execute(stmt).scalars().all()
    return [PermissionResponse.model_validate(p) for p in permissions]
