import sys
import os
sys.path.insert(0, '.')

from app.core.config import get_settings
settings = get_settings()

print("=== SETTINGS ===")
print("Encryption key loaded:", bool(settings.tradecore_password_encryption_key))
key = settings.tradecore_password_encryption_key.strip()
print("Key length:", len(key))
print("Key suffix (last 4):", key[-4:] if key else "EMPTY")

print()
print("=== SECURITY MODULE ===")
from app.core.security import encrypt_password, decrypt_password, verify_password, get_password_hash

test_pw = "tradecore123"
enc = get_password_hash(test_pw)
print("Encrypt succeeded:", bool(enc))
dec = decrypt_password(enc)
print("Decrypt matches:", dec == test_pw)
ver = verify_password(test_pw, enc)
print("verify_password result:", ver)

print()
print("=== DATABASE CHECK ===")
from app.core.database import SessionLocal
from app.models.user import User, UserRole, Role
from sqlalchemy import select

db = SessionLocal()
try:
    users_to_check = ["admin", "quanly01", "kinhdoanh01", "muahang01", "kho01", "xnk01"]
    for username in users_to_check:
        user = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
        if not user:
            print(f"[MISSING] {username} - NOT FOUND IN DATABASE")
            continue

        ep = user.encrypted_password
        ep_exists = bool(ep)
        ep_len = len(ep) if ep else 0
        is_active = user.is_active

        # Try verification
        try:
            ver_result = verify_password("tradecore123", ep)
        except Exception as e:
            ver_result = f"ERROR: {e}"

        # Get roles
        roles = db.execute(
            select(Role).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user.id)
        ).scalars().all()
        role_codes = [r.code for r in roles]

        status = "OK" if ver_result is True else "FAIL"
        print(f"[{status}] {username}: active={is_active}, ep_len={ep_len}, verify={ver_result}, roles={role_codes}")
finally:
    db.close()
