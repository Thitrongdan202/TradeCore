"""
TradeCore — Inventory Models: StockMovement & StockBalance

CRITICAL INVENTORY RULES:
  1. Stock is TRANSACTION-BASED. Never overwrite a quantity field directly.
  2. Every stock change MUST create a StockMovement record.
  3. All stock transactions must be ATOMIC (wrap in DB transaction).
  4. Negative stock is PREVENTED by the application layer (not just DB).
  5. StockBalance is a MATERIALIZED summary — always derived from StockMovements.
  6. StockMovement records are IMMUTABLE after creation (no updates, no deletes).

Movement types:
  receive:    Goods received from supplier (PO confirmation → goods receipt)
  issue:      Goods issued to customer (SO → delivery)
  transfer:   Internal transfer between locations
  adjustment: Manual inventory correction (positive or negative)
  opening:    Initial stock balance loaded during migration
  scrap:      Write-off / damaged goods
  return_in:  Customer return (goods back in)
  return_out: Supplier return (goods sent back to supplier)
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean, CheckConstraint, DateTime, Enum as SAEnum,
    ForeignKey, Numeric, String, Text, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .product import Product
    from .uom import UnitOfMeasure
    from .warehouse import WarehouseLocation
    from .user import User


class MovementType(str, enum.Enum):
    receive    = "receive"
    issue      = "issue"
    transfer   = "transfer"
    adjustment = "adjustment"
    opening    = "opening"
    scrap      = "scrap"
    return_in  = "return_in"
    return_out = "return_out"


class ReferenceType(str, enum.Enum):
    sale_order     = "sale_order"
    purchase_order = "purchase_order"
    shipment       = "shipment"
    manual         = "manual"
    opening        = "opening"
    import_run     = "import_run"


class StockMovement(Base, UUIDPrimaryKeyMixin):
    """
    Immutable stock movement ledger entry.

    IMMUTABILITY: This table should NEVER have UPDATE or DELETE in production.
    Corrections must be made by creating a new offsetting movement.

    qty must always be positive. The direction of stock change is determined by
    from_location_id and to_location_id:
      - from = supplier virtual, to = internal → receive (+stock)
      - from = internal, to = customer virtual → issue (-stock)
      - from = internal A, to = internal B → transfer
      - from = virtual (adjustment), to = internal → positive adjustment
      - from = internal, to = virtual (adjustment) → negative adjustment
    """

    __tablename__ = "stock_movements"

    __table_args__ = (
        CheckConstraint("qty > 0", name="ck_stock_movements_qty_positive"),
    )

    movement_type: Mapped[MovementType] = mapped_column(
        SAEnum(MovementType, name="movement_type"), nullable=False, index=True
    )
    reference_type: Mapped[Optional[ReferenceType]] = mapped_column(
        SAEnum(ReferenceType, name="reference_type"), nullable=True
    )
    reference: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True,
        comment="Human-readable reference: SO-2408-0134, PO-2408-0047, etc."
    )
    reference_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True,
        comment="FK to the originating order/shipment (not enforced by DB constraint)"
    )

    # ── Product & Quantity ───────────────────────────────────────────────
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    uom_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("units_of_measure.id", ondelete="RESTRICT"),
        nullable=True,
    )
    qty: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False,
        comment="Always positive. Direction determined by from/to locations."
    )
    cost_price: Mapped[Optional[float]] = mapped_column(
        Numeric(18, 4), nullable=True, comment="Unit cost at time of movement (VND)"
    )

    # ── Locations (double-entry) ─────────────────────────────────────────
    from_location_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("warehouse_locations.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    to_location_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("warehouse_locations.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    # ── Timestamps ───────────────────────────────────────────────────────
    moved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Business date/time of the stock movement"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── Audit ────────────────────────────────────────────────────────────
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Relationships ────────────────────────────────────────────────────
    product: Mapped["Product"] = relationship("Product", back_populates="stock_movements")
    uom: Mapped[Optional["UnitOfMeasure"]] = relationship(
        "UnitOfMeasure", back_populates="stock_movements"
    )

    def __repr__(self) -> str:
        return (
            f"<StockMovement type={self.movement_type} "
            f"product_id={self.product_id} qty={self.qty}>"
        )


class StockBalance(Base, UUIDPrimaryKeyMixin):
    """
    Materialized current stock per product per location.

    This table is DERIVED from StockMovements. It should be:
      - Updated atomically in the same transaction as each StockMovement insertion.
      - Never updated directly by business logic other than the inventory service.
      - Read-only from any API endpoint (use for dashboard/inventory queries).

    qty_on_hand should equal:
      SUM(qty) for movements TO this location
      MINUS SUM(qty) for movements FROM this location

    The application layer PREVENTS negative qty_on_hand (checked before insert).
    """

    __tablename__ = "stock_balances"

    __table_args__ = (
        UniqueConstraint("product_id", "location_id", name="uq_stock_balance_product_location"),
        CheckConstraint("qty_on_hand >= 0", name="ck_stock_balance_nonnegative"),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("warehouse_locations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    qty_on_hand: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False, default=0
    )
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="stock_balances")
    location: Mapped["WarehouseLocation"] = relationship(
        "WarehouseLocation", back_populates="stock_balances"
    )

    def __repr__(self) -> str:
        return (
            f"<StockBalance product_id={self.product_id} "
            f"location_id={self.location_id} qty={self.qty_on_hand}>"
        )
