# TradeFlow — Phần mềm Quản lý Thương mại Nội bộ

TradeFlow là hệ thống quản lý nội bộ cho doanh nghiệp thương mại, bao gồm:
- **Xác thực & RBAC động**: đăng nhập, phân quyền theo vai trò, phân quyền theo tài nguyên/hành động
- **Quản lý tài khoản & người dùng**: tạo, sửa, phân vai trò, xem mật khẩu (có quyền)
- **Cài đặt hệ thống**: công ty, kiểm tra nhật ký hoạt động, phiên hỗ trợ
- **Import dữ liệu**: sản phẩm, khách hàng, tồn kho, bảng giá

---

## Mục lục

1. [Yêu cầu hệ thống](#1-yêu-cầu-hệ-thống)
2. [Cài đặt môi trường](#2-cài-đặt-môi-trường)
3. [Khởi động PostgreSQL](#3-khởi-động-postgresql)
4. [Cấu hình biến môi trường](#4-cấu-hình-biến-môi-trường)
5. [Khởi động backend (FastAPI)](#5-khởi-động-backend-fastapi)
6. [Alembic migration](#6-alembic-migration)
7. [Seed dữ liệu phát triển](#7-seed-dữ-liệu-phát-triển)
8. [Đăng nhập môi trường phát triển](#8-đăng-nhập-môi-trường-phát-triển)
9. [Khởi động frontend (React)](#9-khởi-động-frontend-react)
10. [Kiểm tra (Tests)](#10-kiểm-tra-tests)
11. [Dừng các service](#11-dừng-các-service)
12. [Xử lý sự cố xác thực](#12-xử-lý-sự-cố-xác-thực)
13. [Cấu trúc dự án](#13-cấu-trúc-dự-án)
14. [Lưu ý bảo mật](#14-lưu-ý-bảo-mật)

---

## 1. Yêu cầu hệ thống

| Thành phần | Phiên bản tối thiểu |
|---|---|
| Python | 3.11+ |
| Node.js | 18+ |
| PostgreSQL | 14+ |
| npm | 9+ |

---

## 2. Cài đặt môi trường

### Backend Python

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
```

### Frontend Node

```bash
# Từ thư mục gốc dự án:
npm install
```

---

## 3. Khởi động PostgreSQL

### Tùy chọn A — Docker (khuyên dùng cho phát triển)

```bash
docker run -d \
  --name tradeflow-postgres \
  -e POSTGRES_USER=tradecore \
  -e POSTGRES_PASSWORD=tradecore_dev_pw \
  -e POSTGRES_DB=tradecore \
  -p 5432:5432 \
  postgres:16
```

### Tùy chọn B — PostgreSQL cài trực tiếp

Tạo database và user thủ công:

```sql
CREATE USER tradecore WITH PASSWORD 'tradecore_dev_pw';
CREATE DATABASE tradecore OWNER tradecore;
```

> **Lưu ý**: Password mặc định chỉ dùng cho môi trường phát triển.  
> Không dùng `tradecore_dev_pw` trong production.

---

## 4. Cấu hình biến môi trường

```bash
cd backend
cp .env.example .env
```

Chỉnh sửa `backend/.env`. Các biến bắt buộc:

| Biến | Mô tả |
|---|---|
| `DATABASE_URL` | URL kết nối PostgreSQL |
| `JWT_SECRET` | Secret key để ký JWT token |
| `TRADECORE_PASSWORD_ENCRYPTION_KEY` | Fernet key 32-byte base64 (mã hóa mật khẩu) |

### Tạo encryption key mới

```bash
cd backend
.venv\Scripts\python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

> ⚠️ **QUAN TRỌNG**: `TRADECORE_PASSWORD_ENCRYPTION_KEY` KHÔNG được commit vào Git.  
> Key này được dùng để mã hóa và giải mã tất cả mật khẩu người dùng.  
> Nếu thay đổi key sau khi đã tạo tài khoản, tất cả mật khẩu cũ sẽ không giải mã được.  
> Chạy `repair_passwords.py` để re-encrypt trong trường hợp đổi key.

---

## 5. Khởi động backend (FastAPI)

```bash
cd backend
.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

Backend chạy tại: http://localhost:8000  
Swagger UI: http://localhost:8000/docs

---

## 6. Alembic migration

```bash
cd backend

# Chạy tất cả migration
.venv\Scripts\alembic upgrade head

# Xem trạng thái
.venv\Scripts\alembic current

# Tạo migration mới (sau khi thay đổi model)
.venv\Scripts\alembic revision --autogenerate -m "mô tả thay đổi"
```

---

## 7. Seed dữ liệu phát triển

```bash
cd backend
.venv\Scripts\python seed_admin.py
```

Script này là idempotent — có thể chạy nhiều lần mà không tạo duplicate.

Tạo:
- Tất cả permissions theo `RESOURCES` trong `app/core/permissions.py`
- Vai trò hệ thống `ADMIN` với đầy đủ quyền
- Các vai trò phát triển: `QUANLY`, `KINHDOANH`, `MUAHANG`, `KHO`, `XNK`
- Tài khoản `admin` với mật khẩu từ `ADMIN_PASSWORD` env var (hoặc random nếu không có)
- Các tài khoản test phát triển (chỉ khi `ENVIRONMENT=development`)

---

## 8. Đăng nhập môi trường phát triển

> ⚠️ **CHỈ DÙNG CHO MÔI TRƯỜNG PHÁT TRIỂN CỤC BỘ**.  
> Không dùng các tài khoản này trong staging hoặc production.

Sau khi chạy `seed_admin.py`, các tài khoản sau có thể đăng nhập:

| Username | Vai trò | Mật khẩu dev |
|---|---|---|
| `admin` | Quản trị viên (toàn quyền) | Từ `ADMIN_PASSWORD` env var |
| `quanly01` | Quản lý | `tradecore123` |
| `kinhdoanh01` | Nhân viên kinh doanh | `tradecore123` |
| `muahang01` | Nhân viên mua hàng | `tradecore123` |
| `kho01` | Nhân viên kho | `tradecore123` |
| `xnk01` | Nhân viên xuất nhập khẩu | `tradecore123` |

> **Mật khẩu admin**: Đặt `ADMIN_PASSWORD=<mật_khẩu>` trong `backend/.env` trước khi seed.  
> Nếu không có, seed script sẽ tự tạo mật khẩu ngẫu nhiên và in ra terminal.

### Kiểm tra đăng nhập qua API

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=admin&password=<mật_khẩu>"

# Lấy thông tin user hiện tại
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
```

---

## 9. Khởi động frontend (React)

```bash
# Từ thư mục gốc dự án:
npm run dev
```

Frontend chạy tại: http://localhost:5173

---

## 10. Kiểm tra (Tests)

### Backend

```bash
cd backend

# Kiểm tra cú pháp Python
.venv\Scripts\python -m compileall app

# Chạy toàn bộ test suite
.venv\Scripts\python -m pytest -v

# Kết quả mong đợi: 67 passed
```

### Frontend

```bash
# Lint (kiểm tra code style)
npm run lint

# Build production
npm run build
```

### Kiểm tra xác thực thực tế (cần backend đang chạy)

```bash
cd backend
.venv\Scripts\python test_api_login.py
```

---

## 11. Dừng các service

### Dừng backend Uvicorn

```
Ctrl + C
```

### Dừng frontend Vite

```
Ctrl + C
```

### Dừng Docker PostgreSQL

```bash
docker stop tradeflow-postgres
docker start tradeflow-postgres  # Khởi động lại khi cần
```

---

## 12. Xử lý sự cố xác thực

### Không đăng nhập được

**Bước 1**: Kiểm tra biến môi trường

```bash
cd backend
.venv\Scripts\python -c "from app.core.config import get_settings; s = get_settings(); print('Key loaded:', bool(s.tradecore_password_encryption_key))"
```

**Bước 2**: Chẩn đoán tài khoản trong database

```bash
cd backend
.venv\Scripts\python diagnose_auth.py
```

**Bước 3**: Nếu cột `verify=False` — key mã hóa đã thay đổi, chạy:

```bash
cd backend
.venv\Scripts\python repair_passwords.py
```

Script này sẽ re-encrypt tất cả mật khẩu dev (`tradecore123`) dùng key hiện tại mà không xóa dữ liệu.

### Lỗi "TRADECORE_PASSWORD_ENCRYPTION_KEY is missing"

Đảm bảo `backend/.env` tồn tại và có giá trị hợp lệ cho `TRADECORE_PASSWORD_ENCRYPTION_KEY`.

Tạo key mới:

```bash
cd backend
.venv\Scripts\python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

> ⚠️ Nếu tạo key mới sau khi đã tồn tại dữ liệu, PHẢI chạy `repair_passwords.py` để re-encrypt lại.

### Lỗi kết nối database

Kiểm tra PostgreSQL đang chạy:

```bash
docker ps | grep postgres
# hoặc
pg_isready -h localhost -p 5432
```

---

## 13. Tính năng: Bảng giá / Báo giá (Pricing Module)

Module Bảng giá được thiết kế riêng biệt để tương thích với cấu trúc báo giá của công ty (0908. GIÁ ĐẠI LÝ_LACASA.xlsx).

**Các tính năng nổi bật:**
- **Tải lên Excel (Upload)**: Xử lý tự động file Excel báo giá.
- **Tự động trích xuất metadata**: Lấy số báo giá, ngày báo giá, điều kiện áp dụng, thông tin VAT từ 8 dòng đầu tiên.
- **Tự động trích xuất hình ảnh (Image Extraction)**: Đọc hình ảnh sản phẩm được chèn bên trong file Excel, đối chiếu và lưu vào local storage `/api/v1/storage/products`.
- **So sánh tự động (Comparison)**: So sánh hai báo giá giữa các kỳ để phát hiện tự động: Tăng giá, Giảm giá, Không đổi, Sản phẩm mới, Ngừng áp dụng.
- **Tải file gốc**: Cho phép tải về đúng file Excel gốc (`.xlsx`) đã dùng để upload.

---

## 14. Cấu trúc dự án

```
tradecore/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI routers (auth, users, products, ...)
│   │   ├── core/          # Config, security, database, permissions
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── schemas/       # Pydantic schemas
│   │   └── importpipeline/ # Data import pipeline
│   ├── alembic/           # Database migrations
│   ├── tests/             # Pytest test suite
│   ├── seed_admin.py      # Development seed script
│   ├── repair_passwords.py # Re-encrypt passwords after key change
│   ├── diagnose_auth.py   # Authentication diagnostic tool
│   ├── pytest.ini         # Pytest configuration
│   ├── .env.example       # Environment variable template
│   └── requirements.txt
├── src/                   # React frontend
│   ├── components/
│   ├── contexts/          # AuthContext, theme
│   ├── layouts/           # Sidebar, Header
│   └── pages/             # Login, Settings, Dashboard, ...
├── data/                  # Local company data files (NOT tracked in Git)
└── scripts/               # Utility scripts
```

---

## 14. Lưu ý bảo mật

- `backend/.env` **KHÔNG được commit** vào Git (được ignore qua `.gitignore`)
- `TRADECORE_PASSWORD_ENCRYPTION_KEY` chỉ nằm trong `.env` cục bộ
- `data/` (file Excel công ty) **KHÔNG được commit** vào Git
- Tài khoản phát triển (`tradecore123`) **KHÔNG** được dùng trong production
- `seed_admin.py` tạo tài khoản test chỉ khi `ENVIRONMENT=development`
- JWT secret nên được thay đổi thành key ngẫu nhiên đủ dài (≥32 bytes) trong production
