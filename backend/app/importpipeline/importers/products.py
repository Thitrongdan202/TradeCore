"""
TradeCore — Product Importer

Pipeline:
  1. Read rows from Excel/CSV via SourceReader
  2. Map columns via ColumnMapper
  3. Validate each row (required fields, numeric parsing, duplicates)
  4. Stage valid rows into staging_products table
  5. Map staged rows to Product ORM objects
  6. Upsert into products table (ON CONFLICT code DO UPDATE)
  7. Log results to import_runs + import_run_rows
  8. Return ImportReport

Safe rules:
  - Never modify source data files
  - Never overwrite production data automatically — always upsert by code
  - Log every row decision in import_run_rows
  - Entire import is wrapped in a transaction; roll back on fatal error
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.importpipeline.mapper import ColumnMapper, PRODUCT_COLUMN_MAP
from app.importpipeline.reader import SourceReader
from app.importpipeline.report import ImportReport
from app.importpipeline.validators import (
    DuplicateDetector, Level, RowResult, ValidationMessage,
    validate_required, validate_product_code, validate_numeric,
    validate_price, validate_string_length, validate_uom,
)
from app.models import (
    Currency, ImportRun, ImportRunRow, Product, ProductCategory,
    StagingProduct, UnitOfMeasure,
)
from app.models.staging import EntityType, ImportRunStatus, RowStatus, SourceType, ValidationStatus


def _get_existing_codes(db: Session) -> Set[str]:
    rows = db.execute(select(Product.code)).scalars().all()
    return {r.upper() for r in rows}


def _get_uom_map(db: Session) -> Dict[str, uuid.UUID]:
    rows = db.execute(select(UnitOfMeasure.name, UnitOfMeasure.id)).all()
    return {name.strip().lower(): uid for name, uid in rows}


def _get_category_map(db: Session) -> Dict[str, uuid.UUID]:
    rows = db.execute(select(ProductCategory.name, ProductCategory.id)).all()
    return {name.strip().lower(): uid for name, uid in rows}


def _get_or_create_category(db: Session, name: str, category_map: Dict[str, uuid.UUID]) -> uuid.UUID:
    key = name.strip().lower()
    if key in category_map:
        return category_map[key]
    cat = ProductCategory(name=name.strip())
    db.add(cat)
    db.flush()
    category_map[key] = cat.id
    return cat.id


def _get_or_create_uom(db: Session, name: str, uom_map: Dict[str, uuid.UUID]) -> uuid.UUID:
    key = name.strip().lower()
    if key in uom_map:
        return uom_map[key]
    from app.models.uom import UoMCategory, UoMType
    uom = UnitOfMeasure(
        name=name.strip(),
        symbol=name.strip(),
        category=UoMCategory.unit,
        uom_type=UoMType.reference,
        factor=1.0,
    )
    db.add(uom)
    db.flush()
    uom_map[key] = uom.id
    return uom.id


def _validate_product_row(
    row: Dict[str, Any],
    row_number: int,
    existing_codes: Set[str],
    dup_detector: DuplicateDetector,
    known_uoms: Set[str],
) -> RowResult:
    result = RowResult(row_number=row_number, source_data=dict(row))

    # Required: code
    result.add(validate_product_code(row.get("code"), "code"))
    # Required: name
    result.add(validate_required(row.get("name"), "name"))
    result.add(validate_string_length(row.get("name"), "name", max_len=500))

    # Duplicate check within batch
    if row.get("code"):
        result.add(dup_detector.check(row["code"], row_number))

    # DB duplicate warning (existing codes get upserted, not rejected)
    code_upper = str(row.get("code", "")).strip().upper()
    if code_upper and code_upper in existing_codes:
        result.messages.append(ValidationMessage(
            level=Level.INFO, code="WILL_UPDATE_EXISTING",
            field="code",
            message=f"Product '{row['code']}' already exists — will update"
        ))

    # Numeric fields
    msgs, _ = validate_price(row.get("cost_price"), "cost_price")
    result.add(msgs)
    msgs, _ = validate_price(row.get("list_price"), "list_price")
    result.add(msgs)
    msgs, _ = validate_numeric(row.get("weight_kg"), "weight_kg", allow_zero=True, allow_negative=False)
    result.add(msgs)
    msgs, _ = validate_numeric(row.get("min_stock"), "min_stock", allow_zero=True, allow_negative=False)
    result.add(msgs)
    msgs, _ = validate_numeric(row.get("max_stock"), "max_stock", allow_zero=True, allow_negative=False)
    result.add(msgs)

    # UoM check (just warning — will auto-create if missing)
    result.add(validate_uom(row.get("uom"), "uom", known_uoms))

    return result


def _parse_decimal(value: Any) -> Optional[float]:
    if not value:
        return None
    from decimal import Decimal, InvalidOperation
    try:
        s = str(value).replace(",", "").replace("₫", "").strip()
        return float(Decimal(s))
    except (InvalidOperation, ValueError):
        return None


def import_products(
    db: Session,
    file_path: str,
    sheet_name: Optional[str] = None,
    skip_rows: int = 0,
    dry_run: bool = False,
    column_map_overrides: Optional[Dict[str, str]] = None,
) -> ImportReport:
    """
    Import products from Excel/CSV file.

    Args:
        db:          SQLAlchemy session (caller manages transaction)
        file_path:   Path to Excel or CSV file
        sheet_name:  Sheet name (optional, uses first sheet if None)
        skip_rows:   Number of rows to skip before header (default 0)
        dry_run:     If True, validate only — do not write to DB
        column_map_overrides: Extra source_col→target_field mappings

    Returns:
        ImportReport with full per-row results
    """
    reader = SourceReader(file_path, sheet_name=sheet_name, skip_rows=skip_rows)
    mapper = ColumnMapper(PRODUCT_COLUMN_MAP, column_map_overrides)
    report = ImportReport(
        entity_type="product",
        source_file=reader.file_name,
    )

    # Create import run record
    run = ImportRun(
        source_type=SourceType.excel,
        entity_type=EntityType.product,
        source_file=file_path,
        source_hash=reader.file_hash,
        status=ImportRunStatus.running,
        created_by="import_pipeline",
    )
    if not dry_run:
        db.add(run)
        db.flush()
        report.import_run_id = str(run.id)

    # Pre-load reference data
    existing_codes = _get_existing_codes(db)
    uom_map = _get_uom_map(db)
    category_map = _get_category_map(db)
    known_uoms: Set[str] = set(uom_map.keys())
    dup_detector = DuplicateDetector("code")

    row_records: List[ImportRunRow] = []
    staging_records: List[StagingProduct] = []

    # ── Pass 1: Read, map, validate ──────────────────────────────────────
    all_results: List[RowResult] = []
    for raw_row in reader.iter_rows():
        row_number = raw_row.get("_row_number", 0)
        mapped = mapper.map_row(raw_row)
        result = _validate_product_row(
            mapped, row_number, existing_codes, dup_detector, known_uoms
        )
        result.mapped_data = {k: v for k, v in mapped.items() if not k.startswith("_")}
        all_results.append(result)

    # ── Pass 2: Write to DB ───────────────────────────────────────────────
    for result in all_results:
        if not dry_run and not result.has_errors:
            mapped = result.mapped_data or {}

            # Resolve/create category
            cat_id = None
            if mapped.get("category"):
                cat_id = _get_or_create_category(db, str(mapped["category"]), category_map)

            # Resolve/create UoM
            uom_id = None
            if mapped.get("uom"):
                uom_id = _get_or_create_uom(db, str(mapped["uom"]), uom_map)

            purchase_uom_id = None
            if mapped.get("purchase_uom"):
                purchase_uom_id = _get_or_create_uom(db, str(mapped["purchase_uom"]), uom_map)

            code = str(mapped["code"]).strip()

            # Construct image_url
            safe_code = "".join(c if c.isalnum() else "_" for c in code)
            image_url = None
            # Basic check if image was extracted earlier
            img_path = Path(f"static/images/products/{safe_code}.jpg")
            if img_path.exists():
                image_url = f"/static/images/products/{safe_code}.jpg"
            elif Path(f"static/images/products/{safe_code}.png").exists():
                image_url = f"/static/images/products/{safe_code}.png"

            # Upsert product by code
            stmt = pg_insert(Product.__table__).values(
                code=code,
                name=str(mapped.get("name", "")).strip(),
                name_en=mapped.get("name_en"),
                description=mapped.get("description"),
                category_id=cat_id,
                uom_id=uom_id,
                purchase_uom_id=purchase_uom_id,
                cost_price=_parse_decimal(mapped.get("cost_price")),
                weight_kg=_parse_decimal(mapped.get("weight_kg")),
                min_stock=_parse_decimal(mapped.get("min_stock")),
                max_stock=_parse_decimal(mapped.get("max_stock")),
                barcode=mapped.get("barcode"),
                is_active=True,
                notes=mapped.get("_extra") and str(mapped.get("_extra", "")),
                image_url=image_url,
            ).on_conflict_do_update(
                index_elements=["code"],
                set_={
                    "name":            text("EXCLUDED.name"),
                    "name_en":         text("EXCLUDED.name_en"),
                    "description":     text("EXCLUDED.description"),
                    "category_id":     text("EXCLUDED.category_id"),
                    "uom_id":          text("EXCLUDED.uom_id"),
                    "purchase_uom_id": text("EXCLUDED.purchase_uom_id"),
                    "cost_price":      text("EXCLUDED.cost_price"),
                    "weight_kg":       text("EXCLUDED.weight_kg"),
                    "min_stock":       text("EXCLUDED.min_stock"),
                    "max_stock":       text("EXCLUDED.max_stock"),
                    "barcode":         text("EXCLUDED.barcode"),
                    "image_url":       text("EXCLUDED.image_url"),
                    "updated_at":      text("now()"),
                },
            ).returning(Product.__table__.c.id)

            res = db.execute(stmt)
            entity_id = res.scalar_one()
            result.entity_id = str(entity_id)

            # Stage record
            sp = StagingProduct(
                import_run_id=run.id,
                row_number=result.row_number,
                raw_code=raw_row.get("code") if (raw_row := result.source_data) else None,
                raw_name=result.source_data.get("name"),
                raw_category=result.source_data.get("category"),
                raw_uom=result.source_data.get("uom"),
                raw_cost_price=result.source_data.get("cost_price"),
                raw_list_price=result.source_data.get("list_price"),
                raw_barcode=result.source_data.get("barcode"),
                raw_extra=result.source_data.get("_extra"),
                mapped_code=code,
                mapped_name=str(mapped.get("name", "")).strip(),
                mapped_category_id=cat_id,
                mapped_uom_id=uom_id,
                validation_status=ValidationStatus.valid,
                product_id=entity_id,
            )
            staging_records.append(sp)

        elif not dry_run and result.has_errors:
            if not dry_run and run:
                sp = StagingProduct(
                    import_run_id=run.id,
                    row_number=result.row_number,
                    raw_code=result.source_data.get("code"),
                    raw_name=result.source_data.get("name"),
                    raw_extra=result.source_data.get("_extra"),
                    validation_status=ValidationStatus.invalid,
                    validation_errors=[m.to_dict() for m in result.messages if m.level == Level.ERROR],
                )
                staging_records.append(sp)

        report.add_row(result)

    # ── Write staging + run rows ──────────────────────────────────────────
    if not dry_run:
        for sp in staging_records:
            db.add(sp)

        for result in all_results:
            rr = ImportRunRow(
                import_run_id=run.id,
                row_number=result.row_number,
                status=RowStatus(result.status if result.status in ("ok","skipped","error","warning") else "error"),
                source_data=result.source_data,
                mapped_data=result.mapped_data,
                messages=[m.to_dict() for m in result.messages],
                entity_id=uuid.UUID(result.entity_id) if result.entity_id else None,
            )
            row_records.append(rr)
            db.add(rr)

        # Update import run
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
