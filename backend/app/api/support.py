import uuid
from datetime import datetime, timedelta, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permission
from app.models.user import SupportSession, User
from app.schemas.support import SupportSessionCreate, SupportSessionResponse
from app.schemas.common import MessageResponse
from app.core.audit import log_activity

router = APIRouter()

@router.get("", response_model=List[SupportSessionResponse], summary="Lấy danh sách phiên hỗ trợ")
def list_support_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("tech_support", "view")),
):
    sessions = db.execute(
        select(SupportSession).order_by(SupportSession.created_at.desc())
    ).scalars().all()
    return sessions


@router.post("", response_model=SupportSessionResponse, summary="Kích hoạt phiên hỗ trợ")
def create_support_session(
    payload: SupportSessionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("tech_support", "update")),
):
    target_user = db.execute(select(User).where(User.id == payload.user_id)).scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    # Deactivate existing active sessions for this user
    active_sessions = db.execute(
        select(SupportSession).where(SupportSession.user_id == payload.user_id, SupportSession.is_active == True)
    ).scalars().all()
    for s in active_sessions:
        s.is_active = False

    # Create new session
    session = SupportSession(
        user_id=target_user.id,
        activated_by_id=current_user.id,
        reason=payload.reason,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=payload.duration_hours),
        is_active=True
    )
    db.add(session)
    
    # Activate the target user account temporarily
    target_user.is_active = True
    
    log_activity(db, "support_session_activated", user_id=current_user.id, entity_id=str(target_user.id), details={"reason": payload.reason}, request=request)
    db.commit()
    db.refresh(session)
    return session


@router.delete("/{session_id}", response_model=MessageResponse, summary="Hủy phiên hỗ trợ")
def cancel_support_session(
    session_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("tech_support", "update")),
):
    session = db.execute(select(SupportSession).where(SupportSession.id == session_id)).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên hỗ trợ")

    session.is_active = False
    
    # Lock the user account
    target_user = db.execute(select(User).where(User.id == session.user_id)).scalar_one()
    target_user.is_active = False
    
    log_activity(db, "support_session_cancelled", user_id=current_user.id, entity_id=str(target_user.id), request=request)
    db.commit()
    return MessageResponse(message="Đã hủy phiên hỗ trợ và khóa tài khoản")
