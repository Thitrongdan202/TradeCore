"""
TradeCore — Partner Schemas: Customer, Supplier, PaymentTerm
Validation and serialization for business partners and commercial terms.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ─── Payment Term Schemas ────────────────────────────────────────────────────

class PaymentTermBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    days_due: Optional[int] = Field(None, ge=0, description="Days until payment is due")
    advance_percent: Optional[float] = Field(None, ge=0, le=100, description="Advance percentage (0–100)")
    is_active: bool = True


class PaymentTermCreate(PaymentTermBase):
    pass


class PaymentTermUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    days_due: Optional[int] = Field(None, ge=0)
    advance_percent: Optional[float] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None


class PaymentTermResponse(PaymentTermBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ─── Customer Schemas ────────────────────────────────────────────────────────

class CustomerBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=40, description="Stable code e.g. KH-0041")
    tax_code: Optional[str] = Field(None, max_length=20, description="MST — Mã số thuế")
    name: str = Field(..., min_length=1, max_length=500)
    short_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=30)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    province: Optional[str] = Field(None, max_length=100)
    country: str = Field("VN", max_length=10)
    payment_term_id: Optional[uuid.UUID] = None
    credit_limit: Optional[float] = Field(None, ge=0)
    is_active: bool = True
    notes: Optional[str] = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=40)
    tax_code: Optional[str] = Field(None, max_length=20)
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    short_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=30)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    province: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=10)
    payment_term_id: Optional[uuid.UUID] = None
    credit_limit: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class CustomerResponse(CustomerBase):
    id: uuid.UUID
    odoo_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CustomerDetailResponse(CustomerResponse):
    payment_term: Optional[PaymentTermResponse] = None


# ─── Supplier Schemas ────────────────────────────────────────────────────────

class SupplierBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=40, description="Stable supplier code e.g. NCC-0012")
    tax_code: Optional[str] = Field(None, max_length=30)
    name: str = Field(..., min_length=1, max_length=500)
    short_name: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=10, description="ISO country code e.g. VN, CN, KR")
    contact_name: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=30)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    payment_term_id: Optional[uuid.UUID] = None
    is_active: bool = True
    notes: Optional[str] = None


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=40)
    tax_code: Optional[str] = Field(None, max_length=30)
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    short_name: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=10)
    contact_name: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=30)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    payment_term_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class SupplierResponse(SupplierBase):
    id: uuid.UUID
    odoo_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SupplierDetailResponse(SupplierResponse):
    payment_term: Optional[PaymentTermResponse] = None
