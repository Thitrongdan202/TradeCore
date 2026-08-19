import uuid
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import Request
from app.models.audit import ActivityLog

def log_activity(
    db: Session,
    action: str,
    user_id: Optional[uuid.UUID] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    details: Optional[dict] = None,
    request: Optional[Request] = None,
):
    ip_address = None
    if request:
        client = request.client
        if client:
            ip_address = client.host

    log = ActivityLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        ip_address=ip_address
    )
    db.add(log)
    db.commit()
