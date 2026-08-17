"""
TradeCore — Unit of Measure Model
Tracks all measurement units used in products, orders, and movements.
Examples: Cái (piece), Chiếc (piece), Bộ (set), Kg, Tấn, Lít, Mét, Cuộn, Thùng.
"""
from __future__ import annotations

import enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Enum as SAEnum, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .product import Product
    from .pricing import PriceListItem
    from .inventory import StockMovement
    from .sales import SalesOrderItem
    from .purchase import PurchaseOrderItem


class UoMType(str, enum.Enum):
    """
    Odoo-aligned UoM type for unit conversion.
    reference: the reference unit in its category (factor = 1)
    smaller:   smaller than reference (factor < 1)
    bigger:    bigger than reference (factor > 1)
    """
    reference = "reference"
    smaller = "smaller"
    bigger = "bigger"


class UoMCategory(str, enum.Enum):
    """Broad category of unit (for grouping in UI)."""
    unit = "unit"          # Cái, Chiếc, Bộ, Hộp, Thùng, Cuộn
    weight = "weight"      # Kg, Tấn, Gram
    volume = "volume"      # Lít, m³
    length = "length"      # Mét, cm, mm
    area = "area"          # m²
    time = "time"          # Ngày, Tháng, Năm
    other = "other"


class UnitOfMeasure(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Unit of Measure master table.

    factor: relative conversion factor within its category.
    For a reference unit, factor = 1.
    For smaller units (e.g. gram vs kg): factor = 0.001.
    For bigger units (e.g. tấn vs kg): factor = 1000.
    """

    __tablename__ = "units_of_measure"

    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    symbol: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    category: Mapped[UoMCategory] = mapped_column(
        SAEnum(UoMCategory, name="uom_category"), nullable=False, default=UoMCategory.unit
    )
    uom_type: Mapped[UoMType] = mapped_column(
        SAEnum(UoMType, name="uom_type"), nullable=False, default=UoMType.reference
    )
    factor: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False, default=1.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    products_sale: Mapped[List["Product"]] = relationship(
        "Product", foreign_keys="Product.uom_id", back_populates="uom"
    )
    products_purchase: Mapped[List["Product"]] = relationship(
        "Product", foreign_keys="Product.purchase_uom_id", back_populates="purchase_uom"
    )
    price_list_items: Mapped[List["PriceListItem"]] = relationship(
        "PriceListItem", back_populates="uom"
    )
    stock_movements: Mapped[List["StockMovement"]] = relationship(
        "StockMovement", back_populates="uom"
    )
    sales_order_items: Mapped[List["SalesOrderItem"]] = relationship(
        "SalesOrderItem", back_populates="uom"
    )
    purchase_order_items: Mapped[List["PurchaseOrderItem"]] = relationship(
        "PurchaseOrderItem", back_populates="uom"
    )

    def __repr__(self) -> str:
        return f"<UnitOfMeasure name={self.name!r} category={self.category}>"
