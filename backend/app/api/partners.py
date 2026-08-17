"""
TradeCore — Partners API Router
Provides CRUD endpoints for Customers, Suppliers, and Payment Terms.
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
from app.models.partner import Customer, PaymentTerm, Supplier
from app.models.sales import SalesOrder
from app.models.purchase import PurchaseOrder
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.partner import (
    CustomerCreate,
    CustomerDetailResponse,
    CustomerResponse,
    CustomerUpdate,
    PaymentTermCreate,
    PaymentTermResponse,
    PaymentTermUpdate,
    SupplierCreate,
    SupplierDetailResponse,
    SupplierResponse,
    SupplierUpdate,
)

router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# PAYMENT TERMS CRUD
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/payment-terms", response_model=List[PaymentTermResponse], summary="Lấy danh sách điều khoản thanh toán")
def list_payment_terms(
    is_active: Optional[bool] = Query(None, description="Lọc theo trạng thái hoạt động"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN, RoleType.MANAGER, RoleType.SALES, RoleType.PURCHASING, RoleType.WAREHOUSE, RoleType.IMPORT_EXPORT])),
):
    """Retrieve all payment terms."""
    query = select(PaymentTerm).order_by(PaymentTerm.name)
    if is_active is not None:
        query = query.where(PaymentTerm.is_active == is_active)
    return db.execute(query).scalars().all()


@router.get("/payment-terms/{term_id}", response_model=PaymentTermResponse, summary="Lấy chi tiết điều khoản thanh toán")
def get_payment_term(
    term_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN, RoleType.MANAGER, RoleType.SALES, RoleType.PURCHASING, RoleType.WAREHOUSE, RoleType.IMPORT_EXPORT])),
):
    """Get single payment term by UUID."""
    term = db.execute(select(PaymentTerm).where(PaymentTerm.id == term_id)).scalar_one_or_none()
    if not term:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy điều khoản thanh toán với ID {term_id}",
        )
    return term


@router.post(
    "/payment-terms",
    response_model=PaymentTermResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo mới điều khoản thanh toán",
)
def create_payment_term(
    payload: PaymentTermCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN, RoleType.MANAGER])),
):
    """Create a new payment term."""
    existing = db.execute(select(PaymentTerm).where(PaymentTerm.name == payload.name.strip())).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Điều khoản thanh toán '{payload.name}' đã tồn tại",
        )

    term = PaymentTerm(
        name=payload.name.strip(),
        description=payload.description,
        days_due=payload.days_due,
        advance_percent=payload.advance_percent,
        is_active=payload.is_active,
    )
    db.add(term)
    db.commit()
    db.refresh(term)
    return term


@router.put("/payment-terms/{term_id}", response_model=PaymentTermResponse, summary="Cập nhật điều khoản thanh toán")
def update_payment_term(
    term_id: uuid.UUID,
    payload: PaymentTermUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN, RoleType.MANAGER])),
):
    """Update payment term."""
    term = db.execute(select(PaymentTerm).where(PaymentTerm.id == term_id)).scalar_one_or_none()
    if not term:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy điều khoản thanh toán với ID {term_id}",
        )

    if payload.name is not None and payload.name.strip() != term.name:
        existing = db.execute(
            select(PaymentTerm).where(PaymentTerm.name == payload.name.strip(), PaymentTerm.id != term_id)
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Điều khoản thanh toán '{payload.name}' đã tồn tại",
            )
        term.name = payload.name.strip()

    if payload.description is not None:
        term.description = payload.description
    if payload.days_due is not None:
        term.days_due = payload.days_due
    if payload.advance_percent is not None:
        term.advance_percent = payload.advance_percent
    if payload.is_active is not None:
        term.is_active = payload.is_active

    db.commit()
    db.refresh(term)
    return term


@router.delete("/payment-terms/{term_id}", response_model=MessageResponse, summary="Xóa điều khoản thanh toán")
def delete_payment_term(
    term_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN, RoleType.MANAGER])),
):
    """Delete payment term if not in use."""
    term = db.execute(select(PaymentTerm).where(PaymentTerm.id == term_id)).scalar_one_or_none()
    if not term:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy điều khoản thanh toán với ID {term_id}",
        )

    # Check customers & suppliers referencing this term
    cust_count = db.execute(select(func.count(Customer.id)).where(Customer.payment_term_id == term_id)).scalar() or 0
    supp_count = db.execute(select(func.count(Supplier.id)).where(Supplier.payment_term_id == term_id)).scalar() or 0
    if cust_count > 0 or supp_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Không thể xóa vì có {cust_count} khách hàng và {supp_count} nhà cung cấp đang liên kết",
        )

    db.delete(term)
    db.commit()
    return MessageResponse(message=f"Đã xóa điều khoản thanh toán '{term.name}' thành công")


# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOMERS CRUD
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/customers", response_model=PaginatedResponse[CustomerDetailResponse], summary="Lấy danh sách khách hàng")
def list_customers(
    page: int = Query(1, ge=1, description="Số trang"),
    page_size: int = Query(20, ge=1, le=100, description="Số bản ghi mỗi trang"),
    search: Optional[str] = Query(None, description="Tìm theo mã KH, tên, MST hoặc SĐT"),
    is_active: Optional[bool] = Query(None, description="Lọc theo trạng thái hoạt động"),
    province: Optional[str] = Query(None, description="Lọc theo tỉnh/thành phố"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN, RoleType.MANAGER, RoleType.SALES, RoleType.PURCHASING, RoleType.WAREHOUSE, RoleType.IMPORT_EXPORT])),
):
    """List customers with search, province filter, and pagination."""
    query = select(Customer).options(selectinload(Customer.payment_term))

    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(
            or_(
                Customer.code.ilike(pattern),
                Customer.name.ilike(pattern),
                Customer.short_name.ilike(pattern),
                Customer.tax_code.ilike(pattern),
                Customer.phone.ilike(pattern),
            )
        )

    if is_active is not None:
        query = query.where(Customer.is_active == is_active)

    if province:
        query = query.where(Customer.province.ilike(f"%{province.strip()}%"))

    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar() or 0

    offset = (page - 1) * page_size
    customers = db.execute(
        query.order_by(Customer.code).offset(offset).limit(page_size)
    ).scalars().all()

    total_pages = math.ceil(total / page_size) if page_size > 0 else 1

    return PaginatedResponse(
        items=customers,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/customers/{customer_id}", response_model=CustomerDetailResponse, summary="Lấy chi tiết khách hàng")
def get_customer(
    customer_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN, RoleType.MANAGER, RoleType.SALES, RoleType.PURCHASING, RoleType.WAREHOUSE, RoleType.IMPORT_EXPORT])),
):
    """Retrieve customer details with payment term."""
    customer = db.execute(
        select(Customer).options(selectinload(Customer.payment_term)).where(Customer.id == customer_id)
    ).scalar_one_or_none()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy khách hàng với ID {customer_id}",
        )
    return customer


@router.post(
    "/customers",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo mới khách hàng",
)
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN, RoleType.MANAGER])),
):
    """Create a new customer."""
    existing = db.execute(select(Customer).where(Customer.code == payload.code.strip())).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Mã khách hàng '{payload.code}' đã tồn tại",
        )

    if payload.payment_term_id:
        term = db.execute(select(PaymentTerm).where(PaymentTerm.id == payload.payment_term_id)).scalar_one_or_none()
        if not term:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không tìm thấy điều khoản thanh toán với ID {payload.payment_term_id}",
            )

    customer = Customer(
        code=payload.code.strip(),
        tax_code=payload.tax_code,
        name=payload.name.strip(),
        short_name=payload.short_name,
        phone=payload.phone,
        email=payload.email,
        address=payload.address,
        city=payload.city,
        province=payload.province,
        country=payload.country,
        payment_term_id=payload.payment_term_id,
        credit_limit=payload.credit_limit,
        is_active=payload.is_active,
        notes=payload.notes,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.put("/customers/{customer_id}", response_model=CustomerResponse, summary="Cập nhật thông tin khách hàng")
def update_customer(
    customer_id: uuid.UUID,
    payload: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN, RoleType.MANAGER])),
):
    """Update customer details."""
    customer = db.execute(select(Customer).where(Customer.id == customer_id)).scalar_one_or_none()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy khách hàng với ID {customer_id}",
        )

    if payload.code is not None and payload.code.strip() != customer.code:
        existing = db.execute(
            select(Customer).where(Customer.code == payload.code.strip(), Customer.id != customer_id)
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Mã khách hàng '{payload.code}' đã tồn tại",
            )
        customer.code = payload.code.strip()

    if payload.payment_term_id is not None:
        term = db.execute(select(PaymentTerm).where(PaymentTerm.id == payload.payment_term_id)).scalar_one_or_none()
        if not term:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không tìm thấy điều khoản thanh toán với ID {payload.payment_term_id}",
            )
        customer.payment_term_id = payload.payment_term_id

    if payload.tax_code is not None:
        customer.tax_code = payload.tax_code
    if payload.name is not None:
        customer.name = payload.name.strip()
    if payload.short_name is not None:
        customer.short_name = payload.short_name
    if payload.phone is not None:
        customer.phone = payload.phone
    if payload.email is not None:
        customer.email = payload.email
    if payload.address is not None:
        customer.address = payload.address
    if payload.city is not None:
        customer.city = payload.city
    if payload.province is not None:
        customer.province = payload.province
    if payload.country is not None:
        customer.country = payload.country
    if payload.credit_limit is not None:
        customer.credit_limit = payload.credit_limit
    if payload.is_active is not None:
        customer.is_active = payload.is_active
    if payload.notes is not None:
        customer.notes = payload.notes

    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/customers/{customer_id}", response_model=MessageResponse, summary="Xóa hoặc vô hiệu hóa khách hàng")
def delete_customer(
    customer_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN, RoleType.MANAGER])),
):
    """Delete a customer or deactivate if orders exist."""
    customer = db.execute(select(Customer).where(Customer.id == customer_id)).scalar_one_or_none()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy khách hàng với ID {customer_id}",
        )

    orders_count = db.execute(
        select(func.count(SalesOrder.id)).where(SalesOrder.customer_id == customer_id)
    ).scalar() or 0

    if orders_count > 0:
        customer.is_active = False
        db.commit()
        return MessageResponse(
            message=f"Khách hàng '{customer.code}' đã có {orders_count} đơn hàng nên đã được chuyển sang trạng thái Ngừng hoạt động (Inactive)"
        )

    db.delete(customer)
    db.commit()
    return MessageResponse(message=f"Đã xóa khách hàng '{customer.code}' thành công")


# ═══════════════════════════════════════════════════════════════════════════════
# SUPPLIERS CRUD
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/suppliers", response_model=PaginatedResponse[SupplierDetailResponse], summary="Lấy danh sách nhà cung cấp")
def list_suppliers(
    page: int = Query(1, ge=1, description="Số trang"),
    page_size: int = Query(20, ge=1, le=100, description="Số bản ghi mỗi trang"),
    search: Optional[str] = Query(None, description="Tìm theo mã NCC, tên, MST, SĐT hoặc người liên hệ"),
    country: Optional[str] = Query(None, description="Lọc theo quốc gia (VN, CN, KR, TW, v.v.)"),
    is_active: Optional[bool] = Query(None, description="Lọc theo trạng thái hoạt động"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN, RoleType.MANAGER, RoleType.SALES, RoleType.PURCHASING, RoleType.WAREHOUSE, RoleType.IMPORT_EXPORT])),
):
    """List suppliers with search, country filter, and pagination."""
    query = select(Supplier).options(selectinload(Supplier.payment_term))

    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(
            or_(
                Supplier.code.ilike(pattern),
                Supplier.name.ilike(pattern),
                Supplier.short_name.ilike(pattern),
                Supplier.tax_code.ilike(pattern),
                Supplier.contact_name.ilike(pattern),
                Supplier.phone.ilike(pattern),
            )
        )

    if country:
        query = query.where(Supplier.country.ilike(country.strip()))

    if is_active is not None:
        query = query.where(Supplier.is_active == is_active)

    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar() or 0

    offset = (page - 1) * page_size
    suppliers = db.execute(
        query.order_by(Supplier.code).offset(offset).limit(page_size)
    ).scalars().all()

    total_pages = math.ceil(total / page_size) if page_size > 0 else 1

    return PaginatedResponse(
        items=suppliers,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/suppliers/{supplier_id}", response_model=SupplierDetailResponse, summary="Lấy chi tiết nhà cung cấp")
def get_supplier(
    supplier_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN, RoleType.MANAGER, RoleType.SALES, RoleType.PURCHASING, RoleType.WAREHOUSE, RoleType.IMPORT_EXPORT])),
):
    """Retrieve supplier details by UUID."""
    supplier = db.execute(
        select(Supplier).options(selectinload(Supplier.payment_term)).where(Supplier.id == supplier_id)
    ).scalar_one_or_none()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy nhà cung cấp với ID {supplier_id}",
        )
    return supplier


@router.post(
    "/suppliers",
    response_model=SupplierResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo mới nhà cung cấp",
)
def create_supplier(
    payload: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN, RoleType.MANAGER])),
):
    """Create a new supplier."""
    existing = db.execute(select(Supplier).where(Supplier.code == payload.code.strip())).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Mã nhà cung cấp '{payload.code}' đã tồn tại",
        )

    if payload.payment_term_id:
        term = db.execute(select(PaymentTerm).where(PaymentTerm.id == payload.payment_term_id)).scalar_one_or_none()
        if not term:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không tìm thấy điều khoản thanh toán với ID {payload.payment_term_id}",
            )

    supplier = Supplier(
        code=payload.code.strip(),
        tax_code=payload.tax_code,
        name=payload.name.strip(),
        short_name=payload.short_name,
        country=payload.country,
        contact_name=payload.contact_name,
        phone=payload.phone,
        email=payload.email,
        address=payload.address,
        payment_term_id=payload.payment_term_id,
        is_active=payload.is_active,
        notes=payload.notes,
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.put("/suppliers/{supplier_id}", response_model=SupplierResponse, summary="Cập nhật nhà cung cấp")
def update_supplier(
    supplier_id: uuid.UUID,
    payload: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN, RoleType.MANAGER])),
):
    """Update supplier details."""
    supplier = db.execute(select(Supplier).where(Supplier.id == supplier_id)).scalar_one_or_none()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy nhà cung cấp với ID {supplier_id}",
        )

    if payload.code is not None and payload.code.strip() != supplier.code:
        existing = db.execute(
            select(Supplier).where(Supplier.code == payload.code.strip(), Supplier.id != supplier_id)
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Mã nhà cung cấp '{payload.code}' đã tồn tại",
            )
        supplier.code = payload.code.strip()

    if payload.payment_term_id is not None:
        term = db.execute(select(PaymentTerm).where(PaymentTerm.id == payload.payment_term_id)).scalar_one_or_none()
        if not term:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không tìm thấy điều khoản thanh toán với ID {payload.payment_term_id}",
            )
        supplier.payment_term_id = payload.payment_term_id

    if payload.tax_code is not None:
        supplier.tax_code = payload.tax_code
    if payload.name is not None:
        supplier.name = payload.name.strip()
    if payload.short_name is not None:
        supplier.short_name = payload.short_name
    if payload.country is not None:
        supplier.country = payload.country
    if payload.contact_name is not None:
        supplier.contact_name = payload.contact_name
    if payload.phone is not None:
        supplier.phone = payload.phone
    if payload.email is not None:
        supplier.email = payload.email
    if payload.address is not None:
        supplier.address = payload.address
    if payload.is_active is not None:
        supplier.is_active = payload.is_active
    if payload.notes is not None:
        supplier.notes = payload.notes

    db.commit()
    db.refresh(supplier)
    return supplier


@router.delete("/suppliers/{supplier_id}", response_model=MessageResponse, summary="Xóa hoặc vô hiệu hóa nhà cung cấp")
def delete_supplier(
    supplier_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleType.ADMIN, RoleType.MANAGER])),
):
    """Delete a supplier or deactivate if purchase orders exist."""
    supplier = db.execute(select(Supplier).where(Supplier.id == supplier_id)).scalar_one_or_none()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy nhà cung cấp với ID {supplier_id}",
        )

    orders_count = db.execute(
        select(func.count(PurchaseOrder.id)).where(PurchaseOrder.supplier_id == supplier_id)
    ).scalar() or 0

    if orders_count > 0:
        supplier.is_active = False
        db.commit()
        return MessageResponse(
            message=f"Nhà cung cấp '{supplier.code}' đã có {orders_count} đơn mua hàng nên đã được chuyển sang trạng thái Ngừng hoạt động (Inactive)"
        )

    db.delete(supplier)
    db.commit()
    return MessageResponse(message=f"Đã xóa nhà cung cấp '{supplier.code}' thành công")
