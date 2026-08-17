"""
TradeCore — Staging & Import Run Models

These tables form the SAFE MIGRATION LAYER between source data and production tables.

Import pipeline:
  Source file (Excel/CSV/Odoo XML)
    → staging table (raw import, no validation)
    → validation pass (detect errors, duplicates, missing fields)
    → mapping pass (transform to TradeCore domain)
    → production tables (only if validation passes)
    → import_run_rows (one row per source row, with status)
    → import_runs (one record per import job, with summary counts)

Rules:
  - Source data is NEVER modified.
  - Production data is NEVER automatically overwritten.
  - Every import is fully auditable via import_runs + import_run_rows.
  - A failed import can be rolled back by referencing the import_run_id.
  - Imports are repeatable (idempotent by default using upsert on stable codes).
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDPrimaryKeyMixin


class SourceType(str, enum.Enum):
    excel     = "excel"
    odoo_csv  = "odoo_csv"
    odoo_xml  = "odoo_xml"
    odoo_json = "odoo_json"
    manual    = "manual"


class EntityType(str, enum.Enum):
    product        = "product"
    product_category = "product_category"
    customer       = "customer"
    supplier       = "supplier"
    uom            = "uom"
    price_item     = "price_item"
    inventory      = "inventory"
    sales_order    = "sales_order"
    purchase_order = "purchase_order"
    shipment       = "shipment"
    currency       = "currency"
    payment_term   = "payment_term"


class ImportRunStatus(str, enum.Enum):
    running      = "running"
    completed    = "completed"
    failed       = "failed"
    rolled_back  = "rolled_back"
    partial      = "partial"


class RowStatus(str, enum.Enum):
    ok      = "ok"
    skipped = "skipped"
    error   = "error"
    warning = "warning"


class ValidationStatus(str, enum.Enum):
    pending = "pending"
    valid   = "valid"
    invalid = "invalid"


class ImportRun(Base, UUIDPrimaryKeyMixin):
    """
    One import run = one invocation of an import script for one entity type.
    Records summary statistics and can be used to roll back all rows from this run.
    """

    __tablename__ = "import_runs"

    source_type: Mapped[SourceType] = mapped_column(
        SAEnum(SourceType, name="source_type"), nullable=False
    )
    entity_type: Mapped[EntityType] = mapped_column(
        SAEnum(EntityType, name="entity_type"), nullable=False, index=True
    )
    source_file: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="Original filename or path"
    )
    source_hash: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="SHA-256 of source file for dedup detection"
    )

    status: Mapped[ImportRunStatus] = mapped_column(
        SAEnum(ImportRunStatus, name="import_run_status"),
        nullable=False,
        default=ImportRunStatus.running,
        index=True,
    )

    # Summary counts
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    imported_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    warning_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_summary: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, comment="Top-level error messages for the run"
    )

    rows: Mapped[list["ImportRunRow"]] = relationship(
        "ImportRunRow", back_populates="import_run", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<ImportRun id={self.id} entity={self.entity_type} "
            f"status={self.status} imported={self.imported_rows}/{self.total_rows}>"
        )


class ImportRunRow(Base, UUIDPrimaryKeyMixin):
    """
    Per-row result of an import run.
    source_data: raw values from the source file (JSON snapshot).
    mapped_data: values after transformation (what would be written to DB).
    messages: list of {level: error|warning|info, code: str, message: str}.
    entity_id: UUID of the created/updated record (if ok).
    """

    __tablename__ = "import_run_rows"

    import_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("import_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[RowStatus] = mapped_column(
        SAEnum(RowStatus, name="row_status"), nullable=False, default=RowStatus.ok, index=True
    )
    source_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    mapped_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    messages: Mapped[Optional[list]] = mapped_column(
        JSONB, nullable=True, comment="[{level, code, message}]"
    )
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True,
        comment="ID of created/updated entity — NULL if skipped or error"
    )

    import_run: Mapped["ImportRun"] = relationship("ImportRun", back_populates="rows")

    def __repr__(self) -> str:
        return f"<ImportRunRow run={self.import_run_id} row={self.row_number} status={self.status}>"


class StagingProduct(Base, UUIDPrimaryKeyMixin):
    """
    Staging table for product imports.
    All columns are nullable — raw data may be incomplete.
    Validation pass fills validation_status and validation_errors.
    """

    __tablename__ = "staging_products"

    import_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("import_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Raw source values (untouched)
    raw_code: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    raw_name: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    raw_name_en: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    raw_category: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    raw_uom: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    raw_purchase_uom: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    raw_cost_price: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    raw_list_price: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    raw_barcode: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    raw_weight: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    raw_min_stock: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    raw_max_stock: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    raw_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_extra: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, comment="Any extra columns not explicitly mapped"
    )

    # Mapped/normalized values (after transformation)
    mapped_code: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    mapped_name: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    mapped_category_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    mapped_uom_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    mapped_purchase_uom_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    mapped_cost_price: Mapped[Optional[float]] = mapped_column(nullable=True)
    mapped_list_price: Mapped[Optional[float]] = mapped_column(nullable=True)

    validation_status: Mapped[ValidationStatus] = mapped_column(
        SAEnum(ValidationStatus, name="validation_status"),
        nullable=False,
        default=ValidationStatus.pending,
        index=True,
    )
    validation_errors: Mapped[Optional[list]] = mapped_column(
        JSONB, nullable=True, comment="[{level, code, field, message}]"
    )

    # FK to the created product (if import succeeded)
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<StagingProduct run={self.import_run_id} "
            f"row={self.row_number} code={self.raw_code!r} status={self.validation_status}>"
        )
