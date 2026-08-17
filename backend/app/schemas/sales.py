"""
TradeCore — Sales Order Pydantic Schemas
Validation and serialization for sales orders and order line items.
"""
from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.partner import CustomerResponse


# ─── Enums ───────────────────────────────────────────────────────────────────

class OrderStatusEnum(str, enum.Enum):
    draft      = "draft"
    pending    = "pending"
    confirmed  = "confirmed"
    processing = "processing"
    shipping   = "shipping"
    completed  = "completed"
    cancelled  = "cancelled"
    returned   = "returned"


class PaymentStatusEnum(str, enum.Enum):
    unpaid   = "unpaid"
    partial  = "partial"
    paid     = "paid"
    overdue  = "overdue"
    refunded = "refunded"


# ─── Sales Order Item Schemas ────────────────────────────────────────────────

class SalesOrderItemBase(BaseModel):
    product_id: Optional[uuid.UUID] = None
    description: Optional[str] = Field(None, max_length=500)
    qty: float = Field(..., gt=0, description="Quantity sold")
    uom_id: Optional[uuid.UUID] = None
    unit_price: Optional[float] = Field(None, ge=0)
    discount_percent: float = Field(0.0, ge=0, le=100)
    notes: Optional[str] = None


class SalesOrderItemCreate(SalesOrderItemBase):
    pass


class SalesOrderItemUpdate(BaseModel):
    product_id: Optional[uuid.UUID] = None
    description: Optional[str] = Field(None, max_length=500)
    qty: Optional[float] = Field(None, gt=0)
    uom_id: Optional[uuid.UUID] = None
    unit_price: Optional[float] = Field(None, ge=0)
    discount_percent: Optional[float] = Field(None, ge=0, le=100)
    notes: Optional[str] = None


class SalesOrderItemResponse(SalesOrderItemBase):
    id: uuid.UUID
    order_id: uuid.UUID
    line_no: int
    subtotal: Optional[float] = None
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    uom_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ─── Sales Order Schemas ─────────────────────────────────────────────────────

class SalesOrderBase(BaseModel):
    customer_id: Optional[uuid.UUID] = None
    currency_id: Optional[uuid.UUID] = None
    payment_term_id: Optional[uuid.UUID] = None
    date: Optional[date] = None
    due_date: Optional[date] = None
    status: OrderStatusEnum = OrderStatusEnum.draft
    payment_status: PaymentStatusEnum = PaymentStatusEnum.unpaid
    notes: Optional[str] = None


class SalesOrderCreate(SalesOrderBase):
    order_number: Optional[str] = Field(None, max_length=40, description="Auto-generated if omitted")
    items: List[SalesOrderItemCreate] = Field(..., min_length=1, description="Order items")


class SalesOrderUpdate(BaseModel):
    customer_id: Optional[uuid.UUID] = None
    currency_id: Optional[uuid.UUID] = None
    payment_term_id: Optional[uuid.UUID] = None
    date: Optional[date] = None
    due_date: Optional[date] = None
    status: Optional[OrderStatusEnum] = None
    payment_status: Optional[PaymentStatusEnum] = None
    notes: Optional[str] = None
    items: Optional[List[SalesOrderItemCreate]] = None


class SalesOrderStatusUpdate(BaseModel):
    status: OrderStatusEnum
    notes: Optional[str] = None


class SalesOrderPaymentUpdate(BaseModel):
    payment_status: PaymentStatusEnum
    amount_paid: Optional[float] = Field(None, ge=0)


class SalesOrderResponse(SalesOrderBase):
    id: uuid.UUID
    order_number: str
    subtotal: Optional[float] = None
    tax_amount: Optional[float] = None
    total: Optional[float] = None
    amount_paid: Optional[float] = None
    odoo_id: Optional[int] = None
    created_by_id: Optional[uuid.UUID] = None
    customer_name: Optional[str] = None
    customer_code: Optional[str] = None
    items_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SalesOrderDetailResponse(SalesOrderResponse):
    customer: Optional[CustomerResponse] = None
    items: List[SalesOrderItemResponse] = []
