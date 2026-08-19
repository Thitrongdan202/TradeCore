import math
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permission
from app.models.audit import ActivityLog
from app.models.user import User
from app.schemas.audit import ActivityLogResponse
from app.schemas.common import PaginatedResponse

router = APIRouter()

@router.get("", response_model=PaginatedResponse[ActivityLogResponse], summary="Lấy danh sách nhật ký hoạt động")
def list_audit_logs(
    page: int = Query(1, ge=1, description="Số trang"),
    page_size: int = Query(50, ge=1, le=200),
    user_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("audit_log", "view")),
):
    query = select(ActivityLog)
    
    if user_id:
        query = query.where(ActivityLog.user_id == user_id)
    if action:
        query = query.where(ActivityLog.action.ilike(f"%{action}%"))

    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar() or 0

    offset = (page - 1) * page_size
    items = db.execute(
        query.order_by(desc(ActivityLog.created_at)).offset(offset).limit(page_size)
    ).scalars().all()

    total_pages = math.ceil(total / page_size) if page_size > 0 else 1

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
