"""
TradeCore — Import CLI Runner

Usage:
    python scripts/import_data.py --help
    python scripts/import_data.py products  data/excel/products.xlsx
    python scripts/import_data.py customers data/excel/customers.xlsx --dry-run
    python scripts/import_data.py suppliers data/excel/suppliers.xlsx
    python scripts/import_data.py pricing   data/excel/pricing.xlsx --price-list "Bảng giá 2024"
    python scripts/import_data.py inventory data/excel/inventory.xlsx

Options:
    --sheet SHEET           Sheet name (default: first sheet)
    --skip-rows N           Skip N rows before header (default: 0)
    --dry-run               Validate only, do not write to DB
    --price-list NAME       PriceList name for pricing imports (default: "Standard")
    --output-json PATH      Save JSON report to file
    --col COL=FIELD         Override column mapping (repeatable)

Exit codes:
    0 = success (0 errors)
    1 = partial (some errors)
    2 = fatal error (import aborted)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Add backend/ to path so we can import app.*
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import get_db_context


ENTITY_IMPORTERS = {
    "products":  "app.importpipeline.importers.products:import_products",
    "customers": "app.importpipeline.importers.customers:import_customers",
    "suppliers": "app.importpipeline.importers.suppliers:import_suppliers",
    "pricing":   "app.importpipeline.importers.pricing:import_pricing",
    "inventory": "app.importpipeline.importers.inventory:import_inventory",
}


def _load_importer(entity: str):
    module_path, func_name = ENTITY_IMPORTERS[entity].split(":")
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, func_name)


def _parse_column_overrides(col_args: list) -> dict:
    """Parse ["SRC=target", ...] into {"SRC": "target"}"""
    result = {}
    for arg in (col_args or []):
        if "=" not in arg:
            print(f"WARNING: Ignoring invalid --col argument: {arg!r} (expected SRC=target)", file=sys.stderr)
            continue
        src, tgt = arg.split("=", 1)
        result[src.strip()] = tgt.strip()
    return result


def main():
    parser = argparse.ArgumentParser(
        description="TradeCore Import Pipeline — imports Excel/CSV data into the database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "entity",
        choices=list(ENTITY_IMPORTERS.keys()),
        help="Type of data to import",
    )
    parser.add_argument(
        "file",
        help="Path to Excel (.xlsx) or CSV (.csv) file",
    )
    parser.add_argument("--sheet",       default=None,       help="Sheet name (default: first sheet)")
    parser.add_argument("--skip-rows",   type=int, default=0, help="Rows to skip before header")
    parser.add_argument("--dry-run",     action="store_true",  help="Validate only, no DB writes")
    parser.add_argument("--price-list",  default="Standard",   help="PriceList name (pricing imports only)")
    parser.add_argument("--output-json", default=None,          help="Write JSON report to this file")
    parser.add_argument("--col",         action="append",        help="Column mapping override: SRC=target")

    args = parser.parse_args()

    if not os.path.isfile(args.file):
        print(f"ERROR: File not found: {args.file}", file=sys.stderr)
        sys.exit(2)

    importer = _load_importer(args.entity)
    col_overrides = _parse_column_overrides(args.col)

    print(f"\n{'='*60}")
    print(f"TradeCore Import — {args.entity.upper()}")
    print(f"File    : {args.file}")
    print(f"Sheet   : {args.sheet or '(first sheet)'}")
    print(f"DryRun  : {args.dry_run}")
    print(f"{'='*60}\n")

    try:
        with get_db_context() as db:
            kwargs = dict(
                db=db,
                file_path=args.file,
                sheet_name=args.sheet,
                skip_rows=args.skip_rows,
                dry_run=args.dry_run,
                column_map_overrides=col_overrides if col_overrides else None,
            )
            if args.entity == "pricing":
                kwargs["price_list_name"] = args.price_list

            report = importer(**kwargs)

        print(report.print_summary())

        if args.output_json:
            with open(args.output_json, "w", encoding="utf-8") as f:
                json.dump(report.to_dict(), f, ensure_ascii=False, indent=2, default=str)
            print(f"\nJSON report written to: {args.output_json}")

        # Exit code
        if report.error_rows == 0:
            sys.exit(0)
        elif report.imported_rows > 0:
            sys.exit(1)  # partial success
        else:
            sys.exit(2)  # nothing imported

    except Exception as exc:
        print(f"\nFATAL ERROR: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    main()
