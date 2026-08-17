# TradeCore — Architecture

## System Overview

TradeCore is a business management system for a Vietnamese trading and import/export company.

```
Browser
  ↓ HTTPS
Frontend (Vite + React 19 + TypeScript)
  ↓ REST / JSON
FastAPI (Python)
  ↓ SQLAlchemy ORM
PostgreSQL 16
```

Odoo is an **external reference system** used only during initial migration. TradeCore does not depend on Odoo at runtime.

---

## Technology Stack

| Layer | Technology | Version |
|---|---|---|
| Frontend | Vite + React + TypeScript | React 19, Vite 8 |
| Backend | FastAPI | 0.115.x |
| ORM | SQLAlchemy | 2.0 |
| Migrations | Alembic | 1.16 |
| Database | PostgreSQL | 16 |
| Auth | JWT (python-jose + passlib/bcrypt) | |
| Data import | openpyxl + pandas | |

---

## Directory Structure

```
tradecore/
├── frontend/                 ← Vite + React SPA
│   ├── src/
│   │   ├── App.tsx           ← Router
│   │   ├── types/index.ts    ← TypeScript domain types
│   │   ├── data/mock.ts      ← Mock data (replace with API calls)
│   │   ├── layouts/          ← AppLayout, Sidebar, Header
│   │   ├── pages/            ← Dashboard + placeholder pages
│   │   ├── components/       ← Badge, Icon, shared UI
│   │   └── styles/           ← Design tokens, base, components CSS
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── main.py           ← FastAPI entry point
│   │   ├── core/
│   │   │   ├── config.py     ← Pydantic settings (reads .env)
│   │   │   └── database.py   ← SQLAlchemy engine + session
│   │   ├── models/           ← SQLAlchemy ORM models (see database.md)
│   │   ├── schemas/          ← Pydantic request/response schemas (Phase 2+)
│   │   ├── services/         ← Business logic (Phase 2+)
│   │   └── api/              ← FastAPI routers (Phase 2+)
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/         ← Migration scripts
│   ├── scripts/
│   │   ├── seed.py           ← Reference data seed
│   │   ├── import_excel.py   ← Excel import pipeline (Phase 2)
│   │   └── import_odoo.py    ← Odoo data import (Phase 2)
│   ├── alembic.ini
│   ├── requirements.txt
│   └── .env.example
│
├── data/                     ← Source files — NEVER MODIFY
│   ├── odoo/                 ← Odoo CSV/XML exports
│   └── excel/                ← Company Excel files
│
├── docs/                     ← This documentation
├── docker-compose.yml
└── README.md
```

---

## Key Design Decisions

### 1. Transaction-based inventory
Stock is never updated by overwriting a quantity field. Every change creates an immutable `StockMovement` record. `StockBalance` is a derived summary updated atomically in the same transaction.

### 2. Stable product codes
`products.code` is the business identifier used as the upsert key during all imports. Do not use the UUID `products.id` as an external reference.

### 3. Double-entry stock locations
Every stock movement has a `from_location_id` and `to_location_id`, mirroring Odoo's double-entry warehouse accounting. Virtual locations (supplier, customer, transit, adjustment) are required for this to work correctly.

### 4. Safe migration pipeline
Source data is never modified. All imports flow through staging tables with validation before touching production tables.

### 5. Multi-currency
VND is the base currency (exchange_rate = 1.0). All other currencies have an exchange rate to VND. Rates are updated manually — not auto-fetched.

---

## API Design (Phase 2+)

All endpoints follow this convention:

```
GET    /api/v1/{resource}           → list (paginated)
GET    /api/v1/{resource}/{id}      → detail
POST   /api/v1/{resource}           → create
PUT    /api/v1/{resource}/{id}      → full update
PATCH  /api/v1/{resource}/{id}      → partial update
DELETE /api/v1/{resource}/{id}      → soft delete (set is_active=False)
```

Pagination: `?page=1&size=50`
Filtering: `?status=confirmed&customer_code=KH-0041`

---

## Running Locally

### Prerequisites
- Docker Desktop (for PostgreSQL)
- Python 3.11+
- Node.js 20+

### Start PostgreSQL
```bash
docker compose up -d postgres
```

### Backend setup
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate       # Windows
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head         # Create all tables
python scripts/seed.py       # Populate reference data
uvicorn app.main:app --reload --port 8000
```

### Frontend setup
```bash
# (from project root)
npm install
npm run dev
```

### API docs
Open http://localhost:8000/docs
