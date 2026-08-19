import os
import re

api_dir = 'backend/app/api'
for f in os.listdir(api_dir):
    if f.endswith('.py'):
        path = os.path.join(api_dir, f)
        with open(path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Replace import
        content = re.sub(r'require_role', 'require_permission', content)
        
        # Replace usage: require_permission(['ADMIN', 'MANAGER']) -> require_permission('overview', 'view')
        content = re.sub(r'require_permission\(\[[^\]]+\]\)', 'require_permission("overview", "view")', content)
        
        with open(path, 'w', encoding='utf-8') as file:
            file.write(content)
print('Done patching require_role')
