"""
TradeCore — FastAPI Application Entry Point
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    debug=settings.app_debug,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ─── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health check ────────────────────────────────────────────────────────────
@app.get("/health", tags=["system"])
def health_check():
    """
    Liveness probe. Returns 200 if the API is running.
    DB connectivity is checked separately via /health/db.
    """
    return {"status": "ok", "version": settings.app_version, "env": settings.app_env}


@app.get("/health/db", tags=["system"])
def health_db():
    """Database connectivity check."""
    from sqlalchemy import text
    from app.core.database import engine

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as exc:
        return {"status": "error", "database": "unreachable", "detail": str(exc)}


# ─── Routers ─────────────────────────────────────────────────────────────────
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.products import router as products_router
from app.api.partners import router as partners_router
from app.api.inventory import router as inventory_router
from app.api.pricing import router as pricing_router
from app.api.sales import router as sales_router
from app.api.purchasing import router as purchasing_router
from app.api.dashboard import router as dashboard_router

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(users_router, prefix="/api/v1/users", tags=["Users & Roles"])
app.include_router(products_router, prefix="/api/v1/products", tags=["Products & Categories"])
app.include_router(partners_router, prefix="/api/v1/partners", tags=["Partners (Customers & Suppliers)"])
app.include_router(inventory_router, prefix="/api/v1/inventory", tags=["Inventory & Warehouses"])
app.include_router(pricing_router, prefix="/api/v1/pricing", tags=["Pricing & Price Lists"])
app.include_router(sales_router, prefix="/api/v1/sales", tags=["Sales Orders"])
app.include_router(purchasing_router, prefix="/api/v1/purchasing", tags=["Purchase Orders"])
app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["Dashboard & Analytics"])
