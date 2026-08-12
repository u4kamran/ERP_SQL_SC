"""User menu rights — sync menus, grant per user, session cache helpers."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.config.site_links import get_internal_link_groups
from app.models.menu import Menu, UserMenuRight
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user_menu_rights import (
    MenuRightGroup,
    MenuRightItem,
    UserMenuRightsResponse,
    UserMenuRightSaveItem,
    UserMenuSessionInfo,
)
from app.utils.auth_flags import is_super_admin


ALWAYS_ALLOWED_PATHS = {
    "/dashboard",
    "/admin/profile",
    "/admin/change-password",
}


def ensure_user_menu_tables(db: Session) -> None:
    """Create Menus / UserMenuRights if missing (idempotent, SQL Server 2008+)."""
    statements = [
        """
        IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[auth].[Menus]') AND type = 'U')
        CREATE TABLE [auth].[Menus] (
            [MenuId] INT IDENTITY(1,1) NOT NULL,
            [MenuCode] NVARCHAR(120) NOT NULL,
            [MenuName] NVARCHAR(150) NOT NULL,
            [MenuGroup] NVARCHAR(100) NOT NULL,
            [ParentMenuCode] NVARCHAR(120) NULL,
            [Path] NVARCHAR(255) NULL,
            [IconClass] NVARCHAR(100) NULL,
            [PermissionCode] NVARCHAR(100) NULL,
            [Description] NVARCHAR(500) NULL,
            [DisplayOrder] INT NOT NULL CONSTRAINT [DF_Menus_DisplayOrder] DEFAULT (0),
            [IsGroup] BIT NOT NULL CONSTRAINT [DF_Menus_IsGroup] DEFAULT (0),
            [CreatedDate] DATETIME NOT NULL CONSTRAINT [DF_Menus_CreatedDate] DEFAULT (GETUTCDATE()),
            [CreatedBy] INT NULL,
            [ModifiedDate] DATETIME NULL,
            [ModifiedBy] INT NULL,
            [IsActive] BIT NOT NULL CONSTRAINT [DF_Menus_IsActive] DEFAULT (1),
            [IsDeleted] BIT NOT NULL CONSTRAINT [DF_Menus_IsDeleted] DEFAULT (0),
            [RowVersion] ROWVERSION NOT NULL,
            CONSTRAINT [PK_Menus] PRIMARY KEY CLUSTERED ([MenuId]),
            CONSTRAINT [UQ_Menus_MenuCode] UNIQUE ([MenuCode])
        )
        """,
        """
        IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[auth].[UserMenuRights]') AND type = 'U')
        CREATE TABLE [auth].[UserMenuRights] (
            [UserMenuRightId] INT IDENTITY(1,1) NOT NULL,
            [UserId] INT NOT NULL,
            [MenuId] INT NOT NULL,
            [CanAccess] BIT NOT NULL CONSTRAINT [DF_UserMenuRights_CanAccess] DEFAULT (0),
            [CreatedDate] DATETIME NOT NULL CONSTRAINT [DF_UserMenuRights_CreatedDate] DEFAULT (GETUTCDATE()),
            [CreatedBy] INT NULL,
            [ModifiedDate] DATETIME NULL,
            [ModifiedBy] INT NULL,
            [IsActive] BIT NOT NULL CONSTRAINT [DF_UserMenuRights_IsActive] DEFAULT (1),
            [IsDeleted] BIT NOT NULL CONSTRAINT [DF_UserMenuRights_IsDeleted] DEFAULT (0),
            [RowVersion] ROWVERSION NOT NULL,
            CONSTRAINT [PK_UserMenuRights] PRIMARY KEY CLUSTERED ([UserMenuRightId]),
            CONSTRAINT [FK_UserMenuRights_Users] FOREIGN KEY ([UserId]) REFERENCES [auth].[Users]([UserId]),
            CONSTRAINT [FK_UserMenuRights_Menus] FOREIGN KEY ([MenuId]) REFERENCES [auth].[Menus]([MenuId]),
            CONSTRAINT [UQ_UserMenuRights_UserMenu] UNIQUE ([UserId], [MenuId])
        )
        """,
    ]
    for sql in statements:
        db.execute(text(sql))
    db.commit()


def _group_code(title: str) -> str:
    safe = "".join(ch if ch.isalnum() else "_" for ch in title.strip()).strip("_")
    return f"group:{safe or 'main'}".lower()


def sync_menus_from_site_links(db: Session, *, actor_user_id: int | None = None) -> int:
    """Upsert menu catalog from site_links registry. Returns menu row count."""
    ensure_user_menu_tables(db)
    order = 0
    touched = 0
    for group in get_internal_link_groups():
        title = group["title"]
        parent_code = _group_code(title)
        order += 10
        parent = db.execute(
            select(Menu).where(Menu.MenuCode == parent_code)
        ).scalar_one_or_none()
        if parent is None:
            parent = Menu(
                MenuCode=parent_code,
                MenuName=title,
                MenuGroup=title,
                ParentMenuCode=None,
                Path=None,
                IconClass="bi-folder",
                PermissionCode=None,
                Description=f"{title} menu group",
                DisplayOrder=order,
                IsGroup=True,
                CreatedBy=actor_user_id,
            )
            db.add(parent)
        else:
            parent.MenuName = title
            parent.MenuGroup = title
            parent.IsGroup = True
            parent.IsDeleted = False
            parent.IsActive = True
            parent.DisplayOrder = order
            parent.ModifiedBy = actor_user_id
            parent.ModifiedDate = datetime.utcnow()
        touched += 1

        for link in group["links"]:
            path = (link.get("path") or "").strip()
            if not path:
                continue
            code = f"menu:{path}"
            order += 1
            row = db.execute(select(Menu).where(Menu.MenuCode == code)).scalar_one_or_none()
            if row is None:
                db.add(
                    Menu(
                        MenuCode=code,
                        MenuName=link.get("label") or path,
                        MenuGroup=title,
                        ParentMenuCode=parent_code,
                        Path=path,
                        IconClass=link.get("icon"),
                        PermissionCode=(link.get("permission") or None),
                        Description=link.get("description"),
                        DisplayOrder=order,
                        IsGroup=False,
                        CreatedBy=actor_user_id,
                    )
                )
            else:
                row.MenuName = link.get("label") or path
                row.MenuGroup = title
                row.ParentMenuCode = parent_code
                row.Path = path
                row.IconClass = link.get("icon")
                row.PermissionCode = link.get("permission") or None
                row.Description = link.get("description")
                row.DisplayOrder = order
                row.IsGroup = False
                row.IsDeleted = False
                row.IsActive = True
                row.ModifiedBy = actor_user_id
                row.ModifiedDate = datetime.utcnow()
            touched += 1
    db.commit()
    return touched


def user_is_system_admin(db: Session, user_id: int) -> bool:
    repo = UserRepository(db)
    roles = [r.RoleCode for r in repo.get_user_roles(user_id)]
    permissions = repo.get_user_permissions(user_id)
    return is_super_admin(roles, permissions)


def get_session_menu_info(db: Session, user_id: int) -> UserMenuSessionInfo:
    """Load once after login / profile — cached in Auth.profile on the client."""
    if user_is_system_admin(db, user_id):
        menus = db.execute(
            select(Menu).where(
                Menu.IsDeleted == False,  # noqa: E712
                Menu.IsActive == True,  # noqa: E712
                Menu.IsGroup == False,  # noqa: E712
            )
        ).scalars().all()
        return UserMenuSessionInfo(
            enforced=False,
            allowed_paths=sorted(
                {*(ALWAYS_ALLOWED_PATHS), *[m.Path for m in menus if m.Path]}
            ),
            allowed_menu_codes=sorted(m.MenuCode for m in menus),
        )

    rights = db.execute(
        select(UserMenuRight).where(
            UserMenuRight.UserId == user_id,
            UserMenuRight.IsDeleted == False,  # noqa: E712
        )
    ).scalars().all()
    if not rights:
        # No dedicated rights yet — fall back to role/feature permissions (not enforced).
        return UserMenuSessionInfo(enforced=False, allowed_paths=[], allowed_menu_codes=[])

    allowed_ids = {r.MenuId for r in rights if r.CanAccess}
    menus = db.execute(
        select(Menu).where(
            Menu.MenuId.in_(allowed_ids) if allowed_ids else False,
            Menu.IsDeleted == False,  # noqa: E712
            Menu.IsActive == True,  # noqa: E712
        )
    ).scalars().all() if allowed_ids else []

    paths = sorted(
        {
            *ALWAYS_ALLOWED_PATHS,
            *[m.Path for m in menus if m.Path and not m.IsGroup],
        }
    )
    codes = sorted(m.MenuCode for m in menus)
    return UserMenuSessionInfo(
        enforced=True,
        allowed_paths=paths,
        allowed_menu_codes=codes,
    )


def build_user_menu_rights_form(db: Session, user: User) -> UserMenuRightsResponse:
    sync_menus_from_site_links(db)
    admin = user_is_system_admin(db, user.UserId)
    menus = db.execute(
        select(Menu).where(
            Menu.IsDeleted == False,  # noqa: E712
            Menu.IsActive == True,  # noqa: E712
        ).order_by(Menu.DisplayOrder, Menu.MenuName)
    ).scalars().all()

    rights_map = {
        r.MenuId: bool(r.CanAccess)
        for r in db.execute(
            select(UserMenuRight).where(
                UserMenuRight.UserId == user.UserId,
                UserMenuRight.IsDeleted == False,  # noqa: E712
            )
        ).scalars().all()
    }

    groups_by_code: dict[str, MenuRightGroup] = {}
    for menu in menus:
        if menu.IsGroup:
            groups_by_code[menu.MenuCode] = MenuRightGroup(
                title=menu.MenuName,
                parent_menu_id=menu.MenuId,
                parent_menu_code=menu.MenuCode,
                parent_can_access=admin or rights_map.get(menu.MenuId, False),
                items=[],
            )

    for menu in menus:
        if menu.IsGroup:
            continue
        parent_code = menu.ParentMenuCode or _group_code(menu.MenuGroup)
        group = groups_by_code.get(parent_code)
        if group is None:
            group = MenuRightGroup(
                title=menu.MenuGroup,
                parent_menu_id=None,
                parent_menu_code=parent_code,
                parent_can_access=False,
                items=[],
            )
            groups_by_code[parent_code] = group
        group.items.append(
            MenuRightItem(
                menu_id=menu.MenuId,
                menu_code=menu.MenuCode,
                menu_name=menu.MenuName,
                menu_group=menu.MenuGroup,
                parent_menu_code=menu.ParentMenuCode,
                path=menu.Path,
                icon=menu.IconClass,
                permission_code=menu.PermissionCode,
                description=menu.Description,
                is_group=False,
                display_order=menu.DisplayOrder,
                can_access=True if admin else rights_map.get(menu.MenuId, False),
            )
        )

    # Preserve site_links group order
    ordered: list[MenuRightGroup] = []
    for group in get_internal_link_groups():
        code = _group_code(group["title"])
        if code in groups_by_code:
            ordered.append(groups_by_code.pop(code))
    ordered.extend(groups_by_code.values())

    return UserMenuRightsResponse(
        user_id=user.UserId,
        username=user.Username,
        full_name=user.full_name,
        is_system_admin=admin,
        groups=ordered,
        message=(
            "System Administrator always has full menu access."
            if admin
            else None
        ),
    )


def save_user_menu_rights(
    db: Session,
    *,
    user: User,
    rights: list[UserMenuRightSaveItem],
    actor_user_id: int,
) -> int:
    if user_is_system_admin(db, user.UserId):
        raise ValueError(
            "System Administrator always has full access. Menu rights cannot be changed."
        )

    sync_menus_from_site_links(db, actor_user_id=actor_user_id)
    valid_ids = {
        m.MenuId
        for m in db.execute(
            select(Menu).where(
                Menu.IsDeleted == False,  # noqa: E712
                Menu.IsActive == True,  # noqa: E712
            )
        ).scalars().all()
    }

    # Deduplicate by menu_id (last write wins)
    desired: dict[int, bool] = {}
    for item in rights:
        if item.menu_id in valid_ids:
            desired[int(item.menu_id)] = bool(item.can_access)

    existing = {
        r.MenuId: r
        for r in db.execute(
            select(UserMenuRight).where(UserMenuRight.UserId == user.UserId)
        ).scalars().all()
    }

    saved = 0
    now = datetime.utcnow()
    for menu_id, can_access in desired.items():
        row = existing.get(menu_id)
        if row is None:
            db.add(
                UserMenuRight(
                    UserId=user.UserId,
                    MenuId=menu_id,
                    CanAccess=can_access,
                    CreatedBy=actor_user_id,
                )
            )
            saved += 1
            continue
        row.CanAccess = can_access
        row.IsDeleted = False
        row.IsActive = True
        row.ModifiedBy = actor_user_id
        row.ModifiedDate = now
        saved += 1

    # Soft-delete rights for menus no longer in desired set (keep uniqueness)
    for menu_id, row in existing.items():
        if menu_id not in desired and not row.IsDeleted:
            row.IsDeleted = True
            row.ModifiedBy = actor_user_id
            row.ModifiedDate = now

    db.commit()
    return saved


def path_is_allowed(session_info: UserMenuSessionInfo, path: str) -> bool:
    if not session_info.enforced:
        return True
    clean = (path or "").split("?", 1)[0].rstrip("/") or "/"
    if clean in ALWAYS_ALLOWED_PATHS:
        return True
    allowed = {p.rstrip("/") or "/" for p in session_info.allowed_paths}
    if clean in allowed:
        return True
    # Child routes of a granted menu (e.g. /admin/fin-inv-order/print/600)
    for base in allowed:
        if base != "/" and (clean == base or clean.startswith(base + "/")):
            return True
    return False
