"""
TradeCore — Audit Logging Utility
"""
from typing import Optional
from sqlalchemy.orm import Session
from app.models.audit import ActivityLog
from app.models.user import User


def log_activity(
    db: Session,
    user: Optional[User],
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
):
    """
    Log an action performed by a user to the activity_logs table.
    """
    log_entry = ActivityLog(
        user_id=user.id if user else None,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else None,
        details=details,
        ip_address=ip_address,
    )
    db.add(log_entry)
    db.commit()
