"""
TradeCore — Personal Account API Router
Provides endpoints for an authenticated user to view their profile and change their own password.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.audit import log_activity
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.user import UserWithRolesResponse
from app.api.users import get_user_roles_list

router = APIRouter()


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


@router.get("/me", response_model=UserWithRolesResponse, summary="Xem thông tin tài khoản của tôi")
def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve personal profile details."""
    resp = UserWithRolesResponse.model_validate(current_user)
    resp.roles = get_user_roles_list(db, current_user.id)
    return resp


@router.put("/password", response_model=MessageResponse, summary="Đổi mật khẩu")
def change_own_password(
    payload: PasswordChangeRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change the authenticated user's password."""
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu hiện tại không chính xác"
        )
        
    current_user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    
    log_activity(db, "password_changed", user_id=current_user.id, entity_id=str(current_user.id), request=request)
    return MessageResponse(message="Đổi mật khẩu thành công")
