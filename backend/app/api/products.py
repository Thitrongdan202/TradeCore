"""
TradeCore — Products and Categories API Router
Provides CRUD endpoints for products, hierarchical categories, and units of measure.
"""
from __future__ import annotations

import math
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, or_
from sqlalchemy.orm import Session, selectinload

from app.core.security import RoleType
from app.api.deps import get_current_user, get_db, require_role
from app.models.inventory import StockBalance
from app.models.product import Product, ProductCategory, ProductType
from app.models.uom import UnitOfMeasure
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.product import (
    ProductCategoryCreate,
    ProductCategoryResponse,
    ProductCategoryTreeResponse,
    ProductCategoryUpdate,
    ProductCreate,
    ProductDetailResponse,
    ProductResponse,
    ProductTypeEnum,
    ProductUpdate,
    UnitOfMeasureCreate,
    UnitOfMeasureResponse,
    UnitOfMeasureUpdate,
)

router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORIES CRUD
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/categories", response_model=List[ProductCategoryResponse], summary="Lấy danh mục sản phẩm")
def list_categories(
    is_active: Optional[bool] = Query(None, description="Lọc theo trạng thái hoạt động"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN, RoleType.MANAGER, RoleType.SALES, RoleType.PURCHASING, RoleType.WAREHOUSE, RoleType.IMPORT_EXPORT])),
):
    """List product categories."""
    query = select(ProductCategory).order_by(ProductCategory.name)
    if is_active is not None:
        query = query.where(ProductCategory.is_active == is_active)
    return db.execute(query).scalars().all()


@router.get("/categories/tree", response_model=List[ProductCategoryTreeResponse], summary="Lấy cây danh mục sản phẩm")
def get_categories_tree(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN, RoleType.MANAGER, RoleType.SALES, RoleType.PURCHASING, RoleType.WAREHOUSE, RoleType.IMPORT_EXPORT])),
):
    """Retrieve top-level categories with nested children."""
    query = (
        select(ProductCategory)
        .options(selectinload(ProductCategory.children))
        .where(ProductCategory.parent_id.is_(None))
        .order_by(ProductCategory.name)
    )
    return db.execute(query).scalars().all()


@router.get("/categories/{category_id}", response_model=ProductCategoryResponse, summary="Lấy thông tin danh mục")
def get_category(
    category_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN, RoleType.MANAGER, RoleType.SALES, RoleType.PURCHASING, RoleType.WAREHOUSE, RoleType.IMPORT_EXPORT])),
):
    """Retrieve a single category by UUID."""
    cat = db.execute(select(ProductCategory).where(ProductCategory.id == category_id)).scalar_one_or_none()
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy danh mục với ID {category_id}",
        )
    return cat


@router.post(
    "/categories",
    response_model=ProductCategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo danh mục sản phẩm",
)
def create_category(
    payload: ProductCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN, RoleType.MANAGER])),
):
    """Create a new product category."""
    if payload.code:
        existing = db.execute(select(ProductCategory).where(ProductCategory.code == payload.code)).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Mã danh mục '{payload.code}' đã tồn tại",
            )

    if payload.parent_id:
        parent = db.execute(select(ProductCategory).where(ProductCategory.id == payload.parent_id)).scalar_one_or_none()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không tìm thấy danh mục cha với ID {payload.parent_id}",
            )

    cat = ProductCategory(
        code=payload.code,
        name=payload.name,
        description=payload.description,
        is_active=payload.is_active,
        parent_id=payload.parent_id,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@router.put("/categories/{category_id}", response_model=ProductCategoryResponse, summary="Cập nhật danh mục")
def update_category(
    category_id: uuid.UUID,
    payload: ProductCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN, RoleType.MANAGER])),
):
    """Update category properties."""
    cat = db.execute(select(ProductCategory).where(ProductCategory.id == category_id)).scalar_one_or_none()
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy danh mục với ID {category_id}",
        )

    if payload.code is not None and payload.code != cat.code:
        existing = db.execute(select(ProductCategory).where(ProductCategory.code == payload.code, ProductCategory.id != category_id)).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Mã danh mục '{payload.code}' đã tồn tại",
            )
        cat.code = payload.code

    if payload.parent_id is not None:
        if payload.parent_id == category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Danh mục không thể làm cha của chính nó",
            )
        parent = db.execute(select(ProductCategory).where(ProductCategory.id == payload.parent_id)).scalar_one_or_none()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không tìm thấy danh mục cha với ID {payload.parent_id}",
            )
        cat.parent_id = payload.parent_id

    if payload.name is not None:
        cat.name = payload.name
    if payload.description is not None:
        cat.description = payload.description
    if payload.is_active is not None:
        cat.is_active = payload.is_active

    db.commit()
    db.refresh(cat)
    return cat


@router.delete("/categories/{category_id}", response_model=MessageResponse, summary="Xóa danh mục")
def delete_category(
    category_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN, RoleType.MANAGER])),
):
    """Delete category if no products or subcategories belong to it."""
    cat = db.execute(select(ProductCategory).where(ProductCategory.id == category_id)).scalar_one_or_none()
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy danh mục với ID {category_id}",
        )

    # Check products
    prod_count = db.execute(select(func.count(Product.id)).where(Product.category_id == category_id)).scalar() or 0
    if prod_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Không thể xóa danh mục vì có {prod_count} sản phẩm đang thuộc danh mục này",
        )

    db.delete(cat)
    db.commit()
    return MessageResponse(message=f"Đã xóa danh mục '{cat.name}' thành công")


# ═══════════════════════════════════════════════════════════════════════════════
# UNITS OF MEASURE CRUD
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/uoms", response_model=List[UnitOfMeasureResponse], summary="Lấy danh sách đơn vị tính")
def list_uoms(
    is_active: Optional[bool] = Query(None, description="Lọc theo trạng thái hoạt động"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN, RoleType.MANAGER, RoleType.SALES, RoleType.PURCHASING, RoleType.WAREHOUSE, RoleType.IMPORT_EXPORT])),
):
    """List units of measure."""
    query = select(UnitOfMeasure).order_by(UnitOfMeasure.name)
    if is_active is not None:
        query = query.where(UnitOfMeasure.is_active == is_active)
    return db.execute(query).scalars().all()


@router.get("/uoms/{uom_id}", response_model=UnitOfMeasureResponse, summary="Lấy thông tin đơn vị tính")
def get_uom(
    uom_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN, RoleType.MANAGER, RoleType.SALES, RoleType.PURCHASING, RoleType.WAREHOUSE, RoleType.IMPORT_EXPORT])),
):
    """Retrieve unit of measure by ID."""
    uom = db.execute(select(UnitOfMeasure).where(UnitOfMeasure.id == uom_id)).scalar_one_or_none()
    if not uom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy đơn vị tính với ID {uom_id}",
        )
    return uom


@router.post(
    "/uoms",
    response_model=UnitOfMeasureResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo mới đơn vị tính",
)
def create_uom(
    payload: UnitOfMeasureCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN, RoleType.MANAGER])),
):
    """Create a new unit of measure."""
    existing = db.execute(select(UnitOfMeasure).where(UnitOfMeasure.name == payload.name)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Đơn vị tính '{payload.name}' đã tồn tại",
        )

    uom = UnitOfMeasure(
        name=payload.name,
        symbol=payload.symbol,
        category=payload.category.value,
        uom_type=payload.uom_type.value,
        factor=payload.factor,
        is_active=payload.is_active,
    )
    db.add(uom)
    db.commit()
    db.refresh(uom)
    return uom


@router.put("/uoms/{uom_id}", response_model=UnitOfMeasureResponse, summary="Cập nhật đơn vị tính")
def update_uom(
    uom_id: uuid.UUID,
    payload: UnitOfMeasureUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN, RoleType.MANAGER])),
):
    """Update unit of measure."""
    uom = db.execute(select(UnitOfMeasure).where(UnitOfMeasure.id == uom_id)).scalar_one_or_none()
    if not uom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy đơn vị tính với ID {uom_id}",
        )

    if payload.name is not None and payload.name != uom.name:
        existing = db.execute(select(UnitOfMeasure).where(UnitOfMeasure.name == payload.name, UnitOfMeasure.id != uom_id)).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Đơn vị tính '{payload.name}' đã tồn tại",
            )
        uom.name = payload.name

    if payload.symbol is not None:
        uom.symbol = payload.symbol
    if payload.category is not None:
        uom.category = payload.category.value
    if payload.uom_type is not None:
        uom.uom_type = payload.uom_type.value
    if payload.factor is not None:
        uom.factor = payload.factor
    if payload.is_active is not None:
        uom.is_active = payload.is_active

    db.commit()
    db.refresh(uom)
    return uom


@router.delete("/uoms/{uom_id}", response_model=MessageResponse, summary="Xóa đơn vị tính")
def delete_uom(
    uom_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN, RoleType.MANAGER])),
):
    """Delete a unit of measure."""
    uom = db.execute(select(UnitOfMeasure).where(UnitOfMeasure.id == uom_id)).scalar_one_or_none()
    if not uom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy đơn vị tính với ID {uom_id}",
        )

    prod_count = db.execute(
        select(func.count(Product.id)).where(or_(Product.uom_id == uom_id, Product.purchase_uom_id == uom_id))
    ).scalar() or 0
    if prod_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Không thể xóa đơn vị tính vì có {prod_count} sản phẩm đang sử dụng",
        )

    db.delete(uom)
    db.commit()
    return MessageResponse(message=f"Đã xóa đơn vị tính '{uom.name}' thành công")


# ═══════════════════════════════════════════════════════════════════════════════
# PRODUCTS CRUD
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("", response_model=PaginatedResponse[ProductDetailResponse], summary="Lấy danh sách sản phẩm")
def list_products(
    page: int = Query(1, ge=1, description="Số trang (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Số bản ghi mỗi trang"),
    search: Optional[str] = Query(None, description="Tìm theo mã sản phẩm, tên hoặc mã vạch"),
    category_id: Optional[uuid.UUID] = Query(None, description="Lọc theo danh mục"),
    product_type: Optional[ProductTypeEnum] = Query(None, description="Lọc theo loại sản phẩm"),
    is_active: Optional[bool] = Query(None, description="Lọc theo trạng thái hoạt động"),
    low_stock_only: bool = Query(False, description="Chỉ lấy sản phẩm tồn kho dưới mức tối thiểu"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN, RoleType.MANAGER, RoleType.SALES, RoleType.PURCHASING, RoleType.WAREHOUSE, RoleType.IMPORT_EXPORT])),
):
    """List products with filters, category/uom details, and current on-hand stock."""
    query = (
        select(Product)
        .options(
            selectinload(Product.category),
            selectinload(Product.uom),
            selectinload(Product.purchase_uom),
        )
    )

    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(
            or_(
                Product.code.ilike(pattern),
                Product.name.ilike(pattern),
                Product.barcode.ilike(pattern),
            )
        )

    if category_id:
        query = query.where(Product.category_id == category_id)

    if product_type:
        query = query.where(Product.product_type == product_type.value)

    if is_active is not None:
        query = query.where(Product.is_active == is_active)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    products = db.execute(
        query.order_by(Product.code).offset(offset).limit(page_size)
    ).scalars().all()

    # Pre-fetch total stock for fetched products
    product_ids = [p.id for p in products]
    stock_map: dict[uuid.UUID, float] = {}
    if product_ids:
        balances = db.execute(
            select(
                StockBalance.product_id,
                func.coalesce(func.sum(StockBalance.qty_on_hand), 0).label("total_stock")
            )
            .where(StockBalance.product_id.in_(product_ids))
            .group_by(StockBalance.product_id)
        ).all()
        stock_map = {row.product_id: float(row.total_stock) for row in balances}

    results: List[ProductDetailResponse] = []
    for p in products:
        qty = stock_map.get(p.id, 0.0)
        if low_stock_only and p.min_stock is not None and qty >= float(p.min_stock):
            continue

        item_dict = {
            "id": p.id,
            "code": p.code,
            "barcode": p.barcode,
            "name": p.name,
            "name_en": p.name_en,
            "description": p.description,
            "product_type": p.product_type,
            "category_id": p.category_id,
            "uom_id": p.uom_id,
            "purchase_uom_id": p.purchase_uom_id,
            "cost_price": float(p.cost_price) if p.cost_price is not None else None,
            "weight_kg": float(p.weight_kg) if p.weight_kg is not None else None,
            "volume_m3": float(p.volume_m3) if p.volume_m3 is not None else None,
            "min_stock": float(p.min_stock) if p.min_stock is not None else None,
            "max_stock": float(p.max_stock) if p.max_stock is not None else None,
            "is_active": p.is_active,
            "notes": p.notes,
            "odoo_id": p.odoo_id,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
            "category": p.category,
            "uom": p.uom,
            "purchase_uom": p.purchase_uom,
            "stock_on_hand": qty,
        }
        results.append(ProductDetailResponse.model_validate(item_dict))

    total_pages = math.ceil(total / page_size) if page_size > 0 else 1

    return PaginatedResponse(
        items=results,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{product_id}", response_model=ProductDetailResponse, summary="Lấy chi tiết sản phẩm")
def get_product(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN, RoleType.MANAGER, RoleType.SALES, RoleType.PURCHASING, RoleType.WAREHOUSE, RoleType.IMPORT_EXPORT])),
):
    """Retrieve product details by UUID."""
    product = db.execute(
        select(Product)
        .options(
            selectinload(Product.category),
            selectinload(Product.uom),
            selectinload(Product.purchase_uom),
        )
        .where(Product.id == product_id)
    ).scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy sản phẩm với ID {product_id}",
        )

    # Get on-hand stock
    stock_on_hand = db.execute(
        select(func.coalesce(func.sum(StockBalance.qty_on_hand), 0)).where(StockBalance.product_id == product_id)
    ).scalar() or 0.0

    return ProductDetailResponse(
        id=product.id,
        code=product.code,
        barcode=product.barcode,
        name=product.name,
        name_en=product.name_en,
        description=product.description,
        product_type=ProductTypeEnum(product.product_type.value),
        category_id=product.category_id,
        uom_id=product.uom_id,
        purchase_uom_id=product.purchase_uom_id,
        cost_price=float(product.cost_price) if product.cost_price is not None else None,
        weight_kg=float(product.weight_kg) if product.weight_kg is not None else None,
        volume_m3=float(product.volume_m3) if product.volume_m3 is not None else None,
        min_stock=float(product.min_stock) if product.min_stock is not None else None,
        max_stock=float(product.max_stock) if product.max_stock is not None else None,
        is_active=product.is_active,
        notes=product.notes,
        odoo_id=product.odoo_id,
        created_at=product.created_at,
        updated_at=product.updated_at,
        category=ProductCategoryResponse.model_validate(product.category) if product.category else None,
        uom=UnitOfMeasureResponse.model_validate(product.uom) if product.uom else None,
        purchase_uom=UnitOfMeasureResponse.model_validate(product.purchase_uom) if product.purchase_uom else None,
        stock_on_hand=float(stock_on_hand),
    )


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED, summary="Tạo mới sản phẩm")
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN, RoleType.MANAGER])),
):
    """Create a new product record."""
    # Check code uniqueness
    existing = db.execute(select(Product).where(Product.code == payload.code.strip())).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Mã sản phẩm '{payload.code}' đã tồn tại trong hệ thống",
        )

    # Validate category
    if payload.category_id:
        cat = db.execute(select(ProductCategory).where(ProductCategory.id == payload.category_id)).scalar_one_or_none()
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không tìm thấy danh mục với ID {payload.category_id}",
            )

    # Validate UoM
    if payload.uom_id:
        uom = db.execute(select(UnitOfMeasure).where(UnitOfMeasure.id == payload.uom_id)).scalar_one_or_none()
        if not uom:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không tìm thấy đơn vị tính với ID {payload.uom_id}",
            )

    # Validate Purchase UoM
    if payload.purchase_uom_id:
        puom = db.execute(select(UnitOfMeasure).where(UnitOfMeasure.id == payload.purchase_uom_id)).scalar_one_or_none()
        if not puom:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không tìm thấy đơn vị tính mua với ID {payload.purchase_uom_id}",
            )

    product = Product(
        code=payload.code.strip(),
        barcode=payload.barcode,
        name=payload.name.strip(),
        name_en=payload.name_en,
        description=payload.description,
        product_type=payload.product_type.value,
        category_id=payload.category_id,
        uom_id=payload.uom_id,
        purchase_uom_id=payload.purchase_uom_id,
        cost_price=payload.cost_price,
        weight_kg=payload.weight_kg,
        volume_m3=payload.volume_m3,
        min_stock=payload.min_stock,
        max_stock=payload.max_stock,
        is_active=payload.is_active,
        notes=payload.notes,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/{product_id}", response_model=ProductResponse, summary="Cập nhật thông tin sản phẩm")
def update_product(
    product_id: uuid.UUID,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN, RoleType.MANAGER])),
):
    """Update product information."""
    product = db.execute(select(Product).where(Product.id == product_id)).scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy sản phẩm với ID {product_id}",
        )

    if payload.code is not None and payload.code.strip() != product.code:
        existing = db.execute(
            select(Product).where(Product.code == payload.code.strip(), Product.id != product_id)
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Mã sản phẩm '{payload.code}' đã tồn tại",
            )
        product.code = payload.code.strip()

    if payload.barcode is not None:
        product.barcode = payload.barcode
    if payload.name is not None:
        product.name = payload.name.strip()
    if payload.name_en is not None:
        product.name_en = payload.name_en
    if payload.description is not None:
        product.description = payload.description
    if payload.product_type is not None:
        product.product_type = payload.product_type.value
    if payload.category_id is not None:
        product.category_id = payload.category_id
    if payload.uom_id is not None:
        product.uom_id = payload.uom_id
    if payload.purchase_uom_id is not None:
        product.purchase_uom_id = payload.purchase_uom_id
    if payload.cost_price is not None:
        product.cost_price = payload.cost_price
    if payload.weight_kg is not None:
        product.weight_kg = payload.weight_kg
    if payload.volume_m3 is not None:
        product.volume_m3 = payload.volume_m3
    if payload.min_stock is not None:
        product.min_stock = payload.min_stock
    if payload.max_stock is not None:
        product.max_stock = payload.max_stock
    if payload.is_active is not None:
        product.is_active = payload.is_active
    if payload.notes is not None:
        product.notes = payload.notes

    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", response_model=MessageResponse, summary="Xóa hoặc vô hiệu hóa sản phẩm")
def delete_product(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN, RoleType.MANAGER])),
):
    """Delete a product or deactivate if it has history."""
    product = db.execute(select(Product).where(Product.id == product_id)).scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy sản phẩm với ID {product_id}",
        )

    # Check if product has stock movements
    movements_count = db.execute(
        select(func.count()).select_from(StockBalance).where(StockBalance.product_id == product_id)
    ).scalar() or 0

    if movements_count > 0:
        # Deactivate rather than hard delete to preserve inventory integrity
        product.is_active = False
        db.commit()
        return MessageResponse(
            message=f"Sản phẩm '{product.code}' có lịch sử tồn kho nên đã được chuyển sang trạng thái Ngừng kinh doanh (Inactive)"
        )

    db.delete(product)
    db.commit()
    return MessageResponse(message=f"Đã xóa sản phẩm '{product.code}' thành công")
