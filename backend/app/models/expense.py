"""
TradeCore — Expense Model
Tracks logistics-related costs: freight, customs duties, insurance, storage, etc.
Not a full accounting module — this is logistics cost tracking only.
"""
from __future__ import annotations

import enum
import uuid
from typing import Optional

from sqlalchemy import Date, Enum as SAEnum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ExpenseCategory(str, enum.Enum):
    freight    = "freight"
    customs    = "customs"
    insurance  = "insurance"
    storage    = "storage"
    handling   = "handling"
    other      = "other"


class Expense(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Logistics-related expense record.
    Linked optionally to a shipment, purchase order, or import/export order.
    """

    __tablename__ = "expenses"

    category: Mapped[ExpenseCategory] = mapped_column(
        SAEnum(ExpenseCategory, name="expense_category"),
        nullable=False,
        default=ExpenseCategory.other,
        index=True,
    )
    reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    currency_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("currencies.id", ondelete="RESTRICT"),
        nullable=True,
    )

    expense_date: Mapped[Optional[str]] = mapped_column(Date, nullable=True, index=True)

    # Optional links
    shipment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shipments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Expense category={self.category} amount={self.amount}>"
