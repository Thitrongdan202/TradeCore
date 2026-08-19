import os
import secrets
import string
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import SessionLocal
from app.models.user import User, Role, Permission, RolePermission, UserRole
from app.core.security import get_password_hash
from app.core.permissions import RESOURCES, ACTION_NAMES

def seed_permissions(db: Session):
    print("Seeding permissions...")
    # 1. Create permissions based on RESOURCES
    perm_cache = {}
    for res_key, res_data in RESOURCES.items():
        res_name = res_data["name"]
        for action in res_data["actions"]:
            action_name = ACTION_NAMES[action]
            
            # Check if exists
            perm = db.execute(
                select(Permission).where(Permission.resource == res_key, Permission.action == action)
            ).scalar_one_or_none()
            
            if not perm:
                perm = Permission(
                    resource=res_key,
                    action=action,
                    name=f"{action_name} {res_name.lower()}"
                )
                db.add(perm)
                db.flush()
            perm_cache[(res_key, action)] = perm
    return perm_cache

def seed_roles(db: Session, perm_cache: dict):
    print("Seeding roles...")
    # System Admin
    admin_role = db.execute(select(Role).where(Role.code == "ADMIN")).scalar_one_or_none()
    if not admin_role:
        admin_role = Role(name="Quản trị viên", code="ADMIN", is_system=True, is_active=True, description="Toàn quyền hệ thống")
        db.add(admin_role)
        db.flush()

    # Assign ALL permissions to admin
    current_role_perms = db.execute(select(RolePermission.permission_id).where(RolePermission.role_id == admin_role.id)).scalars().all()
    current_perm_set = set(current_role_perms)
    
    for perm in perm_cache.values():
        if perm.id not in current_perm_set:
            db.add(RolePermission(role_id=admin_role.id, permission_id=perm.id))

    return admin_role

def seed_admin():
    db = SessionLocal()
    try:
        # Seed permissions and roles
        perm_cache = seed_permissions(db)
        admin_role = seed_roles(db, perm_cache)

        # Seed admin user
        admin_user = db.execute(select(User).where(User.username == "admin")).scalar_one_or_none()
        password = os.getenv("ADMIN_PASSWORD")
        
        if not admin_user:
            if not password:
                alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
                password = ''.join(secrets.choice(alphabet) for i in range(16))
                print(f"\n[WARNING] ADMIN_PASSWORD not found in environment. Generating secure random password.")

            admin_user = User(
                username="admin",
                email="admin@tradecore.vn",
                full_name="Quản Trị Viên",
                hashed_password=get_password_hash(password),
                is_active=True
            )
            db.add(admin_user)
            db.flush()
            print(f"\n==========================================")
            print(f"Admin user created successfully")
            print(f"Username: admin")
            print(f"Password: {password}")
            print(f"==========================================\n")
        else:
            print("Admin user already exists.")

        # Assign user to admin role if not already
        has_role = db.execute(
            select(UserRole).where(UserRole.user_id == admin_user.id, UserRole.role_id == admin_role.id)
        ).scalar_one_or_none()
        
        if not has_role:
            db.add(UserRole(user_id=admin_user.id, role_id=admin_role.id))
            print("Admin role assigned to admin user.")

        db.commit()
    except Exception as e:
        print(f"Error seeding admin: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_admin()
