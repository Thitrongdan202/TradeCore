"""
TradeCore — Seed Script
Populates reference data that must exist before any import:
  - Currencies (VND, USD, EUR, CNY, KRW, TWD, THB)
  - Units of Measure (common Vietnamese trading units)
  - Payment Terms (common Vietnamese payment terms)
  - Default Warehouse + virtual locations
  - Default Roles

Run: python scripts/seed.py
Safe to run multiple times (upserts using ON CONFLICT DO NOTHING).
"""
from __future__ import annotations

import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db_context
from app.models import (
    Currency, UnitOfMeasure, UoMCategory, UoMType,
    PaymentTerm, Warehouse, WarehouseLocation, LocationType, Role,
)


CURRENCIES = [
    dict(code="VND", name="Việt Nam Đồng", symbol="₫", is_base=True,  exchange_rate=1.0,        rate_date=date.today()),
    dict(code="USD", name="US Dollar",     symbol="$", is_base=False, exchange_rate=25500.0,     rate_date=date.today()),
    dict(code="EUR", name="Euro",          symbol="€", is_base=False, exchange_rate=27800.0,     rate_date=date.today()),
    dict(code="CNY", name="Chinese Yuan",  symbol="¥", is_base=False, exchange_rate=3500.0,      rate_date=date.today()),
    dict(code="KRW", name="Korean Won",    symbol="₩", is_base=False, exchange_rate=18.5,        rate_date=date.today()),
    dict(code="TWD", name="New Taiwan Dollar", symbol="NT$", is_base=False, exchange_rate=780.0, rate_date=date.today()),
    dict(code="THB", name="Thai Baht",    symbol="฿", is_base=False, exchange_rate=710.0,        rate_date=date.today()),
    dict(code="JPY", name="Japanese Yen", symbol="¥", is_base=False, exchange_rate=165.0,        rate_date=date.today()),
]

UNITS_OF_MEASURE = [
    # ── Đơn vị đếm (Counting units) ─────────────────────────────────────
    dict(name="Cái",   symbol="cái",  category=UoMCategory.unit,   uom_type=UoMType.reference, factor=1.0),
    dict(name="Chiếc", symbol="chiếc",category=UoMCategory.unit,   uom_type=UoMType.reference, factor=1.0),
    dict(name="Bộ",    symbol="bộ",   category=UoMCategory.unit,   uom_type=UoMType.reference, factor=1.0),
    dict(name="Hộp",   symbol="hộp",  category=UoMCategory.unit,   uom_type=UoMType.reference, factor=1.0),
    dict(name="Thùng", symbol="thùng",category=UoMCategory.unit,   uom_type=UoMType.reference, factor=1.0),
    dict(name="Cuộn",  symbol="cuộn", category=UoMCategory.unit,   uom_type=UoMType.reference, factor=1.0),
    dict(name="Tấm",   symbol="tấm",  category=UoMCategory.unit,   uom_type=UoMType.reference, factor=1.0),
    dict(name="Lô",    symbol="lô",   category=UoMCategory.unit,   uom_type=UoMType.reference, factor=1.0),
    dict(name="Đôi",   symbol="đôi",  category=UoMCategory.unit,   uom_type=UoMType.reference, factor=1.0),
    # ── Khối lượng (Weight) ─────────────────────────────────────────────
    dict(name="Kg",    symbol="kg",   category=UoMCategory.weight, uom_type=UoMType.reference, factor=1.0),
    dict(name="Gram",  symbol="g",    category=UoMCategory.weight, uom_type=UoMType.smaller,   factor=0.001),
    dict(name="Tấn",   symbol="tấn",  category=UoMCategory.weight, uom_type=UoMType.bigger,    factor=1000.0),
    # ── Thể tích (Volume) ────────────────────────────────────────────────
    dict(name="Lít",   symbol="L",    category=UoMCategory.volume, uom_type=UoMType.reference, factor=1.0),
    dict(name="m³",    symbol="m³",   category=UoMCategory.volume, uom_type=UoMType.bigger,    factor=1000.0),
    # ── Độ dài (Length) ─────────────────────────────────────────────────
    dict(name="Mét",   symbol="m",    category=UoMCategory.length, uom_type=UoMType.reference, factor=1.0),
    dict(name="cm",    symbol="cm",   category=UoMCategory.length, uom_type=UoMType.smaller,   factor=0.01),
    dict(name="mm",    symbol="mm",   category=UoMCategory.length, uom_type=UoMType.smaller,   factor=0.001),
    # ── Diện tích (Area) ────────────────────────────────────────────────
    dict(name="m²",    symbol="m²",   category=UoMCategory.area,   uom_type=UoMType.reference, factor=1.0),
    # ── Thời gian (Time) ────────────────────────────────────────────────
    dict(name="Ngày",  symbol="ngày", category=UoMCategory.time,   uom_type=UoMType.reference, factor=1.0),
    dict(name="Tháng", symbol="tháng",category=UoMCategory.time,   uom_type=UoMType.bigger,    factor=30.0),
    dict(name="Năm",   symbol="năm",  category=UoMCategory.time,   uom_type=UoMType.bigger,    factor=365.0),
]

PAYMENT_TERMS = [
    dict(name="Thanh toán ngay",                    description="Immediate payment",           days_due=0,   advance_percent=100),
    dict(name="30 ngày NET",                         description="Net 30 days",                 days_due=30,  advance_percent=0),
    dict(name="60 ngày NET",                         description="Net 60 days",                 days_due=60,  advance_percent=0),
    dict(name="90 ngày NET",                         description="Net 90 days",                 days_due=90,  advance_percent=0),
    dict(name="50% ứng trước, 50% khi nhận hàng",   description="50% advance, 50% on receipt", days_due=0,   advance_percent=50),
    dict(name="30% ứng trước, 70% khi nhận hàng",   description="30% advance, 70% on receipt", days_due=0,   advance_percent=30),
    dict(name="100% ứng trước",                      description="Full advance payment",         days_due=0,   advance_percent=100),
    dict(name="Tín dụng 45 ngày",                   description="45-day credit term",           days_due=45,  advance_percent=0),
]

ROLES = [
    dict(name="admin",       description="System administrator — full access"),
    dict(name="manager",     description="Business manager — read/write all modules"),
    dict(name="sales",       description="Sales staff — sales orders, customers"),
    dict(name="purchasing",  description="Purchasing staff — purchase orders, suppliers"),
    dict(name="warehouse",   description="Warehouse staff — inventory, stock movements"),
    dict(name="logistics",   description="Logistics staff — shipments, import/export"),
    dict(name="accounting",  description="Accounting staff — invoices, payments"),
    dict(name="viewer",      description="Read-only access"),
]


def seed_currencies(db):
    existing = {c.code for c in db.query(Currency).all()}
    count = 0
    for data in CURRENCIES:
        if data["code"] not in existing:
            db.add(Currency(**data))
            count += 1
    print(f"  Currencies: +{count} new ({len(existing)} already existed)")


def seed_uom(db):
    existing = {u.name for u in db.query(UnitOfMeasure).all()}
    count = 0
    for data in UNITS_OF_MEASURE:
        if data["name"] not in existing:
            db.add(UnitOfMeasure(**data))
            count += 1
    print(f"  Units of Measure: +{count} new ({len(existing)} already existed)")


def seed_payment_terms(db):
    existing = {p.name for p in db.query(PaymentTerm).all()}
    count = 0
    for data in PAYMENT_TERMS:
        if data["name"] not in existing:
            db.add(PaymentTerm(**data))
            count += 1
    print(f"  Payment Terms: +{count} new ({len(existing)} already existed)")


def seed_roles(db):
    existing = {r.name for r in db.query(Role).all()}
    count = 0
    for data in ROLES:
        if data["name"] not in existing:
            db.add(Role(**data))
            count += 1
    print(f"  Roles: +{count} new ({len(existing)} already existed)")


def seed_warehouse(db):
    existing = db.query(Warehouse).filter_by(code="WH01").first()
    if existing:
        print("  Warehouse: already exists (skipped)")
        return

    wh = Warehouse(code="WH01", name="Kho chính", address="Vietnam")
    db.add(wh)
    db.flush()

    locations = [
        dict(code="WH01/STOCK",    name="Kho WH01 — Tồn kho",       location_type=LocationType.internal, warehouse_id=wh.id),
        dict(code="VIRTUAL/INPUT",    name="[Ảo] Đầu vào",            location_type=LocationType.virtual,  warehouse_id=None),
        dict(code="VIRTUAL/OUTPUT",   name="[Ảo] Đầu ra",             location_type=LocationType.virtual,  warehouse_id=None),
        dict(code="VIRTUAL/SUPPLIERS",name="[Ảo] Nhà cung cấp",       location_type=LocationType.supplier, warehouse_id=None),
        dict(code="VIRTUAL/CUSTOMERS",name="[Ảo] Khách hàng",         location_type=LocationType.customer, warehouse_id=None),
        dict(code="VIRTUAL/TRANSIT",  name="[Ảo] Hàng đang vận chuyển",location_type=LocationType.transit, warehouse_id=None),
        dict(code="VIRTUAL/ADJUST",   name="[Ảo] Điều chỉnh kho",     location_type=LocationType.virtual,  warehouse_id=None),
        dict(code="VIRTUAL/SCRAP",    name="[Ảo] Hàng hỏng / Phế liệu",location_type=LocationType.virtual, warehouse_id=None),
    ]
    for loc_data in locations:
        db.add(WarehouseLocation(**loc_data))
    print(f"  Warehouse: WH01 created with {len(locations)} locations")


def main():
    print("TradeCore — Seeding reference data...")
    with get_db_context() as db:
        seed_currencies(db)
        seed_uom(db)
        seed_payment_terms(db)
        seed_roles(db)
        seed_warehouse(db)
    print("Seed completed successfully.")


if __name__ == "__main__":
    main()
