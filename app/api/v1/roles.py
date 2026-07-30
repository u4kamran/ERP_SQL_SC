"""Role management API endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, require_permission
from app.database.session import get_db
from app.models.permission import Permission, RolePermission
from app.models.role import Role
from app.schemas import MessageResponse, RoleCreate, RoleResponse, RoleUpdate

router = APIRouter()


@router.get("/", response_model=List[RoleResponse])
def list_roles(
    current_user: CurrentUser = Depends(require_permission("auth.roles.view")),
    db: Session = Depends(get_db),
):
    stmt = select(Role).where(Role.IsDeleted == False).order_by(Role.RoleName)  # noqa: E712
    roles = db.execute(stmt).scalars().all()
    return [RoleResponse.model_validate(r) for r in roles]


@router.post("/", response_model=RoleResponse, status_code=201)
def create_role(
    data: RoleCreate,
    current_user: CurrentUser = Depends(require_permission("auth.roles.manage")),
    db: Session = Depends(get_db),
):
    existing = db.execute(select(Role).where(Role.RoleCode == data.role_code)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role code already exists.")

    role = Role(
        RoleCode=data.role_code,
        RoleName=data.role_name,
        Description=data.description,
        CreatedBy=current_user.user_id,
    )
    db.add(role)
    db.flush()

    for perm_id in data.permission_ids:
        db.add(RolePermission(RoleId=role.RoleId, PermissionId=perm_id, CreatedBy=current_user.user_id))

    db.commit()
    db.refresh(role)
    return RoleResponse.model_validate(role)


@router.put("/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: int,
    data: RoleUpdate,
    current_user: CurrentUser = Depends(require_permission("auth.roles.manage")),
    db: Session = Depends(get_db),
):
    role = db.get(Role, role_id)
    if not role or role.IsDeleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")

    if data.role_name is not None:
        role.RoleName = data.role_name
    if data.description is not None:
        role.Description = data.description
    if data.is_active is not None:
        role.IsActive = data.is_active
    if data.permission_ids is not None:
        db.execute(
            select(RolePermission).where(RolePermission.RoleId == role_id)
        )
        for rp in db.execute(select(RolePermission).where(RolePermission.RoleId == role_id)).scalars():
            rp.IsDeleted = True
        for perm_id in data.permission_ids:
            db.add(RolePermission(RoleId=role_id, PermissionId=perm_id, CreatedBy=current_user.user_id))

    role.ModifiedBy = current_user.user_id
    db.commit()
    db.refresh(role)
    return RoleResponse.model_validate(role)
