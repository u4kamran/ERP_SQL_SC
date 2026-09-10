"""Schemas for System Administration → User Menu Rights."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class MenuRightItem(BaseModel):
    menu_id: int
    menu_code: str
    menu_name: str
    menu_group: str
    parent_menu_code: Optional[str] = None
    path: Optional[str] = None
    icon: Optional[str] = None
    permission_code: Optional[str] = None
    description: Optional[str] = None
    is_group: bool = False
    display_order: int = 0
    can_access: bool = False


class MenuRightGroup(BaseModel):
    title: str
    parent_menu_id: Optional[int] = None
    parent_menu_code: Optional[str] = None
    parent_can_access: bool = False
    items: List[MenuRightItem] = Field(default_factory=list)


class UserMenuRightsResponse(BaseModel):
    user_id: int
    username: str
    full_name: str
    is_system_admin: bool = False
    groups: List[MenuRightGroup] = Field(default_factory=list)
    message: Optional[str] = None


class UserMenuRightSaveItem(BaseModel):
    menu_id: int
    can_access: bool = False


class UserMenuRightsSaveRequest(BaseModel):
    rights: List[UserMenuRightSaveItem] = Field(default_factory=list)


class UserMenuRightsSaveResponse(BaseModel):
    user_id: int
    saved_count: int
    message: str


class UserMenuSessionInfo(BaseModel):
    """Cached on profile after login — used for menu visibility + page guards."""

    enforced: bool = False
    allowed_paths: List[str] = Field(default_factory=list)
    allowed_menu_codes: List[str] = Field(default_factory=list)
