"""
TradeCore — Users and Roles API Router
Provides CRUD endpoints for system users and RBAC roles.
"""
from __future__ import annotations

import math
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, or_
from sqlalchemy.orm import Session, selectinload

from app.core.security import RoleType
from app.api.deps import get_current_user, get_db, require_role
from app.core.security import get_password_hash
from app.models.user import Role, User
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.user import (
    RoleCreate,
    RoleResponse,
    RoleUpdate,
    UserCreate,
    UserResponse,
    UserUpdate,
    UserWithRoleResponse,
)

router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# ROLES CRUD
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/roles", response_model=List[RoleResponse], summary="Lấy danh sách tất cả các vai trò")
def list_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN])),
):
    """Retrieve all roles in the system."""
    roles = db.execute(select(Role).order_by(Role.name)).scalars().all()
    return roles


@router.get("/roles/{role_id}", response_model=RoleResponse, summary="Lấy thông tin chi tiết vai trò")
def get_role(
    role_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN])),
):
    """Retrieve a single role by UUID."""
    role = db.execute(select(Role).where(Role.id == role_id)).scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy vai trò với ID {role_id}",
        )
    return role


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED, summary="Tạo mới vai trò")
def create_role(
    payload: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN])),
):
    """Create a new RBAC role."""
    existing = db.execute(select(Role).where(Role.name == payload.name)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tên vai trò '{payload.name}' đã tồn tại trong hệ thống",
        )
    
    role = Role(
        name=payload.name,
        description=payload.description,
        permissions=payload.permissions if isinstance(payload.permissions, dict) else {"list": payload.permissions} if payload.permissions else None,
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@router.put("/roles/{role_id}", response_model=RoleResponse, summary="Cập nhật thông tin vai trò")
def update_role(
    role_id: uuid.UUID,
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN])),
):
    """Update role details."""
    role = db.execute(select(Role).where(Role.id == role_id)).scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy vai trò với ID {role_id}",
        )

    if payload.name is not None and payload.name != role.name:
        existing = db.execute(select(Role).where(Role.name == payload.name)).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tên vai trò '{payload.name}' đã tồn tại",
            )
        role.name = payload.name

    if payload.description is not None:
        role.description = payload.description
    if payload.permissions is not None:
        role.permissions = payload.permissions if isinstance(payload.permissions, dict) else {"list": payload.permissions}

    db.commit()
    db.refresh(role)
    return role


@router.delete("/roles/{role_id}", response_model=MessageResponse, summary="Xóa vai trò")
def delete_role(
    role_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN])),
):
    """Delete a role if no users are assigned."""
    role = db.execute(select(Role).where(Role.id == role_id)).scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy vai trò với ID {role_id}",
        )

    users_count = db.execute(select(func.count(User.id)).where(User.role_id == role_id)).scalar() or 0
    if users_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Không thể xóa vai trò vì có {users_count} người dùng đang được gán",
        )

    db.delete(role)
    db.commit()
    return MessageResponse(message=f"Đã xóa vai trò '{role.name}' thành công")


# ═══════════════════════════════════════════════════════════════════════════════
# USERS CRUD
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("", response_model=PaginatedResponse[UserWithRoleResponse], summary="Lấy danh sách người dùng")
def list_users(
    page: int = Query(1, ge=1, description="Số trang (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Số bản ghi mỗi trang"),
    search: Optional[str] = Query(None, description="Tìm kiếm theo username, email hoặc họ tên"),
    role_id: Optional[uuid.UUID] = Query(None, description="Lọc theo vai trò"),
    is_active: Optional[bool] = Query(None, description="Lọc theo trạng thái hoạt động"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN])),
):
    """List users with search, role filter, and pagination."""
    query = select(User).options(selectinload(User.role))

    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(
            or_(
                User.username.ilike(pattern),
                User.email.ilike(pattern),
                User.full_name.ilike(pattern),
            )
        )

    if role_id:
        query = query.where(User.role_id == role_id)

    if is_active is not None:
        query = query.where(User.is_active == is_active)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    items = db.execute(
        query.order_by(User.created_at.desc()).offset(offset).limit(page_size)
    ).scalars().all()

    total_pages = math.ceil(total / page_size) if page_size > 0 else 1

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{user_id}", response_model=UserWithRoleResponse, summary="Lấy thông tin người dùng")
def get_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN])),
):
    """Retrieve user details by UUID."""
    user = db.execute(
        select(User).options(selectinload(User.role)).where(User.id == user_id)
    ).scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy người dùng với ID {user_id}",
        )
    return user


@router.post("", response_model=UserWithRoleResponse, status_code=status.HTTP_201_CREATED, summary="Tạo mới người dùng")
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN])),
):
    """Create a new user with hashed password."""
    # Check email uniqueness
    if db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{payload.email}' đã được sử dụng",
        )

    # Check username uniqueness
    if db.execute(select(User).where(User.username == payload.username)).scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tên tài khoản '{payload.username}' đã tồn tại",
        )

    # Check role if supplied
    if payload.role_id:
        role = db.execute(select(Role).where(Role.id == payload.role_id)).scalar_one_or_none()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không tìm thấy vai trò với ID {payload.role_id}",
            )

    user = User(
        email=payload.email,
        username=payload.username,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        is_active=payload.is_active,
        role_id=payload.role_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Reload with role relationship
    return db.execute(
        select(User).options(selectinload(User.role)).where(User.id == user.id)
    ).scalar_one()


@router.put("/{user_id}", response_model=UserWithRoleResponse, summary="Cập nhật người dùng")
def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN])),
):
    """Update user information, role, or password."""
    user = db.execute(
        select(User).options(selectinload(User.role)).where(User.id == user_id)
    ).scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy người dùng với ID {user_id}",
        )

    if payload.email is not None and payload.email != user.email:
        if db.execute(select(User).where(User.email == payload.email, User.id != user_id)).scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email '{payload.email}' đã được sử dụng bởi người dùng khác",
            )
        user.email = payload.email

    if payload.username is not None and payload.username != user.username:
        if db.execute(select(User).where(User.username == payload.username, User.id != user_id)).scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tên tài khoản '{payload.username}' đã tồn tại",
            )
        user.username = payload.username

    if payload.full_name is not None:
        user.full_name = payload.full_name

    if payload.is_active is not None:
        user.is_active = payload.is_active

    if payload.role_id is not None:
        role = db.execute(select(Role).where(Role.id == payload.role_id)).scalar_one_or_none()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không tìm thấy vai trò với ID {payload.role_id}",
            )
        user.role_id = payload.role_id

    if payload.password:
        user.hashed_password = get_password_hash(payload.password)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", response_model=MessageResponse, summary="Xóa người dùng")
def delete_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN])),
):
    """Delete a user account."""
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bạn không thể xóa tài khoản của chính mình",
        )

    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy người dùng với ID {user_id}",
        )

    db.delete(user)
    db.commit()
    return MessageResponse(message=f"Đã xóa người dùng '{user.username}' thành công")
