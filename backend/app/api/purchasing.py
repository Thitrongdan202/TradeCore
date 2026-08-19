"""
TradeCore — Purchase Orders API Router
Provides CRUD endpoints for Purchase Orders, line items calculation, and Goods Receiving.
"""
from __future__ import annotations

import math
import uuid
from datetime import date, datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, or_
from sqlalchemy.orm import Session, selectinload

from app.core.security import RoleType
from app.api.deps import get_current_user, get_db, require_permission
from app.models.currency import Currency
from app.models.inventory import MovementType, ReferenceType, StockBalance, StockMovement
from app.models.partner import PaymentTerm, Supplier
from app.models.product import Product
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.sales import OrderStatus, PaymentStatus
from app.models.user import User
from app.models.warehouse import LocationType, WarehouseLocation
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.partner import SupplierResponse
from app.schemas.purchase import (
    PurchaseOrderCreate,
    PurchaseOrderDetailResponse,
    PurchaseOrderItemResponse,
    PurchaseOrderPaymentUpdate,
    PurchaseOrderReceiveRequest,
    PurchaseOrderResponse,
    PurchaseOrderStatusUpdate,
    PurchaseOrderUpdate,
)
from app.schemas.sales import OrderStatusEnum, PaymentStatusEnum

router = APIRouter()


def generate_po_number(db: Session) -> str:
    """Generate automatic PO number format: PO-YYMM-XXXX."""
    today = date.today()
    prefix = f"PO-{today.strftime('%y%m')}-"
    count = db.execute(
        select(func.count(PurchaseOrder.id)).where(PurchaseOrder.order_number.like(f"{prefix}%"))
    ).scalar() or 0
    return f"{prefix}{count + 1:04d}"


def calculate_po_line_item(item_data, product: Optional[Product] = None) -> tuple[float, float]:
    """Calculate unit_price and subtotal for a purchase order line."""
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
# PURCHASE ORDERS CRUD
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/orders", response_model=PaginatedResponse[PurchaseOrderResponse], summary="Lấy danh sách đơn mua hàng")
def list_purchase_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    supplier_id: Optional[uuid.UUID] = Query(None, description="Lọc theo nhà cung cấp"),
    status_filter: Optional[OrderStatusEnum] = Query(None, alias="status", description="Lọc theo trạng thái đơn"),
    payment_status_filter: Optional[PaymentStatusEnum] = Query(None, alias="payment_status", description="Lọc theo trạng thái thanh toán"),
    from_date: Optional[date] = Query(None, description="Từ ngày"),
    to_date: Optional[date] = Query(None, description="Đến ngày"),
    search: Optional[str] = Query(None, description="Tìm theo mã đơn hoặc tên nhà cung cấp"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """List purchase orders with filters and pagination."""
    query = (
        select(PurchaseOrder)
        .options(
            selectinload(PurchaseOrder.supplier),
            selectinload(PurchaseOrder.items),
        )
    )

    if supplier_id:
        query = query.where(PurchaseOrder.supplier_id == supplier_id)
    if status_filter:
        query = query.where(PurchaseOrder.status == status_filter.value)
    if payment_status_filter:
        query = query.where(PurchaseOrder.payment_status == payment_status_filter.value)
    if from_date:
        query = query.where(PurchaseOrder.date >= from_date)
    if to_date:
        query = query.where(PurchaseOrder.date <= to_date)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.join(PurchaseOrder.supplier, isouter=True).where(
            or_(
                PurchaseOrder.order_number.ilike(pattern),
                Supplier.name.ilike(pattern),
                Supplier.code.ilike(pattern),
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar() or 0

    offset = (page - 1) * page_size
    orders = db.execute(
        query.order_by(PurchaseOrder.created_at.desc()).offset(offset).limit(page_size)
    ).scalars().all()

    items: List[PurchaseOrderResponse] = []
    for order in orders:
        items.append(
            PurchaseOrderResponse(
                id=order.id,
                order_number=order.order_number,
                supplier_id=order.supplier_id,
                currency_id=order.currency_id,
                payment_term_id=order.payment_term_id,
                date=order.date,
                expected_date=order.expected_date,
                status=OrderStatusEnum(order.status.value),
                payment_status=PaymentStatusEnum(order.payment_status.value),
                subtotal=float(order.subtotal) if order.subtotal is not None else None,
                tax_amount=float(order.tax_amount) if order.tax_amount is not None else 0.0,
                total=float(order.total) if order.total is not None else None,
                amount_paid=float(order.amount_paid) if order.amount_paid is not None else 0.0,
                odoo_id=order.odoo_id,
                created_by_id=order.created_by_id,
                notes=order.notes,
                supplier_name=order.supplier.name if order.supplier else None,
                supplier_code=order.supplier.code if order.supplier else None,
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


@router.get("/orders/{order_id}", response_model=PurchaseOrderDetailResponse, summary="Lấy chi tiết đơn mua hàng")
def get_purchase_order(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """Retrieve full purchase order details with items and supplier info."""
    order = db.execute(
        select(PurchaseOrder)
        .options(
            selectinload(PurchaseOrder.supplier),
            selectinload(PurchaseOrder.items).selectinload(PurchaseOrderItem.product),
            selectinload(PurchaseOrder.items).selectinload(PurchaseOrderItem.uom),
        )
        .where(PurchaseOrder.id == order_id)
    ).scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy đơn mua hàng với ID {order_id}",
        )

    item_responses: List[PurchaseOrderItemResponse] = []
    for item in order.items:
        item_responses.append(
            PurchaseOrderItemResponse(
                id=item.id,
                order_id=item.order_id,
                line_no=item.line_no,
                product_id=item.product_id,
                description=item.description,
                qty=float(item.qty),
                qty_received=float(item.qty_received),
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

    return PurchaseOrderDetailResponse(
        id=order.id,
        order_number=order.order_number,
        supplier_id=order.supplier_id,
        currency_id=order.currency_id,
        payment_term_id=order.payment_term_id,
        date=order.date,
        expected_date=order.expected_date,
        status=OrderStatusEnum(order.status.value),
        payment_status=PaymentStatusEnum(order.payment_status.value),
        subtotal=float(order.subtotal) if order.subtotal is not None else None,
        tax_amount=float(order.tax_amount) if order.tax_amount is not None else 0.0,
        total=float(order.total) if order.total is not None else None,
        amount_paid=float(order.amount_paid) if order.amount_paid is not None else 0.0,
        odoo_id=order.odoo_id,
        created_by_id=order.created_by_id,
        notes=order.notes,
        supplier_name=order.supplier.name if order.supplier else None,
        supplier_code=order.supplier.code if order.supplier else None,
        items_count=len(item_responses),
        created_at=order.created_at,
        updated_at=order.updated_at,
        supplier=SupplierResponse.model_validate(order.supplier) if order.supplier else None,
        items=item_responses,
    )


@router.post(
    "/orders",
    response_model=PurchaseOrderDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo mới đơn mua hàng",
)
def create_purchase_order(
    payload: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """Create a new purchase order with calculated line totals."""
    order_number = payload.order_number.strip() if payload.order_number else generate_po_number(db)

    if db.execute(select(PurchaseOrder).where(PurchaseOrder.order_number == order_number)).scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Mã đơn mua hàng '{order_number}' đã tồn tại",
        )

    if payload.supplier_id:
        supp = db.execute(select(Supplier).where(Supplier.id == payload.supplier_id)).scalar_one_or_none()
        if not supp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không tìm thấy nhà cung cấp với ID {payload.supplier_id}",
            )

    order = PurchaseOrder(
        order_number=order_number,
        supplier_id=payload.supplier_id,
        currency_id=payload.currency_id,
        payment_term_id=payload.payment_term_id,
        date=payload.date or date.today(),
        expected_date=payload.expected_date,
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

        unit_price, line_subtotal = calculate_po_line_item(item_data, product)
        total_subtotal += line_subtotal

        item = PurchaseOrderItem(
            order_id=order.id,
            line_no=idx,
            product_id=item_data.product_id,
            description=item_data.description or (product.name if product else None),
            qty=item_data.qty,
            qty_received=0.0,
            uom_id=item_data.uom_id or (product.purchase_uom_id or product.uom_id if product else None),
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

    return get_purchase_order(order.id, db, current_user)


@router.put("/orders/{order_id}", response_model=PurchaseOrderDetailResponse, summary="Cập nhật đơn mua hàng")
def update_purchase_order(
    order_id: uuid.UUID,
    payload: PurchaseOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """Update purchase order details and optionally line items."""
    order = db.execute(select(PurchaseOrder).where(PurchaseOrder.id == order_id)).scalar_one_or_none()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy đơn mua hàng với ID {order_id}",
        )

    if payload.supplier_id is not None:
        order.supplier_id = payload.supplier_id
    if payload.currency_id is not None:
        order.currency_id = payload.currency_id
    if payload.payment_term_id is not None:
        order.payment_term_id = payload.payment_term_id
    if payload.date is not None:
        order.date = payload.date
    if payload.expected_date is not None:
        order.expected_date = payload.expected_date
    if payload.status is not None:
        order.status = payload.status.value
    if payload.payment_status is not None:
        order.payment_status = payload.payment_status.value
    if payload.notes is not None:
        order.notes = payload.notes

    if payload.items is not None:
        db.query(PurchaseOrderItem).filter(PurchaseOrderItem.order_id == order_id).delete()
        total_subtotal = 0.0
        for idx, item_data in enumerate(payload.items, start=1):
            product: Optional[Product] = None
            if item_data.product_id:
                product = db.execute(select(Product).where(Product.id == item_data.product_id)).scalar_one_or_none()

            unit_price, line_subtotal = calculate_po_line_item(item_data, product)
            total_subtotal += line_subtotal

            item = PurchaseOrderItem(
                order_id=order.id,
                line_no=idx,
                product_id=item_data.product_id,
                description=item_data.description or (product.name if product else None),
                qty=item_data.qty,
                qty_received=0.0,
                uom_id=item_data.uom_id or (product.purchase_uom_id or product.uom_id if product else None),
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

    return get_purchase_order(order.id, db, current_user)


@router.patch("/orders/{order_id}/status", response_model=PurchaseOrderDetailResponse, summary="Cập nhật trạng thái đơn mua")
def update_purchase_order_status(
    order_id: uuid.UUID,
    payload: PurchaseOrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """Update lifecycle status of a purchase order."""
    order = db.execute(select(PurchaseOrder).where(PurchaseOrder.id == order_id)).scalar_one_or_none()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy đơn mua hàng với ID {order_id}",
        )

    order.status = payload.status.value
    if payload.notes:
        order.notes = f"{order.notes or ''}\n[Status Change]: {payload.notes}"

    db.commit()
    db.refresh(order)
    return get_purchase_order(order.id, db, current_user)


@router.patch("/orders/{order_id}/payment", response_model=PurchaseOrderDetailResponse, summary="Cập nhật thanh toán đơn mua")
def update_purchase_order_payment(
    order_id: uuid.UUID,
    payload: PurchaseOrderPaymentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """Update payment status and amount paid for a purchase order."""
    order = db.execute(select(PurchaseOrder).where(PurchaseOrder.id == order_id)).scalar_one_or_none()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy đơn mua hàng với ID {order_id}",
        )

    order.payment_status = payload.payment_status.value
    if payload.amount_paid is not None:
        order.amount_paid = payload.amount_paid

    db.commit()
    db.refresh(order)
    return get_purchase_order(order.id, db, current_user)


@router.post("/orders/{order_id}/receive", response_model=PurchaseOrderDetailResponse, summary="Nhập kho hàng mua (Goods Receipt)")
def receive_purchase_order_goods(
    order_id: uuid.UUID,
    payload: PurchaseOrderReceiveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """
    Receive goods for purchase order lines into target warehouse location.
    Updates qty_received, creates StockMovements and increments StockBalances.
    """
    order = db.execute(
        select(PurchaseOrder)
        .options(selectinload(PurchaseOrder.items))
        .where(PurchaseOrder.id == order_id)
    ).scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy đơn mua hàng với ID {order_id}",
        )

    dest_loc = db.execute(
        select(WarehouseLocation).where(WarehouseLocation.id == payload.destination_location_id)
    ).scalar_one_or_none()

    if not dest_loc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy vị trí kho đích với ID {payload.destination_location_id}",
        )

    item_map = {item.id: item for item in order.items}

    for line in payload.items:
        item = item_map.get(line.item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không tìm thấy dòng sản phẩm với ID {line.item_id} trong đơn {order.order_number}",
            )

        if not item.product_id:
            continue

        # Increment qty_received
        item.qty_received = float(item.qty_received) + line.qty_to_receive

        # Create StockMovement
        movement = StockMovement(
            movement_type=MovementType.receive,
            reference_type=ReferenceType.purchase_order,
            reference=order.order_number,
            reference_id=order.id,
            product_id=item.product_id,
            uom_id=item.uom_id,
            qty=line.qty_to_receive,
            cost_price=float(item.unit_price or 0.0),
            from_location_id=None,  # Virtual supplier location
            to_location_id=payload.destination_location_id,
            moved_at=datetime.now(timezone.utc),
            created_by_id=current_user.id,
            notes=f"Nhập kho từ đơn mua {order.order_number}. {payload.notes or ''}",
        )
        db.add(movement)

        # Update or create StockBalance
        balance = db.execute(
            select(StockBalance).where(
                StockBalance.product_id == item.product_id,
                StockBalance.location_id == payload.destination_location_id,
            )
        ).scalar_one_or_none()

        if balance:
            balance.qty_on_hand = float(balance.qty_on_hand) + line.qty_to_receive
            balance.last_updated_at = datetime.now(timezone.utc)
        else:
            balance = StockBalance(
                product_id=item.product_id,
                location_id=payload.destination_location_id,
                qty_on_hand=line.qty_to_receive,
            )
            db.add(balance)

    # Check if all lines are fully received
    all_received = all(float(i.qty_received) >= float(i.qty) for i in order.items)
    if all_received:
        order.status = OrderStatus.completed
    elif order.status == OrderStatus.draft:
        order.status = OrderStatus.processing

    db.commit()
    db.refresh(order)

    return get_purchase_order(order.id, db, current_user)


@router.delete("/orders/{order_id}", response_model=MessageResponse, summary="Hủy hoặc xóa đơn mua hàng")
def delete_purchase_order(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """Cancel or delete purchase order."""
    order = db.execute(select(PurchaseOrder).where(PurchaseOrder.id == order_id)).scalar_one_or_none()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy đơn mua hàng với ID {order_id}",
        )

    # If any goods have been received, cancel instead of hard delete
    has_received = any(float(item.qty_received) > 0 for item in order.items)
    if has_received or order.status in [OrderStatus.completed, OrderStatus.processing]:
        order.status = OrderStatus.cancelled
        db.commit()
        return MessageResponse(
            message=f"Đơn mua hàng '{order.order_number}' đã có phát sinh nhận hàng nên đã được đổi sang trạng thái Đã hủy (Cancelled)"
        )

    db.delete(order)
    db.commit()
    return MessageResponse(message=f"Đã xóa đơn mua hàng '{order.order_number}' thành công")
