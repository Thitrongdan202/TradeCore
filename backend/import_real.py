import os
import sys

# Setup Django/FastAPI path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.core.database import SessionLocal
from app.importpipeline.importers.products import import_products

FILE_PATH = r"C:\Users\thitr\.gemini\antigravity\scratch\tradecore\data\0908. GIÁ ĐẠI LÝ_ LACASA.xlsx"

def run_import():
    print("\n=== REAL IMPORT PIPELINE ===")
    db = SessionLocal()
    try:
        report = import_products(
            db=db,
            file_path=FILE_PATH,
            dry_run=False,
            skip_rows=9
        )
        print("Import Report:")
        print(f"  Total rows read: {report.total_rows}")
        print(f"  Imported (valid): {report.imported_rows}")
        print(f"  Skipped: {report.skipped_rows}")
        print(f"  Errors: {report.error_rows}")
        print(f"  Warnings: {report.warning_rows}")
        
        if report.error_rows > 0:
            print("Sample Errors:")
            for r in report.row_results:
                if r.has_errors:
                    print(f"  Row {r.row_number}: {[m.message for m in r.messages if m.level.name == 'ERROR']}")
        db.commit()
        print("Transaction committed successfully.")
        
    except Exception as e:
        print(f"Import failed: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_import()
