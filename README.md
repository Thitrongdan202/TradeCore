# TradeCore

Hệ thống quản lý bán hàng, mua hàng, kho và xuất nhập khẩu cho doanh nghiệp thương mại.

## Công nghệ

- Frontend: React + TypeScript + Vite
- Backend: Python + FastAPI + Uvicorn
- ORM: SQLAlchemy
- Migration: Alembic
- Database: PostgreSQL 16
- Container: Docker Compose

---

# 1. Yêu cầu

Cài sẵn:

- Python 3.13
- Node.js + npm
- Docker Desktop

Kiểm tra:

```powershell
python --version
node --version
npm --version
docker --version
docker compose version
```

Docker Desktop phải đang chạy trước khi khởi động PostgreSQL.

---

# 2. Mở project bằng PyCharm

Mở thư mục gốc:

```text
TradeCore/
```

Không mở riêng thư mục `backend/` nếu muốn chạy cả frontend và backend.

Cấu trúc chính:

```text
TradeCore/
├── backend/             # FastAPI
├── src/                 # React + Vite
├── public/
├── data/                # Dữ liệu Excel/import
├── docs/
├── docker-compose.yml
├── package.json
└── README.md
```

---

# 3. Cài Frontend

Mở Terminal trong PyCharm tại thư mục gốc:

```powershell
npm install
```

---

# 4. Tạo môi trường Python

Trong PyCharm:

**Settings → Project → Python Interpreter**

Tạo virtual environment:

```text
backend/.venv
```

Hoặc dùng Terminal:

```powershell
cd backend
python -m venv .venv
```

Kích hoạt PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Kiểm tra:

```powershell
python -c "import sys; print(sys.executable)"
```

Đường dẫn phải trỏ tới:

```text
backend\.venv\Scripts\python.exe
```

---

# 5. Cài thư viện Backend

Trong Terminal:

```powershell
cd backend
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---

# 6. Khởi động PostgreSQL

Mở Docker Desktop và chờ Docker Engine chạy.

Từ thư mục gốc TradeCore:

```powershell
docker compose up -d postgres
```

Kiểm tra:

```powershell
docker compose ps
```

Xem log PostgreSQL:

```powershell
docker compose logs postgres --tail=50
```

PostgreSQL phải ở trạng thái `Up`.

---

# 7. Khởi tạo Database

Trong Terminal:

```powershell
cd backend
```

Kích hoạt môi trường:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Chạy migration:

```powershell
python -m alembic upgrade head
```

Nạp dữ liệu nền:

```powershell
python scripts/seed.py
```

---

# 8. Chạy Backend bằng PyCharm

## Cách 1 — Chạy bằng Terminal

Trong Terminal PyCharm:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

ReDoc:

```text
http://127.0.0.1:8000/redoc
```

## Cách 2 — Chạy bằng Run Configuration của PyCharm

Tạo:

**Run → Edit Configurations → + → Python**

Thiết lập:

```text
Name:
TradeCore Backend

Module name:
uvicorn

Parameters:
app.main:app --reload

Working directory:
backend

Python interpreter:
backend/.venv
```

Sau đó bấm:

```text
Run ▶
```

---

# 9. Chạy Frontend

Mở Terminal thứ hai tại thư mục gốc TradeCore:

```powershell
npm run dev
```

Vite thường chạy tại:

```text
http://localhost:5173
```

Mở địa chỉ mà Vite hiển thị trong Terminal.

---

# 10. Chạy toàn bộ hệ thống

Cần 3 tiến trình:

## Terminal 1 — PostgreSQL

```powershell
docker compose up -d postgres
```

## Terminal 2 — Backend

```powershell
cd backend
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

## Terminal 3 — Frontend

```powershell
npm run dev
```

Luồng hệ thống:

```text
React + Vite
     ↓
FastAPI
     ↓
PostgreSQL
```

---

# 11. Kiểm tra hệ thống

## Kiểm tra PostgreSQL

```powershell
docker compose ps
```

## Kiểm tra Backend

Mở:

```text
http://127.0.0.1:8000/docs
```

## Kiểm tra Frontend

Mở:

```text
http://localhost:5173
```

---

# 12. Chạy Test

Trong:

```text
backend/
```

chạy:

```powershell
python -m pytest
```

---

# 13. Kiểm tra Frontend

Từ thư mục gốc:

```powershell
npm run lint
```

Build:

```powershell
npm run build
```

---

# 14. Import dữ liệu Excel

Dữ liệu Excel của công ty được đặt trong thư mục dữ liệu của project, theo cấu hình importer hiện tại.

Ví dụ:

```text
data/
└── 0908. GIÁ ĐẠI LÝ_LACASA.xlsx
```

Hoặc dữ liệu import của backend:

```text
backend/data/
```

Không chỉnh sửa file Excel gốc.

Luôn kiểm tra dữ liệu bằng chế độ `dry-run` trước khi import thật.

Xem cách sử dụng importer:

```powershell
cd backend
python scripts/import_data.py --help
```

Chỉ sử dụng đúng các tham số mà lệnh `--help` hiển thị.

---

# 15. Quy trình Import an toàn

```text
Excel
  ↓
Đọc dữ liệu
  ↓
Kiểm tra / Mapping
  ↓
Dry Run
  ↓
Xem lỗi + cảnh báo
  ↓
Xác nhận
  ↓
Import thật
  ↓
PostgreSQL
```

Không import thật nếu chưa kiểm tra:

- Mã sản phẩm
- Mã hàng cũ
- Mã hàng mới
- Khách hàng
- Nhà cung cấp
- Giá
- Loại tiền
- Đơn vị tính
- Ngày hiệu lực
- Dữ liệu trùng
- Hình ảnh sản phẩm

---

# 16. Bảng giá và hình ảnh sản phẩm

Bảng giá của công ty có thể chứa:

- Số báo giá
- Ngày báo giá
- Thời gian áp dụng
- Nhóm sản phẩm
- Mã hàng mới
- Mã hàng cũ
- Hình ảnh sản phẩm
- Thông tin sản phẩm
- Giá đại lý
- Ghi chú VAT
- Công thức Excel như XLOOKUP

Không coi đây là một bảng `sản phẩm + giá` đơn giản.

Hình ảnh phải được xử lý riêng và không nên lưu trực tiếp dưới dạng dữ liệu lớn trong PostgreSQL nếu không cần thiết.

---

# 17. Database Migration

Tạo migration:

```powershell
cd backend
python -m alembic revision --autogenerate -m "describe change"
```

Chạy migration:

```powershell
python -m alembic upgrade head
```

Xem migration hiện tại:

```powershell
python -m alembic current
```

---

# 18. Dừng hệ thống

Dừng Backend:

```text
Ctrl + C
```

Dừng Frontend:

```text
Ctrl + C
```

Dừng PostgreSQL:

```powershell
docker compose stop postgres
```

Dừng toàn bộ Docker Compose:

```powershell
docker compose down
```

---

# 19. Khởi động lại lần sau

## PostgreSQL

```powershell
docker compose up -d postgres
```

## Backend

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

## Frontend

```powershell
npm run dev
```

---

# 20. Tài khoản và phân quyền

TradeCore có hệ thống:

- Quản trị viên
- Quản lý
- Nhân viên bán hàng
- Nhân viên mua hàng
- Nhân viên kho
- Nhân viên xuất nhập khẩu

Phân quyền phải được kiểm tra ở Backend.

Frontend chỉ dùng để điều khiển giao diện theo quyền; không được coi việc ẩn menu là biện pháp bảo mật.

Không đưa mật khẩu thật, token hoặc khóa bí mật vào Git.

---

# 21. Git

Kiểm tra:

```powershell
git status
```

Xem thay đổi:

```powershell
git diff
```

Commit:

```powershell
git add .
git commit -m "describe change"
```

Kiểm tra lại:

```powershell
git status
```

Các file local không nên commit:

```text
backend/.venv/
__pycache__/
*.pyc
.pytest_cache/
.env
.idea/
.codex/
```

---

# 22. Thứ tự chạy nhanh

Nếu máy đã cài đầy đủ, thông thường chỉ cần:

### Bước 1

```powershell
docker compose up -d postgres
```

### Bước 2

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

### Bước 3

Mở Terminal mới:

```powershell
npm run dev
```

### Bước 4

Mở:

```text
http://localhost:5173
```

API:

```text
http://127.0.0.1:8000/docs
```

---

# Current Status

TradeCore currently includes:

- React + Vite frontend
- FastAPI backend
- PostgreSQL
- Docker Compose
- Alembic
- Reference data seeding
- Authentication
- Role-based access control
- Business APIs
- Excel/CSV import pipeline
- Odoo migration preparation
- Automated tests
- Product pricing support under development

The project is currently under active development.
