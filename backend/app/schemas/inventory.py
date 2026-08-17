"""
TradeCore — Inventory Schemas: Warehouse, Location, StockBalance, StockMovement
Validation and serialization for multi-location warehouse management.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ─── Enums ───────────────────────────────────────────────────────────────────

class LocationTypeEnum(str, enum.Enum):
    internal = "internal"
    supplier = "supplier"
    customer = "customer"
    transit  = "transit"
    virtual  = "virtual"


class MovementTypeEnum(str, enum.Enum):
    receive    = "receive"
    issue      = "issue"
    transfer   = "transfer"
    adjustment = "adjustment"
    opening    = "opening"
    scrap      = "scrap"
    return_in  = "return_in"
    return_out = "return_out"


class ReferenceTypeEnum(str, enum.Enum):
    sale_order     = "sale_order"
    purchase_order = "purchase_order"
    shipment       = "shipment"
    manual         = "manual"
    opening        = "opening"
    import_run     = "import_run"


# ─── Warehouse Schemas ───────────────────────────────────────────────────────

class WarehouseBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=20, description="Warehouse code e.g. WH01")
    name: str = Field(..., min_length=1, max_length=255)
    address: Optional[str] = None
    is_active: bool = True


class WarehouseCreate(WarehouseBase):
    pass


class WarehouseUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    address: Optional[str] = None
    is_active: Optional[bool] = None


class WarehouseResponse(WarehouseBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ─── Warehouse Location Schemas ──────────────────────────────────────────────

class WarehouseLocationBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=60, description="Location code e.g. WH01-A-01")
    name: str = Field(..., min_length=1, max_length=255)
    location_type: LocationTypeEnum = LocationTypeEnum.internal
    is_active: bool = True
    warehouse_id: Optional[uuid.UUID] = None
    parent_id: Optional[uuid.UUID] = None


class WarehouseLocationCreate(WarehouseLocationBase):
    pass


class WarehouseLocationUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=60)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    location_type: Optional[LocationTypeEnum] = None
    is_active: Optional[bool] = None
    warehouse_id: Optional[uuid.UUID] = None
    parent_id: Optional[uuid.UUID] = None


class WarehouseLocationResponse(WarehouseLocationBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WarehouseDetailResponse(WarehouseResponse):
    locations: List[WarehouseLocationResponse] = []


# ─── Stock Balance Schemas ───────────────────────────────────────────────────

class StockBalanceResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    location_id: uuid.UUID
    qty_on_hand: float
    last_updated_at: datetime
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    location_code: Optional[str] = None
    location_name: Optional[str] = None
    warehouse_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ─── Stock Movement Schemas ──────────────────────────────────────────────────

class StockMovementCreate(BaseModel):
    movement_type: MovementTypeEnum
    reference_type: Optional[ReferenceTypeEnum] = None
    reference: Optional[str] = Field(None, max_length=100)
    reference_id: Optional[uuid.UUID] = None
    product_id: uuid.UUID
    uom_id: Optional[uuid.UUID] = None
    qty: float = Field(..., gt=0, description="Positive quantity moved")
    cost_price: Optional[float] = Field(None, ge=0)
    from_location_id: Optional[uuid.UUID] = None
    to_location_id: Optional[uuid.UUID] = None
    moved_at: Optional[datetime] = None
    notes: Optional[str] = None


class StockMovementResponse(StockMovementCreate):
    id: uuid.UUID
    created_at: datetime
    created_by_id: Optional[uuid.UUID] = None
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    from_location_code: Optional[str] = None
    to_location_code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class StockAdjustmentCreate(BaseModel):
    product_id: uuid.UUID
    location_id: uuid.UUID
    counted_qty: float = Field(..., ge=0, description="Actual counted physical quantity")
    cost_price: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None
