"""
TradeCore — User & Role Pydantic Schemas
Validation and serialization for authentication, users, and Dynamic RBAC.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ─── Permission Schemas ──────────────────────────────────────────────────────

class PermissionBase(BaseModel):
    resource: str
    action: str
    name: str
    description: Optional[str] = None

class PermissionResponse(PermissionBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


# ─── Role Schemas ────────────────────────────────────────────────────────────

class RoleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: bool = True

class RoleCreate(RoleBase):
    permission_ids: List[uuid.UUID] = Field(default_factory=list)

class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    permission_ids: Optional[List[uuid.UUID]] = None

class RoleResponse(RoleBase):
    id: uuid.UUID
    is_system: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RoleWithPermissionsResponse(RoleResponse):
    permissions: List[PermissionResponse] = []


# ─── User Schemas ────────────────────────────────────────────────────────────

class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=80)
    full_name: str = Field(..., min_length=1, max_length=255)
    is_active: bool = True

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    role_ids: List[uuid.UUID] = Field(default_factory=list)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=80)
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=6)
    role_ids: Optional[List[uuid.UUID]] = None

class UserResponse(UserBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserWithRolesResponse(UserResponse):
    roles: List[RoleResponse] = []
