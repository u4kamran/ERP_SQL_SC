"""Schemas for role menu-access rights."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class MenuAccessAction(BaseModel):
    """One CRUD action tied to a menu (View / Add / Edit / Delete)."""

    action: str  # view | create | edit | delete
    label: str  # View | Add | Edit | Delete
    permission_code: str
    permission_id: Optional[int] = None
    permission_found: bool = False
    granted: bool = False


class MenuAccessItem(BaseModel):
    label: str
    path: str
    icon: str = ""
    description: str = ""
    group: str
    permission_code: str
    permission_id: Optional[int] = None
    permission_found: bool = False
    granted: bool = False
    actions: List[MenuAccessAction] = Field(default_factory=list)


class MenuAccessGroup(BaseModel):
    title: str
    items: List[MenuAccessItem] = Field(default_factory=list)


class MenuAccessCatalogResponse(BaseModel):
    role_id: int
    role_code: str
    role_name: str
    is_system_role: bool = False
    groups: List[MenuAccessGroup] = Field(default_factory=list)
    missing_permissions: List[str] = Field(default_factory=list)


class MenuAccessUpdateRequest(BaseModel):
    permission_ids: List[int] = Field(default_factory=list)


class MenuAccessUpdateResponse(BaseModel):
    role_id: int
    granted_count: int
    message: str = "Menu access rights saved."
