import os
from openpyxl import load_workbook

data_dir = "data"
files = os.listdir(data_dir)
excel_file = [f for f in files if f.endswith(".xlsx")][0]
excel_path = os.path.join(data_dir, excel_file)

wb = load_workbook(excel_path, data_only=True)
sheet = wb.active

if hasattr(sheet, '_images') and len(sheet._images) > 0:
    img = sheet._images[0]
    print(type(img._data))
    if callable(img._data):
        data = img._data()
    else:
        data = img._data
    print(f"Data length: {len(data)}")
    with open("test_img.png", "wb") as f:
        f.write(data)
    print("Wrote test_img.png")
