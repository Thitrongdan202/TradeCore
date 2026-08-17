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


# ─── Routers (add as modules are built) ──────────────────────────────────────
# from app.api.products import router as products_router
# from app.api.customers import router as customers_router
# app.include_router(products_router, prefix="/api/v1/products", tags=["Products"])
# app.include_router(customers_router, prefix="/api/v1/customers", tags=["Customers"])
