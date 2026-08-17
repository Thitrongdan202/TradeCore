"""
TradeCore — Audit Models (Nhật ký hoạt động)
"""
import uuid
from typing import Optional

from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ActivityLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "activity_logs"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    action: Mapped[str] = mapped_column(String(100), index=True)
    entity_type: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    details: Mapped[Optional[dict]] = mapped_column(JSONB)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50))

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="activity_logs")

    def __repr__(self) -> str:
        return f"<ActivityLog {self.action} on {self.entity_type}:{self.entity_id}>"
