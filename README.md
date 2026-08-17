# TradeCore

TradeCore is a business management system for trading and import/export companies.

The project is designed to manage:

- Sales
- Purchasing
- Products
- Customers
- Suppliers
- Warehouses
- Inventory
- Import operations
- Export operations
- Pricing
- Business reports
- Data migration from Excel and Odoo

---

## Technology Stack

### Frontend

- React
- TypeScript
- Vite

### Backend

- Python
- FastAPI
- Uvicorn
- SQLAlchemy
- Alembic

### Database

- PostgreSQL 16

### Infrastructure

- Docker
- Docker Compose

---

## Requirements

Install the following software before running the project:

- Git
- Node.js
- npm
- Python 3.13
- Docker Desktop

Verify the installation:

```powershell
git --version
node --version
npm --version
python --version
docker --version
docker compose version
```

Docker Desktop must be running before starting the PostgreSQL container.

---

## Project Structure

```text
TradeCore/
├── backend/               # FastAPI backend
│   ├── app/
│   ├── migrations/
│   ├── scripts/
│   ├── tests/
│   └── .venv/
│
├── src/                   # React frontend
├── public/                # Static frontend assets
├── data/                  # Project data and local input files
├── docs/                  # Project documentation
├── docker-compose.yml     # PostgreSQL container configuration
├── package.json           # Frontend dependencies and scripts
├── package-lock.json
├── vite.config.ts
├── tsconfig.json
└── README.md
```

---

# Installation

## 1. Clone the repository

```powershell
git clone <repository-url>
cd TradeCore
```

---

## 2. Install frontend dependencies

From the project root:

```powershell
npm install
```

---

## 3. Create the Python virtual environment

Enter the backend directory:

```powershell
cd backend
```

Create the virtual environment:

```powershell
python -m venv .venv
```

---

## 4. Activate the Python virtual environment

On Windows PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then:

```powershell
.\.venv\Scripts\Activate.ps1
```

A successful activation should show:

```text
(.venv)
```

at the beginning of the terminal prompt.

Verify the Python executable:

```powershell
python -c "import sys; print(sys.executable)"
```

The result should point to:

```text
backend\.venv\Scripts\python.exe
```

---

## 5. Install backend dependencies

Upgrade pip:

```powershell
python -m pip install --upgrade pip
```

If `requirements.txt` is available:

```powershell
python -m pip install -r requirements.txt
```

---

# PostgreSQL

TradeCore uses PostgreSQL as its main database.

PostgreSQL is provided through Docker Compose.

From the project root:

```powershell
docker compose up -d postgres
```

Check the container status:

```powershell
docker compose ps
```

View PostgreSQL logs:

```powershell
docker compose logs postgres --tail=50
```

PostgreSQL should be running before starting the backend.

---

# Database Initialization

Enter the backend directory:

```powershell
cd backend
```

Activate the virtual environment:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Run database migrations:

```powershell
python -m alembic upgrade head
```

Seed the initial reference data:

```powershell
python scripts/seed.py
```

The seed process initializes reference data such as:

- Currencies
- Units of measure
- Payment terms
- Roles
- Warehouses
- Other required reference records

---

# Run the Backend

From the `backend` directory with the virtual environment activated:

```powershell
uvicorn app.main:app --reload
```

The backend normally runs at:

```text
http://127.0.0.1:8000
```

## API Documentation

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

ReDoc:

```text
http://127.0.0.1:8000/redoc
```

---

# Run the Frontend

Open another terminal.

Go to the project root:

```powershell
cd TradeCore
```

Start the Vite development server:

```powershell
npm run dev
```

Vite will display the local URL in the terminal.

The default address is usually:

```text
http://localhost:5173
```

Open the displayed URL in a browser.

---

# Run the Complete Development Environment

TradeCore requires three running services during development.

## Terminal 1 — PostgreSQL

From the project root:

```powershell
docker compose up -d postgres
```

## Terminal 2 — Backend

```powershell
cd backend
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

## Terminal 3 — Frontend

```powershell
npm run dev
```

The architecture is:

```text
React + Vite
      │
      ▼
   FastAPI
      │
      ▼
 PostgreSQL
```

---

# Run Tests

Enter the backend directory:

```powershell
cd backend
```

Activate the virtual environment:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Run the test suite:

```powershell
python -m pytest
```

All tests should pass before merging significant changes.

---

# Frontend Validation

From the project root, run linting:

```powershell
npm run lint
```

Build the frontend:

```powershell
npm run build
```

---

# Database Migrations

Create a new migration:

```powershell
python -m alembic revision --autogenerate -m "describe change"
```

Apply migrations:

```powershell
python -m alembic upgrade head
```

Check the current migration:

```powershell
python -m alembic current
```

---

# Data Import

TradeCore supports importing business data from external sources such as:

- Excel
- CSV
- Odoo exports

Local input data should be placed in the project's data/import location according to the importer configuration.

The recommended import workflow is:

```text
Excel / CSV / Odoo
        │
        ▼
   Data Validation
        │
        ▼
     Dry Run
        │
        ▼
 Review Errors
 and Warnings
        │
        ▼
      Import
        │
        ▼
   PostgreSQL
```

The import process should validate:

- Missing required fields
- Duplicate identifiers
- Invalid dates
- Invalid prices
- Invalid quantities
- Invalid currencies
- Invalid units
- Conflicting records
- Invalid relationships

Source files should never be modified automatically.

---

# Import Safety

Before importing real company data:

1. Run the importer in dry-run mode.
2. Review errors and warnings.
3. Verify field mappings.
4. Verify duplicate records.
5. Confirm the source data.
6. Run the real import only after validation.

Do not overwrite production data automatically.

---

# Odoo Data Migration

Odoo is treated as a source/reference system for business workflows and data migration.

TradeCore should maintain its own PostgreSQL schema and business domain model.

The intended migration flow is:

```text
Odoo
  │
  ▼
Export
  │
  ▼
Validation
  │
  ▼
Mapping
  │
  ▼
TradeCore PostgreSQL
```

TradeCore must not depend permanently on an Odoo database unless explicitly designed for a future integration.

---

# Stop Services

Stop the frontend:

```text
Ctrl + C
```

Stop the backend:

```text
Ctrl + C
```

Stop PostgreSQL:

```powershell
docker compose stop postgres
```

Stop the complete Docker Compose environment:

```powershell
docker compose down
```

---

# Restart the Project

After the initial setup, the normal development workflow is:

## Start PostgreSQL

```powershell
docker compose up -d postgres
```

## Start Backend

```powershell
cd backend
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

## Start Frontend

Open another terminal:

```powershell
npm run dev
```

---

# Environment Variables

Sensitive configuration must be stored in environment variables.

Do not commit:

- Database passwords
- API keys
- JWT secrets
- Authentication secrets
- Private credentials

Use an environment example file such as:

```text
.env.example
```

Never commit the real `.env` file containing production credentials.

---

# Git

Before committing changes:

```powershell
git status
```

Review modified files:

```powershell
git diff
```

Stage changes:

```powershell
git add .
```

Create a commit:

```powershell
git commit -m "describe change"
```

Check the working tree:

```powershell
git status
```

---

# Development Guidelines

- Keep frontend and backend responsibilities separated.
- Frontend must communicate with the backend through APIs.
- Frontend must never access PostgreSQL directly.
- Database changes must use Alembic migrations.
- Inventory changes must be transactional.
- Stock quantities should not be modified without a corresponding stock movement.
- Preserve source data during migration.
- Validate imported data before committing it to the main database.
- Add tests for important business logic.
- Do not commit secrets.
- Avoid unnecessary dependencies.

---

# Current Development Scope

TradeCore is being developed around the following core business areas:

- Dashboard
- Products
- Customers
- Suppliers
- Warehouses
- Inventory
- Purchasing
- Sales
- Import operations
- Export operations
- Shipments
- Containers
- Pricing
- Business reports
- Excel data import
- Odoo data migration

Advanced features such as native mobile applications, multilingual document templates, advanced accounting and SaaS functionality are planned for later phases.

---

# Local Development Architecture

```text
                  TradeCore
                     │
        ┌────────────┴────────────┐
        │                         │
   React + Vite              FastAPI
        │                         │
        └────────────┬────────────┘
                     │
                     ▼
               PostgreSQL
                     │
                  Docker
```

---

# Project Status

Current foundation includes:

- React + Vite frontend
- FastAPI backend
- PostgreSQL
- Docker Compose
- Alembic migrations
- Reference data seeding
- Excel/CSV import framework
- Odoo migration preparation
- Automated tests

The project is currently under active development.
