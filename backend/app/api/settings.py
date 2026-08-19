from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permission
from app.models.company import CompanySettings
from app.models.user import User
from app.schemas.company import CompanySettingsResponse, CompanySettingsUpdate
from app.core.audit import log_activity

router = APIRouter()

@router.get("", response_model=CompanySettingsResponse, summary="Lấy thông hiện cài đặt công ty")
def get_company_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("company_setting", "view")),
):
    settings = db.execute(select(CompanySettings)).scalars().first()
    if not settings:
        settings = CompanySettings(name="My Company")
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.put("", response_model=CompanySettingsResponse, summary="Cập nhật cài đặt công ty")
def update_company_settings(
    payload: CompanySettingsUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("company_setting", "update")),
):
    settings = db.execute(select(CompanySettings)).scalars().first()
    if not settings:
        settings = CompanySettings(name=payload.name)
        db.add(settings)
    
    settings.name = payload.name
    settings.trade_name = payload.trade_name
    settings.tax_code = payload.tax_code
    settings.address = payload.address
    settings.phone = payload.phone
    settings.email = payload.email
    settings.website = payload.website
    settings.logo_url = payload.logo_url

    log_activity(db, "company_settings_updated", user_id=current_user.id, request=request)
    db.commit()
    db.refresh(settings)
    return settings
