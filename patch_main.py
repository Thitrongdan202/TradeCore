import os

file_path = "backend/app/main.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Add imports for the new routers
if "from app.api.account import router as account_router" not in content:
    content = content.replace(
        "from app.api.users import router as users_router",
        "from app.api.users import router as users_router\nfrom app.api.account import router as account_router\nfrom app.api.import_data import router as import_router"
    )

# Register the routers
if 'app.include_router(account_router, prefix="/api/v1/account", tags=["account"])' not in content:
    content = content.replace(
        'app.include_router(users_router, prefix="/api/v1/users", tags=["users"])',
        'app.include_router(users_router, prefix="/api/v1/users", tags=["users"])\napp.include_router(account_router, prefix="/api/v1/account", tags=["account"])\napp.include_router(import_router, prefix="/api/v1/imports", tags=["imports"])'
    )

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
