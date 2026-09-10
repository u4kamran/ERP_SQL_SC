"""Role management API endpoints."""

from typing import List, Set

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, require_permission
from app.database.session import get_db
from app.models.permission import Permission, RolePermission
from app.models.role import Role
from app.schemas import (
    RoleCloneRequest,
    RoleCreate,
    RoleDetailResponse,
    RoleResponse,
    RoleUpdate,
)
from app.schemas.menu_access import (
    MenuAccessCatalogResponse,
    MenuAccessUpdateRequest,
    MenuAccessUpdateResponse,
)
from app.services.menu_access_service import build_menu_access_catalog, save_menu_access

router = APIRouter()

PROTECTED_ROLE_CODES = {"SUPER_ADMIN"}


def _normalize_role_code(code: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in ("_", "-") else "_" for ch in code.strip().upper())
    cleaned = cleaned.replace("-", "_")
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_")


def _active_permission_ids(db: Session, role_id: int) -> List[int]:
    rows = db.execute(
        select(RolePermission.PermissionId).where(
            RolePermission.RoleId == role_id,
            RolePermission.IsDeleted == False,  # noqa: E712
            RolePermission.IsActive == True,  # noqa: E712
        )
    ).scalars().all()
    return list(rows)


def _active_permission_codes(db: Session, role_id: int) -> List[str]:
    rows = db.execute(
        select(Permission.PermissionCode)
        .join(RolePermission, RolePermission.PermissionId == Permission.PermissionId)
        .where(
            RolePermission.RoleId == role_id,
            RolePermission.IsDeleted == False,  # noqa: E712
            RolePermission.IsActive == True,  # noqa: E712
            Permission.IsDeleted == False,  # noqa: E712
            Permission.IsActive == True,  # noqa: E712
        )
        .order_by(Permission.PermissionCode)
    ).scalars().all()
    return list(rows)


def _role_detail(db: Session, role: Role) -> RoleDetailResponse:
    base = RoleResponse.model_validate(role)
    return RoleDetailResponse(
        **base.model_dump(),
        permission_ids=_active_permission_ids(db, role.RoleId),
        permission_codes=_active_permission_codes(db, role.RoleId),
    )


def _set_role_permissions(
    db: Session,
    *,
    role_id: int,
    permission_ids: List[int],
    actor_user_id: int,
) -> None:
    desired: Set[int] = set(int(pid) for pid in permission_ids)
    existing = list(
        db.execute(select(RolePermission).where(RolePermission.RoleId == role_id)).scalars().all()
    )
    for rp in existing:
        if rp.PermissionId in desired:
            rp.IsDeleted = False
            rp.IsActive = True
            rp.ModifiedBy = actor_user_id
            desired.discard(rp.PermissionId)
        else:
            rp.IsDeleted = True
            rp.IsActive = False
            rp.ModifiedBy = actor_user_id
    for perm_id in desired:
        db.add(
            RolePermission(
                RoleId=role_id,
                PermissionId=perm_id,
                CreatedBy=actor_user_id,
            )
        )


@router.get("/", response_model=List[RoleResponse])
def list_roles(
    current_user: CurrentUser = Depends(require_permission("auth.roles.view")),
    db: Session = Depends(get_db),
):
    stmt = select(Role).where(Role.IsDeleted == False).order_by(Role.RoleName)  # noqa: E712
    roles = db.execute(stmt).scalars().all()
    return [RoleResponse.model_validate(r) for r in roles]


@router.get("/{role_id}", response_model=RoleDetailResponse)
def get_role(
    role_id: int,
    current_user: CurrentUser = Depends(require_permission("auth.roles.view")),
    db: Session = Depends(get_db),
):
    role = db.get(Role, role_id)
    if not role or role.IsDeleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")
    return _role_detail(db, role)


@router.get("/{role_id}/menu-access", response_model=MenuAccessCatalogResponse)
def get_role_menu_access(
    role_id: int,
    current_user: CurrentUser = Depends(require_permission("auth.roles.view")),
    db: Session = Depends(get_db),
):
    role = db.get(Role, role_id)
    if not role or role.IsDeleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")
    return build_menu_access_catalog(db, role)


@router.put("/{role_id}/menu-access", response_model=MenuAccessUpdateResponse)
def update_role_menu_access(
    role_id: int,
    body: MenuAccessUpdateRequest,
    current_user: CurrentUser = Depends(require_permission("auth.roles.manage")),
    db: Session = Depends(get_db),
):
    role = db.get(Role, role_id)
    if not role or role.IsDeleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")
    if role.RoleCode == "SUPER_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SUPER_ADMIN already has full access. Menu rights cannot be reduced here.",
        )
    granted = save_menu_access(
        db,
        role=role,
        checked_permission_ids=body.permission_ids,
        actor_user_id=current_user.user_id,
    )
    return MenuAccessUpdateResponse(
        role_id=role_id,
        granted_count=granted,
        message=(
            f"Saved {granted} menu right(s) for role {role.RoleName}. "
            "Users must log in again to refresh the menu."
        ),
    )


@router.post("/", response_model=RoleDetailResponse, status_code=201)
def create_role(
    data: RoleCreate,
    current_user: CurrentUser = Depends(require_permission("auth.roles.manage")),
    db: Session = Depends(get_db),
):
    role_code = _normalize_role_code(data.role_code)
    if not role_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role code.")
    if role_code in PROTECTED_ROLE_CODES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This role code is reserved.")

    existing = db.execute(select(Role).where(Role.RoleCode == role_code)).scalar_one_or_none()
    if existing and not existing.IsDeleted:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role code already exists.")

    if existing and existing.IsDeleted:
        existing.IsDeleted = False
        existing.IsActive = True
        existing.RoleName = data.role_name.strip()
        existing.Description = (data.description or "").strip() or None
        existing.IsSystemRole = False
        existing.ModifiedBy = current_user.user_id
        role = existing
        db.flush()
        _set_role_permissions(
            db,
            role_id=role.RoleId,
            permission_ids=data.permission_ids,
            actor_user_id=current_user.user_id,
        )
    else:
        role = Role(
            RoleCode=role_code,
            RoleName=data.role_name.strip(),
            Description=(data.description or "").strip() or None,
            IsSystemRole=False,
            CreatedBy=current_user.user_id,
        )
        db.add(role)
        db.flush()
        _set_role_permissions(
            db,
            role_id=role.RoleId,
            permission_ids=data.permission_ids,
            actor_user_id=current_user.user_id,
        )

    db.commit()
    db.refresh(role)
    return _role_detail(db, role)


@router.put("/{role_id}", response_model=RoleDetailResponse)
def update_role(
    role_id: int,
    data: RoleUpdate,
    current_user: CurrentUser = Depends(require_permission("auth.roles.manage")),
    db: Session = Depends(get_db),
):
    role = db.get(Role, role_id)
    if not role or role.IsDeleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")

    if role.RoleCode in PROTECTED_ROLE_CODES and data.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SUPER_ADMIN cannot be deactivated.",
        )

    if data.role_name is not None:
        role.RoleName = data.role_name.strip()
    if data.description is not None:
        role.Description = data.description.strip() or None
    if data.is_active is not None:
        role.IsActive = data.is_active
    if data.permission_ids is not None:
        if role.RoleCode in PROTECTED_ROLE_CODES and not data.permission_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SUPER_ADMIN must keep at least one permission.",
            )
        _set_role_permissions(
            db,
            role_id=role_id,
            permission_ids=data.permission_ids,
            actor_user_id=current_user.user_id,
        )

    role.ModifiedBy = current_user.user_id
    db.commit()
    db.refresh(role)
    return _role_detail(db, role)


@router.post("/{role_id}/clone", response_model=RoleDetailResponse, status_code=201)
def clone_role(
    role_id: int,
    data: RoleCloneRequest,
    current_user: CurrentUser = Depends(require_permission("auth.roles.manage")),
    db: Session = Depends(get_db),
):
    source = db.get(Role, role_id)
    if not source or source.IsDeleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")

    role_code = _normalize_role_code(data.role_code)
    if not role_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role code.")
    if role_code in PROTECTED_ROLE_CODES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This role code is reserved.")

    existing = db.execute(select(Role).where(Role.RoleCode == role_code)).scalar_one_or_none()
    if existing and not existing.IsDeleted:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role code already exists.")

    permission_ids = _active_permission_ids(db, source.RoleId)
    description = data.description if data.description is not None else source.Description

    if existing and existing.IsDeleted:
        existing.IsDeleted = False
        existing.IsActive = True
        existing.RoleName = data.role_name.strip()
        existing.Description = (description or "").strip() or None
        existing.IsSystemRole = False
        existing.ModifiedBy = current_user.user_id
        role = existing
        db.flush()
    else:
        role = Role(
            RoleCode=role_code,
            RoleName=data.role_name.strip(),
            Description=(description or "").strip() or None,
            IsSystemRole=False,
            CreatedBy=current_user.user_id,
        )
        db.add(role)
        db.flush()

    _set_role_permissions(
        db,
        role_id=role.RoleId,
        permission_ids=permission_ids,
        actor_user_id=current_user.user_id,
    )
    db.commit()
    db.refresh(role)
    return _role_detail(db, role)


@router.delete("/{role_id}", status_code=status.HTTP_200_OK)
def delete_role(
    role_id: int,
    current_user: CurrentUser = Depends(require_permission("auth.roles.manage")),
    db: Session = Depends(get_db),
):
    role = db.get(Role, role_id)
    if not role or role.IsDeleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")
    if role.IsSystemRole or role.RoleCode in PROTECTED_ROLE_CODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="System roles cannot be deleted. Deactivate instead if needed.",
        )

    role.IsDeleted = True
    role.IsActive = False
    role.ModifiedBy = current_user.user_id
    _set_role_permissions(db, role_id=role_id, permission_ids=[], actor_user_id=current_user.user_id)
    db.commit()
    return {"message": f"Role {role.RoleCode} deleted.", "role_id": role_id}
