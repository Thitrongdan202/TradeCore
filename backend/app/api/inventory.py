"""
TradeCore — Inventory API Router
Provides endpoints for Warehouses, Locations, Stock Balances, Movements, and Adjustments.
"""
from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, or_
from sqlalchemy.orm import Session, selectinload

from app.core.security import RoleType
from app.api.deps import get_current_user, get_db, require_permission
from app.models.inventory import MovementType, ReferenceType, StockBalance, StockMovement
from app.models.product import Product
from app.models.user import User
from app.models.warehouse import LocationType, Warehouse, WarehouseLocation
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.inventory import (
    LocationTypeEnum,
    MovementTypeEnum,
    ReferenceTypeEnum,
    StockAdjustmentCreate,
    StockBalanceResponse,
    StockMovementCreate,
    StockMovementResponse,
    WarehouseCreate,
    WarehouseDetailResponse,
    WarehouseLocationCreate,
    WarehouseLocationResponse,
    WarehouseLocationUpdate,
    WarehouseResponse,
    WarehouseUpdate,
)

router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# WAREHOUSES CRUD
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/warehouses", response_model=List[WarehouseResponse], summary="Lấy danh sách kho hàng")
def list_warehouses(
    is_active: Optional[bool] = Query(None, description="Lọc theo trạng thái hoạt động"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """List all physical warehouses."""
    query = select(Warehouse).order_by(Warehouse.code)
    if is_active is not None:
        query = query.where(Warehouse.is_active == is_active)
    return db.execute(query).scalars().all()


@router.get("/warehouses/{warehouse_id}", response_model=WarehouseDetailResponse, summary="Lấy chi tiết kho hàng")
def get_warehouse(
    warehouse_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """Retrieve warehouse with its internal locations."""
    wh = db.execute(
        select(Warehouse).options(selectinload(Warehouse.locations)).where(Warehouse.id == warehouse_id)
    ).scalar_one_or_none()
    if not wh:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy kho với ID {warehouse_id}",
        )
    return wh


@router.post(
    "/warehouses",
    response_model=WarehouseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo mới kho hàng",
)
def create_warehouse(
    payload: WarehouseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """Create a new physical warehouse and auto-create default Stock internal location."""
    existing = db.execute(select(Warehouse).where(Warehouse.code == payload.code.strip())).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Mã kho '{payload.code}' đã tồn tại",
        )

    wh = Warehouse(
        code=payload.code.strip(),
        name=payload.name.strip(),
        address=payload.address,
        is_active=payload.is_active,
    )
    db.add(wh)
    db.flush()

    # Create default internal location for this warehouse
    default_loc = WarehouseLocation(
        code=f"{wh.code}-STOCK",
        name=f"Kho chính ({wh.name})",
        location_type=LocationType.internal,
        warehouse_id=wh.id,
        is_active=True,
    )
    db.add(default_loc)

    db.commit()
    db.refresh(wh)
    return wh


@router.put("/warehouses/{warehouse_id}", response_model=WarehouseResponse, summary="Cập nhật kho hàng")
def update_warehouse(
    warehouse_id: uuid.UUID,
    payload: WarehouseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """Update warehouse details."""
    wh = db.execute(select(Warehouse).where(Warehouse.id == warehouse_id)).scalar_one_or_none()
    if not wh:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy kho với ID {warehouse_id}",
        )

    if payload.code is not None and payload.code.strip() != wh.code:
        existing = db.execute(
            select(Warehouse).where(Warehouse.code == payload.code.strip(), Warehouse.id != warehouse_id)
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Mã kho '{payload.code}' đã tồn tại",
            )
        wh.code = payload.code.strip()

    if payload.name is not None:
        wh.name = payload.name.strip()
    if payload.address is not None:
        wh.address = payload.address
    if payload.is_active is not None:
        wh.is_active = payload.is_active

    db.commit()
    db.refresh(wh)
    return wh


@router.delete("/warehouses/{warehouse_id}", response_model=MessageResponse, summary="Xóa kho hàng")
def delete_warehouse(
    warehouse_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """Delete warehouse if no stock exists in its locations."""
    wh = db.execute(select(Warehouse).where(Warehouse.id == warehouse_id)).scalar_one_or_none()
    if not wh:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy kho với ID {warehouse_id}",
        )

    # Check stock balances across warehouse locations
    loc_ids = [l.id for l in wh.locations]
    if loc_ids:
        stock_sum = db.execute(
            select(func.coalesce(func.sum(StockBalance.qty_on_hand), 0)).where(StockBalance.location_id.in_(loc_ids))
        ).scalar() or 0
        if stock_sum > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không thể xóa kho vì vẫn còn {stock_sum} sản phẩm tồn trong các vị trí của kho này",
            )

    db.delete(wh)
    db.commit()
    return MessageResponse(message=f"Đã xóa kho hàng '{wh.code}' thành công")


# ═══════════════════════════════════════════════════════════════════════════════
# WAREHOUSE LOCATIONS CRUD
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/locations", response_model=List[WarehouseLocationResponse], summary="Lấy danh sách vị trí kho")
def list_locations(
    warehouse_id: Optional[uuid.UUID] = Query(None, description="Lọc theo kho hàng"),
    location_type: Optional[LocationTypeEnum] = Query(None, description="Lọc theo loại vị trí"),
    is_active: Optional[bool] = Query(None, description="Lọc theo trạng thái"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """List warehouse locations."""
    query = select(WarehouseLocation).order_by(WarehouseLocation.code)

    if warehouse_id:
        query = query.where(WarehouseLocation.warehouse_id == warehouse_id)
    if location_type:
        query = query.where(WarehouseLocation.location_type == location_type.value)
    if is_active is not None:
        query = query.where(WarehouseLocation.is_active == is_active)

    return db.execute(query).scalars().all()


@router.get("/locations/{location_id}", response_model=WarehouseLocationResponse, summary="Lấy chi tiết vị trí kho")
def get_location(
    location_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """Retrieve warehouse location details."""
    loc = db.execute(select(WarehouseLocation).where(WarehouseLocation.id == location_id)).scalar_one_or_none()
    if not loc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy vị trí với ID {location_id}",
        )
    return loc


@router.post(
    "/locations",
    response_model=WarehouseLocationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo mới vị trí kho",
)
def create_location(
    payload: WarehouseLocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """Create a new location inside a warehouse or virtual location."""
    existing = db.execute(select(WarehouseLocation).where(WarehouseLocation.code == payload.code.strip())).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Mã vị trí '{payload.code}' đã tồn tại",
        )

    if payload.warehouse_id:
        wh = db.execute(select(Warehouse).where(Warehouse.id == payload.warehouse_id)).scalar_one_or_none()
        if not wh:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không tìm thấy kho với ID {payload.warehouse_id}",
            )

    loc = WarehouseLocation(
        code=payload.code.strip(),
        name=payload.name.strip(),
        location_type=payload.location_type.value,
        is_active=payload.is_active,
        warehouse_id=payload.warehouse_id,
        parent_id=payload.parent_id,
    )
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return loc


@router.put("/locations/{location_id}", response_model=WarehouseLocationResponse, summary="Cập nhật vị trí kho")
def update_location(
    location_id: uuid.UUID,
    payload: WarehouseLocationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """Update location details."""
    loc = db.execute(select(WarehouseLocation).where(WarehouseLocation.id == location_id)).scalar_one_or_none()
    if not loc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy vị trí với ID {location_id}",
        )

    if payload.code is not None and payload.code.strip() != loc.code:
        existing = db.execute(
            select(WarehouseLocation).where(WarehouseLocation.code == payload.code.strip(), WarehouseLocation.id != location_id)
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Mã vị trí '{payload.code}' đã tồn tại",
            )
        loc.code = payload.code.strip()

    if payload.name is not None:
        loc.name = payload.name.strip()
    if payload.location_type is not None:
        loc.location_type = payload.location_type.value
    if payload.is_active is not None:
        loc.is_active = payload.is_active
    if payload.warehouse_id is not None:
        loc.warehouse_id = payload.warehouse_id
    if payload.parent_id is not None:
        loc.parent_id = payload.parent_id

    db.commit()
    db.refresh(loc)
    return loc


@router.delete("/locations/{location_id}", response_model=MessageResponse, summary="Xóa vị trí kho")
def delete_location(
    location_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """Delete a location if it has no stock balance."""
    loc = db.execute(select(WarehouseLocation).where(WarehouseLocation.id == location_id)).scalar_one_or_none()
    if not loc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy vị trí với ID {location_id}",
        )

    stock_sum = db.execute(
        select(func.coalesce(func.sum(StockBalance.qty_on_hand), 0)).where(StockBalance.location_id == location_id)
    ).scalar() or 0

    if stock_sum > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Không thể xóa vị trí vì vẫn còn {stock_sum} sản phẩm đang lưu tại đây",
        )

    db.delete(loc)
    db.commit()
    return MessageResponse(message=f"Đã xóa vị trí '{loc.code}' thành công")


# ═══════════════════════════════════════════════════════════════════════════════
# STOCK BALANCES
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/balances", response_model=PaginatedResponse[StockBalanceResponse], summary="Xem tồn kho hiện tại")
def list_stock_balances(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    product_id: Optional[uuid.UUID] = Query(None, description="Lọc theo sản phẩm"),
    location_id: Optional[uuid.UUID] = Query(None, description="Lọc theo vị trí"),
    warehouse_id: Optional[uuid.UUID] = Query(None, description="Lọc theo kho"),
    search: Optional[str] = Query(None, description="Tìm theo mã hoặc tên sản phẩm"),
    positive_only: bool = Query(True, description="Chỉ hiển thị tồn kho > 0"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """List stock balances across locations with product and warehouse names."""
    query = (
        select(
            StockBalance,
            Product.code.label("p_code"),
            Product.name.label("p_name"),
            WarehouseLocation.code.label("loc_code"),
            WarehouseLocation.name.label("loc_name"),
            Warehouse.name.label("wh_name"),
        )
        .join(Product, StockBalance.product_id == Product.id)
        .join(WarehouseLocation, StockBalance.location_id == WarehouseLocation.id)
        .outerjoin(Warehouse, WarehouseLocation.warehouse_id == Warehouse.id)
    )

    if product_id:
        query = query.where(StockBalance.product_id == product_id)
    if location_id:
        query = query.where(StockBalance.location_id == location_id)
    if warehouse_id:
        query = query.where(WarehouseLocation.warehouse_id == warehouse_id)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(or_(Product.code.ilike(pattern), Product.name.ilike(pattern)))
    if positive_only:
        query = query.where(StockBalance.qty_on_hand > 0)

    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar() or 0

    offset = (page - 1) * page_size
    rows = db.execute(
        query.order_by(Product.code, WarehouseLocation.code).offset(offset).limit(page_size)
    ).all()

    items: List[StockBalanceResponse] = []
    for sb, p_code, p_name, loc_code, loc_name, wh_name in rows:
        items.append(
            StockBalanceResponse(
                id=sb.id,
                product_id=sb.product_id,
                location_id=sb.location_id,
                qty_on_hand=float(sb.qty_on_hand),
                last_updated_at=sb.last_updated_at,
                product_code=p_code,
                product_name=p_name,
                location_code=loc_code,
                location_name=loc_name,
                warehouse_name=wh_name,
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


@router.get("/balances/product/{product_id}", response_model=List[StockBalanceResponse], summary="Xem tồn kho chi tiết theo sản phẩm")
def get_product_stock_balance(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """Retrieve stock balances for a specific product across all locations."""
    rows = db.execute(
        select(
            StockBalance,
            Product.code.label("p_code"),
            Product.name.label("p_name"),
            WarehouseLocation.code.label("loc_code"),
            WarehouseLocation.name.label("loc_name"),
            Warehouse.name.label("wh_name"),
        )
        .join(Product, StockBalance.product_id == Product.id)
        .join(WarehouseLocation, StockBalance.location_id == WarehouseLocation.id)
        .outerjoin(Warehouse, WarehouseLocation.warehouse_id == Warehouse.id)
        .where(StockBalance.product_id == product_id)
        .order_by(WarehouseLocation.code)
    ).all()

    return [
        StockBalanceResponse(
            id=sb.id,
            product_id=sb.product_id,
            location_id=sb.location_id,
            qty_on_hand=float(sb.qty_on_hand),
            last_updated_at=sb.last_updated_at,
            product_code=p_code,
            product_name=p_name,
            location_code=loc_code,
            location_name=loc_name,
            warehouse_name=wh_name,
        )
        for sb, p_code, p_name, loc_code, loc_name, wh_name in rows
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# STOCK MOVEMENTS & ADJUSTMENTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/movements", response_model=PaginatedResponse[StockMovementResponse], summary="Lịch sử biến động kho")
def list_stock_movements(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    product_id: Optional[uuid.UUID] = Query(None, description="Lọc theo sản phẩm"),
    movement_type: Optional[MovementTypeEnum] = Query(None, description="Lọc theo loại biến động"),
    reference: Optional[str] = Query(None, description="Tìm theo mã chứng từ SO/PO/v.v."),
    from_date: Optional[datetime] = Query(None, description="Từ ngày"),
    to_date: Optional[datetime] = Query(None, description="Đến ngày"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """List immutable stock movements history."""
    query = (
        select(StockMovement)
        .options(
            selectinload(StockMovement.product),
        )
    )

    if product_id:
        query = query.where(StockMovement.product_id == product_id)
    if movement_type:
        query = query.where(StockMovement.movement_type == movement_type.value)
    if reference:
        query = query.where(StockMovement.reference.ilike(f"%{reference.strip()}%"))
    if from_date:
        query = query.where(StockMovement.moved_at >= from_date)
    if to_date:
        query = query.where(StockMovement.moved_at <= to_date)

    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar() or 0

    offset = (page - 1) * page_size
    movements = db.execute(
        query.order_by(StockMovement.moved_at.desc(), StockMovement.created_at.desc())
        .offset(offset)
        .limit(page_size)
    ).scalars().all()

    # Get location codes for display
    loc_ids = set()
    for m in movements:
        if m.from_location_id:
            loc_ids.add(m.from_location_id)
        if m.to_location_id:
            loc_ids.add(m.to_location_id)

    loc_map: dict[uuid.UUID, str] = {}
    if loc_ids:
        locs = db.execute(select(WarehouseLocation).where(WarehouseLocation.id.in_(loc_ids))).scalars().all()
        loc_map = {l.id: f"{l.code} ({l.name})" for l in locs}

    items: List[StockMovementResponse] = []
    for m in movements:
        items.append(
            StockMovementResponse(
                id=m.id,
                movement_type=MovementTypeEnum(m.movement_type.value),
                reference_type=ReferenceTypeEnum(m.reference_type.value) if m.reference_type else None,
                reference=m.reference,
                reference_id=m.reference_id,
                product_id=m.product_id,
                uom_id=m.uom_id,
                qty=float(m.qty),
                cost_price=float(m.cost_price) if m.cost_price is not None else None,
                from_location_id=m.from_location_id,
                to_location_id=m.to_location_id,
                moved_at=m.moved_at,
                created_at=m.created_at,
                created_by_id=m.created_by_id,
                notes=m.notes,
                product_code=m.product.code if m.product else None,
                product_name=m.product.name if m.product else None,
                from_location_code=loc_map.get(m.from_location_id) if m.from_location_id else None,
                to_location_code=loc_map.get(m.to_location_id) if m.to_location_id else None,
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


@router.post(
    "/movements",
    response_model=StockMovementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo mới biến động kho (Giao dịch xuất/nhập/chuyển kho)",
)
def create_stock_movement(
    payload: StockMovementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """
    Execute an atomic stock movement and update materialized StockBalance.
    Rules:
      - qty must be > 0.
      - from_location decreases stock, to_location increases stock.
      - Checks for negative stock on from_location if it is an internal warehouse location.
    """
    product = db.execute(select(Product).where(Product.id == payload.product_id)).scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy sản phẩm với ID {payload.product_id}",
        )

    # Validate from_location
    from_loc: Optional[WarehouseLocation] = None
    if payload.from_location_id:
        from_loc = db.execute(select(WarehouseLocation).where(WarehouseLocation.id == payload.from_location_id)).scalar_one_or_none()
        if not from_loc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy vị trí nguồn với ID {payload.from_location_id}",
            )

    # Validate to_location
    to_loc: Optional[WarehouseLocation] = None
    if payload.to_location_id:
        to_loc = db.execute(select(WarehouseLocation).where(WarehouseLocation.id == payload.to_location_id)).scalar_one_or_none()
        if not to_loc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy vị trí đích với ID {payload.to_location_id}",
            )

    # 1. Update source balance (decrement)
    if payload.from_location_id:
        from_balance = db.execute(
            select(StockBalance).where(
                StockBalance.product_id == payload.product_id,
                StockBalance.location_id == payload.from_location_id,
            )
        ).scalar_one_or_none()

        current_qty = float(from_balance.qty_on_hand) if from_balance else 0.0

        # Prevent negative stock for internal locations
        if from_loc and from_loc.location_type == LocationType.internal:
            if current_qty < payload.qty:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Không đủ tồn kho để xuất. Tồn hiện tại tại {from_loc.code}: {current_qty}, yêu cầu xuất: {payload.qty}",
                )

        if from_balance:
            from_balance.qty_on_hand = max(0.0, current_qty - payload.qty)
            from_balance.last_updated_at = datetime.now(timezone.utc)
        else:
            from_balance = StockBalance(
                product_id=payload.product_id,
                location_id=payload.from_location_id,
                qty_on_hand=0.0,
            )
            db.add(from_balance)

    # 2. Update destination balance (increment)
    if payload.to_location_id:
        to_balance = db.execute(
            select(StockBalance).where(
                StockBalance.product_id == payload.product_id,
                StockBalance.location_id == payload.to_location_id,
            )
        ).scalar_one_or_none()

        if to_balance:
            to_balance.qty_on_hand = float(to_balance.qty_on_hand) + payload.qty
            to_balance.last_updated_at = datetime.now(timezone.utc)
        else:
            to_balance = StockBalance(
                product_id=payload.product_id,
                location_id=payload.to_location_id,
                qty_on_hand=payload.qty,
            )
            db.add(to_balance)

    # 3. Create immutable StockMovement entry
    movement = StockMovement(
        movement_type=payload.movement_type.value,
        reference_type=payload.reference_type.value if payload.reference_type else None,
        reference=payload.reference,
        reference_id=payload.reference_id,
        product_id=payload.product_id,
        uom_id=payload.uom_id or product.uom_id,
        qty=payload.qty,
        cost_price=payload.cost_price if payload.cost_price is not None else float(product.cost_price or 0.0),
        from_location_id=payload.from_location_id,
        to_location_id=payload.to_location_id,
        moved_at=payload.moved_at or datetime.now(timezone.utc),
        created_by_id=current_user.id,
        notes=payload.notes,
    )
    db.add(movement)
    db.commit()
    db.refresh(movement)

    return StockMovementResponse(
        id=movement.id,
        movement_type=MovementTypeEnum(movement.movement_type.value),
        reference_type=ReferenceTypeEnum(movement.reference_type.value) if movement.reference_type else None,
        reference=movement.reference,
        reference_id=movement.reference_id,
        product_id=movement.product_id,
        uom_id=movement.uom_id,
        qty=float(movement.qty),
        cost_price=float(movement.cost_price) if movement.cost_price is not None else None,
        from_location_id=movement.from_location_id,
        to_location_id=movement.to_location_id,
        moved_at=movement.moved_at,
        created_at=movement.created_at,
        created_by_id=movement.created_by_id,
        notes=movement.notes,
        product_code=product.code,
        product_name=product.name,
        from_location_code=from_loc.code if from_loc else None,
        to_location_code=to_loc.code if to_loc else None,
    )


@router.post("/adjustments", response_model=MessageResponse, summary="Điều chỉnh kiểm kê kho")
def adjust_inventory(
    payload: StockAdjustmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("overview", "view")),
):
    """Adjust physical stock quantity to match counted stock."""
    product = db.execute(select(Product).where(Product.id == payload.product_id)).scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy sản phẩm với ID {payload.product_id}",
        )

    loc = db.execute(select(WarehouseLocation).where(WarehouseLocation.id == payload.location_id)).scalar_one_or_none()
    if not loc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy vị trí kho với ID {payload.location_id}",
        )

    balance = db.execute(
        select(StockBalance).where(
            StockBalance.product_id == payload.product_id,
            StockBalance.location_id == payload.location_id,
        )
    ).scalar_one_or_none()

    current_qty = float(balance.qty_on_hand) if balance else 0.0
    delta = payload.counted_qty - current_qty

    if abs(delta) < 0.0001:
        return MessageResponse(message="Tồn kho thực tế trùng khớp với số liệu hệ thống, không có thay đổi")

    # If delta > 0: positive adjustment (receive into location)
    # If delta < 0: negative adjustment (issue out of location)
    if delta > 0:
        movement = StockMovement(
            movement_type=MovementType.adjustment,
            reference_type=ReferenceType.manual,
            reference="KIEM-KE-TON",
            product_id=payload.product_id,
            uom_id=product.uom_id,
            qty=delta,
            cost_price=payload.cost_price or (float(product.cost_price) if product.cost_price else 0.0),
            from_location_id=None,
            to_location_id=payload.location_id,
            moved_at=datetime.now(timezone.utc),
            created_by_id=current_user.id,
            notes=f"Kiểm kê kho: điều chỉnh tăng từ {current_qty} lên {payload.counted_qty}. {payload.notes or ''}",
        )
    else:
        movement = StockMovement(
            movement_type=MovementType.adjustment,
            reference_type=ReferenceType.manual,
            reference="KIEM-KE-TON",
            product_id=payload.product_id,
            uom_id=product.uom_id,
            qty=abs(delta),
            cost_price=payload.cost_price or (float(product.cost_price) if product.cost_price else 0.0),
            from_location_id=payload.location_id,
            to_location_id=None,
            moved_at=datetime.now(timezone.utc),
            created_by_id=current_user.id,
            notes=f"Kiểm kê kho: điều chỉnh giảm từ {current_qty} xuống {payload.counted_qty}. {payload.notes or ''}",
        )

    db.add(movement)

    # Update balance
    if balance:
        balance.qty_on_hand = payload.counted_qty
        balance.last_updated_at = datetime.now(timezone.utc)
    else:
        balance = StockBalance(
            product_id=payload.product_id,
            location_id=payload.location_id,
            qty_on_hand=payload.counted_qty,
        )
        db.add(balance)

    db.commit()
    return MessageResponse(
        message=f"Đã cập nhật tồn kho sản phẩm '{product.code}' tại vị trí '{loc.code}' thành {payload.counted_qty}"
    )
