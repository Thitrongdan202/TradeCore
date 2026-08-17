"""
TradeCore — Supplier Importer

Pipeline: Read Excel/CSV → Map columns → Validate → Upsert suppliers table → Log import_run
Upsert key: suppliers.code (NCC-XXXX or any stable code)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import select, text as sa_text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.importpipeline.mapper import ColumnMapper, SUPPLIER_COLUMN_MAP
from app.importpipeline.reader import SourceReader
from app.importpipeline.report import ImportReport
from app.importpipeline.validators import (
    DuplicateDetector, Level, RowResult, ValidationMessage,
    validate_required, validate_string_length, validate_email, validate_phone,
)
from app.models import ImportRun, ImportRunRow, PaymentTerm, Supplier
from app.models.staging import EntityType, ImportRunStatus, RowStatus, SourceType


def _get_existing_codes(db: Session) -> Set[str]:
    return {r.upper() for r in db.execute(select(Supplier.code)).scalars().all()}


def _get_payment_term_map(db: Session) -> Dict[str, uuid.UUID]:
    return {name.strip().lower(): uid
            for name, uid in db.execute(select(PaymentTerm.name, PaymentTerm.id)).all()}


def _validate_row(
    row: Dict[str, Any],
    row_number: int,
    existing_codes: Set[str],
    dup_detector: DuplicateDetector,
) -> RowResult:
    result = RowResult(row_number=row_number, source_data=dict(row))
    result.add(validate_required(row.get("code"), "code"))
    result.add(validate_required(row.get("name"), "name"))
    result.add(validate_string_length(row.get("code"), "code", min_len=2, max_len=40))
    result.add(validate_string_length(row.get("name"), "name", max_len=500))

    if row.get("code"):
        result.add(dup_detector.check(row["code"], row_number))
        if str(row["code"]).strip().upper() in existing_codes:
            result.messages.append(ValidationMessage(
                level=Level.INFO, code="WILL_UPDATE_EXISTING",
                field="code",
                message=f"Supplier '{row['code']}' already exists — will update"
            ))

    result.add(validate_email(row.get("email"), "email"))
    result.add(validate_phone(row.get("phone"), "phone"))
    return result


def import_suppliers(
    db: Session,
    file_path: str,
    sheet_name: Optional[str] = None,
    skip_rows: int = 0,
    dry_run: bool = False,
    column_map_overrides: Optional[Dict[str, str]] = None,
) -> ImportReport:
    """Import suppliers from Excel/CSV. Upserts by code."""
    reader = SourceReader(file_path, sheet_name=sheet_name, skip_rows=skip_rows)
    mapper = ColumnMapper(SUPPLIER_COLUMN_MAP, column_map_overrides)
    report = ImportReport(entity_type="supplier", source_file=reader.file_name)

    run = ImportRun(
        source_type=SourceType.excel,
        entity_type=EntityType.supplier,
        source_file=file_path,
        source_hash=reader.file_hash,
        status=ImportRunStatus.running,
        created_by="import_pipeline",
    )
    if not dry_run:
        db.add(run)
        db.flush()
        report.import_run_id = str(run.id)

    existing_codes = _get_existing_codes(db)
    payment_term_map = _get_payment_term_map(db)
    dup_detector = DuplicateDetector("code")
    all_results: List[RowResult] = []

    for raw_row in reader.iter_rows():
        row_number = raw_row.get("_row_number", 0)
        mapped = mapper.map_row(raw_row)
        result = _validate_row(mapped, row_number, existing_codes, dup_detector)
        result.mapped_data = {k: v for k, v in mapped.items() if not k.startswith("_")}
        all_results.append(result)

    for result in all_results:
        if not dry_run and not result.has_errors:
            mapped = result.mapped_data or {}
            code = str(mapped["code"]).strip()
            pt_id = payment_term_map.get(str(mapped.get("payment_term", "")).strip().lower()) if mapped.get("payment_term") else None

            stmt = pg_insert(Supplier.__table__).values(
                code=code,
                name=str(mapped.get("name", "")).strip(),
                short_name=mapped.get("short_name"),
                tax_code=mapped.get("tax_code"),
                country=mapped.get("country"),
                contact_name=mapped.get("contact_name"),
                phone=mapped.get("phone"),
                email=str(mapped.get("email", "")).lower() if mapped.get("email") else None,
                address=mapped.get("address"),
                payment_term_id=pt_id,
                is_active=True,
                notes=mapped.get("notes"),
            ).on_conflict_do_update(
                index_elements=["code"],
                set_={c.name: sa_text(f"EXCLUDED.{c.name}") for c in Supplier.__table__.c
                      if c.name not in ("id", "code", "created_at")},
            ).returning(Supplier.__table__.c.id)

            result.entity_id = str(db.execute(stmt).scalar_one())

        report.add_row(result)

    if not dry_run:
        for result in all_results:
            db.add(ImportRunRow(
                import_run_id=run.id,
                row_number=result.row_number,
                status=RowStatus(result.status if result.status in ("ok", "skipped", "error", "warning") else "error"),
                source_data=result.source_data,
                mapped_data=result.mapped_data,
                messages=[m.to_dict() for m in result.messages],
                entity_id=uuid.UUID(result.entity_id) if result.entity_id else None,
            ))

        run.total_rows = report.total_rows
        run.imported_rows = report.imported_rows
        run.skipped_rows = report.skipped_rows
        run.error_rows = report.error_rows
        run.warning_rows = report.warning_rows
        run.status = ImportRunStatus.completed if report.error_rows == 0 else ImportRunStatus.partial
        run.completed_at = datetime.now(timezone.utc)
        db.flush()

    report.finish()
    return report
