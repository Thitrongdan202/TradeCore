import os
from openpyxl import load_workbook

data_dir = "data"
files = os.listdir(data_dir)
excel_file = [f for f in files if f.endswith(".xlsx")][0]
excel_path = os.path.join(data_dir, excel_file)

wb = load_workbook(excel_path, data_only=True)
sheet = wb.active

with open("analyze_images.txt", "w", encoding="utf-8") as f:
    if hasattr(sheet, '_images'):
        images = sheet._images
        f.write(f"Found {len(images)} images in the sheet.\n")
        for i, img in enumerate(images[:5]): # Check first 5 images
            # openpyxl image anchors usually have `_from.row` (0-indexed) or similar
            if hasattr(img, 'anchor') and img.anchor:
                try:
                    # In newer openpyxl: img.anchor._from.row
                    # In older openpyxl: img.anchor.from_.row
                    if hasattr(img.anchor, '_from'):
                        row = img.anchor._from.row
                        col = img.anchor._from.col
                    else:
                        row = img.anchor.from_.row
                        col = img.anchor.from_.col
                    f.write(f"Image {i} is anchored at row {row}, col {col}\n")
                except Exception as e:
                    f.write(f"Image {i} anchor error: {e}\n")
            else:
                f.write(f"Image {i} has no anchor info.\n")
    else:
        f.write("No _images attribute found on sheet.\n")
