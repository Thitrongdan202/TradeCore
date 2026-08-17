"""
TradeCore — Dashboard API Router
Calculates aggregated KPIs, revenue charts, and operational summaries directly from the database.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, and_, or_
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, get_db
from app.models.inventory import StockBalance
from app.models.partner import Customer, Supplier
from app.models.product import Product
from app.models.purchase import PurchaseOrder
from app.models.sales import OrderStatus, SalesOrder
from app.models.uom import UnitOfMeasure
from app.models.user import User
from app.schemas.dashboard import (
    DashboardKPISummary,
    DashboardResponse,
    LowStockItem,
    RecentPurchaseOrderSummary,
    RecentSalesOrderSummary,
    RevenueChartDataPoint,
)

router = APIRouter()


@router.get("/summary", response_model=DashboardKPISummary, summary="Lấy tóm tắt chỉ số KPI")
def get_kpi_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Calculate core business KPI metrics."""
    # Total revenue from non-cancelled sales orders
    total_rev = db.execute(
        select(func.coalesce(func.sum(SalesOrder.total), 0.0)).where(
            SalesOrder.status != OrderStatus.cancelled
        )
    ).scalar() or 0.0

    total_so = db.execute(select(func.count(SalesOrder.id))).scalar() or 0
    total_po = db.execute(select(func.count(PurchaseOrder.id))).scalar() or 0
    total_cust = db.execute(select(func.count(Customer.id)).where(Customer.is_active == True)).scalar() or 0
    total_supp = db.execute(select(func.count(Supplier.id)).where(Supplier.is_active == True)).scalar() or 0
    total_prod = db.execute(select(func.count(Product.id)).where(Product.is_active == True)).scalar() or 0

    pending_so = db.execute(
        select(func.count(SalesOrder.id)).where(
            SalesOrder.status.in_([OrderStatus.draft, OrderStatus.pending, OrderStatus.confirmed, OrderStatus.processing, OrderStatus.shipping])
        )
    ).scalar() or 0

    pending_po = db.execute(
        select(func.count(PurchaseOrder.id)).where(
            PurchaseOrder.status.in_([OrderStatus.draft, OrderStatus.pending, OrderStatus.processing])
        )
    ).scalar() or 0

    # Low stock count
    low_stock_count = db.execute(
        select(func.count(Product.id))
        .select_from(Product)
        .outerjoin(StockBalance, Product.id == StockBalance.product_id)
        .where(Product.is_active == True, Product.min_stock.is_not(None), Product.min_stock > 0)
        .group_by(Product.id, Product.min_stock)
        .having(func.coalesce(func.sum(StockBalance.qty_on_hand), 0) < Product.min_stock)
    ).all()

    return DashboardKPISummary(
        total_revenue=float(total_rev),
        total_sales_orders=total_so,
        total_purchase_orders=total_po,
        total_customers=total_cust,
        total_suppliers=total_supp,
        total_products=total_prod,
        low_stock_count=len(low_stock_count),
        pending_sales_orders=pending_so,
        pending_purchase_orders=pending_po,
    )


@router.get("/revenue-chart", response_model=List[RevenueChartDataPoint], summary="Biểu đồ doanh thu 6 tháng gần nhất")
def get_revenue_chart(
    months: int = Query(6, ge=1, le=24, description="Số tháng thống kê"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve monthly revenue trends for charting."""
    today = date.today()
    chart_points: List[RevenueChartDataPoint] = []

    # Generate month labels for the last N months
    for i in range(months - 1, -1, -1):
        # Calculate first day and last day of target month
        year = today.year
        month = today.month - i
        while month <= 0:
            month += 12
            year -= 1

        label = f"{year:04d}-{month:02d}"
        label_display = f"T{month:02d}/{year}"

        # Month bounds
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)

        result = db.execute(
            select(
                func.coalesce(func.sum(SalesOrder.total), 0.0).label("revenue"),
                func.count(SalesOrder.id).label("order_count"),
            ).where(
                SalesOrder.date >= start_date,
                SalesOrder.date <= end_date,
                SalesOrder.status != OrderStatus.cancelled,
            )
        ).first()

        rev = float(result.revenue) if result else 0.0
        cnt = int(result.order_count) if result else 0

        chart_points.append(
            RevenueChartDataPoint(
                label=label_display,
                revenue=rev,
                order_count=cnt,
            )
        )

    return chart_points


@router.get("/recent-orders", summary="Lấy danh sách đơn hàng gần đây")
def get_recent_orders(
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve top recent sales and purchase orders."""
    recent_sales = db.execute(
        select(SalesOrder)
        .options(selectinload(SalesOrder.customer))
        .order_by(SalesOrder.created_at.desc())
        .limit(limit)
    ).scalars().all()

    recent_purchases = db.execute(
        select(PurchaseOrder)
        .options(selectinload(PurchaseOrder.supplier))
        .order_by(PurchaseOrder.created_at.desc())
        .limit(limit)
    ).scalars().all()

    sales_items = [
        RecentSalesOrderSummary(
            id=s.id,
            order_number=s.order_number,
            customer_name=s.customer.name if s.customer else None,
            date=str(s.date) if s.date else None,
            total=float(s.total or 0.0),
            status=s.status.value,
            payment_status=s.payment_status.value,
        )
        for s in recent_sales
    ]

    purchase_items = [
        RecentPurchaseOrderSummary(
            id=p.id,
            order_number=p.order_number,
            supplier_name=p.supplier.name if p.supplier else None,
            date=str(p.date) if p.date else None,
            total=float(p.total or 0.0),
            status=p.status.value,
            payment_status=p.payment_status.value,
        )
        for p in recent_purchases
    ]

    return {
        "recent_sales": sales_items,
        "recent_purchases": purchase_items,
    }


@router.get("/low-stock", response_model=List[LowStockItem], summary="Danh sách sản phẩm sắp hết hàng")
def get_low_stock_items(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve products where total stock on hand is below min_stock threshold."""
    rows = db.execute(
        select(
            Product.id,
            Product.code,
            Product.name,
            func.coalesce(func.sum(StockBalance.qty_on_hand), 0).label("current_stock"),
            Product.min_stock,
            UnitOfMeasure.name.label("uom_name"),
        )
        .outerjoin(StockBalance, Product.id == StockBalance.product_id)
        .outerjoin(UnitOfMeasure, Product.uom_id == UnitOfMeasure.id)
        .where(Product.is_active == True, Product.min_stock.is_not(None), Product.min_stock > 0)
        .group_by(Product.id, Product.code, Product.name, Product.min_stock, UnitOfMeasure.name)
        .having(func.coalesce(func.sum(StockBalance.qty_on_hand), 0) < Product.min_stock)
        .order_by(func.coalesce(func.sum(StockBalance.qty_on_hand), 0) - Product.min_stock)
        .limit(limit)
    ).all()

    return [
        LowStockItem(
            product_id=row.id,
            product_code=row.code,
            product_name=row.name,
            current_stock=float(row.current_stock),
            min_stock=float(row.min_stock),
            uom_name=row.uom_name,
        )
        for row in rows
    ]


@router.get("", response_model=DashboardResponse, summary="Tổng quan Dashboard hợp nhất")
def get_full_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Unified endpoint returning KPIs, revenue chart, recent orders, and low-stock alerts."""
    kpi = get_kpi_summary(db, current_user)
    chart = get_revenue_chart(6, db, current_user)
    orders = get_recent_orders(5, db, current_user)
    low_stock = get_low_stock_items(10, db, current_user)

    return DashboardResponse(
        kpi=kpi,
        revenue_chart=chart,
        recent_sales=orders["recent_sales"],
        recent_purchases=orders["recent_purchases"],
        low_stock_items=low_stock,
    )
