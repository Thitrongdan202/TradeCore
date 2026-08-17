"""
TradeCore — Shipment, Container, ImportOrder, ExportOrder Models

Covers import/export logistics:
  Shipment: the sea/air freight shipment (lô hàng)
  Container: individual containers within a shipment
  ImportOrder: customs-cleared import declaration (tờ khai nhập khẩu)
  ExportOrder: customs-cleared export declaration (tờ khai xuất khẩu)
"""
from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Date, Enum as SAEnum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .partner import Supplier
    from .purchase import PurchaseOrder


class ShipmentType(str, enum.Enum):
    import_ = "import"
    export  = "export"
    both    = "both"


class ShipmentStatus(str, enum.Enum):
    booking   = "booking"
    loading   = "loading"
    in_transit = "in_transit"
    arrived   = "arrived"
    customs   = "customs"
    warehoused = "warehoused"
    completed = "completed"
    cancelled = "cancelled"


class ContainerType(str, enum.Enum):
    fcl_20gp = "20GP"
    fcl_40gp = "40GP"
    fcl_40hc = "40HC"
    lcl      = "LCL"
    air      = "AIR"


class Shipment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Sea/air freight shipment (lô hàng).
    shipment_number follows SHP-YYMM-XXXX convention.

    ETD = Estimated Time of Departure
    ETA = Estimated Time of Arrival
    ATA = Actual Time of Arrival (filled on arrival)
    """

    __tablename__ = "shipments"

    shipment_number: Mapped[str] = mapped_column(
        String(40), unique=True, nullable=False, index=True
    )
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    shipment_type: Mapped[ShipmentType] = mapped_column(
        SAEnum(ShipmentType, name="shipment_type"),
        nullable=False,
        default=ShipmentType.import_,
    )

    # ── Partners ─────────────────────────────────────────────────────────
    supplier_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Route ────────────────────────────────────────────────────────────
    origin_country: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    destination_country: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    port_origin: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    port_destination: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    incoterm: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # ── Dates ────────────────────────────────────────────────────────────
    etd: Mapped[Optional[str]] = mapped_column(Date, nullable=True)
    eta: Mapped[Optional[str]] = mapped_column(Date, nullable=True)
    ata: Mapped[Optional[str]] = mapped_column(Date, nullable=True)

    # ── Status ───────────────────────────────────────────────────────────
    status: Mapped[ShipmentStatus] = mapped_column(
        SAEnum(ShipmentStatus, name="shipment_status"),
        nullable=False,
        default=ShipmentStatus.booking,
        index=True,
    )

    # ── Cargo summary ────────────────────────────────────────────────────
    total_weight_kg: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    total_value_usd: Mapped[Optional[float]] = mapped_column(Numeric(18, 2), nullable=True)
    freight_cost: Mapped[Optional[float]] = mapped_column(Numeric(18, 2), nullable=True)
    freight_currency: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    supplier: Mapped[Optional["Supplier"]] = relationship("Supplier", back_populates="shipments")
    containers: Mapped[List["Container"]] = relationship(
        "Container", back_populates="shipment", cascade="all, delete-orphan"
    )
    import_orders: Mapped[List["ImportOrder"]] = relationship(
        "ImportOrder", back_populates="shipment"
    )
    export_orders: Mapped[List["ExportOrder"]] = relationship(
        "ExportOrder", back_populates="shipment"
    )

    def __repr__(self) -> str:
        return f"<Shipment number={self.shipment_number!r} status={self.status}>"


class Container(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Individual container within a shipment."""

    __tablename__ = "containers"

    shipment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shipments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    container_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    seal_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    container_type: Mapped[Optional[ContainerType]] = mapped_column(
        SAEnum(ContainerType, name="container_type"), nullable=True
    )
    weight_kg: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    shipment: Mapped["Shipment"] = relationship("Shipment", back_populates="containers")

    def __repr__(self) -> str:
        return f"<Container number={self.container_number!r} type={self.container_type}>"


class ImportOrder(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Customs import declaration (tờ khai nhập khẩu).
    Linked to the shipment it covers.
    """

    __tablename__ = "import_orders"

    reference_number: Mapped[Optional[str]] = mapped_column(String(60), nullable=True, index=True)
    customs_declaration_number: Mapped[Optional[str]] = mapped_column(String(60), nullable=True, index=True)

    shipment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shipments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    import_date: Mapped[Optional[str]] = mapped_column(Date, nullable=True)
    total_value_vnd: Mapped[Optional[float]] = mapped_column(Numeric(18, 2), nullable=True)
    total_tax_vnd: Mapped[Optional[float]] = mapped_column(Numeric(18, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    shipment: Mapped[Optional["Shipment"]] = relationship("Shipment", back_populates="import_orders")

    def __repr__(self) -> str:
        return f"<ImportOrder ref={self.reference_number!r} status={self.status!r}>"


class ExportOrder(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Customs export declaration (tờ khai xuất khẩu).
    Linked to the shipment it covers.
    """

    __tablename__ = "export_orders"

    reference_number: Mapped[Optional[str]] = mapped_column(String(60), nullable=True, index=True)
    customs_declaration_number: Mapped[Optional[str]] = mapped_column(String(60), nullable=True, index=True)

    shipment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shipments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    export_date: Mapped[Optional[str]] = mapped_column(Date, nullable=True)
    total_value_usd: Mapped[Optional[float]] = mapped_column(Numeric(18, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    shipment: Mapped[Optional["Shipment"]] = relationship("Shipment", back_populates="export_orders")

    def __repr__(self) -> str:
        return f"<ExportOrder ref={self.reference_number!r} status={self.status!r}>"
