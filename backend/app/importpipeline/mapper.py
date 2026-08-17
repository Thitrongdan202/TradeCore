"""
TradeCore — Import Pipeline: Column Mapper

Maps raw Excel/CSV column names to TradeCore field names.

Why this exists:
  Companies name columns differently in every file. This module provides
  a flexible mapping layer between source column names and the TradeCore
  domain model, without requiring the user to rename their spreadsheet columns.

Mapping strategy:
  1. Exact match against aliases list (case-insensitive, strip whitespace)
  2. Normalized match (diacritics removed, spaces→underscores)
  3. Fuzzy match (optional — for typo tolerance)
  4. Manual override (user-provided column_map dict)

Usage:
    mapper = ColumnMapper(PRODUCT_COLUMN_MAP)
    mapped = mapper.map_row(raw_row)
    # mapped["code"], mapped["name"], etc.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


# ─── Known column aliases for each entity ────────────────────────────────────
# Each entry: target_field → list of known source column name variants
# Variants are matched case-insensitively with normalized whitespace/diacritics

PRODUCT_COLUMN_MAP: Dict[str, List[str]] = {
    # Code / identifier
    "code": [
        "ma_hang", "ma_hang_hoa", "ma_vat_tu", "ma_sp", "ma_san_pham",
        "product_code", "item_code", "code", "sku", "default_code",
        "ma", "item_no", "item_number", "hang_hoa", "ma_hang_hoa_vt",
        "ma_hang_moi",
    ],
    # Name
    "name": [
        "ten_hang", "ten_hang_hoa", "ten_vat_tu", "ten_sp", "ten_san_pham",
        "product_name", "name", "description", "ten", "mo_ta",
        "ten_hang_hoa", "product", "item_name", "thong_tin_san_pham",
    ],
    # English name
    "name_en": [
        "ten_tieng_anh", "english_name", "name_en", "name_english",
        "ten_anh", "product_name_en",
    ],
    # Category
    "category": [
        "nhom_hang", "loai_hang", "danh_muc", "category", "product_category",
        "nhom", "nhom_vat_tu", "phan_loai", "nhom_sp",
    ],
    # Unit of measure (sale)
    "uom": [
        "don_vi_tinh", "dvt", "don_vi", "unit", "uom", "uom_id",
        "unit_of_measure", "don_vi_ban", "dvt_ban",
    ],
    # Unit of measure (purchase)
    "purchase_uom": [
        "don_vi_mua", "dvt_mua", "purchase_unit", "purchase_uom",
        "don_vi_tinh_mua",
    ],
    # Cost price
    "cost_price": [
        "gia_von", "gia_nhap", "cost", "cost_price", "unit_cost",
        "gia_mua", "purchase_price", "gia_cost",
    ],
    # List/sale price
    "list_price": [
        "gia_ban", "gia_list", "list_price", "sale_price", "unit_price",
        "gia_niem_yet", "gia_ban_le", "price", "gia_dai_ly_km_chua_vat",
    ],
    # Barcode
    "barcode": [
        "barcode", "ma_vach", "ean", "ean13", "upc",
    ],
    # Weight
    "weight_kg": [
        "trong_luong", "weight", "weight_kg", "kl", "khoi_luong",
    ],
    # Min stock
    "min_stock": [
        "ton_toi_thieu", "min_stock", "reorder_point", "diem_dat_hang",
        "minimum_stock", "so_luong_toi_thieu",
    ],
    # Max stock
    "max_stock": [
        "ton_toi_da", "max_stock", "maximum_stock", "so_luong_toi_da",
    ],
    # Description
    "description": [
        "mo_ta_chi_tiet", "ghi_chu", "notes", "note",
        "remarks", "specifications",
    ],
    # Active
    "is_active": [
        "trang_thai", "active", "is_active", "status",
    ],
}

CUSTOMER_COLUMN_MAP: Dict[str, List[str]] = {
    "code": [
        "ma_kh", "ma_khach_hang", "customer_code", "code", "ma",
        "khach_hang_ma", "customer_id",
    ],
    "name": [
        "ten_kh", "ten_khach_hang", "customer_name", "name", "ten",
        "company_name", "ten_cong_ty",
    ],
    "short_name": [
        "ten_viet_tat", "short_name", "alias", "ten_rut_gon",
    ],
    "tax_code": [
        "ma_so_thue", "mst", "tax_code", "vat_number", "ma_thue",
    ],
    "phone": [
        "so_dien_thoai", "dien_thoai", "phone", "tel", "mobile",
        "so_dt", "dt",
    ],
    "email": [
        "email", "e_mail", "dia_chi_email",
    ],
    "address": [
        "dia_chi", "address", "diachi", "so_nha_duong",
    ],
    "city": [
        "thanh_pho", "city", "quan_huyen", "district",
    ],
    "province": [
        "tinh_thanh", "province", "tinh", "thanh_pho_tinh",
    ],
    "country": [
        "quoc_gia", "country", "country_code",
    ],
    "credit_limit": [
        "han_muc_tin_dung", "credit_limit", "han_muc",
    ],
    "payment_term": [
        "dieu_kien_thanh_toan", "payment_term", "ky_han_thanh_toan",
    ],
    "notes": [
        "ghi_chu", "notes", "note", "remarks",
    ],
}

SUPPLIER_COLUMN_MAP: Dict[str, List[str]] = {
    "code": [
        "ma_ncc", "ma_nha_cung_cap", "supplier_code", "code", "ma",
        "vendor_code",
    ],
    "name": [
        "ten_ncc", "ten_nha_cung_cap", "supplier_name", "name", "ten",
        "vendor_name", "company_name",
    ],
    "short_name": [
        "ten_viet_tat", "short_name",
    ],
    "country": [
        "quoc_gia", "country", "nuoc",
    ],
    "contact_name": [
        "nguoi_lien_lac", "contact_name", "contact", "ten_lien_lac",
    ],
    "phone": [
        "so_dien_thoai", "phone", "tel",
    ],
    "email": [
        "email",
    ],
    "address": [
        "dia_chi", "address",
    ],
    "tax_code": [
        "ma_so_thue", "tax_code", "vat",
    ],
    "payment_term": [
        "dieu_kien_thanh_toan", "payment_term",
    ],
    "notes": [
        "ghi_chu", "notes",
    ],
}

PRICE_COLUMN_MAP: Dict[str, List[str]] = {
    "product_code": [
        "ma_hang", "ma_sp", "ma_hang_hoa", "product_code", "code",
        "item_code", "sku",
    ],
    "product_name": [
        "ten_hang", "ten_sp", "product_name", "name",
    ],
    "price": [
        "don_gia", "gia_ban", "price", "unit_price", "gia",
        "gia_niem_yet", "list_price",
    ],
    "currency": [
        "tien_te", "currency", "don_vi_tien", "loai_tien",
    ],
    "uom": [
        "don_vi_tinh", "dvt", "unit", "uom",
    ],
    "min_qty": [
        "so_luong_toi_thieu", "min_qty", "min_quantity", "quantity_from",
        "tu_so_luong",
    ],
    "effective_from": [
        "ngay_hieu_luc", "effective_from", "valid_from", "tu_ngay",
    ],
    "effective_to": [
        "ngay_het_hieu_luc", "effective_to", "valid_to", "den_ngay",
    ],
    "customer_code": [
        "ma_kh", "customer_code", "khach_hang",
    ],
}

INVENTORY_COLUMN_MAP: Dict[str, List[str]] = {
    "product_code": [
        "ma_hang", "ma_sp", "ma_hang_hoa", "product_code", "code",
    ],
    "product_name": [
        "ten_hang", "ten_sp", "product_name", "name",
    ],
    "warehouse_code": [
        "ma_kho", "kho", "warehouse", "warehouse_code",
    ],
    "location_code": [
        "vi_tri", "location", "location_code", "bin",
    ],
    "qty": [
        "so_luong", "ton_kho", "quantity", "qty", "sl",
        "so_luong_ton", "ton",
    ],
    "uom": [
        "don_vi_tinh", "dvt", "unit", "uom",
    ],
    "cost_price": [
        "gia_von", "cost_price", "don_gia_von",
    ],
    "as_of_date": [
        "ngay", "ngay_chot", "date", "as_of_date", "ky_chot",
    ],
}


# ─── ColumnMapper ─────────────────────────────────────────────────────────────

class ColumnMapper:
    """
    Maps normalized source column names to TradeCore field names
    using a configurable alias dictionary.
    """

    def __init__(
        self,
        alias_map: Dict[str, List[str]],
        extra_map: Optional[Dict[str, str]] = None,
    ):
        """
        alias_map:  target_field → [alias1, alias2, ...]
        extra_map:  manual override: source_column → target_field
        """
        self._target_to_aliases = alias_map
        self._extra_map = extra_map or {}

        # Build reverse lookup: alias (lower, normalized) → target_field
        self._lookup: Dict[str, str] = {}
        for target, aliases in alias_map.items():
            for alias in aliases:
                self._lookup[self._normalize(alias)] = target
        # Manual overrides take priority
        for src, tgt in self._extra_map.items():
            self._lookup[self._normalize(src)] = tgt

    @staticmethod
    def _normalize(s: str) -> str:
        import re, unicodedata
        nfkd = unicodedata.normalize("NFKD", s.strip().lower())
        ascii_str = "".join(c for c in nfkd if not unicodedata.combining(c))
        safe = "".join(c if c.isalnum() else "_" for c in ascii_str)
        return re.sub(r"_+", "_", safe).strip("_")

    def resolve_column(self, source_column: str) -> Optional[str]:
        """Return the target field name for a given source column, or None."""
        return self._lookup.get(self._normalize(source_column))

    def map_row(self, raw_row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map a raw row dict (normalized keys) to a TradeCore field dict.
        Unmapped columns are stored under '_extra' for JSONB raw_extra.
        The '_row_number' key is always preserved.
        """
        mapped: Dict[str, Any] = {}
        extra: Dict[str, Any] = {}

        for raw_key, value in raw_row.items():
            if raw_key == "_row_number":
                mapped["_row_number"] = value
                continue
            target = self.resolve_column(raw_key)
            if target:
                # First mapping wins (don't overwrite with a second alias match)
                if target not in mapped:
                    mapped[target] = value
            else:
                extra[raw_key] = value

        if extra:
            mapped["_extra"] = extra

        return mapped

    def report_unmapped(self, sample_row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Given a sample row, report which columns are mapped and which are not.
        Useful for previewing mappings before a full import.
        """
        result = {"mapped": {}, "unmapped": []}
        for key in sample_row:
            if key.startswith("_"):
                continue
            target = self.resolve_column(key)
            if target:
                result["mapped"][key] = target
            else:
                result["unmapped"].append(key)
        return result
