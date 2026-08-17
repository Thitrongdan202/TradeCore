"""
TradeCore — Authentication API
Login and token generation.
"""
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
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
    role: str | None = None

    class Config:
        from_attributes = True


@router.post("/login", response_model=Token)
def login_access_token(
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
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản hoặc mật khẩu không chính xác",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Tài khoản đã bị khóa"
        )
        
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    
    return {
        "access_token": create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)) -> Any:
    """Get current user."""
    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role.name if current_user.role else None,
    }
