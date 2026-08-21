from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_permission
from app.models.pricing import PriceList, PriceListItem
from app.schemas.price_list import PriceListCreate, PriceListResponse, PriceListItemResponse
from app.schemas.common import PaginatedResponse
from app.models.user import User

router = APIRouter()

@router.get("", response_model=PaginatedResponse[PriceListResponse])
def list_price_lists(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    year: Optional[int] = None,
    quarter: Optional[int] = None,
    month: Optional[int] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(require_permission("pricing", "view")),
):
    query = db.query(PriceList)
    if year:
        query = query.filter(PriceList.year == year)
    if quarter:
        query = query.filter(PriceList.quarter == quarter)
    if month:
        query = query.filter(PriceList.month == month)
    if status_filter:
        query = query.filter(PriceList.status == status_filter)
        
    total = query.count()
    items = query.order_by(PriceList.effective_from.desc().nullslast()).offset((page - 1) * size).limit(size).all()
    
    return PaginatedResponse(
        items=[PriceListResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )

@router.get("/{id}", response_model=PriceListResponse)
def get_price_list(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("pricing", "view")),
):
    pl = db.query(PriceList).filter(PriceList.id == id).first()
    if not pl:
        raise HTTPException(status_code=404, detail="Không tìm thấy bảng giá")
    return pl

@router.get("/{id}/items", response_model=List[PriceListItemResponse])
def get_price_list_items(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("pricing", "view")),
):
    items = db.query(PriceListItem).filter(PriceListItem.price_list_id == id).all()
    return items
