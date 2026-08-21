"""
TradeCore — API Authorization Tests (Dynamic RBAC)

Tests that backend authorization correctly:
  - Allows authenticated users who have the required permission
  - Rejects authenticated users who lack the required permission (403)
  - Rejects unauthenticated requests (401)

Architecture note:
  require_permission() creates a new closure each call, so dependency_overrides
  on the returned callable won't work. Instead we:
    1. Override get_current_user to bypass JWT
    2. Patch get_user_permissions to control what permissions the mock user has
"""
import uuid
import pytest
from unittest.mock import patch
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_current_user


def make_mock_user(uid=None):
    """Create a minimal User-like object for DI mocking."""
    class _User:
        id = uid or uuid.UUID("00000000-0000-0000-0000-000000000001")
        username = "mockuser"
        email = "mockuser@tradecore.vn"
        full_name = "Mock User"
        is_active = True
        user_roles = []
        activity_logs = []
        support_sessions = []
        password_resets = []
    return _User()


MOCK_USER = make_mock_user()


def dep_mock_user():
    return MOCK_USER


def teardown_function():
    app.dependency_overrides = {}


# ── 1. Unauthenticated ───────────────────────────────────────────────────────

def test_unauthorized_access_no_token():
    """Accessing any protected endpoint without a token must return 401."""
    app.dependency_overrides = {}
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/api/v1/users/")
    assert response.status_code == 401


# ── 2. Users Endpoint RBAC ───────────────────────────────────────────────────

def test_users_endpoint_allowed():
    """Authenticated user WITH user:view permission → not 401/403."""
    app.dependency_overrides[get_current_user] = dep_mock_user

    # Grant all permissions to the mock user
    all_permissions = {("user", "view"), ("user", "create"), ("role", "view")}
    with patch("app.api.deps.get_user_permissions", return_value=all_permissions):
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/users/")
        assert response.status_code not in (401, 403)


def test_users_endpoint_forbidden():
    """Authenticated user WITHOUT user:view permission → 403."""
    app.dependency_overrides[get_current_user] = dep_mock_user

    # Return empty permissions = no access
    with patch("app.api.deps.get_user_permissions", return_value=set()):
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/users/")
        assert response.status_code == 403


# ── 3. Sales Endpoint RBAC ───────────────────────────────────────────────────

def test_sales_endpoint_forbidden():
    """User WITHOUT overview:view permission → 403 (sales router requires overview:view)."""
    app.dependency_overrides[get_current_user] = dep_mock_user

    with patch("app.api.deps.get_user_permissions", return_value=set()):
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/sales/orders")
        assert response.status_code == 403


def test_sales_endpoint_allowed():
    """User WITH overview:view → not 401/403."""
    app.dependency_overrides[get_current_user] = dep_mock_user

    with patch("app.api.deps.get_user_permissions", return_value={("overview", "view")}):
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/sales/orders")
        assert response.status_code not in (401, 403)


# ── 4. Products Write RBAC ────────────────────────────────────────────────────

def test_products_write_forbidden():
    """POST /products without overview:view permission → 403."""
    app.dependency_overrides[get_current_user] = dep_mock_user

    with patch("app.api.deps.get_user_permissions", return_value=set()):
        client = TestClient(app, raise_server_exceptions=False)
        response = client.post("/api/v1/products/", json={"name": "Test", "code": "T"})
        assert response.status_code == 403


def test_products_write_allowed():
    """POST /products WITH overview:view → not 401/403."""
    app.dependency_overrides[get_current_user] = dep_mock_user

    all_perms = {("overview", "view")}
    with patch("app.api.deps.get_user_permissions", return_value=all_perms):
        client = TestClient(app, raise_server_exceptions=False)
        response = client.post("/api/v1/products/", json={"name": "Test", "code": "T"})
        assert response.status_code not in (401, 403)
