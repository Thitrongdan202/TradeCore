"""
TradeCore — Authentication API
Login and token generation.
"""
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from app.core.audit import log_activity
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
settings = get_settings()
from app.core.security import verify_password, create_access_token
from app.api.deps import get_db, get_current_user
from app.models.user import User

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
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    Supports email or username as the "username" field.
    """
    # Check if username is an email or a regular username
    user = db.execute(
        select(User).where(
            (User.email == form_data.username) | (User.username == form_data.username)
        )
    ).scalar_one_or_none()
    
<<<<<<< Updated upstream
    if not user or not verify_password(form_data.password, user.hashed_password):
=======
    if not user or not verify_password(form_data.password, user.encrypted_password):
>>>>>>> Stashed changes
        log_activity(db, "login_failed", details={"username": form_data.username}, request=request)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản hoặc mật khẩu không chính xác",
        )
    if not user.is_active:
        log_activity(db, "login_failed_locked", user_id=user.id, request=request)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Tài khoản đã bị khóa"
        )
        
    log_activity(db, "login_success", user_id=user.id, request=request)
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    
    return {
        "access_token": create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


from app.api.deps import get_user_permissions

@router.get("/me", response_model=UserResponse)
def read_current_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get current user with dynamic permissions."""
    perms = get_user_permissions(db, str(current_user.id))
    permission_strings = [f"{res}:{act}" for res, act in perms]
    
    role_names = [ur.role.name for ur in current_user.user_roles if ur.role.is_active]

    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "roles": role_names,
        "permissions": permission_strings,
    }


import secrets
from datetime import datetime, timezone
from app.models.user import PasswordReset

class PasswordRecoveryRequest(BaseModel):
    email: str

class PasswordResetRequest(BaseModel):
    token: str
    new_password: str

@router.post("/recover-password")
def recover_password(payload: PasswordRecoveryRequest, request: Request, db: Session = Depends(get_db)):
    """Generate a password reset token for the given email."""
    user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if not user:
        # Prevent email enumeration by returning a generic success message
        return {"message": "Nếu email hợp lệ, hướng dẫn khôi phục mật khẩu đã được gửi."}
    
    token = secrets.token_urlsafe(32)
    reset_record = PasswordReset(
        user_id=user.id,
        reset_token_hash=get_password_hash(token),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    db.add(reset_record)
    log_activity(db, "password_recovery_requested", user_id=user.id, request=request)
    db.commit()
    
    # Note: In a real system we would send an email here.
    return {"message": "Nếu email hợp lệ, hướng dẫn khôi phục mật khẩu đã được gửi.", "dev_token": token}

@router.post("/reset-password")
def reset_password(payload: PasswordResetRequest, request: Request, db: Session = Depends(get_db)):
    """Reset password using a valid token."""
    now = datetime.now(timezone.utc)
    valid_resets = db.execute(
        select(PasswordReset).where(PasswordReset.is_used == False, PasswordReset.expires_at > now)
    ).scalars().all()
    
    target_reset = None
    for r in valid_resets:
        if verify_password(payload.token, r.reset_token_hash):
            target_reset = r
            break
            
    if not target_reset:
        raise HTTPException(status_code=400, detail="Mã khôi phục không hợp lệ hoặc đã hết hạn")
        
    user = db.execute(select(User).where(User.id == target_reset.user_id)).scalar_one()
<<<<<<< Updated upstream
    user.hashed_password = get_password_hash(payload.new_password)
=======
    user.encrypted_password = get_password_hash(payload.new_password)
>>>>>>> Stashed changes
    target_reset.is_used = True
    
    log_activity(db, "password_reset_completed", user_id=user.id, request=request)
    db.commit()
    return {"message": "Mật khẩu đã được cập nhật thành công."}
