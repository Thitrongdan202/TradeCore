"""
Targeted repair: Re-encrypt the admin account's password using the current
TRADECORE_PASSWORD_ENCRYPTION_KEY so that verify_password("tradecore123", ...)
returns True.

This script is SAFE — it only modifies the encrypted_password of accounts
whose current password cannot be decrypted (stale/wrong key).

It does NOT touch accounts that already work.
It does NOT drop or recreate any table.
It is idempotent.
"""
import sys
import os
sys.path.insert(0, '.')

from app.core.database import SessionLocal
from app.models.user import User, UserRole, Role
from app.core.security import verify_password, get_password_hash
from sqlalchemy import select

# Map of username -> known dev password to repair
DEV_ACCOUNTS = {
    "admin": "tradecore123",
    "quanly01": "tradecore123",
    "kinhdoanh01": "tradecore123",
    "muahang01": "tradecore123",
    "kho01": "tradecore123",
    "xnk01": "tradecore123",
}

db = SessionLocal()
try:
    repaired = 0
    for username, known_password in DEV_ACCOUNTS.items():
        user = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
        if not user:
            print(f"[SKIP] {username}: not found in database")
            continue

        if verify_password(known_password, user.encrypted_password):
            print(f"[OK]   {username}: password already correct")
        else:
            print(f"[FIX]  {username}: re-encrypting password with current key")
            user.encrypted_password = get_password_hash(known_password)
            db.flush()
            repaired += 1

    db.commit()
    if repaired > 0:
        print(f"\nRepaired {repaired} account(s). Verifying again...")
        for username, known_password in DEV_ACCOUNTS.items():
            user = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
            if user:
                ok = verify_password(known_password, user.encrypted_password)
                print(f"  [{'+' if ok else 'X'}] {username}: verify={ok}")
    else:
        print("\nAll accounts are already correct. No changes made.")
finally:
    db.close()
