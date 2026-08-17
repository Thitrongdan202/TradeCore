"""
TradeCore — Inventory Opening Balance Importer

Imports opening stock balances from Excel/CSV.

CRITICAL RULES:
  - Every quantity change creates an immutable StockMovement record
  - StockBalance is updated atomically in the same transaction
  - movement_type = 'opening' for all opening balance rows
  - reference_type = 'import_run'
  - Products must exist before inventory can be imported
  - Location is resolved by warehouse_code / location_code from seed data
  - If location not found, defaults to WH01/STOCK
  - NEVER overwrites an existing balance — always creates a movement to adjust
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from sqlalchemy import select, text as sa_text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.importpipeline.mapper import ColumnMapper, INVENTORY_COLUMN_MAP
from app.importpipeline.reader import SourceReader
from app.importpipeline.report import ImportReport
from app.importpipeline.validators import (
    DuplicateDetector, Level, RowResult, ValidationMessage,
    validate_required, validate_quantity, validate_price, validate_date,
)
from app.models import ImportRun, ImportRunRow, Product, StockBalance, StockMovement, UnitOfMeasure, WarehouseLocation
from app.models.inventory import MovementType, ReferenceType
from app.models.staging import EntityType, ImportRunStatus, RowStatus, SourceType


def _get_product_map(db: Session) -> Dict[str, Dict]:
    """Returns code.upper() → {id, uom_id}"""
    rows = db.execute(select(Product.code, Product.id, Product.uom_id)).all()
    return {code.upper(): {"id": pid, "uom_id": uom_id} for code, pid, uom_id in rows}


def _get_location_map(db: Session) -> Dict[str, uuid.UUID]:
    """code.upper() → location.id"""
    rows = db.execute(select(WarehouseLocation.code, WarehouseLocation.id)).all()
    return {code.upper(): uid for code, uid in rows}


def _get_default_location(db: Session) -> Optional[uuid.UUID]:
    """Returns WH01/STOCK id, the default internal stock location."""
    return db.execute(
        select(WarehouseLocation.id).where(WarehouseLocation.code == "WH01/STOCK")
    ).scalar_one_or_none()


def _get_virtual_supplier_location(db: Session) -> Optional[uuid.UUID]:
    return db.execute(
        select(WarehouseLocation.id).where(WarehouseLocation.code == "VIRTUAL/SUPPLIERS")
    ).scalar_one_or_none()


def _parse_decimal(value: Any) -> Optional[Decimal]:
    if not value:
        return None
    try:
        return Decimal(str(value).replace(",", "").strip())
    except InvalidOperation:
        return None


def _validate_row(
    row: Dict[str, Any],
    row_number: int,
    product_map: Dict[str, Dict],
    dup_detector: DuplicateDetector,
) -> RowResult:
    result = RowResult(row_number=row_number, source_data=dict(row))
    result.add(validate_required(row.get("product_code"), "product_code"))

    msgs, qty = validate_quantity(row.get("qty"), "qty")
    result.add(msgs)
    if qty is None and not result.has_errors:
        result.messages.append(ValidationMessage(
            level=Level.ERROR, code="QTY_REQUIRED", field="qty",
            message="Quantity is required for inventory import"
        ))

    if row.get("product_code"):
        code = str(row["product_code"]).strip().upper()
        if code not in product_map:
            result.messages.append(ValidationMessage(
                level=Level.ERROR, code="PRODUCT_NOT_FOUND", field="product_code",
                message=f"Product '{row['product_code']}' not found. Import products first."
            ))
        else:
            # Check for duplicate product+location in batch
            loc = str(row.get("location_code") or row.get("warehouse_code") or "WH01/STOCK")
            dup_key = f"{code}::{loc}"
            result.add(dup_detector.check(dup_key, row_number))

    msgs, _ = validate_price(row.get("cost_price"), "cost_price")
    result.add(msgs)

    return result


def import_inventory(
    db: Session,
    file_path: str,
    sheet_name: Optional[str] = None,
    skip_rows: int = 0,
    dry_run: bool = False,
    column_map_overrides: Optional[Dict[str, str]] = None,
    movement_date: Optional[date] = None,
) -> ImportReport:
    """
    Import opening inventory balances from Excel/CSV.

    Each row creates an opening StockMovement and updates StockBalance.
    """
    reader = SourceReader(file_path, sheet_name=sheet_name, skip_rows=skip_rows)
    mapper = ColumnMapper(INVENTORY_COLUMN_MAP, column_map_overrides)
    report = ImportReport(entity_type="inventory", source_file=reader.file_name)

    run = ImportRun(
        source_type=SourceType.excel,
        entity_type=EntityType.inventory,
        source_file=file_path,
        source_hash=reader.file_hash,
        status=ImportRunStatus.running,
        created_by="import_pipeline",
    )
    if not dry_run:
        db.add(run)
        db.flush()
        report.import_run_id = str(run.id)

    product_map = _get_product_map(db)
    location_map = _get_location_map(db)
    default_location_id = _get_default_location(db)
    supplier_location_id = _get_virtual_supplier_location(db)

    dup_detector = DuplicateDetector("product_code+location")
    all_results: List[RowResult] = []
    as_of = movement_date or date.today()

    for raw_row in reader.iter_rows():
        row_number = raw_row.get("_row_number", 0)
        mapped = mapper.map_row(raw_row)
        result = _validate_row(mapped, row_number, product_map, dup_detector)
        result.mapped_data = {k: v for k, v in mapped.items() if not k.startswith("_")}
        all_results.append(result)

    for result in all_results:
        if not dry_run and not result.has_errors:
            mapped = result.mapped_data or {}
            code = str(mapped["product_code"]).strip().upper()
            product_info = product_map.get(code, {})
            product_id = product_info.get("id")
            uom_id = product_info.get("uom_id")
            if not product_id:
                report.add_row(result)
                continue

            # Resolve location
            loc_code = str(mapped.get("location_code") or mapped.get("warehouse_code") or "").strip().upper()
            if loc_code and loc_code in location_map:
                to_location_id = location_map[loc_code]
            elif loc_code and not loc_code.startswith("WH"):
                # Try prefixing with WH01/
                to_location_id = location_map.get(f"WH01/{loc_code}", default_location_id)
            else:
                to_location_id = default_location_id

            qty = _parse_decimal(mapped.get("qty"))
            cost_price = _parse_decimal(mapped.get("cost_price"))

            if not qty or qty <= 0:
                report.add_row(result)
                continue

            # Create opening stock movement
            movement = StockMovement(
                movement_type=MovementType.opening,
                reference_type=ReferenceType.import_run,
                reference=str(run.id),
                product_id=product_id,
                uom_id=uom_id,
                qty=float(qty),
                cost_price=float(cost_price) if cost_price else None,
                from_location_id=supplier_location_id,
                to_location_id=to_location_id,
                moved_at=datetime.combine(as_of, datetime.min.time()).replace(tzinfo=timezone.utc),
                notes=f"Opening balance imported from {reader.file_name}",
            )
            db.add(movement)
            db.flush()

            # Upsert stock balance
            stmt = pg_insert(StockBalance.__table__).values(
                product_id=product_id,
                location_id=to_location_id,
                qty_on_hand=float(qty),
                last_updated_at=datetime.now(timezone.utc),
            ).on_conflict_do_update(
                index_elements=["product_id", "location_id"],
                set_={
                    "qty_on_hand":     sa_text("stock_balances.qty_on_hand + EXCLUDED.qty_on_hand"),
                    "last_updated_at": sa_text("now()"),
                },
            ).returning(StockBalance.__table__.c.id)
            balance_id = db.execute(stmt).scalar_one()
            result.entity_id = str(movement.id)

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
