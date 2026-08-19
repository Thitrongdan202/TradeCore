import os
import re

file_path = "backend/app/api/users.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix the duplicate logging in create_user (around line 322)
content = content.replace(
    'log_activity(db, "user_created", user_id=current_user.id, entity_id=str(user.id), request=request)\n    log_activity(db, "user_updated", user_id=current_user.id, entity_id=str(user.id), request=request)',
    'log_activity(db, "user_created", user_id=current_user.id, entity_id=str(user.id), request=request)'
)

# Fix the duplicate logging in update_user (around line 400)
content = content.replace(
    'log_activity(db, "user_created", user_id=current_user.id, entity_id=str(user.id), request=request)\n    log_activity(db, "user_updated", user_id=current_user.id, entity_id=str(user.id), request=request)',
    'log_activity(db, "user_updated", user_id=current_user.id, entity_id=str(user.id), request=request)'
)

# Append new endpoints at the end of the file
new_endpoints = """

from pydantic import BaseModel
class AdminPasswordReset(BaseModel):
    new_password: str

@router.put("/{user_id}/reset-password", response_model=MessageResponse, summary="Admin đặt lại mật khẩu")
def admin_reset_password(
    user_id: uuid.UUID,
    payload: AdminPasswordReset,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user", "update")),
):
    \"\"\"Admin resets another user's password.\"\"\"
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    log_activity(db, "admin_password_reset", user_id=current_user.id, entity_id=str(user.id), request=request, details={"target_username": user.username})
    return MessageResponse(message=f"Đã đặt lại mật khẩu cho '{user.username}'")


@router.get("/{user_id}/effective-permissions", response_model=List[PermissionResponse], summary="Lấy quyền hiệu lực của người dùng")
def get_user_effective_permissions(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user", "view")),
):
    \"\"\"Get all effective permissions for a user.\"\"\"
    perms = db.execute(
        select(Permission)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(UserRole, UserRole.role_id == RolePermission.role_id)
        .where(UserRole.user_id == user_id)
    ).scalars().all()
    
    # Deduplicate permissions
    seen = set()
    unique_perms = []
    for p in perms:
        if p.id not in seen:
            seen.add(p.id)
            unique_perms.append(p)
            
    return unique_perms
"""

content += new_endpoints

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
