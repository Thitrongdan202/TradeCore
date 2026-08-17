"""
TradeCore — Common Pydantic Schemas
Generic pagination and standard API response wrappers.
"""
from typing import Generic, List, TypeVar, Optional
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class MessageResponse(BaseModel):
    """Standard message response for delete and status actions."""
    message: str
    success: bool = True


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated list wrapper."""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)
