import os

file_path = "backend/app/api/users.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Add decrypt_password import
if "from app.core.security import get_password_hash" in content:
    content = content.replace(
        "from app.core.security import get_password_hash",
        "from app.core.security import get_password_hash, decrypt_password"
    )

new_endpoint = """

@router.get("/{user_id}/password", summary="Xem mật khẩu người dùng (dành cho Admin)")
def view_user_password(
    user_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user", "password_view")),
):
    \"\"\"Return the plaintext password for a user. Only allowed for admins with specific permission.\"\"\"
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    plain_pass = decrypt_password(user.encrypted_password)
    if not plain_pass:
        raise HTTPException(status_code=400, detail="Không thể giải mã mật khẩu (có thể là mật khẩu cũ)")

    log_activity(db, "password_viewed", user_id=current_user.id, entity_id=str(user.id), request=request, details={"target_username": user.username})
    
    return {"password": plain_pass}
"""

if "def view_user_password" not in content:
    content += new_endpoint

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
