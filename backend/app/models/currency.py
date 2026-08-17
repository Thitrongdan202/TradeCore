"""
TradeCore — Currency Model
Supports multi-currency. VND is the base currency for domestic transactions.
USD is primary for import/export transactions.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional
from datetime import date

from sqlalchemy import Boolean, Date, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .pricing import PriceList
    from .sales import SalesOrder
    from .purchase import PurchaseOrder
    from .inventory import StockMovement
    from .expense import Expense


class Currency(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    ISO 4217 currency definition.

    exchange_rate: rate to VND (base currency).
    Example: USD has exchange_rate ≈ 25500 (meaning 1 USD = 25500 VND).
    VND itself has exchange_rate = 1.

    rate_date: the date this exchange rate was set. Rates are updated manually
    or via a future rate-update process. Do not auto-overwrite rates.
    """

    __tablename__ = "currencies"

    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False)
    is_base: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    exchange_rate: Mapped[Optional[float]] = mapped_column(
        Numeric(18, 6), nullable=True, comment="Rate to VND (base currency)"
    )
    rate_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships (back references — defined on the owning side)
    price_lists: Mapped[List["PriceList"]] = relationship("PriceList", back_populates="currency")
    sales_orders: Mapped[List["SalesOrder"]] = relationship("SalesOrder", back_populates="currency")
    purchase_orders: Mapped[List["PurchaseOrder"]] = relationship("PurchaseOrder", back_populates="currency")

    def __repr__(self) -> str:
        return f"<Currency code={self.code!r} rate={self.exchange_rate}>"
