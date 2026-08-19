"""
TradeCore — API Dependencies
Provides database sessions, authenticated users, and RBAC enforcement.
"""
from typing import Generator
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
settings = get_settings()
from app.core.database import SessionLocal
from app.models.user import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_db() -> Generator[Session, None, None]:
    """Dependency to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """Validate JWT and return current active user."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Phiên đăng nhập không hợp lệ (Không tìm thấy user_id)",
            )
    except (jwt.ExpiredSignatureError, jwt.PyJWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Phiên đăng nhập đã hết hạn hoặc không hợp lệ",
        )
    
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Tài khoản đã bị khóa")
    
    return user


from app.models.user import UserRole, RolePermission, Permission, Role

def get_user_permissions(db: Session, user_id: str) -> set[tuple[str, str]]:
    """Get all (resource, action) permissions for a user based on their active roles."""
    perms = db.execute(
        select(Permission.resource, Permission.action)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(Role, Role.id == RolePermission.role_id)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id, Role.is_active == True)
    ).all()
    return {(p.resource, p.action) for p in perms}

def require_permission(resource: str, action: str):
    """
    Dependency factory to check if the current user has a specific permission.
    """
    def permission_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        perms = get_user_permissions(db, str(current_user.id))
        if (resource, action) not in perms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Bạn không có quyền thực hiện thao tác này (yêu cầu: {action} trên {resource})"
            )
        return current_user
    return permission_checker
