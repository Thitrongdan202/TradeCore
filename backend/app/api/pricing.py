"""
TradeCore — Pricing API Router
Provides CRUD endpoints for Price Lists, Tiered Items, and Smart Price Lookup.
"""
from __future__ import annotations

import math
import uuid
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, and_, or_
from sqlalchemy.orm import Session, selectinload

from app.core.security import RoleType
from app.api.deps import get_current_user, get_db, require_permission
from app.models.currency import Currency
from app.models.partner import Customer
from app.models.pricing import PriceList, PriceListItem
from app.models.product import Product
from app.models.uom import UnitOfMeasure
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.pricing import (
    PriceListCreate,
    PriceListDetailResponse,
    PriceListItemCreate,
    PriceListItemResponse,
    PriceListItemUpdate,
    PriceListResponse,
    PriceListUpdate,
    PriceLookupResponse,
)

router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# PRICE LISTS CRUD
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/price-lists", response_model=PaginatedResponse[PriceListResponse], summary="Lấy danh sách bảng giá")
def list_price_lists(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    customer_id: Optional[uuid.UUID] = Query(None, description="Lọc theo khách hàng"),
    is_active: Optional[bool] = Query(None, description="Lọc theo trạng thái"),
    search: Optional[str] = Query(None, description="Tìm theo tên bảng giá"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """List price lists with customer and currency information."""
    query = select(PriceList).options(
        selectinload(PriceList.customer),
        selectinload(PriceList.currency),
    )

    if customer_id:
        query = query.where(PriceList.customer_id == customer_id)
    if is_active is not None:
        query = query.where(PriceList.is_active == is_active)
    if search:
        query = query.where(PriceList.name.ilike(f"%{search.strip()}%"))

    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar() or 0

    offset = (page - 1) * page_size
    price_lists = db.execute(
        query.order_by(PriceList.name).offset(offset).limit(page_size)
    ).scalars().all()

    # Pre-fetch items counts
    pl_ids = [pl.id for pl in price_lists]
    counts_map: dict[uuid.UUID, int] = {}
    if pl_ids:
        counts = db.execute(
            select(PriceListItem.price_list_id, func.count(PriceListItem.id))
            .where(PriceListItem.price_list_id.in_(pl_ids))
            .group_by(PriceListItem.price_list_id)
        ).all()
        counts_map = {row[0]: row[1] for row in counts}

    items: List[PriceListResponse] = []
    for pl in price_lists:
        items.append(
            PriceListResponse(
                id=pl.id,
                name=pl.name,
                currency_id=pl.currency_id,
                customer_id=pl.customer_id,
                effective_from=pl.effective_from,
                effective_to=pl.effective_to,
                is_active=pl.is_active,
                notes=pl.notes,
                customer_name=pl.customer.name if pl.customer else None,
                currency_code=pl.currency.code if pl.currency else "VND",
                items_count=counts_map.get(pl.id, 0),
                created_at=pl.created_at,
                updated_at=pl.updated_at,
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


@router.get("/price-lists/{price_list_id}", response_model=PriceListDetailResponse, summary="Lấy chi tiết bảng giá")
def get_price_list(
    price_list_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """Retrieve a single price list with all product pricing tiers."""
    pl = db.execute(
        select(PriceList)
        .options(
            selectinload(PriceList.customer),
            selectinload(PriceList.currency),
            selectinload(PriceList.items).selectinload(PriceListItem.product),
            selectinload(PriceList.items).selectinload(PriceListItem.uom),
        )
        .where(PriceList.id == price_list_id)
    ).scalar_one_or_none()

    if not pl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy bảng giá với ID {price_list_id}",
        )

    item_responses: List[PriceListItemResponse] = []
    for item in pl.items:
        item_responses.append(
            PriceListItemResponse(
                id=item.id,
                price_list_id=item.price_list_id,
                product_id=item.product_id,
                uom_id=item.uom_id,
                min_qty=float(item.min_qty),
                price=float(item.price),
                source_price=float(item.source_price) if item.source_price is not None else None,
                source_currency=item.source_currency,
                notes=item.notes,
                product_code=item.product.code if item.product else None,
                product_name=item.product.name if item.product else None,
                uom_name=item.uom.name if item.uom else None,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
        )

    return PriceListDetailResponse(
        id=pl.id,
        name=pl.name,
        currency_id=pl.currency_id,
        customer_id=pl.customer_id,
        effective_from=pl.effective_from,
        effective_to=pl.effective_to,
        is_active=pl.is_active,
        notes=pl.notes,
        customer_name=pl.customer.name if pl.customer else None,
        currency_code=pl.currency.code if pl.currency else "VND",
        items_count=len(item_responses),
        created_at=pl.created_at,
        updated_at=pl.updated_at,
        items=item_responses,
    )


@router.post(
    "/price-lists",
    response_model=PriceListDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo mới bảng giá",
)
def create_price_list(
    payload: PriceListCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """Create a new price list with optional initial items."""
    if payload.customer_id:
        cust = db.execute(select(Customer).where(Customer.id == payload.customer_id)).scalar_one_or_none()
        if not cust:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không tìm thấy khách hàng với ID {payload.customer_id}",
            )

    if payload.currency_id:
        curr = db.execute(select(Currency).where(Currency.id == payload.currency_id)).scalar_one_or_none()
        if not curr:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không tìm thấy loại tiền tệ với ID {payload.currency_id}",
            )

    pl = PriceList(
        name=payload.name.strip(),
        currency_id=payload.currency_id,
        customer_id=payload.customer_id,
        effective_from=payload.effective_from,
        effective_to=payload.effective_to,
        is_active=payload.is_active,
        notes=payload.notes,
    )
    db.add(pl)
    db.flush()

    if payload.items:
        for item_data in payload.items:
            item = PriceListItem(
                price_list_id=pl.id,
                product_id=item_data.product_id,
                uom_id=item_data.uom_id,
                min_qty=item_data.min_qty,
                price=item_data.price,
                source_price=item_data.source_price,
                source_currency=item_data.source_currency,
                notes=item_data.notes,
            )
            db.add(item)

    db.commit()
    db.refresh(pl)

    return get_price_list(pl.id, db, current_user)


@router.put("/price-lists/{price_list_id}", response_model=PriceListResponse, summary="Cập nhật bảng giá")
def update_price_list(
    price_list_id: uuid.UUID,
    payload: PriceListUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """Update price list metadata."""
    pl = db.execute(select(PriceList).where(PriceList.id == price_list_id)).scalar_one_or_none()
    if not pl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy bảng giá với ID {price_list_id}",
        )

    if payload.name is not None:
        pl.name = payload.name.strip()
    if payload.currency_id is not None:
        pl.currency_id = payload.currency_id
    if payload.customer_id is not None:
        pl.customer_id = payload.customer_id
    if payload.effective_from is not None:
        pl.effective_from = payload.effective_from
    if payload.effective_to is not None:
        pl.effective_to = payload.effective_to
    if payload.is_active is not None:
        pl.is_active = payload.is_active
    if payload.notes is not None:
        pl.notes = payload.notes

    db.commit()
    db.refresh(pl)

    return PriceListResponse(
        id=pl.id,
        name=pl.name,
        currency_id=pl.currency_id,
        customer_id=pl.customer_id,
        effective_from=pl.effective_from,
        effective_to=pl.effective_to,
        is_active=pl.is_active,
        notes=pl.notes,
        customer_name=pl.customer.name if pl.customer else None,
        currency_code=pl.currency.code if pl.currency else "VND",
        items_count=len(pl.items),
        created_at=pl.created_at,
        updated_at=pl.updated_at,
    )


@router.delete("/price-lists/{price_list_id}", response_model=MessageResponse, summary="Xóa bảng giá")
def delete_price_list(
    price_list_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """Delete a price list and all its tiered items."""
    pl = db.execute(select(PriceList).where(PriceList.id == price_list_id)).scalar_one_or_none()
    if not pl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy bảng giá với ID {price_list_id}",
        )

    db.delete(pl)
    db.commit()
    return MessageResponse(message=f"Đã xóa bảng giá '{pl.name}' thành công")


# ═══════════════════════════════════════════════════════════════════════════════
# PRICE LIST ITEMS CRUD
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/price-lists/{price_list_id}/items", response_model=List[PriceListItemResponse], summary="Lấy danh sách mặt hàng trong bảng giá")
def list_price_list_items(
    price_list_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """List all item tiers in a price list."""
    items = db.execute(
        select(PriceListItem)
        .options(selectinload(PriceListItem.product), selectinload(PriceListItem.uom))
        .where(PriceListItem.price_list_id == price_list_id)
        .order_by(PriceListItem.product_id, PriceListItem.min_qty)
    ).scalars().all()

    return [
        PriceListItemResponse(
            id=i.id,
            price_list_id=i.price_list_id,
            product_id=i.product_id,
            uom_id=i.uom_id,
            min_qty=float(i.min_qty),
            price=float(i.price),
            source_price=float(i.source_price) if i.source_price is not None else None,
            source_currency=i.source_currency,
            notes=i.notes,
            product_code=i.product.code if i.product else None,
            product_name=i.product.name if i.product else None,
            uom_name=i.uom.name if i.uom else None,
            created_at=i.created_at,
            updated_at=i.updated_at,
        )
        for i in items
    ]


@router.post(
    "/price-lists/{price_list_id}/items",
    response_model=PriceListItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Thêm mặt hàng vào bảng giá",
)
def add_price_list_item(
    price_list_id: uuid.UUID,
    payload: PriceListItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """Add a product price tier to a price list."""
    pl = db.execute(select(PriceList).where(PriceList.id == price_list_id)).scalar_one_or_none()
    if not pl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy bảng giá với ID {price_list_id}",
        )

    product = db.execute(select(Product).where(Product.id == payload.product_id)).scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy sản phẩm với ID {payload.product_id}",
        )

    item = PriceListItem(
        price_list_id=price_list_id,
        product_id=payload.product_id,
        uom_id=payload.uom_id or product.uom_id,
        min_qty=payload.min_qty,
        price=payload.price,
        source_price=payload.source_price,
        source_currency=payload.source_currency,
        notes=payload.notes,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    return PriceListItemResponse(
        id=item.id,
        price_list_id=item.price_list_id,
        product_id=item.product_id,
        uom_id=item.uom_id,
        min_qty=float(item.min_qty),
        price=float(item.price),
        source_price=float(item.source_price) if item.source_price is not None else None,
        source_currency=item.source_currency,
        notes=item.notes,
        product_code=product.code,
        product_name=product.name,
        uom_name=product.uom.name if product.uom else None,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.put("/items/{item_id}", response_model=PriceListItemResponse, summary="Cập nhật dòng giá")
def update_price_list_item(
    item_id: uuid.UUID,
    payload: PriceListItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """Update a specific price list line item."""
    item = db.execute(
        select(PriceListItem)
        .options(selectinload(PriceListItem.product), selectinload(PriceListItem.uom))
        .where(PriceListItem.id == item_id)
    ).scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy dòng giá với ID {item_id}",
        )

    if payload.product_id is not None:
        item.product_id = payload.product_id
    if payload.uom_id is not None:
        item.uom_id = payload.uom_id
    if payload.min_qty is not None:
        item.min_qty = payload.min_qty
    if payload.price is not None:
        item.price = payload.price
    if payload.source_price is not None:
        item.source_price = payload.source_price
    if payload.source_currency is not None:
        item.source_currency = payload.source_currency
    if payload.notes is not None:
        item.notes = payload.notes

    db.commit()
    db.refresh(item)

    return PriceListItemResponse(
        id=item.id,
        price_list_id=item.price_list_id,
        product_id=item.product_id,
        uom_id=item.uom_id,
        min_qty=float(item.min_qty),
        price=float(item.price),
        source_price=float(item.source_price) if item.source_price is not None else None,
        source_currency=item.source_currency,
        notes=item.notes,
        product_code=item.product.code if item.product else None,
        product_name=item.product.name if item.product else None,
        uom_name=item.uom.name if item.uom else None,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.delete("/items/{item_id}", response_model=MessageResponse, summary="Xóa dòng giá")
def delete_price_list_item(
    item_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """Delete a price list line item."""
    item = db.execute(select(PriceListItem).where(PriceListItem.id == item_id)).scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy dòng giá với ID {item_id}",
        )

    db.delete(item)
    db.commit()
    return MessageResponse(message="Đã xóa dòng bảng giá thành công")


# ═══════════════════════════════════════════════════════════════════════════════
# PRICE LOOKUP
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/lookup", response_model=PriceLookupResponse, summary="Tra cứu giá bán tự động")
def lookup_price(
    product_id: uuid.UUID = Query(..., description="ID sản phẩm"),
    customer_id: Optional[uuid.UUID] = Query(None, description="ID khách hàng"),
    qty: float = Query(1.0, gt=0, description="Số lượng đặt mua"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """
    Lookup appropriate unit price using customer-specific price list first,
    then fallback to standard price list, or product cost price.
    """
    product = db.execute(select(Product).where(Product.id == product_id)).scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy sản phẩm với ID {product_id}",
        )

    today = date.today()

    # 1. Look for customer-specific price list
    if customer_id:
        cust_item = db.execute(
            select(PriceListItem, PriceList)
            .join(PriceList, PriceListItem.price_list_id == PriceList.id)
            .where(
                PriceList.customer_id == customer_id,
                PriceList.is_active == True,
                PriceListItem.product_id == product_id,
                PriceListItem.min_qty <= qty,
                or_(PriceList.effective_from.is_(None), PriceList.effective_from <= today),
                or_(PriceList.effective_to.is_(None), PriceList.effective_to >= today),
            )
            .order_by(PriceListItem.min_qty.desc())
        ).first()

        if cust_item:
            item, pl = cust_item
            curr_code = pl.currency.code if pl.currency else "VND"
            return PriceLookupResponse(
                product_id=product.id,
                product_code=product.code,
                product_name=product.name,
                unit_price=float(item.price),
                currency_code=curr_code,
                price_list_id=pl.id,
                price_list_name=pl.name,
                is_customer_specific=True,
            )

    # 2. Look for standard (general) price list
    std_item = db.execute(
        select(PriceListItem, PriceList)
        .join(PriceList, PriceListItem.price_list_id == PriceList.id)
        .where(
            PriceList.customer_id.is_(None),
            PriceList.is_active == True,
            PriceListItem.product_id == product_id,
            PriceListItem.min_qty <= qty,
            or_(PriceList.effective_from.is_(None), PriceList.effective_from <= today),
            or_(PriceList.effective_to.is_(None), PriceList.effective_to >= today),
        )
        .order_by(PriceListItem.min_qty.desc())
    ).first()

    if std_item:
        item, pl = std_item
        curr_code = pl.currency.code if pl.currency else "VND"
        return PriceLookupResponse(
            product_id=product.id,
            product_code=product.code,
            product_name=product.name,
            unit_price=float(item.price),
            currency_code=curr_code,
            price_list_id=pl.id,
            price_list_name=pl.name,
            is_customer_specific=False,
        )

    # 3. Fallback to product cost_price or 0.0
    fallback_price = float(product.cost_price or 0.0)
    return PriceLookupResponse(
        product_id=product.id,
        product_code=product.code,
        product_name=product.name,
        unit_price=fallback_price,
        currency_code="VND",
        price_list_id=None,
        price_list_name="Giá gốc mặc định",
        is_customer_specific=False,
    )
