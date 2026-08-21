"""
TradeCore — Pricing Schemas: PriceList & PriceListItem
Validation and serialization for multi-tier and customer-specific price lists.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ─── Price List Item Schemas ─────────────────────────────────────────────────

class PriceListItemBase(BaseModel):
    product_id: uuid.UUID
    uom_id: Optional[uuid.UUID] = None
    min_qty: float = Field(0.0, ge=0, description="Minimum quantity for this tier")
    price: float = Field(..., ge=0, description="Unit price in price list currency")
    source_price: Optional[float] = Field(None, ge=0)
    source_currency: Optional[str] = Field(None, max_length=10)
    notes: Optional[str] = None


class PriceListItemCreate(PriceListItemBase):
    pass


class PriceListItemUpdate(BaseModel):
    product_id: Optional[uuid.UUID] = None
    uom_id: Optional[uuid.UUID] = None
    min_qty: Optional[float] = Field(None, ge=0)
    price: Optional[float] = Field(None, ge=0)
    source_price: Optional[float] = Field(None, ge=0)
    source_currency: Optional[str] = Field(None, max_length=10)
    notes: Optional[str] = None


class PriceListItemResponse(PriceListItemBase):
    id: uuid.UUID
    price_list_id: uuid.UUID
    product_code: Optional[str] = None
    old_code: Optional[str] = None
    invoice_code: Optional[str] = None
    qr_code: Optional[str] = None
    specifications: Optional[str] = None
    image_url: Optional[str] = None
    product_name: Optional[str] = None
    category_name: Optional[str] = None
    uom_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ─── Price List Schemas ──────────────────────────────────────────────────────

class PriceListBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field("Nháp", max_length=50)
    quotation_number: Optional[str] = Field(None, max_length=100)
    quotation_date: Optional[str] = Field(None, max_length=100)
    month: Optional[int] = None
    quarter: Optional[int] = None
    year: Optional[int] = None
    pricing_conditions: Optional[str] = None
    vat_notes: Optional[str] = None
    source_excel_file: Optional[str] = None
    currency_id: Optional[uuid.UUID] = None
    customer_id: Optional[uuid.UUID] = Field(
        None, description="NULL for standard general price list, or specific customer ID"
    )
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    is_active: bool = True
    notes: Optional[str] = None


class PriceListCreate(PriceListBase):
    items: Optional[List[PriceListItemBase]] = None


class PriceListUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    currency_id: Optional[uuid.UUID] = None
    customer_id: Optional[uuid.UUID] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class PriceListResponse(PriceListBase):
    id: uuid.UUID
    customer_name: Optional[str] = None
    currency_code: Optional[str] = None
    items_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PriceListDetailResponse(PriceListResponse):
    items: List[PriceListItemResponse] = []


# ─── Price Lookup Schemas ────────────────────────────────────────────────────

class PriceLookupResponse(BaseModel):
    product_id: uuid.UUID
    product_code: str
    product_name: str
    unit_price: float
    currency_code: str
    price_list_id: Optional[uuid.UUID] = None
    price_list_name: Optional[str] = None
    is_customer_specific: bool = False
