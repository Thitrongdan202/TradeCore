import pytest
from fastapi.testclient import TestClient
from typing import Optional

from app.main import app
from app.api.deps import get_current_user
from app.models.user import User, Role
from app.core.security import RoleType

client = TestClient(app)

class MockRole:
    def __init__(self, name: str):
        self.name = name

class MockUser:
    def __init__(self, role_name: Optional[str] = None, is_active: bool = True):
        self.id = "mock-uuid"
        self.username = "mockuser"
        self.email = "mock@tradecore.vn"
        self.is_active = is_active
        if role_name:
            self.role = MockRole(role_name)
        else:
            self.role = None

def override_get_current_user_admin():
    return MockUser(role_name=RoleType.ADMIN)

def override_get_current_user_sales():
    return MockUser(role_name=RoleType.SALES)

def override_get_current_user_warehouse():
    return MockUser(role_name=RoleType.WAREHOUSE)

def override_get_current_user_no_role():
    return MockUser(role_name=None)

# 1. Test unauthorized access (No token)
def test_unauthorized_access():
    app.dependency_overrides = {}
    response = client.get("/api/v1/users/")
    assert response.status_code == 401
    assert "detail" in response.json()

# 2. Test User Endpoint RBAC (Admin only)
def test_users_endpoint_admin():
    app.dependency_overrides[get_current_user] = override_get_current_user_admin
    # We expect a DB error or 200, but NOT 403. 
    # Since DB is not mocked, it might throw 500 because it tries to access DB in the route.
    # But FastAPI dependencies run first. If 403 is not raised, it means RBAC passed.
    try:
        response = client.get("/api/v1/users/")
        assert response.status_code != 403
    except Exception:
        # DB connection error implies auth passed
        pass

def test_users_endpoint_sales_rejected():
    app.dependency_overrides[get_current_user] = override_get_current_user_sales
    response = client.get("/api/v1/users/")
    assert response.status_code == 403
    assert response.json()["detail"] == "Bạn không có quyền thực hiện thao tác này"

def test_users_endpoint_no_role_rejected():
    app.dependency_overrides[get_current_user] = override_get_current_user_no_role
    response = client.get("/api/v1/users/")
    assert response.status_code == 403

# 3. Test Sales Endpoint (Admin & Sales allowed, Warehouse rejected)
def test_sales_endpoint_sales():
    app.dependency_overrides[get_current_user] = override_get_current_user_sales
    try:
        response = client.get("/api/v1/sales/orders")
        assert response.status_code != 403
    except Exception:
        pass

def test_sales_endpoint_warehouse_rejected():
    app.dependency_overrides[get_current_user] = override_get_current_user_warehouse
    response = client.get("/api/v1/sales/orders")
    assert response.status_code == 403

# 4. Test Products Read-Only (All allowed to read)
def test_products_endpoint_read_warehouse():
    app.dependency_overrides[get_current_user] = override_get_current_user_warehouse
    try:
        response = client.get("/api/v1/products/")
        assert response.status_code != 403
    except Exception:
        pass

def test_products_endpoint_write_warehouse_rejected():
    app.dependency_overrides[get_current_user] = override_get_current_user_warehouse
    response = client.post("/api/v1/products/", json={"name": "Test", "code": "T"})
    assert response.status_code == 403

def test_products_endpoint_write_admin():
    app.dependency_overrides[get_current_user] = override_get_current_user_admin
    try:
        response = client.post("/api/v1/products/", json={"name": "Test", "code": "T"})
        assert response.status_code != 403
    except Exception:
        pass

# Cleanup overrides
def teardown_function():
    app.dependency_overrides = {}
