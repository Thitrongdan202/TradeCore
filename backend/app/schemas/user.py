"""
TradeCore — User & Role Pydantic Schemas
Validation and serialization for authentication, users, and RBAC roles.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ─── Role Schemas ────────────────────────────────────────────────────────────

class RoleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=80, description="Role identifier, e.g. admin, sales")
    description: Optional[str] = Field(None, description="Human readable description")
    permissions: Optional[Dict[str, Any] | List[str]] = Field(
        None, description="Array or object defining granted permissions"
    )


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=80)
    description: Optional[str] = None
    permissions: Optional[Dict[str, Any] | List[str]] = None


class RoleResponse(RoleBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ─── User Schemas ────────────────────────────────────────────────────────────

class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=80)
    full_name: str = Field(..., min_length=1, max_length=255)
    is_active: bool = True
    role_id: Optional[uuid.UUID] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="Plain text password to be hashed")


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=80)
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None
    role_id: Optional[uuid.UUID] = None
    password: Optional[str] = Field(None, min_length=6, description="Optional new password")


class UserResponse(UserBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserWithRoleResponse(UserResponse):
    role: Optional[RoleResponse] = None
