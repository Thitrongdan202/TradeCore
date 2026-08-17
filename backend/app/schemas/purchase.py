"""
TradeCore — Purchase Order Pydantic Schemas
Validation and serialization for purchase orders, line items, and goods receiving.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.partner import SupplierResponse
from app.schemas.sales import OrderStatusEnum, PaymentStatusEnum


# ─── Purchase Order Item Schemas ─────────────────────────────────────────────

class PurchaseOrderItemBase(BaseModel):
    product_id: Optional[uuid.UUID] = None
    description: Optional[str] = Field(None, max_length=500)
    qty: float = Field(..., gt=0, description="Quantity ordered")
    uom_id: Optional[uuid.UUID] = None
    unit_price: Optional[float] = Field(None, ge=0)
    discount_percent: float = Field(0.0, ge=0, le=100)
    notes: Optional[str] = None


class PurchaseOrderItemCreate(PurchaseOrderItemBase):
    pass


class PurchaseOrderItemUpdate(BaseModel):
    product_id: Optional[uuid.UUID] = None
    description: Optional[str] = Field(None, max_length=500)
    qty: Optional[float] = Field(None, gt=0)
    uom_id: Optional[uuid.UUID] = None
    unit_price: Optional[float] = Field(None, ge=0)
    discount_percent: Optional[float] = Field(None, ge=0, le=100)
    notes: Optional[str] = None


class PurchaseOrderItemResponse(PurchaseOrderItemBase):
    id: uuid.UUID
    order_id: uuid.UUID
    line_no: int
    qty_received: float = 0.0
    subtotal: Optional[float] = None
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    uom_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ─── Purchase Order Schemas ──────────────────────────────────────────────────

class PurchaseOrderBase(BaseModel):
    supplier_id: Optional[uuid.UUID] = None
    currency_id: Optional[uuid.UUID] = None
    payment_term_id: Optional[uuid.UUID] = None
    date: Optional[date] = None
    expected_date: Optional[date] = None
    status: OrderStatusEnum = OrderStatusEnum.draft
    payment_status: PaymentStatusEnum = PaymentStatusEnum.unpaid
    notes: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    order_number: Optional[str] = Field(None, max_length=40, description="Auto-generated if omitted")
    items: List[PurchaseOrderItemCreate] = Field(..., min_length=1, description="Order items")


class PurchaseOrderUpdate(BaseModel):
    supplier_id: Optional[uuid.UUID] = None
    currency_id: Optional[uuid.UUID] = None
    payment_term_id: Optional[uuid.UUID] = None
    date: Optional[date] = None
    expected_date: Optional[date] = None
    status: Optional[OrderStatusEnum] = None
    payment_status: Optional[PaymentStatusEnum] = None
    notes: Optional[str] = None
    items: Optional[List[PurchaseOrderItemCreate]] = None


class PurchaseOrderStatusUpdate(BaseModel):
    status: OrderStatusEnum
    notes: Optional[str] = None


class PurchaseOrderPaymentUpdate(BaseModel):
    payment_status: PaymentStatusEnum
    amount_paid: Optional[float] = Field(None, ge=0)


class PurchaseOrderReceiveLine(BaseModel):
    item_id: uuid.UUID
    qty_to_receive: float = Field(..., gt=0)


class PurchaseOrderReceiveRequest(BaseModel):
    destination_location_id: uuid.UUID
    items: List[PurchaseOrderReceiveLine] = Field(..., min_length=1)
    notes: Optional[str] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    id: uuid.UUID
    order_number: str
    subtotal: Optional[float] = None
    tax_amount: Optional[float] = None
    total: Optional[float] = None
    amount_paid: Optional[float] = None
    odoo_id: Optional[int] = None
    created_by_id: Optional[uuid.UUID] = None
    supplier_name: Optional[str] = None
    supplier_code: Optional[str] = None
    items_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderDetailResponse(PurchaseOrderResponse):
    supplier: Optional[SupplierResponse] = None
    items: List[PurchaseOrderItemResponse] = []
