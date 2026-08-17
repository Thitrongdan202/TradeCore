"""
TradeCore — Dashboard Pydantic Schemas
Aggregated KPI metrics, revenue charts, and operational summary views.
"""
from __future__ import annotations

import uuid
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class DashboardKPISummary(BaseModel):
    total_revenue: float = 0.0
    total_sales_orders: int = 0
    total_purchase_orders: int = 0
    total_customers: int = 0
    total_suppliers: int = 0
    total_products: int = 0
    low_stock_count: int = 0
    pending_sales_orders: int = 0
    pending_purchase_orders: int = 0


class RevenueChartDataPoint(BaseModel):
    label: str  # e.g. "2026-01", "T01/2026", "2026-08-01"
    revenue: float
    order_count: int


class RecentSalesOrderSummary(BaseModel):
    id: uuid.UUID
    order_number: str
    customer_name: Optional[str] = None
    date: Optional[str] = None
    total: float = 0.0
    status: str
    payment_status: str

    model_config = ConfigDict(from_attributes=True)


class RecentPurchaseOrderSummary(BaseModel):
    id: uuid.UUID
    order_number: str
    supplier_name: Optional[str] = None
    date: Optional[str] = None
    total: float = 0.0
    status: str
    payment_status: str

    model_config = ConfigDict(from_attributes=True)


class LowStockItem(BaseModel):
    product_id: uuid.UUID
    product_code: str
    product_name: str
    current_stock: float
    min_stock: float
    uom_name: Optional[str] = None


class DashboardResponse(BaseModel):
    kpi: DashboardKPISummary
    revenue_chart: List[RevenueChartDataPoint]
    recent_sales: List[RecentSalesOrderSummary]
    recent_purchases: List[RecentPurchaseOrderSummary]
    low_stock_items: List[LowStockItem]
