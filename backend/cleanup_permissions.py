import os
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import SessionLocal
from app.models.user import Permission, RolePermission
from app.core.permissions import RESOURCES, ACTION_NAMES

def cleanup_and_seed():
    db = SessionLocal()
    try:
        # 1. Fetch all valid combinations
        valid_perms = set()
        for res, data in RESOURCES.items():
            for action in data["actions"]:
                valid_perms.add((res, action))

        # 2. Get all existing perms from DB
        all_db_perms = db.execute(select(Permission)).scalars().all()
        
        for p in all_db_perms:
            if (p.resource, p.action) not in valid_perms:
                print(f"Deleting obsolete permission: {p.resource}:{p.action}")
                db.delete(p)
            elif p.name != f"{ACTION_NAMES[p.action]} {RESOURCES[p.resource]['name'].lower()}":
                # Update name if it changed
                p.name = f"{ACTION_NAMES[p.action]} {RESOURCES[p.resource]['name'].lower()}"

        db.commit()

        # 3. Import seed_admin and run it to add missing perms
        from seed_admin import seed_permissions, seed_roles
        perm_cache = seed_permissions(db)
        seed_roles(db, perm_cache)
        db.commit()
        print("Permissions cleaned up and re-seeded successfully.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_and_seed()
