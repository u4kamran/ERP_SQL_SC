"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.datetime_types import OptionalUtcDatetime, UtcDatetime


class MessageResponse(BaseModel):
    message: str
    success: bool = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    must_change_password: bool = False


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1)
    remember_me: bool = False


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class ResetPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordConfirmRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=30)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    role_ids: List[int] = []


class AdminResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=8)
    must_change_password: bool = True


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=30)
    is_active: Optional[bool] = None
    role_ids: Optional[List[int]] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int = Field(validation_alias="UserId")
    username: str = Field(validation_alias="Username")
    email: str = Field(validation_alias="Email")
    first_name: Optional[str] = Field(None, validation_alias="FirstName")
    last_name: Optional[str] = Field(None, validation_alias="LastName")
    phone_number: Optional[str] = Field(None, validation_alias="PhoneNumber")
    is_active: bool = Field(validation_alias="IsActive")
    must_change_password: bool = Field(validation_alias="MustChangePassword")
    last_login_date: OptionalUtcDatetime = Field(None, validation_alias="LastLoginDate")
    roles: List[str] = []
    role_ids: List[int] = []


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role_id: int = Field(validation_alias="RoleId")
    role_code: str = Field(validation_alias="RoleCode")
    role_name: str = Field(validation_alias="RoleName")
    description: Optional[str] = Field(None, validation_alias="Description")
    is_system_role: bool = Field(validation_alias="IsSystemRole")
    is_active: bool = Field(validation_alias="IsActive")


class RoleDetailResponse(RoleResponse):
    permission_ids: List[int] = []
    permission_codes: List[str] = []


class RoleCreate(BaseModel):
    role_code: str = Field(..., min_length=2, max_length=50)
    role_name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    permission_ids: List[int] = []


class RoleUpdate(BaseModel):
    role_name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    permission_ids: Optional[List[int]] = None


class RoleCloneRequest(BaseModel):
    role_code: str = Field(..., min_length=2, max_length=50)
    role_name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    permission_id: int = Field(validation_alias="PermissionId")
    permission_code: str = Field(validation_alias="PermissionCode")
    permission_name: str = Field(validation_alias="PermissionName")
    description: Optional[str] = Field(None, validation_alias="Description")
    module_id: Optional[int] = Field(None, validation_alias="ModuleId")


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: UUID = Field(validation_alias="SessionId")
    ip_address: Optional[str] = Field(None, validation_alias="IpAddress")
    browser: Optional[str] = Field(None, validation_alias="Browser")
    device: Optional[str] = Field(None, validation_alias="Device")
    operating_system: Optional[str] = Field(None, validation_alias="OperatingSystem")
    is_remember_me: bool = Field(validation_alias="IsRememberMe")
    last_activity_date: UtcDatetime = Field(validation_alias="LastActivityDate")
    created_date: UtcDatetime = Field(validation_alias="CreatedDate")
    is_current: bool = False


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    audit_log_id: int = Field(validation_alias="AuditLogId")
    user_id: Optional[int] = Field(None, validation_alias="UserId")
    username: Optional[str] = Field(None, validation_alias="Username")
    action: str = Field(validation_alias="Action")
    entity_type: Optional[str] = Field(None, validation_alias="EntityType")
    entity_id: Optional[str] = Field(None, validation_alias="EntityId")
    ip_address: Optional[str] = Field(None, validation_alias="IpAddress")
    status: str = Field(validation_alias="Status")
    created_date: UtcDatetime = Field(validation_alias="CreatedDate")


class ProfileUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=30)


class PreferenceUpdate(BaseModel):
    theme: Optional[str] = Field(None, pattern="^(light|dark|auto)$")
    language: Optional[str] = Field(None, max_length=10)
    timezone: Optional[str] = Field(None, max_length=50)


class ProfileResponse(BaseModel):
    user_id: int
    username: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    phone_number: Optional[str]
    profile_image_url: Optional[str]
    roles: List[str]
    permissions: List[str]
    is_super_admin: bool = False
    preferences: dict = {}
    menu_access_enforced: bool = False
    allowed_menu_paths: List[str] = []
    allowed_menu_codes: List[str] = []
