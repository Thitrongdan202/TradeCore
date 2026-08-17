"""
TradeCore — Partner Models: PaymentTerm, Customer, Supplier

Vietnamese business context:
  - Customers use MST (Mã số thuế) as tax identifier
  - Customer codes follow KH-XXXX convention
  - Supplier codes follow NCC-XXXX convention
  - Foreign suppliers have country codes (CN, KR, TW, TH, JP, DE, etc.)
"""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .pricing import PriceList
    from .sales import SalesOrder
    from .purchase import PurchaseOrder
    from .shipment import Shipment


class PaymentTerm(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Payment terms used on sales and purchase orders.
    Examples:
      - "Thanh toán ngay" (immediate)
      - "30 ngày NET"
      - "50% ứng trước, 50% khi nhận hàng"
      - "Tín dụng 60 ngày"
    """

    __tablename__ = "payment_terms"

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    days_due: Mapped[Optional[int]] = mapped_column(nullable=True, comment="Days until payment due")
    advance_percent: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2), nullable=True, comment="Advance payment percentage (0–100)"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    customers: Mapped[List["Customer"]] = relationship("Customer", back_populates="payment_term")
    suppliers: Mapped[List["Supplier"]] = relationship("Supplier", back_populates="payment_term")
    sales_orders: Mapped[List["SalesOrder"]] = relationship("SalesOrder", back_populates="payment_term")
    purchase_orders: Mapped[List["PurchaseOrder"]] = relationship("PurchaseOrder", back_populates="payment_term")

    def __repr__(self) -> str:
        return f"<PaymentTerm name={self.name!r} days={self.days_due}>"


class Customer(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Customer (domestic buyer).
    code is the stable identifier (KH-XXXX). Used as upsert key during imports.
    tax_code is the Vietnamese MST (Mã số thuế doanh nghiệp).
    """

    __tablename__ = "customers"

    # ── Identifiers ──────────────────────────────────────────────────────
    code: Mapped[str] = mapped_column(
        String(40), unique=True, nullable=False, index=True,
        comment="Stable customer code, e.g. KH-0041"
    )
    tax_code: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, index=True, comment="MST — Mã số thuế"
    )

    # ── Names ─────────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    short_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # ── Contact ───────────────────────────────────────────────────────────
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    province: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(10), nullable=False, default="VN")

    # ── Commercial terms ─────────────────────────────────────────────────
    payment_term_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payment_terms.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    credit_limit: Mapped[Optional[float]] = mapped_column(
        Numeric(18, 2), nullable=True, comment="Credit limit in VND"
    )

    # ── Status & Notes ───────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Migration traceability ───────────────────────────────────────────
    odoo_id: Mapped[Optional[int]] = mapped_column(
        nullable=True, index=True, comment="Odoo res.partner ID — migration only"
    )

    # ── Relationships ────────────────────────────────────────────────────
    payment_term: Mapped[Optional["PaymentTerm"]] = relationship(
        "PaymentTerm", back_populates="customers"
    )
    sales_orders: Mapped[List["SalesOrder"]] = relationship(
        "SalesOrder", back_populates="customer"
    )
    price_lists: Mapped[List["PriceList"]] = relationship(
        "PriceList", back_populates="customer"
    )

    def __repr__(self) -> str:
        return f"<Customer code={self.code!r} name={self.name!r}>"


class Supplier(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Supplier (domestic or foreign vendor).
    code is the stable identifier (NCC-XXXX). Used as upsert key during imports.
    country: ISO 3166-1 alpha-2 code (CN, KR, TW, TH, VN, JP, DE, etc.)
    """

    __tablename__ = "suppliers"

    # ── Identifiers ──────────────────────────────────────────────────────
    code: Mapped[str] = mapped_column(
        String(40), unique=True, nullable=False, index=True,
        comment="Stable supplier code, e.g. NCC-0012"
    )
    tax_code: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True, index=True, comment="VAT / GST / MST of supplier"
    )

    # ── Names ─────────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    short_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # ── Contact ───────────────────────────────────────────────────────────
    country: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, index=True)
    contact_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Commercial terms ─────────────────────────────────────────────────
    payment_term_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payment_terms.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Status & Notes ───────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Migration traceability ───────────────────────────────────────────
    odoo_id: Mapped[Optional[int]] = mapped_column(
        nullable=True, index=True, comment="Odoo res.partner ID — migration only"
    )

    # ── Relationships ────────────────────────────────────────────────────
    payment_term: Mapped[Optional["PaymentTerm"]] = relationship(
        "PaymentTerm", back_populates="suppliers"
    )
    purchase_orders: Mapped[List["PurchaseOrder"]] = relationship(
        "PurchaseOrder", back_populates="supplier"
    )
    shipments: Mapped[List["Shipment"]] = relationship(
        "Shipment", back_populates="supplier"
    )

    def __repr__(self) -> str:
        return f"<Supplier code={self.code!r} name={self.name!r} country={self.country!r}>"
