"""Initial schema — all TradeCore core tables

Revision ID: 0001
Revises:
Create Date: 2026-08-17

Uses raw SQL via op.execute() for full control over enum type creation.
All 27 tables, 17 enum types, 60+ indexes.
"""
from __future__ import annotations

from typing import Sequence, Union
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
-- ─────────────────────────────────────────────────────────────────────────────
-- EXTENSIONS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ─────────────────────────────────────────────────────────────────────────────
-- ENUM TYPES
-- ─────────────────────────────────────────────────────────────────────────────
DO $$ BEGIN CREATE TYPE uom_category AS ENUM ('unit','weight','volume','length','area','time','other'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE uom_type AS ENUM ('reference','smaller','bigger'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE product_type AS ENUM ('product','consumable','service'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE location_type AS ENUM ('internal','supplier','customer','transit','virtual'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE movement_type AS ENUM ('receive','issue','transfer','adjustment','opening','scrap','return_in','return_out'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE reference_type AS ENUM ('sale_order','purchase_order','shipment','manual','opening','import_run'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE order_status AS ENUM ('draft','pending','confirmed','processing','shipping','completed','cancelled','returned'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE payment_status AS ENUM ('unpaid','partial','paid','overdue','refunded'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE shipment_type AS ENUM ('import','export','both'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE shipment_status AS ENUM ('booking','loading','in_transit','arrived','customs','warehoused','completed','cancelled'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE container_type AS ENUM ('20GP','40GP','40HC','LCL','AIR'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE expense_category AS ENUM ('freight','customs','insurance','storage','handling','other'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE source_type AS ENUM ('excel','odoo_csv','odoo_xml','odoo_json','manual'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE entity_type AS ENUM ('product','product_category','customer','supplier','uom','price_item','inventory','sales_order','purchase_order','shipment','currency','payment_term'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE import_run_status AS ENUM ('running','completed','failed','rolled_back','partial'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE row_status AS ENUM ('ok','skipped','error','warning'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE validation_status AS ENUM ('pending','valid','invalid'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- ─────────────────────────────────────────────────────────────────────────────
-- ROLES
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS roles (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(80) NOT NULL UNIQUE,
    description TEXT,
    permissions JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_roles_name ON roles(name);

-- ─────────────────────────────────────────────────────────────────────────────
-- USERS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) NOT NULL UNIQUE,
    username        VARCHAR(80)  NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name       VARCHAR(255) NOT NULL,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    role_id         UUID         REFERENCES roles(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_users_email    ON users(email);
CREATE INDEX IF NOT EXISTS ix_users_username ON users(username);
CREATE INDEX IF NOT EXISTS ix_users_role_id  ON users(role_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- CURRENCIES
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS currencies (
    id            UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    code          VARCHAR(10)   NOT NULL UNIQUE,
    name          VARCHAR(100)  NOT NULL,
    symbol        VARCHAR(10)   NOT NULL,
    is_base       BOOLEAN       NOT NULL DEFAULT FALSE,
    exchange_rate NUMERIC(18,6),
    rate_date     DATE,
    is_active     BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ   NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_currencies_code ON currencies(code);

-- ─────────────────────────────────────────────────────────────────────────────
-- UNITS OF MEASURE
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS units_of_measure (
    id         UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    name       VARCHAR(80)     NOT NULL UNIQUE,
    symbol     VARCHAR(20),
    category   uom_category    NOT NULL,
    uom_type   uom_type        NOT NULL,
    factor     NUMERIC(18,6)   NOT NULL DEFAULT 1.0,
    is_active  BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ     NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_units_of_measure_name ON units_of_measure(name);

-- ─────────────────────────────────────────────────────────────────────────────
-- PAYMENT TERMS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS payment_terms (
    id               UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    name             VARCHAR(255) NOT NULL UNIQUE,
    description      TEXT,
    days_due         INTEGER,
    advance_percent  NUMERIC(5,2),
    is_active        BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_payment_terms_name ON payment_terms(name);

-- ─────────────────────────────────────────────────────────────────────────────
-- PRODUCT CATEGORIES
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS product_categories (
    id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    code        VARCHAR(40)  UNIQUE,
    name        VARCHAR(255) NOT NULL,
    description TEXT,
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
    parent_id   UUID         REFERENCES product_categories(id) ON DELETE SET NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_product_categories_code      ON product_categories(code);
CREATE INDEX IF NOT EXISTS ix_product_categories_name      ON product_categories(name);
CREATE INDEX IF NOT EXISTS ix_product_categories_parent_id ON product_categories(parent_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- PRODUCTS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS products (
    id               UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    code             VARCHAR(80)   NOT NULL UNIQUE,
    barcode          VARCHAR(100),
    name             VARCHAR(500)  NOT NULL,
    name_en          VARCHAR(500),
    description      TEXT,
    product_type     product_type  NOT NULL DEFAULT 'product',
    category_id      UUID          REFERENCES product_categories(id) ON DELETE SET NULL,
    uom_id           UUID          REFERENCES units_of_measure(id) ON DELETE RESTRICT,
    purchase_uom_id  UUID          REFERENCES units_of_measure(id) ON DELETE RESTRICT,
    cost_price       NUMERIC(18,4),
    weight_kg        NUMERIC(10,4),
    volume_m3        NUMERIC(10,6),
    min_stock        NUMERIC(18,4),
    max_stock        NUMERIC(18,4),
    is_active        BOOLEAN       NOT NULL DEFAULT TRUE,
    notes            TEXT,
    odoo_id          INTEGER,
    created_at       TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ   NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_products_code        ON products(code);
CREATE INDEX IF NOT EXISTS ix_products_name        ON products(name);
CREATE INDEX IF NOT EXISTS ix_products_barcode     ON products(barcode);
CREATE INDEX IF NOT EXISTS ix_products_category_id ON products(category_id);
CREATE INDEX IF NOT EXISTS ix_products_uom_id      ON products(uom_id);
CREATE INDEX IF NOT EXISTS ix_products_odoo_id     ON products(odoo_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- CUSTOMERS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS customers (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    code            VARCHAR(40)  NOT NULL UNIQUE,
    tax_code        VARCHAR(20),
    name            VARCHAR(500) NOT NULL,
    short_name      VARCHAR(100),
    phone           VARCHAR(30),
    email           VARCHAR(255),
    address         TEXT,
    city            VARCHAR(100),
    province        VARCHAR(100),
    country         VARCHAR(10)  NOT NULL DEFAULT 'VN',
    payment_term_id UUID         REFERENCES payment_terms(id) ON DELETE SET NULL,
    credit_limit    NUMERIC(18,2),
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    notes           TEXT,
    odoo_id         INTEGER,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_customers_code            ON customers(code);
CREATE INDEX IF NOT EXISTS ix_customers_name            ON customers(name);
CREATE INDEX IF NOT EXISTS ix_customers_tax_code        ON customers(tax_code);
CREATE INDEX IF NOT EXISTS ix_customers_email           ON customers(email);
CREATE INDEX IF NOT EXISTS ix_customers_odoo_id         ON customers(odoo_id);
CREATE INDEX IF NOT EXISTS ix_customers_payment_term_id ON customers(payment_term_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- SUPPLIERS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS suppliers (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    code            VARCHAR(40)  NOT NULL UNIQUE,
    tax_code        VARCHAR(30),
    name            VARCHAR(500) NOT NULL,
    short_name      VARCHAR(100),
    country         VARCHAR(10),
    contact_name    VARCHAR(255),
    phone           VARCHAR(30),
    email           VARCHAR(255),
    address         TEXT,
    payment_term_id UUID         REFERENCES payment_terms(id) ON DELETE SET NULL,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    notes           TEXT,
    odoo_id         INTEGER,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_suppliers_code            ON suppliers(code);
CREATE INDEX IF NOT EXISTS ix_suppliers_name            ON suppliers(name);
CREATE INDEX IF NOT EXISTS ix_suppliers_country         ON suppliers(country);
CREATE INDEX IF NOT EXISTS ix_suppliers_email           ON suppliers(email);
CREATE INDEX IF NOT EXISTS ix_suppliers_tax_code        ON suppliers(tax_code);
CREATE INDEX IF NOT EXISTS ix_suppliers_odoo_id         ON suppliers(odoo_id);
CREATE INDEX IF NOT EXISTS ix_suppliers_payment_term_id ON suppliers(payment_term_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- PRICE LISTS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS price_lists (
    id             UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    name           VARCHAR(255) NOT NULL,
    currency_id    UUID         REFERENCES currencies(id) ON DELETE RESTRICT,
    customer_id    UUID         REFERENCES customers(id)  ON DELETE CASCADE,
    effective_from DATE,
    effective_to   DATE,
    is_active      BOOLEAN      NOT NULL DEFAULT TRUE,
    notes          TEXT,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_price_lists_name        ON price_lists(name);
CREATE INDEX IF NOT EXISTS ix_price_lists_currency_id ON price_lists(currency_id);
CREATE INDEX IF NOT EXISTS ix_price_lists_customer_id ON price_lists(customer_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- PRICE LIST ITEMS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS price_list_items (
    id            UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    price_list_id UUID          NOT NULL REFERENCES price_lists(id) ON DELETE CASCADE,
    product_id    UUID          NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    uom_id        UUID          REFERENCES units_of_measure(id) ON DELETE RESTRICT,
    min_qty       NUMERIC(18,4) NOT NULL DEFAULT 0,
    price         NUMERIC(18,4) NOT NULL,
    source_price  NUMERIC(18,4),
    source_currency VARCHAR(10),
    notes         TEXT,
    created_at    TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ   NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_price_list_items_price_list_id ON price_list_items(price_list_id);
CREATE INDEX IF NOT EXISTS ix_price_list_items_product_id    ON price_list_items(product_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- WAREHOUSES
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS warehouses (
    id         UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    code       VARCHAR(20)  NOT NULL UNIQUE,
    name       VARCHAR(255) NOT NULL,
    address    TEXT,
    is_active  BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_warehouses_code ON warehouses(code);

-- ─────────────────────────────────────────────────────────────────────────────
-- WAREHOUSE LOCATIONS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS warehouse_locations (
    id            UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    code          VARCHAR(60)   NOT NULL UNIQUE,
    name          VARCHAR(255)  NOT NULL,
    location_type location_type NOT NULL,
    is_active     BOOLEAN       NOT NULL DEFAULT TRUE,
    warehouse_id  UUID          REFERENCES warehouses(id) ON DELETE SET NULL,
    parent_id     UUID          REFERENCES warehouse_locations(id) ON DELETE SET NULL,
    created_at    TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ   NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_warehouse_locations_code         ON warehouse_locations(code);
CREATE INDEX IF NOT EXISTS ix_warehouse_locations_warehouse_id ON warehouse_locations(warehouse_id);
CREATE INDEX IF NOT EXISTS ix_warehouse_locations_parent_id    ON warehouse_locations(parent_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- STOCK MOVEMENTS  (immutable ledger — never UPDATE or DELETE)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS stock_movements (
    id               UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    movement_type    movement_type  NOT NULL,
    reference_type   reference_type,
    reference        VARCHAR(100),
    reference_id     UUID,
    product_id       UUID           NOT NULL REFERENCES products(id)           ON DELETE RESTRICT,
    uom_id           UUID           REFERENCES units_of_measure(id)            ON DELETE RESTRICT,
    qty              NUMERIC(18,4)  NOT NULL CHECK (qty > 0),
    cost_price       NUMERIC(18,4),
    from_location_id UUID           REFERENCES warehouse_locations(id)         ON DELETE RESTRICT,
    to_location_id   UUID           REFERENCES warehouse_locations(id)         ON DELETE RESTRICT,
    moved_at         TIMESTAMPTZ    NOT NULL DEFAULT now(),
    created_at       TIMESTAMPTZ    NOT NULL DEFAULT now(),
    created_by_id    UUID           REFERENCES users(id)                       ON DELETE SET NULL,
    notes            TEXT
);
CREATE INDEX IF NOT EXISTS ix_stock_movements_movement_type    ON stock_movements(movement_type);
CREATE INDEX IF NOT EXISTS ix_stock_movements_product_id       ON stock_movements(product_id);
CREATE INDEX IF NOT EXISTS ix_stock_movements_from_location_id ON stock_movements(from_location_id);
CREATE INDEX IF NOT EXISTS ix_stock_movements_to_location_id   ON stock_movements(to_location_id);
CREATE INDEX IF NOT EXISTS ix_stock_movements_moved_at         ON stock_movements(moved_at);
CREATE INDEX IF NOT EXISTS ix_stock_movements_reference        ON stock_movements(reference);

-- ─────────────────────────────────────────────────────────────────────────────
-- STOCK BALANCES  (materialized snapshot — updated atomically with movements)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS stock_balances (
    id              UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id      UUID          NOT NULL REFERENCES products(id)          ON DELETE CASCADE,
    location_id     UUID          NOT NULL REFERENCES warehouse_locations(id) ON DELETE CASCADE,
    qty_on_hand     NUMERIC(18,4) NOT NULL DEFAULT 0 CHECK (qty_on_hand >= 0),
    last_updated_at TIMESTAMPTZ   NOT NULL DEFAULT now(),
    UNIQUE (product_id, location_id)
);
CREATE INDEX IF NOT EXISTS ix_stock_balances_product_id  ON stock_balances(product_id);
CREATE INDEX IF NOT EXISTS ix_stock_balances_location_id ON stock_balances(location_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- SALES ORDERS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sales_orders (
    id              UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number    VARCHAR(40)   NOT NULL UNIQUE,
    customer_id     UUID          REFERENCES customers(id)     ON DELETE RESTRICT,
    currency_id     UUID          REFERENCES currencies(id)    ON DELETE RESTRICT,
    payment_term_id UUID          REFERENCES payment_terms(id) ON DELETE SET NULL,
    date            DATE,
    due_date        DATE,
    status          order_status  NOT NULL DEFAULT 'draft',
    payment_status  payment_status NOT NULL DEFAULT 'unpaid',
    subtotal        NUMERIC(18,4),
    tax_amount      NUMERIC(18,4) DEFAULT 0,
    total           NUMERIC(18,4),
    amount_paid     NUMERIC(18,4) DEFAULT 0,
    notes           TEXT,
    odoo_id         INTEGER,
    created_by_id   UUID          REFERENCES users(id)         ON DELETE SET NULL,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ   NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_sales_orders_order_number    ON sales_orders(order_number);
CREATE INDEX IF NOT EXISTS ix_sales_orders_customer_id     ON sales_orders(customer_id);
CREATE INDEX IF NOT EXISTS ix_sales_orders_date            ON sales_orders(date);
CREATE INDEX IF NOT EXISTS ix_sales_orders_status          ON sales_orders(status);
CREATE INDEX IF NOT EXISTS ix_sales_orders_payment_status  ON sales_orders(payment_status);
CREATE INDEX IF NOT EXISTS ix_sales_orders_odoo_id         ON sales_orders(odoo_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- SALES ORDER ITEMS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sales_order_items (
    id               UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id         UUID          NOT NULL REFERENCES sales_orders(id) ON DELETE CASCADE,
    line_no          INTEGER       NOT NULL DEFAULT 1,
    product_id       UUID          REFERENCES products(id)          ON DELETE RESTRICT,
    description      VARCHAR(500),
    qty              NUMERIC(18,4) NOT NULL CHECK (qty > 0),
    uom_id           UUID          REFERENCES units_of_measure(id)  ON DELETE RESTRICT,
    unit_price       NUMERIC(18,4),
    discount_percent NUMERIC(5,2)  NOT NULL DEFAULT 0 CHECK (discount_percent >= 0 AND discount_percent <= 100),
    subtotal         NUMERIC(18,4),
    notes            TEXT
);
CREATE INDEX IF NOT EXISTS ix_sales_order_items_order_id   ON sales_order_items(order_id);
CREATE INDEX IF NOT EXISTS ix_sales_order_items_product_id ON sales_order_items(product_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- PURCHASE ORDERS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS purchase_orders (
    id              UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number    VARCHAR(40)    NOT NULL UNIQUE,
    supplier_id     UUID           REFERENCES suppliers(id)     ON DELETE RESTRICT,
    currency_id     UUID           REFERENCES currencies(id)    ON DELETE RESTRICT,
    payment_term_id UUID           REFERENCES payment_terms(id) ON DELETE SET NULL,
    date            DATE,
    expected_date   DATE,
    status          order_status   NOT NULL DEFAULT 'draft',
    payment_status  payment_status NOT NULL DEFAULT 'unpaid',
    subtotal        NUMERIC(18,4),
    tax_amount      NUMERIC(18,4)  DEFAULT 0,
    total           NUMERIC(18,4),
    amount_paid     NUMERIC(18,4)  DEFAULT 0,
    notes           TEXT,
    odoo_id         INTEGER,
    created_by_id   UUID           REFERENCES users(id)         ON DELETE SET NULL,
    created_at      TIMESTAMPTZ    NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ    NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_purchase_orders_order_number ON purchase_orders(order_number);
CREATE INDEX IF NOT EXISTS ix_purchase_orders_supplier_id  ON purchase_orders(supplier_id);
CREATE INDEX IF NOT EXISTS ix_purchase_orders_date         ON purchase_orders(date);
CREATE INDEX IF NOT EXISTS ix_purchase_orders_status       ON purchase_orders(status);
CREATE INDEX IF NOT EXISTS ix_purchase_orders_odoo_id      ON purchase_orders(odoo_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- PURCHASE ORDER ITEMS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS purchase_order_items (
    id               UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id         UUID          NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    line_no          INTEGER       NOT NULL DEFAULT 1,
    product_id       UUID          REFERENCES products(id)         ON DELETE RESTRICT,
    description      VARCHAR(500),
    qty              NUMERIC(18,4) NOT NULL CHECK (qty > 0),
    qty_received     NUMERIC(18,4) NOT NULL DEFAULT 0,
    uom_id           UUID          REFERENCES units_of_measure(id) ON DELETE RESTRICT,
    unit_price       NUMERIC(18,4),
    discount_percent NUMERIC(5,2)  NOT NULL DEFAULT 0 CHECK (discount_percent >= 0 AND discount_percent <= 100),
    subtotal         NUMERIC(18,4),
    notes            TEXT
);
CREATE INDEX IF NOT EXISTS ix_purchase_order_items_order_id   ON purchase_order_items(order_id);
CREATE INDEX IF NOT EXISTS ix_purchase_order_items_product_id ON purchase_order_items(product_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- SHIPMENTS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS shipments (
    id                  UUID             PRIMARY KEY DEFAULT gen_random_uuid(),
    shipment_number     VARCHAR(40)      NOT NULL UNIQUE,
    description         VARCHAR(500),
    shipment_type       shipment_type    NOT NULL DEFAULT 'import',
    supplier_id         UUID             REFERENCES suppliers(id)       ON DELETE SET NULL,
    purchase_order_id   UUID             REFERENCES purchase_orders(id) ON DELETE SET NULL,
    origin_country      VARCHAR(10),
    destination_country VARCHAR(10),
    port_origin         VARCHAR(100),
    port_destination    VARCHAR(100),
    incoterm            VARCHAR(10),
    etd                 DATE,
    eta                 DATE,
    ata                 DATE,
    status              shipment_status  NOT NULL DEFAULT 'booking',
    total_weight_kg     NUMERIC(12,2),
    total_value_usd     NUMERIC(18,2),
    freight_cost        NUMERIC(18,2),
    freight_currency    VARCHAR(10),
    notes               TEXT,
    created_at          TIMESTAMPTZ      NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ      NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_shipments_shipment_number   ON shipments(shipment_number);
CREATE INDEX IF NOT EXISTS ix_shipments_status            ON shipments(status);
CREATE INDEX IF NOT EXISTS ix_shipments_supplier_id       ON shipments(supplier_id);
CREATE INDEX IF NOT EXISTS ix_shipments_purchase_order_id ON shipments(purchase_order_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- CONTAINERS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS containers (
    id               UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    shipment_id      UUID           NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
    container_number VARCHAR(20),
    seal_number      VARCHAR(30),
    container_type   container_type,
    weight_kg        NUMERIC(12,2),
    notes            TEXT,
    created_at       TIMESTAMPTZ    NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ    NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_containers_shipment_id      ON containers(shipment_id);
CREATE INDEX IF NOT EXISTS ix_containers_container_number ON containers(container_number);

-- ─────────────────────────────────────────────────────────────────────────────
-- IMPORT ORDERS (tờ khai nhập khẩu)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS import_orders (
    id                         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    reference_number           VARCHAR(60),
    customs_declaration_number VARCHAR(60),
    shipment_id                UUID        REFERENCES shipments(id) ON DELETE SET NULL,
    import_date                DATE,
    total_value_vnd            NUMERIC(18,2),
    total_tax_vnd              NUMERIC(18,2),
    status                     VARCHAR(30) NOT NULL DEFAULT 'draft',
    notes                      TEXT,
    created_at                 TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                 TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_import_orders_reference_number ON import_orders(reference_number);
CREATE INDEX IF NOT EXISTS ix_import_orders_shipment_id      ON import_orders(shipment_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- EXPORT ORDERS (tờ khai xuất khẩu)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS export_orders (
    id                         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    reference_number           VARCHAR(60),
    customs_declaration_number VARCHAR(60),
    shipment_id                UUID        REFERENCES shipments(id) ON DELETE SET NULL,
    export_date                DATE,
    total_value_usd            NUMERIC(18,2),
    status                     VARCHAR(30) NOT NULL DEFAULT 'draft',
    notes                      TEXT,
    created_at                 TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                 TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_export_orders_reference_number ON export_orders(reference_number);
CREATE INDEX IF NOT EXISTS ix_export_orders_shipment_id      ON export_orders(shipment_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- EXPENSES
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS expenses (
    id                UUID             PRIMARY KEY DEFAULT gen_random_uuid(),
    category          expense_category NOT NULL,
    reference         VARCHAR(100),
    description       VARCHAR(500),
    amount            NUMERIC(18,4)    NOT NULL,
    currency_id       UUID             REFERENCES currencies(id)      ON DELETE RESTRICT,
    expense_date      DATE,
    shipment_id       UUID             REFERENCES shipments(id)       ON DELETE SET NULL,
    purchase_order_id UUID             REFERENCES purchase_orders(id) ON DELETE SET NULL,
    notes             TEXT,
    created_at        TIMESTAMPTZ      NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ      NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_expenses_category          ON expenses(category);
CREATE INDEX IF NOT EXISTS ix_expenses_expense_date      ON expenses(expense_date);
CREATE INDEX IF NOT EXISTS ix_expenses_shipment_id       ON expenses(shipment_id);
CREATE INDEX IF NOT EXISTS ix_expenses_purchase_order_id ON expenses(purchase_order_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- IMPORT RUNS  (one record per import job)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS import_runs (
    id            UUID              PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type   source_type       NOT NULL,
    entity_type   entity_type       NOT NULL,
    source_file   VARCHAR(500),
    source_hash   VARCHAR(64),
    status        import_run_status NOT NULL DEFAULT 'running',
    total_rows    INTEGER           NOT NULL DEFAULT 0,
    imported_rows INTEGER           NOT NULL DEFAULT 0,
    skipped_rows  INTEGER           NOT NULL DEFAULT 0,
    error_rows    INTEGER           NOT NULL DEFAULT 0,
    warning_rows  INTEGER           NOT NULL DEFAULT 0,
    started_at    TIMESTAMPTZ       NOT NULL DEFAULT now(),
    completed_at  TIMESTAMPTZ,
    created_by    VARCHAR(100),
    error_summary JSONB
);
CREATE INDEX IF NOT EXISTS ix_import_runs_entity_type ON import_runs(entity_type);
CREATE INDEX IF NOT EXISTS ix_import_runs_status      ON import_runs(status);

-- ─────────────────────────────────────────────────────────────────────────────
-- IMPORT RUN ROWS  (per-row audit trail)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS import_run_rows (
    id            UUID       PRIMARY KEY DEFAULT gen_random_uuid(),
    import_run_id UUID       NOT NULL REFERENCES import_runs(id) ON DELETE CASCADE,
    row_number    INTEGER    NOT NULL,
    status        row_status NOT NULL DEFAULT 'ok',
    source_data   JSONB,
    mapped_data   JSONB,
    messages      JSONB,
    entity_id     UUID
);
CREATE INDEX IF NOT EXISTS ix_import_run_rows_import_run_id ON import_run_rows(import_run_id);
CREATE INDEX IF NOT EXISTS ix_import_run_rows_status        ON import_run_rows(status);

-- ─────────────────────────────────────────────────────────────────────────────
-- STAGING PRODUCTS  (intermediate table for product imports)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS staging_products (
    id                    UUID              PRIMARY KEY DEFAULT gen_random_uuid(),
    import_run_id         UUID              NOT NULL REFERENCES import_runs(id) ON DELETE CASCADE,
    row_number            INTEGER           NOT NULL,
    raw_code              VARCHAR(200),
    raw_name              VARCHAR(500),
    raw_name_en           VARCHAR(500),
    raw_category          VARCHAR(255),
    raw_uom               VARCHAR(80),
    raw_purchase_uom      VARCHAR(80),
    raw_cost_price        VARCHAR(50),
    raw_list_price        VARCHAR(50),
    raw_barcode           VARCHAR(100),
    raw_weight            VARCHAR(50),
    raw_min_stock         VARCHAR(50),
    raw_max_stock         VARCHAR(50),
    raw_description       TEXT,
    raw_extra             JSONB,
    mapped_code           VARCHAR(80),
    mapped_name           VARCHAR(500),
    mapped_category_id    UUID,
    mapped_uom_id         UUID,
    mapped_purchase_uom_id UUID,
    mapped_cost_price     NUMERIC(18,4),
    mapped_list_price     NUMERIC(18,4),
    validation_status     validation_status NOT NULL DEFAULT 'pending',
    validation_errors     JSONB,
    product_id            UUID
);
CREATE INDEX IF NOT EXISTS ix_staging_products_import_run_id     ON staging_products(import_run_id);
CREATE INDEX IF NOT EXISTS ix_staging_products_validation_status ON staging_products(validation_status);
    """)


def downgrade() -> None:
    op.execute("""
        DROP TABLE IF EXISTS staging_products      CASCADE;
        DROP TABLE IF EXISTS import_run_rows       CASCADE;
        DROP TABLE IF EXISTS import_runs           CASCADE;
        DROP TABLE IF EXISTS expenses              CASCADE;
        DROP TABLE IF EXISTS export_orders         CASCADE;
        DROP TABLE IF EXISTS import_orders         CASCADE;
        DROP TABLE IF EXISTS containers            CASCADE;
        DROP TABLE IF EXISTS shipments             CASCADE;
        DROP TABLE IF EXISTS purchase_order_items  CASCADE;
        DROP TABLE IF EXISTS purchase_orders       CASCADE;
        DROP TABLE IF EXISTS sales_order_items     CASCADE;
        DROP TABLE IF EXISTS sales_orders          CASCADE;
        DROP TABLE IF EXISTS stock_balances        CASCADE;
        DROP TABLE IF EXISTS stock_movements       CASCADE;
        DROP TABLE IF EXISTS warehouse_locations   CASCADE;
        DROP TABLE IF EXISTS warehouses            CASCADE;
        DROP TABLE IF EXISTS price_list_items      CASCADE;
        DROP TABLE IF EXISTS price_lists           CASCADE;
        DROP TABLE IF EXISTS suppliers             CASCADE;
        DROP TABLE IF EXISTS customers             CASCADE;
        DROP TABLE IF EXISTS products              CASCADE;
        DROP TABLE IF EXISTS product_categories    CASCADE;
        DROP TABLE IF EXISTS payment_terms         CASCADE;
        DROP TABLE IF EXISTS units_of_measure      CASCADE;
        DROP TABLE IF EXISTS currencies            CASCADE;
        DROP TABLE IF EXISTS users                 CASCADE;
        DROP TABLE IF EXISTS roles                 CASCADE;

        DROP TYPE IF EXISTS validation_status;
        DROP TYPE IF EXISTS row_status;
        DROP TYPE IF EXISTS import_run_status;
        DROP TYPE IF EXISTS entity_type;
        DROP TYPE IF EXISTS source_type;
        DROP TYPE IF EXISTS expense_category;
        DROP TYPE IF EXISTS container_type;
        DROP TYPE IF EXISTS shipment_status;
        DROP TYPE IF EXISTS shipment_type;
        DROP TYPE IF EXISTS payment_status;
        DROP TYPE IF EXISTS order_status;
        DROP TYPE IF EXISTS reference_type;
        DROP TYPE IF EXISTS movement_type;
        DROP TYPE IF EXISTS location_type;
        DROP TYPE IF EXISTS product_type;
        DROP TYPE IF EXISTS uom_type;
        DROP TYPE IF EXISTS uom_category;
    """)
