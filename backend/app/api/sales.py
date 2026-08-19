"""
TradeCore — Sales Orders API Router
Provides CRUD endpoints for Sales Orders, line items calculation, and lifecycle management.
"""
from __future__ import annotations

import math
import uuid
from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, or_
from sqlalchemy.orm import Session, selectinload

from app.core.security import RoleType
from app.api.deps import get_current_user, get_db, require_permission
from app.models.currency import Currency
from app.models.partner import Customer, PaymentTerm
from app.models.product import Product
from app.models.sales import OrderStatus, PaymentStatus, SalesOrder, SalesOrderItem
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.partner import CustomerResponse
from app.schemas.sales import (
    OrderStatusEnum,
    PaymentStatusEnum,
    SalesOrderCreate,
    SalesOrderDetailResponse,
    SalesOrderItemResponse,
    SalesOrderPaymentUpdate,
    SalesOrderResponse,
    SalesOrderStatusUpdate,
    SalesOrderUpdate,
)

router = APIRouter()


def generate_so_number(db: Session) -> str:
    """Generate automatic SO number format: SO-YYMM-XXXX."""
    today = date.today()
    prefix = f"SO-{today.strftime('%y%m')}-"
    count = db.execute(
        select(func.count(SalesOrder.id)).where(SalesOrder.order_number.like(f"{prefix}%"))
    ).scalar() or 0
    return f"{prefix}{count + 1:04d}"


def calculate_line_item(item_data, product: Optional[Product] = None) -> tuple[float, float]:
    """Calculate unit_price and subtotal for a sales order line."""
    price = item_data.unit_price
    if price is None and product and product.cost_price is not None:
        price = float(product.cost_price)
    elif price is None:
        price = 0.0

    discount = float(item_data.discount_percent or 0.0)
    qty = float(item_data.qty)
    subtotal = qty * price * (1.0 - (discount / 100.0))
    return price, round(subtotal, 4)


# ═══════════════════════════════════════════════════════════════════════════════
# SALES ORDERS CRUD
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/orders", response_model=PaginatedResponse[SalesOrderResponse], summary="Lấy danh sách đơn bán hàng")
def list_sales_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    customer_id: Optional[uuid.UUID] = Query(None, description="Lọc theo khách hàng"),
    status_filter: Optional[OrderStatusEnum] = Query(None, alias="status", description="Lọc theo trạng thái đơn"),
    payment_status_filter: Optional[PaymentStatusEnum] = Query(None, alias="payment_status", description="Lọc theo trạng thái thanh toán"),
    from_date: Optional[date] = Query(None, description="Từ ngày"),
    to_date: Optional[date] = Query(None, description="Đến ngày"),
    search: Optional[str] = Query(None, description="Tìm theo mã đơn hoặc tên khách hàng"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """List sales orders with filters and pagination."""
    query = (
        select(SalesOrder)
        .options(
            selectinload(SalesOrder.customer),
            selectinload(SalesOrder.items),
        )
    )

    if customer_id:
        query = query.where(SalesOrder.customer_id == customer_id)
    if status_filter:
        query = query.where(SalesOrder.status == status_filter.value)
    if payment_status_filter:
        query = query.where(SalesOrder.payment_status == payment_status_filter.value)
    if from_date:
        query = query.where(SalesOrder.date >= from_date)
    if to_date:
        query = query.where(SalesOrder.date <= to_date)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.join(SalesOrder.customer, isouter=True).where(
            or_(
                SalesOrder.order_number.ilike(pattern),
                Customer.name.ilike(pattern),
                Customer.code.ilike(pattern),
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar() or 0

    offset = (page - 1) * page_size
    orders = db.execute(
        query.order_by(SalesOrder.created_at.desc()).offset(offset).limit(page_size)
    ).scalars().all()

    items: List[SalesOrderResponse] = []
    for order in orders:
        items.append(
            SalesOrderResponse(
                id=order.id,
                order_number=order.order_number,
                customer_id=order.customer_id,
                currency_id=order.currency_id,
                payment_term_id=order.payment_term_id,
                date=order.date,
                due_date=order.due_date,
                status=OrderStatusEnum(order.status.value),
                payment_status=PaymentStatusEnum(order.payment_status.value),
                subtotal=float(order.subtotal) if order.subtotal is not None else None,
                tax_amount=float(order.tax_amount) if order.tax_amount is not None else 0.0,
                total=float(order.total) if order.total is not None else None,
                amount_paid=float(order.amount_paid) if order.amount_paid is not None else 0.0,
                odoo_id=order.odoo_id,
                created_by_id=order.created_by_id,
                notes=order.notes,
                customer_name=order.customer.name if order.customer else None,
                customer_code=order.customer.code if order.customer else None,
                items_count=len(order.items),
                created_at=order.created_at,
                updated_at=order.updated_at,
            )
        )

    total_pages = math.ceil(total / page_size) if page_size > 0 else 1

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/orders/{order_id}", response_model=SalesOrderDetailResponse, summary="Lấy chi tiết đơn bán hàng")
def get_sales_order(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """Retrieve full sales order details with items and customer info."""
    order = db.execute(
        select(SalesOrder)
        .options(
            selectinload(SalesOrder.customer),
            selectinload(SalesOrder.items).selectinload(SalesOrderItem.product),
            selectinload(SalesOrder.items).selectinload(SalesOrderItem.uom),
        )
        .where(SalesOrder.id == order_id)
    ).scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy đơn bán hàng với ID {order_id}",
        )

    item_responses: List[SalesOrderItemResponse] = []
    for item in order.items:
        item_responses.append(
            SalesOrderItemResponse(
                id=item.id,
                order_id=item.order_id,
                line_no=item.line_no,
                product_id=item.product_id,
                description=item.description,
                qty=float(item.qty),
                uom_id=item.uom_id,
                unit_price=float(item.unit_price) if item.unit_price is not None else None,
                discount_percent=float(item.discount_percent),
                subtotal=float(item.subtotal) if item.subtotal is not None else None,
                notes=item.notes,
                product_code=item.product.code if item.product else None,
                product_name=item.product.name if item.product else None,
                uom_name=item.uom.name if item.uom else None,
            )
        )

    return SalesOrderDetailResponse(
        id=order.id,
        order_number=order.order_number,
        customer_id=order.customer_id,
        currency_id=order.currency_id,
        payment_term_id=order.payment_term_id,
        date=order.date,
        due_date=order.due_date,
        status=OrderStatusEnum(order.status.value),
        payment_status=PaymentStatusEnum(order.payment_status.value),
        subtotal=float(order.subtotal) if order.subtotal is not None else None,
        tax_amount=float(order.tax_amount) if order.tax_amount is not None else 0.0,
        total=float(order.total) if order.total is not None else None,
        amount_paid=float(order.amount_paid) if order.amount_paid is not None else 0.0,
        odoo_id=order.odoo_id,
        created_by_id=order.created_by_id,
        notes=order.notes,
        customer_name=order.customer.name if order.customer else None,
        customer_code=order.customer.code if order.customer else None,
        items_count=len(item_responses),
        created_at=order.created_at,
        updated_at=order.updated_at,
        customer=CustomerResponse.model_validate(order.customer) if order.customer else None,
        items=item_responses,
    )


@router.post(
    "/orders",
    response_model=SalesOrderDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo mới đơn bán hàng",
)
def create_sales_order(
    payload: SalesOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """Create a new sales order with calculated line totals."""
    order_number = payload.order_number.strip() if payload.order_number else generate_so_number(db)

    # Check order_number uniqueness
    if db.execute(select(SalesOrder).where(SalesOrder.order_number == order_number)).scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Mã đơn hàng '{order_number}' đã tồn tại",
        )

    # Validate customer
    if payload.customer_id:
        cust = db.execute(select(Customer).where(Customer.id == payload.customer_id)).scalar_one_or_none()
        if not cust:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không tìm thấy khách hàng với ID {payload.customer_id}",
            )

    order = SalesOrder(
        order_number=order_number,
        customer_id=payload.customer_id,
        currency_id=payload.currency_id,
        payment_term_id=payload.payment_term_id,
        date=payload.date or date.today(),
        due_date=payload.due_date,
        status=payload.status.value,
        payment_status=payload.payment_status.value,
        notes=payload.notes,
        created_by_id=current_user.id,
    )
    db.add(order)
    db.flush()

    total_subtotal = 0.0
    for idx, item_data in enumerate(payload.items, start=1):
        product: Optional[Product] = None
        if item_data.product_id:
            product = db.execute(select(Product).where(Product.id == item_data.product_id)).scalar_one_or_none()

        unit_price, line_subtotal = calculate_line_item(item_data, product)
        total_subtotal += line_subtotal

        item = SalesOrderItem(
            order_id=order.id,
            line_no=idx,
            product_id=item_data.product_id,
            description=item_data.description or (product.name if product else None),
            qty=item_data.qty,
            uom_id=item_data.uom_id or (product.uom_id if product else None),
            unit_price=unit_price,
            discount_percent=item_data.discount_percent,
            subtotal=line_subtotal,
            notes=item_data.notes,
        )
        db.add(item)

    order.subtotal = total_subtotal
    order.tax_amount = round(total_subtotal * 0.1, 2)  # Default 10% VAT
    order.total = round(order.subtotal + order.tax_amount, 2)

    db.commit()
    db.refresh(order)

    return get_sales_order(order.id, db, current_user)


@router.put("/orders/{order_id}", response_model=SalesOrderDetailResponse, summary="Cập nhật đơn bán hàng")
def update_sales_order(
    order_id: uuid.UUID,
    payload: SalesOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """Update sales order details and optionally replace items."""
    order = db.execute(select(SalesOrder).where(SalesOrder.id == order_id)).scalar_one_or_none()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy đơn bán hàng với ID {order_id}",
        )

    if payload.customer_id is not None:
        order.customer_id = payload.customer_id
    if payload.currency_id is not None:
        order.currency_id = payload.currency_id
    if payload.payment_term_id is not None:
        order.payment_term_id = payload.payment_term_id
    if payload.date is not None:
        order.date = payload.date
    if payload.due_date is not None:
        order.due_date = payload.due_date
    if payload.status is not None:
        order.status = payload.status.value
    if payload.payment_status is not None:
        order.payment_status = payload.payment_status.value
    if payload.notes is not None:
        order.notes = payload.notes

    if payload.items is not None:
        # Delete existing items and add new ones
        db.query(SalesOrderItem).filter(SalesOrderItem.order_id == order_id).delete()
        total_subtotal = 0.0
        for idx, item_data in enumerate(payload.items, start=1):
            product: Optional[Product] = None
            if item_data.product_id:
                product = db.execute(select(Product).where(Product.id == item_data.product_id)).scalar_one_or_none()

            unit_price, line_subtotal = calculate_line_item(item_data, product)
            total_subtotal += line_subtotal

            item = SalesOrderItem(
                order_id=order.id,
                line_no=idx,
                product_id=item_data.product_id,
                description=item_data.description or (product.name if product else None),
                qty=item_data.qty,
                uom_id=item_data.uom_id or (product.uom_id if product else None),
                unit_price=unit_price,
                discount_percent=item_data.discount_percent,
                subtotal=line_subtotal,
                notes=item_data.notes,
            )
            db.add(item)

        order.subtotal = total_subtotal
        order.tax_amount = round(total_subtotal * 0.1, 2)
        order.total = round(order.subtotal + order.tax_amount, 2)

    db.commit()
    db.refresh(order)

    return get_sales_order(order.id, db, current_user)


@router.patch("/orders/{order_id}/status", response_model=SalesOrderDetailResponse, summary="Cập nhật trạng thái đơn hàng")
def update_order_status(
    order_id: uuid.UUID,
    payload: SalesOrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """Update lifecycle status of a sales order."""
    order = db.execute(select(SalesOrder).where(SalesOrder.id == order_id)).scalar_one_or_none()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy đơn bán hàng với ID {order_id}",
        )

    order.status = payload.status.value
    if payload.notes:
        order.notes = f"{order.notes or ''}\n[Status Change]: {payload.notes}"

    db.commit()
    db.refresh(order)
    return get_sales_order(order.id, db, current_user)


@router.patch("/orders/{order_id}/payment", response_model=SalesOrderDetailResponse, summary="Cập nhật trạng thái thanh toán")
def update_order_payment(
    order_id: uuid.UUID,
    payload: SalesOrderPaymentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """Update payment status and amount paid."""
    order = db.execute(select(SalesOrder).where(SalesOrder.id == order_id)).scalar_one_or_none()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy đơn bán hàng với ID {order_id}",
        )

    order.payment_status = payload.payment_status.value
    if payload.amount_paid is not None:
        order.amount_paid = payload.amount_paid

    db.commit()
    db.refresh(order)
    return get_sales_order(order.id, db, current_user)


@router.delete("/orders/{order_id}", response_model=MessageResponse, summary="Hủy hoặc xóa đơn bán hàng")
def delete_sales_order(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """Cancel or delete sales order."""
    order = db.execute(select(SalesOrder).where(SalesOrder.id == order_id)).scalar_one_or_none()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy đơn bán hàng với ID {order_id}",
        )

    if order.status in [OrderStatus.completed, OrderStatus.shipping]:
        order.status = OrderStatus.cancelled
        db.commit()
        return MessageResponse(
            message=f"Đơn hàng '{order.order_number}' đang trong quá trình thực hiện nên đã được đổi sang trạng thái Đã hủy (Cancelled)"
        )

    db.delete(order)
    db.commit()
    return MessageResponse(message=f"Đã xóa đơn bán hàng '{order.order_number}' thành công")
