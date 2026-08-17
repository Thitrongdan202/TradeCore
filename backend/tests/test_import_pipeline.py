"""
TradeCore — Import Pipeline Test Suite

Tests cover:
  - Validator functions (unit tests, no DB)
  - ColumnMapper (unit tests, no DB)
  - SourceReader with synthetic data (no real files needed)
  - ImportReport accumulation
  - Full import pipeline integration tests (uses real DB)
  - Duplicate detection (batch + DB)
  - Error handling and rollback
  - Vietnamese character handling

Run:
    cd backend
    .venv\\Scripts\\pytest tests/test_import_pipeline.py -v
"""
from __future__ import annotations

import csv
import io
import tempfile
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Dict, Any
from unittest.mock import MagicMock, patch

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# VALIDATOR UNIT TESTS  (pure Python, no DB)
# ─────────────────────────────────────────────────────────────────────────────

class TestValidateRequired:
    def test_none_is_error(self):
        from app.importpipeline.validators import validate_required, Level
        msgs = validate_required(None, "code")
        assert len(msgs) == 1
        assert msgs[0].level == Level.ERROR
        assert msgs[0].code == "REQUIRED_FIELD_MISSING"

    def test_empty_string_is_error(self):
        from app.importpipeline.validators import validate_required, Level
        msgs = validate_required("   ", "code")
        assert any(m.level == Level.ERROR for m in msgs)

    def test_valid_value_passes(self):
        from app.importpipeline.validators import validate_required
        msgs = validate_required("HH-0001", "code")
        assert msgs == []

    def test_zero_is_valid(self):
        from app.importpipeline.validators import validate_required
        msgs = validate_required(0, "quantity")
        assert msgs == []


class TestValidateNumeric:
    def test_valid_integer(self):
        from app.importpipeline.validators import validate_numeric
        msgs, val = validate_numeric("100", "qty")
        assert msgs == []
        assert val == Decimal("100")

    def test_valid_decimal(self):
        from app.importpipeline.validators import validate_numeric
        msgs, val = validate_numeric("99.99", "price")
        assert msgs == []
        assert val == Decimal("99.99")

    def test_comma_thousands_separator(self):
        from app.importpipeline.validators import validate_numeric
        msgs, val = validate_numeric("1,234,567", "amount")
        assert msgs == []
        assert val == Decimal("1234567")

    def test_negative_rejected_by_default(self):
        from app.importpipeline.validators import validate_numeric, Level
        msgs, val = validate_numeric("-5", "qty", allow_negative=False)
        assert any(m.level == Level.ERROR for m in msgs)

    def test_negative_allowed(self):
        from app.importpipeline.validators import validate_numeric
        msgs, val = validate_numeric("-5", "adjustment", allow_negative=True)
        assert msgs == []
        assert val == Decimal("-5")

    def test_invalid_string(self):
        from app.importpipeline.validators import validate_numeric, Level
        msgs, val = validate_numeric("abc", "qty")
        assert any(m.code == "INVALID_NUMBER" for m in msgs)
        assert val is None

    def test_none_returns_none(self):
        from app.importpipeline.validators import validate_numeric
        msgs, val = validate_numeric(None, "qty")
        assert msgs == []
        assert val is None

    def test_vnd_symbol_stripped(self):
        from app.importpipeline.validators import validate_numeric
        msgs, val = validate_numeric("500,000₫", "price")
        assert msgs == []
        assert val == Decimal("500000")


class TestValidateDate:
    def test_iso_format(self):
        from app.importpipeline.validators import validate_date
        msgs, d = validate_date("2024-01-15", "date")
        assert msgs == []
        assert d.year == 2024
        assert d.month == 1
        assert d.day == 15

    def test_vn_format(self):
        from app.importpipeline.validators import validate_date
        msgs, d = validate_date("15/01/2024", "date")
        assert msgs == []
        assert d.year == 2024

    def test_invalid_date(self):
        from app.importpipeline.validators import validate_date, Level
        msgs, d = validate_date("not-a-date", "date")
        assert any(m.level == Level.ERROR for m in msgs)
        assert d is None

    def test_none_returns_none(self):
        from app.importpipeline.validators import validate_date
        msgs, d = validate_date(None, "date")
        assert msgs == []
        assert d is None


class TestValidateEmail:
    def test_valid_email(self):
        from app.importpipeline.validators import validate_email
        msgs = validate_email("user@example.com", "email")
        assert msgs == []

    def test_invalid_email_warns(self):
        from app.importpipeline.validators import validate_email, Level
        msgs = validate_email("not-an-email", "email")
        assert any(m.level == Level.WARNING for m in msgs)

    def test_none_passes(self):
        from app.importpipeline.validators import validate_email
        msgs = validate_email(None, "email")
        assert msgs == []


class TestValidateProductCode:
    def test_valid_code(self):
        from app.importpipeline.validators import validate_product_code
        msgs = validate_product_code("HH-0001")
        assert msgs == []

    def test_single_char_rejected(self):
        from app.importpipeline.validators import validate_product_code, Level
        msgs = validate_product_code("X")
        assert any(m.level == Level.ERROR for m in msgs)

    def test_none_rejected(self):
        from app.importpipeline.validators import validate_product_code, Level
        msgs = validate_product_code(None)
        assert any(m.level == Level.ERROR for m in msgs)

    def test_xss_char_warns(self):
        from app.importpipeline.validators import validate_product_code, Level
        msgs = validate_product_code("<script>")
        assert any(m.level == Level.WARNING for m in msgs)


class TestDuplicateDetector:
    def test_first_occurrence_ok(self):
        from app.importpipeline.validators import DuplicateDetector
        d = DuplicateDetector("code")
        msgs = d.check("HH-0001", 1)
        assert msgs == []

    def test_second_occurrence_errors(self):
        from app.importpipeline.validators import DuplicateDetector, Level
        d = DuplicateDetector("code")
        d.check("HH-0001", 1)
        msgs = d.check("HH-0001", 5)
        assert any(m.level == Level.ERROR for m in msgs)
        assert "row 1" in msgs[0].message

    def test_case_insensitive(self):
        from app.importpipeline.validators import DuplicateDetector, Level
        d = DuplicateDetector("code")
        d.check("hh-0001", 1)
        msgs = d.check("HH-0001", 2)
        assert any(m.level == Level.ERROR for m in msgs)


# ─────────────────────────────────────────────────────────────────────────────
# COLUMN MAPPER TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestColumnMapper:
    def test_exact_alias_match(self):
        from app.importpipeline.mapper import ColumnMapper, PRODUCT_COLUMN_MAP
        mapper = ColumnMapper(PRODUCT_COLUMN_MAP)
        assert mapper.resolve_column("ma_hang") == "code"
        assert mapper.resolve_column("ten_hang") == "name"
        assert mapper.resolve_column("don_vi_tinh") == "uom"

    def test_case_insensitive_match(self):
        from app.importpipeline.mapper import ColumnMapper, PRODUCT_COLUMN_MAP
        mapper = ColumnMapper(PRODUCT_COLUMN_MAP)
        assert mapper.resolve_column("MA_HANG") == "code"
        assert mapper.resolve_column("Product Code") == "code"

    def test_unmapped_column(self):
        from app.importpipeline.mapper import ColumnMapper, PRODUCT_COLUMN_MAP
        mapper = ColumnMapper(PRODUCT_COLUMN_MAP)
        assert mapper.resolve_column("unknown_column_xyz") is None

    def test_map_row_basic(self):
        from app.importpipeline.mapper import ColumnMapper, PRODUCT_COLUMN_MAP
        mapper = ColumnMapper(PRODUCT_COLUMN_MAP)
        raw = {"_row_number": 1, "ma_hang": "HH-0001", "ten_hang": "Cáp điện"}
        mapped = mapper.map_row(raw)
        assert mapped["code"] == "HH-0001"
        assert mapped["name"] == "Cáp điện"
        assert mapped["_row_number"] == 1

    def test_extra_columns_captured(self):
        from app.importpipeline.mapper import ColumnMapper, PRODUCT_COLUMN_MAP
        mapper = ColumnMapper(PRODUCT_COLUMN_MAP)
        raw = {"_row_number": 1, "ma_hang": "HH-0001", "custom_field_xyz": "value"}
        mapped = mapper.map_row(raw)
        assert "custom_field_xyz" in mapped.get("_extra", {})

    def test_manual_override(self):
        from app.importpipeline.mapper import ColumnMapper, PRODUCT_COLUMN_MAP
        mapper = ColumnMapper(PRODUCT_COLUMN_MAP, extra_map={"so_hieusp": "code"})
        assert mapper.resolve_column("so_hieusp") == "code"

    def test_report_unmapped(self):
        from app.importpipeline.mapper import ColumnMapper, PRODUCT_COLUMN_MAP
        mapper = ColumnMapper(PRODUCT_COLUMN_MAP)
        sample = {"ma_hang": "X", "ten_hang": "Y", "col_xyz": "Z"}
        report = mapper.report_unmapped(sample)
        assert "ma_hang" in report["mapped"]
        assert "col_xyz" in report["unmapped"]

    def test_vietnamese_diacritics_in_alias(self):
        """Vietnamese column headers with full diacritics should map correctly."""
        from app.importpipeline.mapper import ColumnMapper, PRODUCT_COLUMN_MAP
        mapper = ColumnMapper(PRODUCT_COLUMN_MAP)
        # "Mã hàng" (with full Vietnamese diacritics) should resolve to "code"
        # because "ma_hang" is an alias and the normalizer strips diacritics
        result = mapper.resolve_column("Mã hàng")
        assert result == "code"


# ─────────────────────────────────────────────────────────────────────────────
# IMPORT REPORT TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestImportReport:
    def _make_result(self, row_num, status, entity_id=None):
        from app.importpipeline.validators import RowResult
        r = RowResult(row_number=row_num, source_data={"code": f"P{row_num}"})
        r.entity_id = entity_id
        return r

    def test_counts_ok_rows(self):
        from app.importpipeline.report import ImportReport
        from app.importpipeline.validators import RowResult
        report = ImportReport(entity_type="product", source_file="test.xlsx")

        r = RowResult(row_number=1, source_data={})
        r.entity_id = str(uuid.uuid4())
        report.add_row(r)

        assert report.total_rows == 1
        assert report.imported_rows == 1
        assert report.error_rows == 0

    def test_counts_error_rows(self):
        from app.importpipeline.report import ImportReport
        from app.importpipeline.validators import RowResult, validate_required, Level
        report = ImportReport(entity_type="product", source_file="test.xlsx")

        r = RowResult(row_number=1, source_data={})
        r.add(validate_required(None, "code"))  # ERROR
        report.add_row(r)

        assert report.error_rows == 1
        assert report.imported_rows == 0

    def test_success_rate(self):
        from app.importpipeline.report import ImportReport
        from app.importpipeline.validators import RowResult, validate_required
        report = ImportReport(entity_type="product", source_file="test.xlsx")

        ok = RowResult(row_number=1, source_data={})
        ok.entity_id = str(uuid.uuid4())
        report.add_row(ok)

        err = RowResult(row_number=2, source_data={})
        err.add(validate_required(None, "code"))
        report.add_row(err)

        assert report.success_rate == 50.0

    def test_print_summary_contains_key_info(self):
        from app.importpipeline.report import ImportReport
        report = ImportReport(entity_type="product", source_file="test.xlsx")
        report.finish()
        summary = report.print_summary()
        assert "IMPORT REPORT" in summary
        assert "Total rows" in summary

    def test_to_dict_serializable(self):
        import json
        from app.importpipeline.report import ImportReport
        report = ImportReport(entity_type="product", source_file="test.xlsx")
        report.finish()
        d = report.to_dict()
        # Must be JSON-serializable
        json.dumps(d, default=str)

    def test_duplicate_row_counted(self):
        from app.importpipeline.report import ImportReport
        from app.importpipeline.validators import RowResult, DuplicateDetector
        report = ImportReport(entity_type="product", source_file="test.xlsx")
        dup = DuplicateDetector("code")
        dup.check("HH-0001", 1)

        r = RowResult(row_number=2, source_data={"code": "HH-0001"})
        r.add(dup.check("HH-0001", 2))
        report.add_row(r)

        assert report.duplicate_rows == 1


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE READER TESTS (uses temp files)
# ─────────────────────────────────────────────────────────────────────────────

class TestSourceReader:
    def test_read_csv_basic(self, tmp_path):
        from app.importpipeline.reader import SourceReader
        csv_file = tmp_path / "products.csv"
        csv_file.write_text(
            "ma_hang,ten_hang,don_vi_tinh\n"
            "HH-0001,Cable,Cai\n"
            "HH-0002,Wire,Met\n",
            encoding="utf-8",
        )
        reader = SourceReader(str(csv_file))
        rows = list(reader.iter_rows())
        assert len(rows) == 2
        assert rows[0]["ma_hang"] == "HH-0001"
        assert rows[1]["ten_hang"] == "Wire"

    def test_row_numbers_are_1_based(self, tmp_path):
        from app.importpipeline.reader import SourceReader
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("code,name\nA,Alpha\nB,Beta\n", encoding="utf-8")
        reader = SourceReader(str(csv_file))
        rows = list(reader.iter_rows())
        assert rows[0]["_row_number"] == 1
        assert rows[1]["_row_number"] == 2

    def test_header_normalization(self, tmp_path):
        from app.importpipeline.reader import SourceReader
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("Product Code,  Name  ,Unit\nX,Y,Z\n", encoding="utf-8")
        reader = SourceReader(str(csv_file))
        rows = list(reader.iter_rows())
        assert "product_code" in rows[0]
        assert "name" in rows[0]
        assert "unit" in rows[0]

    def test_empty_rows_skipped(self, tmp_path):
        from app.importpipeline.reader import SourceReader
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("code,name\nA,Alpha\n,\nB,Beta\n", encoding="utf-8")
        reader = SourceReader(str(csv_file))
        rows = list(reader.iter_rows())
        # Empty row (,,) should be dropped
        assert len(rows) == 2

    def test_file_hash_computed(self, tmp_path):
        from app.importpipeline.reader import SourceReader
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("code,name\nA,Alpha\n", encoding="utf-8")
        reader = SourceReader(str(csv_file))
        assert len(reader.file_hash) == 64  # SHA-256 hex

    def test_unsupported_extension_raises(self, tmp_path):
        from app.importpipeline.reader import SourceReader
        f = tmp_path / "test.pdf"
        f.write_text("x")
        reader = SourceReader(str(f))
        with pytest.raises(ValueError, match="Unsupported file type"):
            list(reader.iter_rows())

    def test_vietnamese_values_preserved(self, tmp_path):
        from app.importpipeline.reader import SourceReader
        csv_file = tmp_path / "vn.csv"
        csv_file.write_text("ma_hang,ten_hang\nHH-001,Cáp điện\n", encoding="utf-8")
        reader = SourceReader(str(csv_file))
        rows = list(reader.iter_rows())
        assert rows[0]["ten_hang"] == "Cáp điện"


# ─────────────────────────────────────────────────────────────────────────────
# INTEGRATION TESTS  (require real PostgreSQL DB)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def db_session():
    """
    Provides a real DB session for integration tests.
    Rolls back all changes after the test completes.
    """
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


class TestProductImportIntegration:
    def test_dry_run_produces_report_no_db_write(self, db_session, tmp_path):
        from app.importpipeline.importers.products import import_products
        from sqlalchemy import select, text
        from app.models import Product

        csv_file = tmp_path / "products.csv"
        csv_file.write_text(
            "ma_hang,ten_hang,don_vi_tinh\n"
            "TEST-DRY-001,Test Product Dry Run,Cai\n",
            encoding="utf-8",
        )
        count_before = db_session.execute(
            select(text("count(*)")).select_from(Product.__table__)
        ).scalar()

        report = import_products(db_session, str(csv_file), dry_run=True)
        db_session.rollback()

        count_after = db_session.execute(
            select(text("count(*)")).select_from(Product.__table__)
        ).scalar()

        assert count_before == count_after
        assert report.total_rows == 1

    def test_valid_products_imported(self, db_session, tmp_path):
        from app.importpipeline.importers.products import import_products

        csv_file = tmp_path / "products.csv"
        csv_file.write_text(
            "ma_hang,ten_hang,don_vi_tinh,gia_von\n"
            "TEST-INT-001,Integration Product 1,Cai,100000\n"
            "TEST-INT-002,Integration Product 2,Met,200000\n",
            encoding="utf-8",
        )
        report = import_products(db_session, str(csv_file), dry_run=False)
        db_session.flush()

        assert report.imported_rows == 2
        assert report.error_rows == 0

    def test_missing_code_rejected(self, db_session, tmp_path):
        from app.importpipeline.importers.products import import_products

        csv_file = tmp_path / "invalid_products.csv"
        csv_file.write_text(
            "ma_hang,ten_hang\n"
            ",Missing Code Product\n",
            encoding="utf-8",
        )
        report = import_products(db_session, str(csv_file), dry_run=True)
        assert report.error_rows == 1
        assert report.imported_rows == 0

    def test_duplicate_code_in_batch_rejected(self, db_session, tmp_path):
        from app.importpipeline.importers.products import import_products

        csv_file = tmp_path / "dupes.csv"
        csv_file.write_text(
            "ma_hang,ten_hang\n"
            "DUP-001,First Product\n"
            "DUP-001,Duplicate Product\n",
            encoding="utf-8",
        )
        report = import_products(db_session, str(csv_file), dry_run=True)
        assert report.duplicate_rows >= 1
        assert report.error_rows >= 1

    def test_upsert_existing_product_updates(self, db_session, tmp_path):
        from app.importpipeline.importers.products import import_products

        csv_file = tmp_path / "upsert.csv"
        # First import
        csv_file.write_text(
            "ma_hang,ten_hang\nTEST-UPS-001,Original Name\n",
            encoding="utf-8",
        )
        import_products(db_session, str(csv_file), dry_run=False)
        db_session.flush()

        # Second import with updated name
        csv_file.write_text(
            "ma_hang,ten_hang\nTEST-UPS-001,Updated Name\n",
            encoding="utf-8",
        )
        report2 = import_products(db_session, str(csv_file), dry_run=False)
        db_session.flush()

        # Should be "imported" (upsert) not error
        assert report2.error_rows == 0


class TestCustomerImportIntegration:
    def test_valid_customers_imported(self, db_session, tmp_path):
        from app.importpipeline.importers.customers import import_customers

        csv_file = tmp_path / "customers.csv"
        csv_file.write_text(
            "ma_kh,ten_kh,email,so_dien_thoai\n"
            "KH-TEST-001,Test Customer 1,test1@example.com,0901234567\n"
            "KH-TEST-002,Test Customer 2,test2@example.com,0901234568\n",
            encoding="utf-8",
        )
        report = import_customers(db_session, str(csv_file), dry_run=False)
        db_session.flush()
        assert report.imported_rows == 2
        assert report.error_rows == 0

    def test_invalid_email_warns(self, db_session, tmp_path):
        from app.importpipeline.importers.customers import import_customers

        csv_file = tmp_path / "customers.csv"
        csv_file.write_text(
            "ma_kh,ten_kh,email\n"
            "KH-WARN-001,Test Customer,not-valid-email\n",
            encoding="utf-8",
        )
        report = import_customers(db_session, str(csv_file), dry_run=True)
        # Should import with warning, not error
        assert report.error_rows == 0
        assert report.warning_rows >= 1


class TestInventoryImportIntegration:
    def test_inventory_requires_products_first(self, db_session, tmp_path):
        from app.importpipeline.importers.inventory import import_inventory

        csv_file = tmp_path / "inventory.csv"
        csv_file.write_text(
            "ma_hang,so_luong\n"
            "NONEXISTENT-PRODUCT-999,100\n",
            encoding="utf-8",
        )
        report = import_inventory(db_session, str(csv_file), dry_run=True)
        assert report.error_rows >= 1
        assert any("PRODUCT_NOT_FOUND" in (m.code for m in r.messages)
                   for r in report.row_results)

    def test_valid_inventory_creates_movement(self, db_session, tmp_path):
        from app.importpipeline.importers.products import import_products
        from app.importpipeline.importers.inventory import import_inventory
        from sqlalchemy import select
        from app.models import StockMovement

        # First import the product
        prod_file = tmp_path / "prod.csv"
        prod_file.write_text("ma_hang,ten_hang\nINV-TEST-001,Inventory Test Product\n", encoding="utf-8")
        import_products(db_session, str(prod_file), dry_run=False)
        db_session.flush()

        # Then import inventory
        inv_file = tmp_path / "inv.csv"
        inv_file.write_text("ma_hang,so_luong\nINV-TEST-001,50\n", encoding="utf-8")
        report = import_inventory(db_session, str(inv_file), dry_run=False)
        db_session.flush()

        assert report.imported_rows == 1
        assert report.error_rows == 0


class TestPricingImportIntegration:
    def test_pricing_requires_products_first(self, db_session, tmp_path):
        from app.importpipeline.importers.pricing import import_pricing

        csv_file = tmp_path / "pricing.csv"
        csv_file.write_text(
            "ma_hang,don_gia,tien_te\n"
            "NONEXISTENT-PROD-999,100000,VND\n",
            encoding="utf-8",
        )
        report = import_pricing(db_session, str(csv_file), dry_run=True)
        assert report.error_rows >= 1

    def test_valid_pricing_imported(self, db_session, tmp_path):
        from app.importpipeline.importers.products import import_products
        from app.importpipeline.importers.pricing import import_pricing

        # Import product first
        prod_file = tmp_path / "prod.csv"
        prod_file.write_text("ma_hang,ten_hang\nPRICE-TEST-001,Price Test Product\n", encoding="utf-8")
        import_products(db_session, str(prod_file), dry_run=False)
        db_session.flush()

        # Import pricing
        price_file = tmp_path / "pricing.csv"
        price_file.write_text(
            "ma_hang,don_gia,tien_te\n"
            "PRICE-TEST-001,250000,VND\n",
            encoding="utf-8",
        )
        report = import_pricing(db_session, str(price_file),
                                price_list_name="Test Price List", dry_run=False)
        db_session.flush()

        assert report.imported_rows == 1
        assert report.error_rows == 0
