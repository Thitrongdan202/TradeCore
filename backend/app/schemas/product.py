"""
TradeCore — Product & Category Pydantic Schemas
Validation and serialization for products, categories, and units of measure.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ─── Enums ───────────────────────────────────────────────────────────────────

class ProductTypeEnum(str, enum.Enum):
    product = "product"
    consumable = "consumable"
    service = "service"


class UoMCategoryEnum(str, enum.Enum):
    unit = "unit"
    weight = "weight"
    volume = "volume"
    length = "length"
    area = "area"
    time = "time"
    other = "other"


class UoMTypeEnum(str, enum.Enum):
    reference = "reference"
    smaller = "smaller"
    bigger = "bigger"


# ─── Unit of Measure Schemas ─────────────────────────────────────────────────

class UnitOfMeasureBase(BaseModel):
    name: str = Field(..., max_length=80)
    symbol: Optional[str] = Field(None, max_length=20)
    category: UoMCategoryEnum = UoMCategoryEnum.unit
    uom_type: UoMTypeEnum = UoMTypeEnum.reference
    factor: float = Field(1.0, ge=0.000001)
    is_active: bool = True


class UnitOfMeasureCreate(UnitOfMeasureBase):
    pass


class UnitOfMeasureUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=80)
    symbol: Optional[str] = Field(None, max_length=20)
    category: Optional[UoMCategoryEnum] = None
    uom_type: Optional[UoMTypeEnum] = None
    factor: Optional[float] = Field(None, ge=0.000001)
    is_active: Optional[bool] = None


class UnitOfMeasureResponse(UnitOfMeasureBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ─── Product Category Schemas ────────────────────────────────────────────────

class ProductCategoryBase(BaseModel):
    code: Optional[str] = Field(None, max_length=40)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: bool = True
    parent_id: Optional[uuid.UUID] = None


class ProductCategoryCreate(ProductCategoryBase):
    pass


class ProductCategoryUpdate(BaseModel):
    code: Optional[str] = Field(None, max_length=40)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    parent_id: Optional[uuid.UUID] = None


class ProductCategoryResponse(ProductCategoryBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductCategoryTreeResponse(ProductCategoryResponse):
    children: List[ProductCategoryTreeResponse] = []


# ─── Product Schemas ─────────────────────────────────────────────────────────

class ProductBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=80, description="Stable business code e.g. HH-2041")
    barcode: Optional[str] = Field(None, max_length=100)
    name: str = Field(..., min_length=1, max_length=500)
    name_en: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    product_type: ProductTypeEnum = ProductTypeEnum.product
    category_id: Optional[uuid.UUID] = None
    uom_id: Optional[uuid.UUID] = None
    purchase_uom_id: Optional[uuid.UUID] = None
    cost_price: Optional[float] = Field(None, ge=0)
    weight_kg: Optional[float] = Field(None, ge=0)
    volume_m3: Optional[float] = Field(None, ge=0)
    min_stock: Optional[float] = Field(None, ge=0)
    max_stock: Optional[float] = Field(None, ge=0)
    is_active: bool = True
    notes: Optional[str] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=80)
    barcode: Optional[str] = Field(None, max_length=100)
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    name_en: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    product_type: Optional[ProductTypeEnum] = None
    category_id: Optional[uuid.UUID] = None
    uom_id: Optional[uuid.UUID] = None
    purchase_uom_id: Optional[uuid.UUID] = None
    cost_price: Optional[float] = Field(None, ge=0)
    weight_kg: Optional[float] = Field(None, ge=0)
    volume_m3: Optional[float] = Field(None, ge=0)
    min_stock: Optional[float] = Field(None, ge=0)
    max_stock: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class ProductResponse(ProductBase):
    id: uuid.UUID
    odoo_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductDetailResponse(ProductResponse):
    category: Optional[ProductCategoryResponse] = None
    uom: Optional[UnitOfMeasureResponse] = None
    purchase_uom: Optional[UnitOfMeasureResponse] = None
    stock_on_hand: float = 0.0
