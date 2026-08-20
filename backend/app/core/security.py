"""
TradeCore — Security Module
Handles reversible password encryption (AES-128-CBC with HMAC via Fernet)
and JWT token generation.
"""
from datetime import datetime, timedelta, timezone
import jwt
from enum import Enum
from cryptography.fernet import Fernet, InvalidToken
from app.core.config import get_settings

settings = get_settings()

if not settings.tradecore_password_encryption_key:
    raise ValueError("TRADECORE_PASSWORD_ENCRYPTION_KEY environment variable is missing!")

fernet = Fernet(settings.tradecore_password_encryption_key.encode('utf-8'))

class RoleType(str, Enum):
    ADMIN = "Quản trị viên"
    MANAGER = "Quản lý"
    SALES = "Nhân viên bán hàng"
    PURCHASING = "Nhân viên mua hàng"
    WAREHOUSE = "Nhân viên kho"
    IMPORT_EXPORT = "Nhân viên xuất nhập khẩu"


def encrypt_password(plain_password: str) -> str:
    """Encrypt a plaintext password."""
    return fernet.encrypt(plain_password.encode('utf-8')).decode('utf-8')


def decrypt_password(encrypted_password: str) -> str:
    """Decrypt an encrypted password."""
    try:
        return fernet.decrypt(encrypted_password.encode('utf-8')).decode('utf-8')
    except InvalidToken:
        return "" # Fail safely if it can't be decrypted


def verify_password(plain_password: str, encrypted_password: str) -> bool:
    """Verify a plain password against an encrypted one."""
    decrypted = decrypt_password(encrypted_password)
    if not decrypted:
        # If decryption fails (e.g. old bcrypt hash), fail safely.
        return False
    return plain_password == decrypted


# Keep this for backward compatibility with old code that hasn't been updated yet
def get_password_hash(password: str) -> str:
    return encrypt_password(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    secret_key = getattr(settings, "jwt_secret", "fallback-secret-key-change-me")
    algorithm = getattr(settings, "jwt_algorithm", "HS256")
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return encoded_jwt
