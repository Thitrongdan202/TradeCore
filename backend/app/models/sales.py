"""
TradeCore — Sales Order Models
"""
from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    CheckConstraint, Enum as SAEnum, ForeignKey, Integer,
    Numeric, String, Text, Date,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .partner import Customer, PaymentTerm
    from .currency import Currency
    from .product import Product
    from .uom import UnitOfMeasure
    from .user import User


class OrderStatus(str, enum.Enum):
    draft      = "draft"
    pending    = "pending"
    confirmed  = "confirmed"
    processing = "processing"
    shipping   = "shipping"
    completed  = "completed"
    cancelled  = "cancelled"
    returned   = "returned"


class PaymentStatus(str, enum.Enum):
    unpaid   = "unpaid"
    partial  = "partial"
    paid     = "paid"
    overdue  = "overdue"
    refunded = "refunded"


class SalesOrder(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Sales order (Đơn hàng bán).
    order_number follows SO-YYMM-XXXX convention.
    """

    __tablename__ = "sales_orders"

    order_number: Mapped[str] = mapped_column(
        String(40), unique=True, nullable=False, index=True
    )
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    currency_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("currencies.id", ondelete="RESTRICT"),
        nullable=True,
    )
    payment_term_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payment_terms.id", ondelete="SET NULL"),
        nullable=True,
    )

    date: Mapped[Optional[str]] = mapped_column(Date, nullable=True, index=True)
    due_date: Mapped[Optional[str]] = mapped_column(Date, nullable=True)

    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(OrderStatus, name="order_status", create_type=True),
        nullable=False,
        default=OrderStatus.draft,
        index=True,
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus, name="payment_status", create_type=True),
        nullable=False,
        default=PaymentStatus.unpaid,
        index=True,
    )

    subtotal: Mapped[Optional[float]] = mapped_column(Numeric(18, 4), nullable=True)
    tax_amount: Mapped[Optional[float]] = mapped_column(Numeric(18, 4), nullable=True, default=0)
    total: Mapped[Optional[float]] = mapped_column(Numeric(18, 4), nullable=True)
    amount_paid: Mapped[Optional[float]] = mapped_column(Numeric(18, 4), nullable=True, default=0)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    odoo_id: Mapped[Optional[int]] = mapped_column(
        nullable=True, index=True, comment="Odoo sale.order ID — migration only"
    )

    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    customer: Mapped[Optional["Customer"]] = relationship("Customer", back_populates="sales_orders")
    currency: Mapped[Optional["Currency"]] = relationship("Currency", back_populates="sales_orders")
    payment_term: Mapped[Optional["PaymentTerm"]] = relationship(
        "PaymentTerm", back_populates="sales_orders"
    )
    items: Mapped[List["SalesOrderItem"]] = relationship(
        "SalesOrderItem", back_populates="order", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<SalesOrder number={self.order_number!r} status={self.status}>"


class SalesOrderItem(Base, UUIDPrimaryKeyMixin):
    """
    Line item within a sales order.
    subtotal = qty × unit_price × (1 − discount_percent / 100)
    """

    __tablename__ = "sales_order_items"

    __table_args__ = (
        CheckConstraint("qty > 0", name="ck_so_item_qty_positive"),
        CheckConstraint(
            "discount_percent >= 0 AND discount_percent <= 100",
            name="ck_so_item_discount_range",
        ),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sales_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_no: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    qty: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    uom_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("units_of_measure.id", ondelete="RESTRICT"),
        nullable=True,
    )
    unit_price: Mapped[Optional[float]] = mapped_column(Numeric(18, 4), nullable=True)
    discount_percent: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    subtotal: Mapped[Optional[float]] = mapped_column(Numeric(18, 4), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    order: Mapped["SalesOrder"] = relationship("SalesOrder", back_populates="items")
    product: Mapped[Optional["Product"]] = relationship(
        "Product", back_populates="sales_order_items"
    )
    uom: Mapped[Optional["UnitOfMeasure"]] = relationship(
        "UnitOfMeasure", back_populates="sales_order_items"
    )

    def __repr__(self) -> str:
        return f"<SalesOrderItem order_id={self.order_id} line={self.line_no} qty={self.qty}>"
