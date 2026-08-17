"""
TradeCore — Import Pipeline: Excel/CSV Reader

Reads Excel (.xlsx) and CSV files into a normalized list of dicts.
Each row becomes: {column_name: raw_value, "_row_number": int}

Features:
  - Detects file type from extension
  - Normalizes column header names (strip whitespace, lowercase, replace spaces with _)
  - Preserves original column names in a header map for error messages
  - Handles multiple sheets (uses first sheet or named sheet)
  - Strips leading/trailing whitespace from string values
  - Converts NaN/None to None
  - Returns raw strings — parsing/validation is done by validators
"""
from __future__ import annotations

import csv
import hashlib
import io
import os
from pathlib import Path
from typing import Dict, Iterator, List, Optional

import pandas as pd


def _sha256(path: str) -> str:
    """Compute SHA-256 of a file for deduplication tracking."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _normalize_header(name: str) -> str:
    """
    Normalize a column header to a safe Python identifier-like string.
    Examples:
      "Mã hàng hóa"  → "ma_hang_hoa"   (Vietnamese)
      "Product Code" → "product_code"
      "  Name  "     → "name"
    """
    import unicodedata
    s = str(name).strip()
    # Decompose Unicode and keep ASCII
    nfkd = unicodedata.normalize("NFKD", s)
    # Remove combining characters (diacritics)
    ascii_str = "".join(c for c in nfkd if not unicodedata.combining(c))
    # Replace special characters with underscore
    safe = "".join(c if c.isalnum() else "_" for c in ascii_str.lower())
    # Collapse multiple underscores and strip leading/trailing
    import re
    safe = re.sub(r"_+", "_", safe).strip("_")
    return safe or f"col_{id(name)}"


def _clean_value(v) -> Optional[str]:
    """Convert a cell value to str or None."""
    if v is None:
        return None
    if isinstance(v, float):
        import math
        if math.isnan(v):
            return None
        # Return as string without trailing .0 for integers stored as float
        if v == int(v):
            return str(int(v))
        return str(v)
    return str(v).strip() or None


class SourceReader:
    """
    Reads an Excel or CSV file and returns rows as dicts with normalized keys.

    Usage:
        reader = SourceReader("data/excel/products.xlsx")
        for row in reader.iter_rows():
            print(row["ma_hang"])   # normalized key
    """

    def __init__(
        self,
        file_path: str,
        sheet_name: Optional[str] = None,
        skip_rows: int = 0,
        header_row: int = 0,
        encoding: str = "utf-8-sig",
    ):
        self.file_path = str(file_path)
        self.sheet_name = sheet_name
        self.skip_rows = skip_rows
        self.header_row = header_row
        self.encoding = encoding

        self._file_hash: Optional[str] = None
        self._raw_headers: List[str] = []
        self._normalized_to_raw: Dict[str, str] = {}

    @property
    def file_hash(self) -> str:
        if self._file_hash is None:
            self._file_hash = _sha256(self.file_path)
        return self._file_hash

    @property
    def file_name(self) -> str:
        return os.path.basename(self.file_path)

    def _read_dataframe(self) -> pd.DataFrame:
        ext = Path(self.file_path).suffix.lower()
        if ext in (".xlsx", ".xls", ".xlsm", ".ods"):
            df = pd.read_excel(
                self.file_path,
                sheet_name=self.sheet_name or 0,
                skiprows=self.skip_rows,
                header=self.header_row,
                dtype=str,          # Keep everything as string — validators do parsing
                keep_default_na=False,
                na_values=[""],
            )
        elif ext == ".csv":
            df = pd.read_csv(
                self.file_path,
                encoding=self.encoding,
                skiprows=self.skip_rows,
                header=self.header_row,
                dtype=str,
                keep_default_na=False,
                na_values=[""],
            )
        else:
            raise ValueError(f"Unsupported file type: {ext}. Expected .xlsx, .xls, .csv, .ods")

        return df

    def get_sheets(self) -> List[str]:
        """Return list of sheet names for Excel files."""
        ext = Path(self.file_path).suffix.lower()
        if ext in (".xlsx", ".xls", ".xlsm"):
            xl = pd.ExcelFile(self.file_path)
            return xl.sheet_names
        return ["sheet1"]

    def iter_rows(self) -> Iterator[Dict[str, Optional[str]]]:
        """
        Yield each data row as a dict with normalized header keys.
        The special key '_row_number' contains the 1-based row index
        (counting from the first data row after the header, not from row 1 in the file).
        """
        df = self._read_dataframe()

        # Build header mapping
        raw_headers = list(df.columns)
        self._raw_headers = raw_headers
        self._normalized_to_raw = {}
        normalized_headers = []

        for h in raw_headers:
            norm = _normalize_header(str(h))
            # Handle duplicate normalized names by appending suffix
            if norm in self._normalized_to_raw:
                suffix = 2
                candidate = f"{norm}_{suffix}"
                while candidate in self._normalized_to_raw:
                    suffix += 1
                    candidate = f"{norm}_{suffix}"
                norm = candidate
            self._normalized_to_raw[norm] = str(h)
            normalized_headers.append(norm)

        # Rename DataFrame columns
        df.columns = normalized_headers

        # Drop rows that are entirely empty
        df = df.dropna(how="all")

        for idx, row in df.iterrows():
            row_num = int(idx) + 1  # 1-based
            row_dict: Dict[str, Optional[str]] = {"_row_number": row_num}
            for norm_key in normalized_headers:
                v = row.get(norm_key)
                row_dict[norm_key] = _clean_value(v)
            yield row_dict

    def preview(self, n: int = 5) -> List[Dict[str, Optional[str]]]:
        """Return first N rows for inspection."""
        rows = []
        for i, row in enumerate(self.iter_rows()):
            if i >= n:
                break
            rows.append(row)
        return rows

    @property
    def header_map(self) -> Dict[str, str]:
        """Returns mapping of normalized_header → original_header."""
        return dict(self._normalized_to_raw)
