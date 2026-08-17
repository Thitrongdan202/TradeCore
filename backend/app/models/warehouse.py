"""
TradeCore — Warehouse & Location Models

Modelled after Odoo's stock.warehouse / stock.location concepts.

location_type mirrors Odoo location types:
  internal:  physical location inside a warehouse (bins, shelves, zones)
  supplier:  virtual incoming location (source of goods from suppliers)
  customer:  virtual outgoing location (destination of goods to customers)
  transit:   virtual transit location (in-transit shipments)
  virtual:   adjustments, losses, write-offs
"""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List, Optional

import enum
from sqlalchemy import Boolean, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .inventory import StockBalance, StockMovement


class LocationType(str, enum.Enum):
    internal = "internal"
    supplier = "supplier"
    customer = "customer"
    transit  = "transit"
    virtual  = "virtual"


class Warehouse(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Physical warehouse. The company may have one or more warehouses.
    All inventory transactions reference a warehouse location.
    """

    __tablename__ = "warehouses"

    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    locations: Mapped[List["WarehouseLocation"]] = relationship(
        "WarehouseLocation", back_populates="warehouse"
    )

    def __repr__(self) -> str:
        return f"<Warehouse code={self.code!r} name={self.name!r}>"


class WarehouseLocation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Hierarchical location within or linked to a warehouse.
    Supports multi-level bin/shelf/zone structures.

    Virtual locations (supplier, customer, transit, virtual) are not tied to
    a physical warehouse but are required for double-entry stock accounting.

    Examples:
      WH01 / Stock / Zone A / Shelf 1 / Bin A-01
      [Virtual] / Suppliers
      [Virtual] / Customers
      [Virtual] / Transit
    """

    __tablename__ = "warehouse_locations"

    code: Mapped[str] = mapped_column(String(60), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location_type: Mapped[LocationType] = mapped_column(
        SAEnum(LocationType, name="location_type"),
        nullable=False,
        default=LocationType.internal,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Which warehouse this physical location belongs to (NULL for virtual locations)
    warehouse_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Self-referential hierarchy
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("warehouse_locations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    parent: Mapped[Optional["WarehouseLocation"]] = relationship(
        "WarehouseLocation",
        remote_side="WarehouseLocation.id",
        back_populates="children",
    )
    children: Mapped[List["WarehouseLocation"]] = relationship(
        "WarehouseLocation", back_populates="parent"
    )

    # Relationships
    warehouse: Mapped[Optional["Warehouse"]] = relationship(
        "Warehouse", back_populates="locations"
    )
    stock_balances: Mapped[List["StockBalance"]] = relationship(
        "StockBalance", back_populates="location"
    )

    def __repr__(self) -> str:
        return f"<WarehouseLocation code={self.code!r} type={self.location_type}>"
