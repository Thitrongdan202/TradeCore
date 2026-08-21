"""
TradeCore — Users, Roles, and Permissions API Router
Provides CRUD endpoints for system users, RBAC roles, and permissions.
"""
from __future__ import annotations

import math
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from app.core.audit import log_activity
from sqlalchemy import func, select, or_
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, get_db, require_permission
from app.core.security import get_password_hash, decrypt_password
from app.models.user import Role, User, Permission, RolePermission, UserRole
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.user import (
    RoleCreate,
    RoleResponse,
    RoleUpdate,
    RoleWithPermissionsResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
    UserWithRolesResponse,
    PermissionResponse
)

router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# PERMISSIONS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/permissions", response_model=List[PermissionResponse], summary="Lấy danh sách tất cả quyền")
def list_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("permission", "view")),
):
    """Retrieve all available permissions in the system."""
    perms = db.execute(select(Permission).order_by(Permission.resource, Permission.action)).scalars().all()
    return perms


# ═══════════════════════════════════════════════════════════════════════════════
# ROLES CRUD
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/roles", response_model=List[RoleResponse], summary="Lấy danh sách tất cả các vai trò")
def list_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role", "view")),
):
    """Retrieve all roles in the system."""
    roles = db.execute(select(Role).order_by(Role.name)).scalars().all()
    return roles


@router.get("/roles/{role_id}", response_model=RoleWithPermissionsResponse, summary="Lấy thông tin chi tiết vai trò")
def get_role(
    role_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role", "view")),
):
    """Retrieve a single role by UUID, including permissions."""
    role = db.execute(
        select(Role).where(Role.id == role_id)
    ).scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy vai trò với ID {role_id}",
        )
    
    # Load permissions
    perms = db.execute(
        select(Permission).join(RolePermission, RolePermission.permission_id == Permission.id).where(RolePermission.role_id == role.id)
    ).scalars().all()
    
    resp = RoleWithPermissionsResponse.model_validate(role)
    resp.permissions = perms
    return resp


@router.post("/roles", response_model=RoleWithPermissionsResponse, status_code=status.HTTP_201_CREATED, summary="Tạo mới vai trò")
def create_role(
    payload: RoleCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role", "create")),
):
    """Create a new RBAC role."""
    existing = db.execute(select(Role).where(Role.code == payload.code)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Mã vai trò '{payload.code}' đã tồn tại",
        )
        
    role = Role(
        name=payload.name,
        code=payload.code,
        description=payload.description,
        is_active=payload.is_active,
        is_system=False
    )
    db.add(role)
    db.flush()
    
    perms = []
    if payload.permission_ids:
        # Validate permissions
        db_perms = db.execute(select(Permission).where(Permission.id.in_(payload.permission_ids))).scalars().all()
        if len(db_perms) != len(payload.permission_ids):
            raise HTTPException(status_code=400, detail="Một số ID quyền không hợp lệ")
            
        for pid in payload.permission_ids:
            db.add(RolePermission(role_id=role.id, permission_id=pid))
        perms = db_perms

    db.commit()
    log_activity(db, "role_created", user_id=current_user.id, entity_id=str(role.id), request=request)
    db.refresh(role)
    
    resp = RoleWithPermissionsResponse.model_validate(role)
    resp.permissions = perms
    return resp


@router.put("/roles/{role_id}", response_model=RoleWithPermissionsResponse, summary="Cập nhật thông tin vai trò")
def update_role(
    role_id: uuid.UUID,
    payload: RoleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role", "update")),
):
    """Update role details and permissions."""
    role = db.execute(select(Role).where(Role.id == role_id)).scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy vai trò")

    if payload.name is not None:
        role.name = payload.name
    if payload.description is not None:
        role.description = payload.description
    
    if payload.is_active is not None:
        if role.is_system and not payload.is_active:
             raise HTTPException(status_code=400, detail="Không thể vô hiệu hóa vai trò hệ thống")
        role.is_active = payload.is_active

    if payload.permission_ids is not None:
        # Delete old permissions
        db.execute(RolePermission.__table__.delete().where(RolePermission.role_id == role.id))
        
        # Add new permissions
        if payload.permission_ids:
            db_perms = db.execute(select(Permission).where(Permission.id.in_(payload.permission_ids))).scalars().all()
            if len(db_perms) != len(payload.permission_ids):
                raise HTTPException(status_code=400, detail="Một số ID quyền không hợp lệ")
            for pid in payload.permission_ids:
                db.add(RolePermission(role_id=role.id, permission_id=pid))

    db.commit()
    log_activity(db, "role_updated", user_id=current_user.id, entity_id=str(role.id), request=request)
    db.refresh(role)
    
    perms = db.execute(
        select(Permission).join(RolePermission).where(RolePermission.role_id == role.id)
    ).scalars().all()
    
    resp = RoleWithPermissionsResponse.model_validate(role)
    resp.permissions = perms
    return resp


@router.delete("/roles/{role_id}", response_model=MessageResponse, summary="Xóa vai trò")
def delete_role(
    role_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role", "delete")),
):
    """Delete a role if no users are assigned and it's not system."""
    role = db.execute(select(Role).where(Role.id == role_id)).scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Không tìm thấy vai trò")

    if role.is_system:
        raise HTTPException(status_code=400, detail="Không thể xóa vai trò hệ thống")

    users_count = db.execute(select(func.count(UserRole.user_id)).where(UserRole.role_id == role_id)).scalar() or 0
    if users_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Không thể xóa vai trò vì có {users_count} người dùng đang được gán",
        )

    db.delete(role)
    log_activity(db, "role_deleted", user_id=current_user.id, entity_id=str(role.id), request=request)
    db.commit()
    return MessageResponse(message=f"Đã xóa vai trò '{role.name}' thành công")


# ═══════════════════════════════════════════════════════════════════════════════
# USERS CRUD
# ═══════════════════════════════════════════════════════════════════════════════

def get_user_roles_list(db: Session, user_id: uuid.UUID):
    return db.execute(
        select(Role).join(UserRole).where(UserRole.user_id == user_id)
    ).scalars().all()

@router.get("", response_model=PaginatedResponse[UserWithRolesResponse], summary="Lấy danh sách người dùng")
def list_users(
    page: int = Query(1, ge=1, description="Số trang"),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user", "view")),
):
    """List users with search, and pagination."""
    query = select(User)

    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(
            or_(
                User.username.ilike(pattern),
                User.email.ilike(pattern),
                User.full_name.ilike(pattern),
            )
        )

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

    # Attach roles
    results = []
    for u in items:
        resp = UserWithRolesResponse.model_validate(u)
        resp.roles = get_user_roles_list(db, u.id)
        results.append(resp)

    return PaginatedResponse(
        items=results,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{user_id}", response_model=UserWithRolesResponse, summary="Lấy thông tin người dùng")
def get_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user", "view")),
):
    """Retrieve user details by UUID."""
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    
    resp = UserWithRolesResponse.model_validate(user)
    resp.roles = get_user_roles_list(db, user.id)
    return resp


@router.post("", response_model=UserWithRolesResponse, status_code=status.HTTP_201_CREATED, summary="Tạo mới người dùng")
def create_user(
    payload: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user", "create")),
):
    """Create a new user with hashed password."""
    if db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email đã được sử dụng")

    if db.execute(select(User).where(User.username == payload.username)).scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Tên tài khoản đã tồn tại")

    user = User(
        email=payload.email,
        username=payload.username,
        encrypted_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        is_active=payload.is_active,
    )
    db.add(user)
    db.flush()

    roles = []
    if payload.role_ids:
        db_roles = db.execute(select(Role).where(Role.id.in_(payload.role_ids))).scalars().all()
        if len(db_roles) != len(payload.role_ids):
            raise HTTPException(status_code=400, detail="Một số ID vai trò không hợp lệ")
        for rid in payload.role_ids:
            db.add(UserRole(user_id=user.id, role_id=rid))
        roles = db_roles

    db.commit()
    log_activity(db, "user_created", user_id=current_user.id, entity_id=str(user.id), request=request)
    db.refresh(user)
    
    resp = UserWithRolesResponse.model_validate(user)
    resp.roles = roles
    return resp


@router.put("/{user_id}", response_model=UserWithRolesResponse, summary="Cập nhật người dùng")
def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user", "update")),
):
    """Update user information, roles, or password."""
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    # Safegurad: If this is the ONLY active admin, prevent deactivation or role removal
    is_admin = False
    admin_role_ids = []
    current_roles = get_user_roles_list(db, user.id)
    for r in current_roles:
        if r.is_system and r.code == "ADMIN":
            is_admin = True
            admin_role_ids.append(r.id)

    if is_admin:
        # Count other active admins
        other_admins = db.execute(
            select(func.count(User.id))
            .join(UserRole).join(Role)
            .where(Role.code == "ADMIN", User.id != user_id, User.is_active == True)
        ).scalar() or 0
        
        if other_admins == 0:
            if payload.is_active is False:
                raise HTTPException(status_code=400, detail="Không thể khóa quản trị viên duy nhất")
            
            if payload.role_ids is not None:
                # Ensure they still have the admin role
                if not any(rid in payload.role_ids for rid in admin_role_ids):
                    raise HTTPException(status_code=400, detail="Không thể gỡ bỏ quyền quản trị viên duy nhất")


    if payload.email is not None and payload.email != user.email:
        if db.execute(select(User).where(User.email == payload.email, User.id != user_id)).scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email đã được sử dụng")
        user.email = payload.email

    if payload.username is not None and payload.username != user.username:
        if db.execute(select(User).where(User.username == payload.username, User.id != user_id)).scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Tên tài khoản đã tồn tại")
        user.username = payload.username

    if payload.full_name is not None:
        user.full_name = payload.full_name

    if payload.is_active is not None:
        user.is_active = payload.is_active

    if payload.role_ids is not None:
        db.execute(UserRole.__table__.delete().where(UserRole.user_id == user.id))
        if payload.role_ids:
            db_roles = db.execute(select(Role).where(Role.id.in_(payload.role_ids))).scalars().all()
            if len(db_roles) != len(payload.role_ids):
                raise HTTPException(status_code=400, detail="Một số ID vai trò không hợp lệ")
            for rid in payload.role_ids:
                db.add(UserRole(user_id=user.id, role_id=rid))

    if payload.password:
        user.encrypted_password = get_password_hash(payload.password)

    db.commit()
    log_activity(db, "user_created", user_id=current_user.id, entity_id=str(user.id), request=request)
    db.refresh(user)
    
    resp = UserWithRolesResponse.model_validate(user)
    resp.roles = get_user_roles_list(db, user.id)
    return resp


@router.delete("/{user_id}", response_model=MessageResponse, summary="Xóa người dùng")
def delete_user(
    user_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user", "delete")),
):
    """Delete a user account."""
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Bạn không thể xóa tài khoản của chính mình")

    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    # Check if this is the last admin
    current_roles = get_user_roles_list(db, user.id)
    is_admin = any(r.code == "ADMIN" for r in current_roles)
    if is_admin:
        other_admins = db.execute(
            select(func.count(User.id))
            .join(UserRole).join(Role)
            .where(Role.code == "ADMIN", User.id != user_id)
        ).scalar() or 0
        if other_admins == 0:
            raise HTTPException(status_code=400, detail="Không thể xóa quản trị viên duy nhất của hệ thống")

    db.delete(user)
    log_activity(db, "user_deleted", user_id=current_user.id, entity_id=str(user.id), request=request)
    db.commit()
    return MessageResponse(message=f"Đã xóa người dùng '{user.username}' thành công")


from pydantic import BaseModel
class AdminPasswordReset(BaseModel):
    new_password: str

@router.put("/{user_id}/reset-password", response_model=MessageResponse, summary="Admin đặt lại mật khẩu")
def admin_reset_password(
    user_id: uuid.UUID,
    payload: AdminPasswordReset,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user", "update")),
):
    """Admin resets another user's password."""
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    user.encrypted_password = get_password_hash(payload.new_password)
    db.commit()
    log_activity(db, "admin_password_reset", user_id=current_user.id, entity_id=str(user.id), request=request, details={"target_username": user.username})
    return MessageResponse(message=f"Đã đặt lại mật khẩu cho '{user.username}'")


@router.get("/{user_id}/effective-permissions", response_model=List[PermissionResponse], summary="Lấy quyền hiệu lực của người dùng")
def get_user_effective_permissions(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user", "view")),
):
    """Get all effective permissions for a user."""
    perms = db.execute(
        select(Permission)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(UserRole, UserRole.role_id == RolePermission.role_id)
        .where(UserRole.user_id == user_id)
    ).scalars().all()
    
    # Deduplicate permissions
    seen = set()
    unique_perms = []
    for p in perms:
        if p.id not in seen:
            seen.add(p.id)
            unique_perms.append(p)
            
    return unique_perms


@router.get("/{user_id}/password", summary="Xem mật khẩu người dùng (dành cho Admin)")
def view_user_password(
    user_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user", "password_view")),
):
    """Return the plaintext password for a user. Only allowed for admins with specific permission."""
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    plain_pass = decrypt_password(user.encrypted_password)
    if not plain_pass:
        raise HTTPException(status_code=400, detail="Không thể giải mã mật khẩu (có thể là mật khẩu cũ)")

    log_activity(db, "password_viewed", user_id=current_user.id, entity_id=str(user.id), request=request, details={"target_username": user.username})
    
    return {"password": plain_pass}
