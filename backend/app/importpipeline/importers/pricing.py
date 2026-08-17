"""
TradeCore — Pricing Importer

Imports product pricing from Excel/CSV into price_list_items.

Strategy:
  - Each import file creates or reuses a named PriceList
  - If the product exists (by code), a PriceListItem is upserted
  - If the product does not exist, the row is flagged as error (products must be imported first)
  - Preserves original source_price and source_currency for audit trail

Upsert key: (price_list_id, product_id, min_qty) — allows quantity-break pricing
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from sqlalchemy import select, text as sa_text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.importpipeline.mapper import ColumnMapper, PRICE_COLUMN_MAP
from app.importpipeline.reader import SourceReader
from app.importpipeline.report import ImportReport
from app.importpipeline.validators import (
    DuplicateDetector, Level, RowResult, ValidationMessage,
    validate_required, validate_price, validate_numeric, validate_date,
)
from app.models import Currency, ImportRun, ImportRunRow, PriceList, PriceListItem, Product
from app.models.staging import EntityType, ImportRunStatus, RowStatus, SourceType


def _get_product_map(db: Session) -> Dict[str, uuid.UUID]:
    """code (upper) → product.id"""
    return {code.upper(): uid
            for code, uid in db.execute(select(Product.code, Product.id)).all()}


def _get_currency_map(db: Session) -> Dict[str, uuid.UUID]:
    return {code.upper(): uid
            for code, uid in db.execute(select(Currency.code, Currency.id)).all()}


def _get_or_create_pricelist(
    db: Session,
    name: str,
    currency_id: Optional[uuid.UUID],
    customer_id: Optional[uuid.UUID] = None,
) -> uuid.UUID:
    existing = db.execute(select(PriceList.id).where(PriceList.name == name)).scalar_one_or_none()
    if existing:
        return existing
    pl = PriceList(name=name, currency_id=currency_id, customer_id=customer_id, is_active=True)
    db.add(pl)
    db.flush()
    return pl.id


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
    product_map: Dict[str, uuid.UUID],
    known_currencies: set,
) -> RowResult:
    result = RowResult(row_number=row_number, source_data=dict(row))

    result.add(validate_required(row.get("product_code"), "product_code"))
    msgs, price = validate_price(row.get("price"), "price")
    result.add(msgs)
    if price is None and not result.has_errors:
        result.messages.append(ValidationMessage(
            level=Level.ERROR, code="PRICE_REQUIRED", field="price",
            message="Price is required for pricing import"
        ))

    if row.get("product_code"):
        code = str(row["product_code"]).strip().upper()
        if code not in product_map:
            result.messages.append(ValidationMessage(
                level=Level.ERROR, code="PRODUCT_NOT_FOUND", field="product_code",
                message=f"Product '{row['product_code']}' not found. Import products first."
            ))

    if row.get("currency") and str(row["currency"]).strip().upper() not in known_currencies:
        result.messages.append(ValidationMessage(
            level=Level.WARNING, code="UNKNOWN_CURRENCY", field="currency",
            message=f"Currency '{row['currency']}' not in system — defaulting to VND"
        ))

    msgs, _ = validate_numeric(row.get("min_qty"), "min_qty", allow_zero=True, allow_negative=False)
    result.add(msgs)

    return result


def import_pricing(
    db: Session,
    file_path: str,
    price_list_name: str = "Standard",
    sheet_name: Optional[str] = None,
    skip_rows: int = 0,
    dry_run: bool = False,
    column_map_overrides: Optional[Dict[str, str]] = None,
) -> ImportReport:
    """
    Import pricing from Excel/CSV into a named PriceList.

    Args:
        price_list_name: Name of the PriceList to use (created if not exists)
        dry_run: Validate only, no DB writes
    """
    reader = SourceReader(file_path, sheet_name=sheet_name, skip_rows=skip_rows)
    mapper = ColumnMapper(PRICE_COLUMN_MAP, column_map_overrides)
    report = ImportReport(entity_type="price_item", source_file=reader.file_name)

    run = ImportRun(
        source_type=SourceType.excel,
        entity_type=EntityType.price_item,
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
    currency_map = _get_currency_map(db)
    known_currencies = set(currency_map.keys())

    # Default currency = VND
    vnd_id = currency_map.get("VND")

    all_results: List[RowResult] = []

    for raw_row in reader.iter_rows():
        row_number = raw_row.get("_row_number", 0)
        mapped = mapper.map_row(raw_row)
        result = _validate_row(mapped, row_number, product_map, known_currencies)
        result.mapped_data = {k: v for k, v in mapped.items() if not k.startswith("_")}
        all_results.append(result)

    # Create PriceList once (before processing rows)
    price_list_id = None
    if not dry_run:
        price_list_id = _get_or_create_pricelist(db, price_list_name, vnd_id)

    for result in all_results:
        if not dry_run and not result.has_errors and price_list_id:
            mapped = result.mapped_data or {}
            code = str(mapped["product_code"]).strip().upper()
            product_id = product_map.get(code)
            if not product_id:
                report.add_row(result)
                continue

            # Resolve currency
            curr_code = str(mapped.get("currency", "VND")).strip().upper()
            currency_id = currency_map.get(curr_code, vnd_id)

            price = _parse_decimal(mapped.get("price"))
            min_qty = _parse_decimal(mapped.get("min_qty")) or Decimal("0")
            source_price = _parse_decimal(mapped.get("price"))  # preserve original

            # Upsert on (price_list_id, product_id, min_qty)
            existing = db.execute(
                select(PriceListItem.id).where(
                    PriceListItem.price_list_id == price_list_id,
                    PriceListItem.product_id == product_id,
                    PriceListItem.min_qty == float(min_qty),
                )
            ).scalar_one_or_none()

            if existing:
                db.execute(
                    PriceListItem.__table__.update()
                    .where(PriceListItem.__table__.c.id == existing)
                    .values(
                        price=float(price) if price else 0,
                        source_price=float(source_price) if source_price else None,
                        source_currency=curr_code,
                        updated_at=datetime.now(timezone.utc),
                    )
                )
                result.entity_id = str(existing)
            else:
                item = PriceListItem(
                    price_list_id=price_list_id,
                    product_id=product_id,
                    min_qty=float(min_qty),
                    price=float(price) if price else 0,
                    source_price=float(source_price) if source_price else None,
                    source_currency=curr_code,
                )
                db.add(item)
                db.flush()
                result.entity_id = str(item.id)

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
