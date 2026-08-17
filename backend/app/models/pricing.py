"""
TradeCore — Pricing Models: PriceList & PriceListItem

Pricing rules:
  - A PriceList without a customer_id is the STANDARD list (applies to all).
  - A PriceList with a customer_id is customer-specific.
  - PriceListItem.min_qty enables quantity-break pricing.
  - Do NOT overwrite existing prices automatically — always create a new import run.
  - Preserve original source values (source_price, source_currency) for audit.
"""
from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .currency import Currency
    from .product import Product
    from .partner import Customer
    from .uom import UnitOfMeasure


class PriceList(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    A named price list, optionally tied to a specific customer.
    effective_from / effective_to: date range for validity.
    If effective_to is NULL, the list is open-ended (currently active).
    """

    __tablename__ = "price_lists"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    currency_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("currencies.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="NULL = standard list applicable to all customers",
    )
    effective_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    effective_to: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment="NULL = no expiry"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    currency: Mapped[Optional["Currency"]] = relationship("Currency", back_populates="price_lists")
    customer: Mapped[Optional["Customer"]] = relationship("Customer", back_populates="price_lists")
    items: Mapped[List["PriceListItem"]] = relationship(
        "PriceListItem", back_populates="price_list", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<PriceList name={self.name!r} customer_id={self.customer_id}>"


class PriceListItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    One price entry within a price list.

    Quantity-break example:
      min_qty=0    → price = 100,000 VND
      min_qty=10   → price = 95,000 VND
      min_qty=100  → price = 88,000 VND

    source_price / source_currency: original raw values from Excel/Odoo import.
    These MUST NOT be overwritten during re-imports.
    """

    __tablename__ = "price_list_items"

    price_list_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("price_lists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    uom_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("units_of_measure.id", ondelete="RESTRICT"),
        nullable=True,
    )

    min_qty: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False, default=0,
        comment="Minimum quantity for this price tier to apply"
    )
    price: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False,
        comment="Price in the price list's currency"
    )

    # Original source values — do not overwrite
    source_price: Mapped[Optional[float]] = mapped_column(
        Numeric(18, 4), nullable=True, comment="Original price from source file"
    )
    source_currency: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True, comment="Currency code from source file"
    )

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    price_list: Mapped["PriceList"] = relationship("PriceList", back_populates="items")
    product: Mapped["Product"] = relationship("Product", back_populates="price_list_items")
    uom: Mapped[Optional["UnitOfMeasure"]] = relationship("UnitOfMeasure", back_populates="price_list_items")

    def __repr__(self) -> str:
        return f"<PriceListItem product_id={self.product_id} min_qty={self.min_qty} price={self.price}>"
