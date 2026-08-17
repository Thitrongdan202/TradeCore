"""
TradeCore — Product Category & Product Models

CRITICAL BUSINESS RULE:
  Product codes (products.code) are STABLE IDENTIFIERS.
  Never duplicate a product because its name differs slightly.
  All upserts must use products.code as the primary lookup key.
  odoo_id and excel_row_hash fields are for migration traceability only.
"""
from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Enum as SAEnum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .uom import UnitOfMeasure
    from .pricing import PriceListItem
    from .inventory import StockMovement, StockBalance
    from .sales import SalesOrderItem
    from .purchase import PurchaseOrderItem
    from .staging import StagingProduct


class ProductType(str, enum.Enum):
    """
    Odoo-aligned product type.
    product:     Storable — tracked in inventory.
    consumable:  Not tracked in inventory (always considered in stock).
    service:     Service — no physical item.
    """
    product = "product"
    consumable = "consumable"
    service = "service"


class ProductCategory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Hierarchical product category.
    Parent categories can have child categories (tree structure, max 5 levels recommended).
    """

    __tablename__ = "product_categories"

    code: Mapped[Optional[str]] = mapped_column(String(40), unique=True, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Self-referential hierarchy
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    parent: Mapped[Optional["ProductCategory"]] = relationship(
        "ProductCategory",
        remote_side="ProductCategory.id",
        back_populates="children",
    )
    children: Mapped[List["ProductCategory"]] = relationship(
        "ProductCategory", back_populates="parent", cascade="all, delete-orphan"
    )

    # Products in this category
    products: Mapped[List["Product"]] = relationship("Product", back_populates="category")

    def __repr__(self) -> str:
        return f"<ProductCategory code={self.code!r} name={self.name!r}>"


class Product(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Product master record.

    products.code is the STABLE BUSINESS IDENTIFIER used as upsert key.
    Do not use products.id as the external code.

    Migration note:
      odoo_id: integer ID from Odoo res.product.template (for tracing origin).
      Source data is NEVER modified; this field is purely for audit.
    """

    __tablename__ = "products"

    # ── Identifiers ──────────────────────────────────────────────────────
    code: Mapped[str] = mapped_column(
        String(80), unique=True, nullable=False, index=True,
        comment="Stable business code — use as upsert key. Example: HH-2041"
    )
    barcode: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    # ── Names ─────────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    name_en: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Classification ────────────────────────────────────────────────────
    product_type: Mapped[ProductType] = mapped_column(
        SAEnum(ProductType, name="product_type"),
        nullable=False,
        default=ProductType.product,
    )
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Units of Measure ─────────────────────────────────────────────────
    uom_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("units_of_measure.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
        comment="Sale / stock unit",
    )
    purchase_uom_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("units_of_measure.id", ondelete="RESTRICT"),
        nullable=True,
        comment="Purchase unit (may differ from sale unit)",
    )

    # ── Pricing ──────────────────────────────────────────────────────────
    cost_price: Mapped[Optional[float]] = mapped_column(
        Numeric(18, 4), nullable=True, comment="Cost/COGS price in VND"
    )

    # ── Physical dimensions ──────────────────────────────────────────────
    weight_kg: Mapped[Optional[float]] = mapped_column(Numeric(10, 4), nullable=True)
    volume_m3: Mapped[Optional[float]] = mapped_column(Numeric(10, 6), nullable=True)

    # ── Stock thresholds ─────────────────────────────────────────────────
    min_stock: Mapped[Optional[float]] = mapped_column(
        Numeric(18, 4), nullable=True, comment="Reorder point / alert threshold"
    )
    max_stock: Mapped[Optional[float]] = mapped_column(
        Numeric(18, 4), nullable=True, comment="Maximum target stock level"
    )

    # ── Status & Notes ───────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Migration traceability ───────────────────────────────────────────
    odoo_id: Mapped[Optional[int]] = mapped_column(
        nullable=True, index=True, comment="Odoo product.template ID — migration only"
    )

    # ── Relationships ────────────────────────────────────────────────────
    category: Mapped[Optional["ProductCategory"]] = relationship(
        "ProductCategory", back_populates="products"
    )
    uom: Mapped[Optional["UnitOfMeasure"]] = relationship(
        "UnitOfMeasure", foreign_keys=[uom_id], back_populates="products_sale"
    )
    purchase_uom: Mapped[Optional["UnitOfMeasure"]] = relationship(
        "UnitOfMeasure", foreign_keys=[purchase_uom_id], back_populates="products_purchase"
    )
    price_list_items: Mapped[List["PriceListItem"]] = relationship(
        "PriceListItem", back_populates="product"
    )
    stock_movements: Mapped[List["StockMovement"]] = relationship(
        "StockMovement", back_populates="product"
    )
    stock_balances: Mapped[List["StockBalance"]] = relationship(
        "StockBalance", back_populates="product"
    )
    sales_order_items: Mapped[List["SalesOrderItem"]] = relationship(
        "SalesOrderItem", back_populates="product"
    )
    purchase_order_items: Mapped[List["PurchaseOrderItem"]] = relationship(
        "PurchaseOrderItem", back_populates="product"
    )

    def __repr__(self) -> str:
        return f"<Product code={self.code!r} name={self.name!r}>"
