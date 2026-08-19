from typing import Optional
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class SupportSessionCreate(BaseModel):
    user_id: uuid.UUID
    reason: str
    duration_hours: int = 24

class SupportSessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    activated_by_id: Optional[uuid.UUID] = None
    reason: str
    expires_at: datetime
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
