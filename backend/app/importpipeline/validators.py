"""
TradeCore — Import Pipeline: Validation Framework

Every import row passes through this module before touching production tables.
Validators return a list of ValidationMessage objects.
A row with any ERROR-level message is rejected.
A row with only WARNING-level messages may be imported with warnings noted.

Checks performed:
  - Required field presence
  - Duplicate code detection (against both DB and current batch)
  - Numeric parsing and range validation
  - Date parsing
  - Currency code lookup
  - Unit of measure lookup
  - Suspicious value detection (negative quantities, zero prices, etc.)
  - Malformed product codes
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Dict, List, Optional, Set


# ─── Validation message ───────────────────────────────────────────────────────

class Level(str, Enum):
    ERROR   = "error"
    WARNING = "warning"
    INFO    = "info"


@dataclass
class ValidationMessage:
    level:   Level
    code:    str
    field:   Optional[str]
    message: str

    def to_dict(self) -> dict:
        return {
            "level":   self.level.value,
            "code":    self.code,
            "field":   self.field,
            "message": self.message,
        }


def _err(code: str, field: str, msg: str) -> ValidationMessage:
    return ValidationMessage(Level.ERROR, code, field, msg)


def _warn(code: str, field: str, msg: str) -> ValidationMessage:
    return ValidationMessage(Level.WARNING, code, field, msg)


def _info(code: str, field: str, msg: str) -> ValidationMessage:
    return ValidationMessage(Level.INFO, code, field, msg)


# ─── Field-level validators ───────────────────────────────────────────────────

def validate_required(value: Any, field_name: str) -> List[ValidationMessage]:
    """Field must be present and non-empty."""
    if value is None or str(value).strip() == "":
        return [_err("REQUIRED_FIELD_MISSING", field_name,
                     f"Required field '{field_name}' is missing or empty")]
    return []


def validate_string_length(
    value: Any, field_name: str,
    min_len: int = 0, max_len: int = 500
) -> List[ValidationMessage]:
    if value is None:
        return []
    s = str(value).strip()
    msgs = []
    if len(s) < min_len:
        msgs.append(_err("STRING_TOO_SHORT", field_name,
                         f"'{field_name}' is too short (min {min_len} chars)"))
    if len(s) > max_len:
        msgs.append(_err("STRING_TOO_LONG", field_name,
                         f"'{field_name}' exceeds max length {max_len} (got {len(s)})"))
    return msgs


def validate_product_code(value: Any, field_name: str = "code") -> List[ValidationMessage]:
    """Product code must be non-empty and not contain suspicious characters."""
    msgs = validate_required(value, field_name)
    if msgs:
        return msgs
    code = str(value).strip()
    if len(code) < 2:
        msgs.append(_err("CODE_TOO_SHORT", field_name,
                         f"Product code '{code}' is too short (min 2 chars)"))
    if len(code) > 80:
        msgs.append(_err("CODE_TOO_LONG", field_name,
                         f"Product code '{code}' exceeds 80 chars"))
    if re.search(r'[<>&\'"]', code):
        msgs.append(_warn("CODE_SUSPICIOUS_CHARS", field_name,
                          f"Product code '{code}' contains potentially problematic characters"))
    return msgs


def validate_numeric(
    value: Any, field_name: str,
    allow_zero: bool = True,
    allow_negative: bool = False,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
) -> tuple[List[ValidationMessage], Optional[Decimal]]:
    """
    Parse and validate a numeric field.
    Returns (messages, parsed_value). parsed_value is None if parsing failed.
    """
    if value is None or str(value).strip() == "":
        return [], None

    raw = str(value).strip()
    # Remove common formatting: commas as thousands separators, VND symbol
    cleaned = raw.replace(",", "").replace("₫", "").replace("đ", "").strip()

    try:
        parsed = Decimal(cleaned)
    except InvalidOperation:
        return [_err("INVALID_NUMBER", field_name,
                     f"Cannot parse '{raw}' as a number for field '{field_name}'")], None

    msgs: List[ValidationMessage] = []

    if not allow_negative and parsed < 0:
        msgs.append(_err("NEGATIVE_VALUE", field_name,
                         f"'{field_name}' must not be negative (got {parsed})"))
    if not allow_zero and parsed == 0:
        msgs.append(_warn("ZERO_VALUE", field_name,
                          f"'{field_name}' is zero — is this intentional?"))
    if min_val is not None and parsed < Decimal(str(min_val)):
        msgs.append(_err("BELOW_MIN", field_name,
                         f"'{field_name}' = {parsed} is below minimum {min_val}"))
    if max_val is not None and parsed > Decimal(str(max_val)):
        msgs.append(_warn("ABOVE_MAX", field_name,
                          f"'{field_name}' = {parsed} is above expected maximum {max_val}"))

    return msgs, parsed


def validate_price(value: Any, field_name: str) -> tuple[List[ValidationMessage], Optional[Decimal]]:
    """Price must be a non-negative number. Zero price triggers a warning."""
    msgs, parsed = validate_numeric(value, field_name, allow_zero=True, allow_negative=False)
    if parsed is not None and parsed == 0:
        msgs.append(_warn("ZERO_PRICE", field_name,
                          f"Price in field '{field_name}' is zero — verify intentional"))
    if parsed is not None and parsed > Decimal("1_000_000_000_000"):
        msgs.append(_warn("SUSPICIOUS_PRICE", field_name,
                          f"Price {parsed} seems unusually large — verify"))
    return msgs, parsed


def validate_quantity(value: Any, field_name: str) -> tuple[List[ValidationMessage], Optional[Decimal]]:
    """Quantity must be positive and non-negative."""
    msgs, parsed = validate_numeric(value, field_name, allow_zero=False, allow_negative=False)
    if parsed is not None and parsed < 0:
        msgs.append(_err("NEGATIVE_QUANTITY", field_name,
                         f"Quantity in '{field_name}' is negative: {parsed}"))
    return msgs, parsed


def validate_date(
    value: Any, field_name: str,
    formats: Optional[List[str]] = None
) -> tuple[List[ValidationMessage], Optional[date]]:
    """
    Parse date from string. Tries multiple common formats.
    Returns (messages, parsed_date).
    """
    if value is None or str(value).strip() == "":
        return [], None

    if isinstance(value, (date, datetime)):
        d = value.date() if isinstance(value, datetime) else value
        return [], d

    raw = str(value).strip()
    default_formats = [
        "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y",
        "%m/%d/%Y", "%Y/%m/%d",
        "%d/%m/%y", "%d-%m-%y",
    ]
    for fmt in (formats or default_formats):
        try:
            return [], datetime.strptime(raw, fmt).date()
        except ValueError:
            continue

    return [_err("INVALID_DATE", field_name,
                 f"Cannot parse '{raw}' as a date for field '{field_name}'. "
                 f"Expected formats: YYYY-MM-DD, DD/MM/YYYY")], None


def validate_email(value: Any, field_name: str = "email") -> List[ValidationMessage]:
    if value is None or str(value).strip() == "":
        return []
    raw = str(value).strip()
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, raw):
        return [_warn("INVALID_EMAIL", field_name,
                      f"'{raw}' does not look like a valid email address")]
    return []


def validate_phone(value: Any, field_name: str = "phone") -> List[ValidationMessage]:
    if value is None or str(value).strip() == "":
        return []
    raw = str(value).strip()
    # Remove common formatting
    digits = re.sub(r"[\s\-\(\)\+\.]", "", raw)
    if not digits.isdigit():
        return [_warn("INVALID_PHONE", field_name,
                      f"'{raw}' contains non-digit characters in phone number")]
    if len(digits) < 7 or len(digits) > 15:
        return [_warn("SUSPICIOUS_PHONE", field_name,
                      f"Phone number '{raw}' has unusual length ({len(digits)} digits)")]
    return []


def validate_currency_code(
    value: Any, field_name: str,
    known_codes: Set[str]
) -> List[ValidationMessage]:
    if value is None or str(value).strip() == "":
        return []
    code = str(value).strip().upper()
    if code not in known_codes:
        return [_err("UNKNOWN_CURRENCY", field_name,
                     f"Currency code '{code}' is not in the system. "
                     f"Known: {', '.join(sorted(known_codes))}")]
    return []


def validate_uom(
    value: Any, field_name: str,
    known_uoms: Set[str]
) -> List[ValidationMessage]:
    if value is None or str(value).strip() == "":
        return []
    uom = str(value).strip()
    if uom not in known_uoms:
        return [_warn("UNKNOWN_UOM", field_name,
                      f"Unit of measure '{uom}' not found. "
                      f"It will be created automatically if possible.")]
    return []


def validate_discount_percent(value: Any, field_name: str = "discount_percent") -> tuple[List[ValidationMessage], Optional[Decimal]]:
    msgs, parsed = validate_numeric(value, field_name, allow_zero=True, allow_negative=False)
    if parsed is not None and parsed > 100:
        msgs.append(_err("DISCOUNT_EXCEEDS_100", field_name,
                         f"Discount percent {parsed} exceeds 100%"))
    return msgs, parsed


# ─── Batch-level duplicate detection ─────────────────────────────────────────

class DuplicateDetector:
    """
    Tracks seen values within the current import batch to detect duplicates
    before they hit the database UNIQUE constraint.
    """

    def __init__(self, field_name: str):
        self.field_name = field_name
        self._seen: Dict[str, int] = {}  # value → first row number

    def check(self, value: Any, row_number: int) -> List[ValidationMessage]:
        if value is None or str(value).strip() == "":
            return []
        key = str(value).strip().upper()
        if key in self._seen:
            return [_err("DUPLICATE_IN_BATCH", self.field_name,
                         f"Duplicate {self.field_name} '{value}' — "
                         f"first seen at row {self._seen[key]}")]
        self._seen[key] = row_number
        return []

    @property
    def seen_values(self) -> Set[str]:
        return set(self._seen.keys())


# ─── Row-level result ─────────────────────────────────────────────────────────

@dataclass
class RowResult:
    row_number:  int
    source_data: Dict[str, Any]
    messages:    List[ValidationMessage] = field(default_factory=list)
    mapped_data: Optional[Dict[str, Any]] = None
    entity_id:   Optional[str] = None
    is_skipped:  bool = False

    @property
    def has_errors(self) -> bool:
        return any(m.level == Level.ERROR for m in self.messages)

    @property
    def has_warnings(self) -> bool:
        return any(m.level == Level.WARNING for m in self.messages)

    @property
    def status(self) -> str:
        if self.has_errors:
            return "error"
        if self.is_skipped:
            return "skipped"
        if self.has_warnings:
            return "warning"
        return "ok"

    def add(self, msgs: List[ValidationMessage]) -> "RowResult":
        self.messages.extend(msgs)
        return self

    def to_dict(self) -> dict:
        return {
            "row_number":  self.row_number,
            "status":      self.status,
            "source_data": self.source_data,
            "mapped_data": self.mapped_data,
            "messages":    [m.to_dict() for m in self.messages],
            "entity_id":   str(self.entity_id) if self.entity_id else None,
        }
