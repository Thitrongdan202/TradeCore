from typing import Optional
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class CompanySettingsBase(BaseModel):
    name: str = Field(..., max_length=255)
    trade_name: Optional[str] = Field(None, max_length=255)
    tax_code: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=255)
    logo_url: Optional[str] = Field(None, max_length=500)

class CompanySettingsUpdate(CompanySettingsBase):
    pass

class CompanySettingsResponse(CompanySettingsBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
