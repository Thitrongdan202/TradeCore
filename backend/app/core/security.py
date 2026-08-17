"""
TradeCore — Security Module
Handles password hashing and verification.
"""
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
import jwt
from enum import Enum
from app.core.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class RoleType(str, Enum):
    ADMIN = "Quản trị viên"
    MANAGER = "Quản lý"
    SALES = "Nhân viên bán hàng"
    PURCHASING = "Nhân viên mua hàng"
    WAREHOUSE = "Nhân viên kho"
    IMPORT_EXPORT = "Nhân viên xuất nhập khẩu"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed one."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate a hashed version of the password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    # Since settings doesn't have a secret key yet, we will provide a default
    # But we should add it to settings later.
    secret_key = getattr(settings, "jwt_secret", "fallback-secret-key-change-me")
    algorithm = getattr(settings, "jwt_algorithm", "HS256")
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return encoded_jwt
