# React + TypeScript + Vite

<<<<<<< Updated upstream
Hệ thống quản lý bán hàng, mua hàng, kho và xuất nhập khẩu cho doanh nghiệp.
=======
This template provides a minimal setup to get React working in Vite with HMR and some Oxlint rules.
>>>>>>> Stashed changes

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

<<<<<<< Updated upstream
# 1. Yêu cầu môi trường
=======
The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).
>>>>>>> Stashed changes

## Expanding the Oxlint configuration

<<<<<<< Updated upstream
- Python 3.13
- Node.js
- npm
- Docker Desktop
- Git
- PyCharm (khuyến nghị)

Kiểm tra:

```powershell
python --version
node --version
npm --version
docker --version
docker compose version
git --version
```

Docker Desktop phải đang chạy trước khi khởi động PostgreSQL.

---

# 2. Mở project bằng PyCharm

Mở thư mục gốc:

```text
TradeCore/
```

Không mở riêng thư mục `backend/` nếu muốn làm việc với cả frontend và backend.

Cấu trúc chính:

```text
TradeCore/
├── backend/              # FastAPI backend
├── src/                  # React + Vite frontend
├── public/
├── data/                 # Dữ liệu Excel/CSV nguồn
├── docs/
├── docker-compose.yml
├── package.json
├── package-lock.json
├── vite.config.ts
└── README.md
```

---

# 3. Cài đặt lần đầu

## 3.1. Cài frontend

Mở Terminal tại thư mục gốc:

```powershell
npm install
```

---

## 3.2. Tạo Python virtual environment

Vào thư mục backend:

```powershell
cd backend
```

Tạo môi trường:

```powershell
python -m venv .venv
```

---

## 3.3. Kích hoạt Python virtual environment

PowerShell có thể chặn `Activate.ps1`. Cho phép script trong phiên hiện tại:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Kích hoạt:

```powershell
.\.venv\Scripts\Activate.ps1
```

Kiểm tra:

```powershell
python -c "import sys; print(sys.executable)"
```

Đường dẫn phải trỏ vào:

```text
backend\.venv\Scripts\python.exe
```

---

## 3.4. Cài thư viện backend

Trong `backend/`:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Kiểm tra Alembic:

```powershell
python -m alembic --version
```

---

# 4. Khởi động PostgreSQL bằng Docker

Mở Docker Desktop và chờ Docker Engine chạy hoàn toàn.

Kiểm tra:

```powershell
docker info
```

Từ thư mục gốc TradeCore:

```powershell
docker compose up -d postgres
```

Kiểm tra:

```powershell
docker compose ps
```

Xem log:

```powershell
docker compose logs postgres --tail=50
```

PostgreSQL phải ở trạng thái `Up`.

---

# 5. Khởi tạo database

Chỉ thực hiện khi cài lần đầu hoặc khi cần cập nhật database.

Vào backend:

```powershell
cd backend
```

Kích hoạt `.venv`:

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

Không cần chạy `seed.py` ở mỗi lần khởi động.

---

# 6. Chạy Backend

Mở một Terminal riêng:

```powershell
cd backend
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
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

Giữ Terminal này mở khi phát triển backend.

---

# 7. Chạy Frontend

Mở Terminal thứ hai tại thư mục gốc:

```powershell
npm run dev
```

Vite thường chạy tại:

```text
http://localhost:5173
```

Mở địa chỉ mà Vite hiển thị trong Terminal.

Giữ Terminal này mở khi phát triển frontend.

---

# 8. Chạy toàn bộ TradeCore

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

Địa chỉ:

```text
Frontend:
http://localhost:5173

Backend:
http://127.0.0.1:8000

Swagger:
http://127.0.0.1:8000/docs
```

---

# 9. Chạy bằng PyCharm

## Backend

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

Bấm **Run**.

## Frontend

Có thể dùng Terminal:

```powershell
npm run dev
```

Hoặc tạo NPM Run Configuration với script:

```text
dev
```

---

# 10. Kiểm thử

## Backend

Trong `backend/`:

```powershell
python -m pytest -v
```

## Frontend lint

Từ thư mục gốc:

```powershell
npm run lint
```

## Frontend build

```powershell
npm run build
```

---

# 11. Database migration

Tạo migration:

```powershell
cd backend
python -m alembic revision --autogenerate -m "describe change"
```

Áp dụng:

```powershell
python -m alembic upgrade head
```

Xem migration hiện tại:

```powershell
python -m alembic current
```

---

# 12. Nhập dữ liệu Excel

Dữ liệu doanh nghiệp có thể được nhập thông qua:

```text
Cài đặt → Nhập dữ liệu
```

Nguồn có thể gồm:

- Excel
- CSV
- Dữ liệu xuất từ Odoo

Quy trình:

```text
Chọn loại dữ liệu
        ↓
Tải tệp lên
        ↓
Kiểm tra dữ liệu
        ↓
Dry Run
        ↓
Xem lỗi và cảnh báo
        ↓
Xác nhận
        ↓
Import vào PostgreSQL
```

Không sửa file Excel gốc.

Không import thật khi chưa kiểm tra dry-run.

---

# 13. Bảng giá và hình ảnh

Bảng giá doanh nghiệp có thể chứa:

- Số báo giá
- Ngày báo giá
- Thời gian áp dụng
- Nhóm sản phẩm
- Mã hàng mới
- Mã hàng cũ
- Hình ảnh sản phẩm
- Thông tin sản phẩm
- Giá
- VAT
- Công thức Excel
- Dữ liệu tham chiếu từ workbook khác

Hình ảnh sản phẩm được quản lý riêng với dữ liệu sản phẩm.

---

# 14. Thoát Backend

Trong Terminal đang chạy Uvicorn:

```text
Ctrl + C
```

---

# 15. Thoát Frontend

Trong Terminal đang chạy Vite:

```text
Ctrl + C
```

---

# 16. Dừng PostgreSQL

Dừng riêng PostgreSQL nhưng giữ dữ liệu:

```powershell
docker compose stop postgres
```

Kiểm tra:

```powershell
docker compose ps
```

---

# 17. Dừng toàn bộ Docker Compose

```powershell
docker compose down
```

Không dùng:

```powershell
docker compose down -v
```

trừ khi bạn thực sự muốn xóa volume dữ liệu PostgreSQL.

---

# 18. Thoát toàn bộ môi trường phát triển

1. Terminal Backend → `Ctrl + C`
2. Terminal Frontend → `Ctrl + C`
3. Dừng PostgreSQL:

```powershell
docker compose stop postgres
```

Hoặc:

```powershell
docker compose down
```

Sau đó có thể đóng PyCharm và Docker Desktop.

---

# 19. Khởi động lại lần sau

Không cần tạo lại `.venv` hoặc cài lại npm.

## PostgreSQL

```powershell
docker compose up -d postgres
```

## Backend

```powershell
cd backend
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

## Frontend

Mở Terminal mới:

```powershell
npm run dev
```

---

# 20. Tài khoản và phân quyền

TradeCore hỗ trợ:

- Tài khoản người dùng
- Vai trò động
- Phân quyền theo chức năng
- Đổi mật khẩu
- Đặt lại mật khẩu
- Cài đặt công ty
- Nhật ký hoạt động
- Hỗ trợ kỹ thuật có kiểm soát

Quản trị viên có thể tạo vai trò và gán quyền cho người dùng.

Quyền được kiểm tra tại backend, không chỉ ẩn menu frontend.

---

# 21. File môi trường và Git

Không commit:

```text
backend/.venv/
node_modules/
dist/
__pycache__/
*.pyc
.pytest_cache/
.env
.idea/
.codex/
```

Không commit:

- Mật khẩu
- API key
- JWT secret
- Database password
- Token
- Dữ liệu nhạy cảm
- File Excel dữ liệu kinh doanh nếu repository không được phép chứa chúng

`.env.example` có thể được commit.

---

# 22. Kiến trúc

```text
                    TradeCore
                        │
          ┌─────────────┴─────────────┐
          │                           │
     React + Vite                 FastAPI
          │                           │
          └─────────────┬─────────────┘
                        │
                    PostgreSQL
                        │
                      Docker
```

---

# 23. Truy cập local

Frontend:

```text
http://localhost:5173
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

Giai đoạn phát triển chỉ chạy local.

Khi triển khai trên máy của công ty và cần truy cập từ xa, có thể sử dụng mạng riêng/VPN như Tailscale. Không công khai PostgreSQL `5432` ra Internet.

---

# 24. Trạng thái dự án

TradeCore hiện có:

- React + Vite
- FastAPI
- PostgreSQL
- Docker Compose
- Alembic
- Xác thực người dùng
- Vai trò động
- Phân quyền theo chức năng
- Quản lý tài khoản
- Đổi mật khẩu
- Đặt lại mật khẩu
- Cài đặt công ty
- Nhật ký hoạt động
- Phiên hỗ trợ kỹ thuật
- Nhập dữ liệu Excel/CSV
- Chuẩn bị dữ liệu từ Odoo
- Kiểm thử tự động

Các nghiệp vụ đang tiếp tục phát triển:

- Sản phẩm
- Khách hàng
- Nhà cung cấp
- Kho hàng
- Bảng giá
- Báo giá
- Bán hàng
- Mua hàng
- Nhập khẩu
- Xuất khẩu
- Lô hàng
- Container
- Báo cáo
=======
If you are developing a production application, we recommend enabling type-aware lint rules by installing `oxlint-tsgolint` and editing `.oxlintrc.json`:

```json
{
  "$schema": "./node_modules/oxlint/configuration_schema.json",
  "plugins": ["react", "typescript", "oxc"],
  "options": {
    "typeAware": true
  },
  "rules": {
    "react/rules-of-hooks": "error",
    "react/only-export-components": ["warn", { "allowConstantExport": true }]
  }
}
```

See the [Oxlint rules documentation](https://oxc.rs/docs/guide/usage/linter/rules) for the full list of rules and categories.
>>>>>>> Stashed changes
