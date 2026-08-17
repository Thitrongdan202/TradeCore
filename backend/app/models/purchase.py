"""
TradeCore — Purchase Order Models
"""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    CheckConstraint, Enum as SAEnum, ForeignKey, Integer,
    Numeric, String, Text, Date,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from .sales import OrderStatus, PaymentStatus  # reuse same enums

if TYPE_CHECKING:
    from .partner import Supplier, PaymentTerm
    from .currency import Currency
    from .product import Product
    from .uom import UnitOfMeasure
    from .user import User


class PurchaseOrder(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Purchase order (Đơn đặt hàng mua).
    order_number follows PO-YYMM-XXXX convention.
    """

    __tablename__ = "purchase_orders"

    order_number: Mapped[str] = mapped_column(
        String(40), unique=True, nullable=False, index=True
    )
    supplier_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
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
    expected_date: Mapped[Optional[str]] = mapped_column(Date, nullable=True)

    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(OrderStatus, name="order_status", create_constraint=False),
        nullable=False,
        default=OrderStatus.draft,
        index=True,
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus, name="payment_status", create_constraint=False),
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
        nullable=True, index=True, comment="Odoo purchase.order ID — migration only"
    )

    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    supplier: Mapped[Optional["Supplier"]] = relationship("Supplier", back_populates="purchase_orders")
    currency: Mapped[Optional["Currency"]] = relationship("Currency", back_populates="purchase_orders")
    payment_term: Mapped[Optional["PaymentTerm"]] = relationship(
        "PaymentTerm", back_populates="purchase_orders"
    )
    items: Mapped[List["PurchaseOrderItem"]] = relationship(
        "PurchaseOrderItem", back_populates="order", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder number={self.order_number!r} status={self.status}>"


class PurchaseOrderItem(Base, UUIDPrimaryKeyMixin):
    """Line item within a purchase order."""

    __tablename__ = "purchase_order_items"

    __table_args__ = (
        CheckConstraint("qty > 0", name="ck_po_item_qty_positive"),
        CheckConstraint(
            "discount_percent >= 0 AND discount_percent <= 100",
            name="ck_po_item_discount_range",
        ),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
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
    qty_received: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
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
    order: Mapped["PurchaseOrder"] = relationship("PurchaseOrder", back_populates="items")
    product: Mapped[Optional["Product"]] = relationship(
        "Product", back_populates="purchase_order_items"
    )
    uom: Mapped[Optional["UnitOfMeasure"]] = relationship(
        "UnitOfMeasure", back_populates="purchase_order_items"
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrderItem order_id={self.order_id} line={self.line_no} qty={self.qty}>"
