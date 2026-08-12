"""Role menu-access service — grant/hide admin menu items per role."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.site_links import get_internal_link_groups
from app.models.permission import Permission, RolePermission
from app.models.role import Role
from app.schemas.menu_access import (
    MenuAccessAction,
    MenuAccessCatalogResponse,
    MenuAccessGroup,
    MenuAccessItem,
)

# Sidebar links use *.view — also manage sibling CRUD codes for the same feature.
_ACTION_SPECS = (
    ("view", "View"),
    ("create", "Add"),
    ("edit", "Edit"),
    ("delete", "Delete"),
)


def _action_codes_for_view(view_code: str) -> list[tuple[str, str, str]]:
    """Return (action, label, permission_code) for view/create/edit/delete."""
    code = (view_code or "").strip()
    if not code:
        return []
    if code.endswith(".view"):
        stem = code[: -len(".view")]
        return [(action, label, f"{stem}.{action}") for action, label in _ACTION_SPECS]
    # Non-standard codes: only the exact permission (treat as View)
    return [("view", "View", code)]


def menu_permission_codes() -> list[str]:
    """Unique permission codes managed by Menu Access (view + Add/Edit/Delete)."""
    codes: list[str] = []
    seen: set[str] = set()
    for group in get_internal_link_groups():
        for link in group["links"]:
            view_code = (link.get("permission") or "").strip()
            if not view_code:
                continue
            for _action, _label, code in _action_codes_for_view(view_code):
                if code not in seen:
                    seen.add(code)
                    codes.append(code)
    return codes


def _permission_map(db: Session) -> dict[str, Permission]:
    codes = menu_permission_codes()
    if not codes:
        return {}
    rows = db.execute(
        select(Permission).where(
            Permission.PermissionCode.in_(codes),
            Permission.IsDeleted == False,  # noqa: E712
        )
    ).scalars().all()
    return {p.PermissionCode: p for p in rows}


def _active_role_permission_ids(db: Session, role_id: int) -> set[int]:
    rows = db.execute(
        select(RolePermission.PermissionId).where(
            RolePermission.RoleId == role_id,
            RolePermission.IsDeleted == False,  # noqa: E712
        )
    ).scalars().all()
    return set(rows)


def build_menu_access_catalog(db: Session, role: Role) -> MenuAccessCatalogResponse:
    perm_by_code = _permission_map(db)
    granted_ids = _active_role_permission_ids(db, role.RoleId)
    groups: list[MenuAccessGroup] = []
    missing: list[str] = []

    for group in get_internal_link_groups():
        items: list[MenuAccessItem] = []
        for link in group["links"]:
            view_code = (link.get("permission") or "").strip()
            if not view_code:
                # Always-visible account items (Dashboard/Profile/Password) are not grantable.
                continue

            actions: list[MenuAccessAction] = []
            for action, label, code in _action_codes_for_view(view_code):
                perm = perm_by_code.get(code)
                # Only flag missing View permissions in the banner (CRUD may not exist for every menu).
                if not perm and action == "view" and code not in missing:
                    missing.append(code)
                actions.append(
                    MenuAccessAction(
                        action=action,
                        label=label,
                        permission_code=code,
                        permission_id=perm.PermissionId if perm else None,
                        permission_found=bool(perm),
                        granted=bool(perm and perm.PermissionId in granted_ids),
                    )
                )

            view_action = next((a for a in actions if a.action == "view"), None)
            view_perm = perm_by_code.get(view_code)
            items.append(
                MenuAccessItem(
                    label=link.get("label") or view_code,
                    path=link.get("path") or "",
                    icon=link.get("icon") or "",
                    description=link.get("description") or "",
                    group=group["title"],
                    permission_code=view_code,
                    permission_id=view_perm.PermissionId if view_perm else (
                        view_action.permission_id if view_action else None
                    ),
                    permission_found=bool(view_perm) if view_perm is not None else bool(
                        view_action and view_action.permission_found
                    ),
                    granted=bool(view_action and view_action.granted),
                    actions=actions,
                )
            )
        if items:
            groups.append(MenuAccessGroup(title=group["title"], items=items))

    # De-dupe missing while preserving order
    seen_m: set[str] = set()
    missing_unique: list[str] = []
    for code in missing:
        if code not in seen_m:
            seen_m.add(code)
            missing_unique.append(code)

    return MenuAccessCatalogResponse(
        role_id=role.RoleId,
        role_code=role.RoleCode,
        role_name=role.RoleName,
        is_system_role=bool(role.IsSystemRole),
        groups=groups,
        missing_permissions=missing_unique,
    )


def save_menu_access(
    db: Session,
    *,
    role: Role,
    checked_permission_ids: list[int],
    actor_user_id: int,
) -> int:
    """
    Update menu-linked permissions for a role (View / Add / Edit / Delete).
    Non-menu permissions (API-only, admin.full, etc.) are preserved.
    """
    perm_by_code = _permission_map(db)
    menu_ids = {p.PermissionId for p in perm_by_code.values()}
    checked = {int(pid) for pid in checked_permission_ids if int(pid) in menu_ids}

    # Current active permissions
    current_rows = db.execute(
        select(RolePermission).where(RolePermission.RoleId == role.RoleId)
    ).scalars().all()

    active_ids = {
        rp.PermissionId for rp in current_rows if not rp.IsDeleted
    }
    non_menu_active = {pid for pid in active_ids if pid not in menu_ids}
    desired = non_menu_active | checked

    # Soft-delete active grants that should go away
    for rp in current_rows:
        if rp.IsDeleted:
            continue
        if rp.PermissionId not in desired:
            rp.IsDeleted = True
            rp.ModifiedBy = actor_user_id

    # Restore soft-deleted or insert missing desired grants
    by_perm: dict[int, list[RolePermission]] = {}
    for rp in current_rows:
        by_perm.setdefault(rp.PermissionId, []).append(rp)

    for pid in desired:
        existing = by_perm.get(pid) or []
        active = next((rp for rp in existing if not rp.IsDeleted), None)
        if active:
            continue
        soft = next((rp for rp in existing if rp.IsDeleted), None)
        if soft:
            soft.IsDeleted = False
            soft.ModifiedBy = actor_user_id
            continue
        db.add(
            RolePermission(
                RoleId=role.RoleId,
                PermissionId=pid,
                CreatedBy=actor_user_id,
            )
        )

    role.ModifiedBy = actor_user_id
    db.commit()
    return len(checked)
