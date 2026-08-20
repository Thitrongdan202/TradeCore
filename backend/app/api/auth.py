"""
TradeCore — Authentication API
Login and token generation.
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, get_user_permissions
from app.core.audit import log_activity
from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.models.user import PasswordReset, User

settings = get_settings()

router = APIRouter()


class Token(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    roles: list[str] = []
    permissions: list[str] = []

    class Config:
        from_attributes = True


@router.post("/login", response_model=Token)
def login_access_token(
    request: Request,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2 compatible token login.

    Supports email or username as the username field.
    """
    user = db.execute(
        select(User).where(
            (User.email == form_data.username)
            | (User.username == form_data.username)
        )
    ).scalar_one_or_none()

    if not user or not verify_password(
        form_data.password,
        user.encrypted_password,
    ):
        log_activity(
            db,
            "login_failed",
            details={"username": form_data.username},
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản hoặc mật khẩu không chính xác",
        )

    if not user.is_active:
        log_activity(
            db,
            "login_failed_locked",
            user_id=user.id,
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tài khoản đã bị khóa",
        )

    log_activity(
        db,
        "login_success",
        user_id=user.id,
        request=request,
    )

    access_token_expires = timedelta(
        minutes=settings.access_token_expire_minutes
    )

    return {
        "access_token": create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires,
        ),
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserResponse)
def read_current_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Get current user with dynamic permissions."""
    perms = get_user_permissions(db, str(current_user.id))
    permission_strings = [
        f"{resource}:{action}" for resource, action in perms
    ]

    role_names = [
        user_role.role.name
        for user_role in current_user.user_roles
        if user_role.role.is_active
    ]

    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "roles": role_names,
        "permissions": permission_strings,
    }


class PasswordRecoveryRequest(BaseModel):
    email: str


class PasswordResetRequest(BaseModel):
    token: str
    new_password: str


@router.post("/recover-password")
def recover_password(
    payload: PasswordRecoveryRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Generate a password reset token for the given email."""
    user = db.execute(
        select(User).where(User.email == payload.email)
    ).scalar_one_or_none()

    if not user:
        return {
            "message": (
                "Nếu email hợp lệ, hướng dẫn khôi phục "
                "mật khẩu đã được gửi."
            )
        }

    token = secrets.token_urlsafe(32)

    reset_record = PasswordReset(
        user_id=user.id,
        reset_token_hash=get_password_hash(token),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )

    db.add(reset_record)

    log_activity(
        db,
        "password_recovery_requested",
        user_id=user.id,
        request=request,
    )

    db.commit()

    # Development only: token is returned temporarily.
    # In production, this should be sent through a secure
    # password-reset delivery mechanism.
    return {
        "message": (
            "Nếu email hợp lệ, hướng dẫn khôi phục "
            "mật khẩu đã được gửi."
        ),
        "dev_token": token,
    }


@router.post("/reset-password")
def reset_password(
    payload: PasswordResetRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Reset password using a valid token."""
    now = datetime.now(timezone.utc)

    valid_resets = (
        db.execute(
            select(PasswordReset).where(
                PasswordReset.is_used.is_(False),
                PasswordReset.expires_at > now,
            )
        )
        .scalars()
        .all()
    )

    target_reset = None

    for reset in valid_resets:
        if verify_password(
            payload.token,
            reset.reset_token_hash,
        ):
            target_reset = reset
            break

    if not target_reset:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mã khôi phục không hợp lệ hoặc đã hết hạn",
        )

    user = db.execute(
        select(User).where(User.id == target_reset.user_id)
    ).scalar_one()

    user.encrypted_password = get_password_hash(
        payload.new_password
    )
    target_reset.is_used = True

    log_activity(
        db,
        "password_reset_completed",
        user_id=user.id,
        request=request,
    )

    db.commit()

    return {
        "message": "Mật khẩu đã được cập nhật thành công."
    }