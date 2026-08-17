import os
import re

API_DIR = "app/api"

ROLE_MAP = {
    "users.py": "[RoleType.ADMIN]",
    "sales.py": "[RoleType.ADMIN, RoleType.MANAGER, RoleType.SALES]",
    "purchasing.py": "[RoleType.ADMIN, RoleType.MANAGER, RoleType.PURCHASING]",
    "inventory.py": "[RoleType.ADMIN, RoleType.MANAGER, RoleType.WAREHOUSE]",
    "pricing.py": "[RoleType.ADMIN, RoleType.MANAGER, RoleType.SALES]",
}

READ_ROLES = "[RoleType.ADMIN, RoleType.MANAGER, RoleType.SALES, RoleType.PURCHASING, RoleType.WAREHOUSE, RoleType.IMPORT_EXPORT]"
WRITE_ROLES = "[RoleType.ADMIN, RoleType.MANAGER]"

for filename in os.listdir(API_DIR):
    if not filename.endswith(".py"):
        continue
        
    if filename in ["auth.py", "deps.py", "dashboard.py"]:
        continue
        
    filepath = os.path.join(API_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if "require_role" not in content:
        content = re.sub(
            r"from app\.api\.deps import get_current_user, get_db",
            "from app.api.deps import get_current_user, get_db, require_role",
            content
        )
    
    if "RoleType" not in content:
        content = content.replace(
            "from app.api.deps import",
            "from app.core.security import RoleType\nfrom app.api.deps import"
        )

    # We can use regex to find endpoints: @router.(get|post|put|delete|patch)(...) 
    # and then the function definition, and then the Depends(get_current_user)
    
    # Actually, simpler: split by "@router."
    parts = content.split("@router.")
    new_parts = [parts[0]]
    
    for part in parts[1:]:
        method = part.split('("')[0].strip() # get, post, put, delete, patch
        
        roles = None
        if filename in ROLE_MAP:
            roles = ROLE_MAP[filename]
        else:
            # products.py or partners.py
            if method == "get":
                roles = READ_ROLES
            else:
                roles = WRITE_ROLES
                
        # replace get_current_user with require_role(roles)
        part = part.replace("Depends(get_current_user)", f"Depends(require_role({roles}))")
        new_parts.append(part)
        
    new_content = "@router.".join(new_parts)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)
        
print("RBAC applied successfully!")
