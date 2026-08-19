import os
import re

files = [
    "src/App.tsx",
    "src/pages/Settings/AuditLogSettings.tsx",
    "src/pages/Settings/PermissionsSettings.tsx",
    "src/pages/Settings/SettingsLayout.tsx"
]

for f in files:
    with open(f, "r", encoding="utf-8") as file:
        content = file.read()
    
    # Remove unused imports
    if f == "src/App.tsx":
        content = content.replace("import { BrowserRouter, Routes, Route, Navigate }", "import { BrowserRouter, Routes, Route }")
    elif f == "src/pages/Settings/PermissionsSettings.tsx":
        content = content.replace("import React, { useState, useEffect }", "import { useState, useEffect }")
        content = content.replace("{perms.map", "{(perms as any[]).map")
    elif f == "src/pages/Settings/AuditLogSettings.tsx":
        content = content.replace("import React, { useState, useEffect }", "import { useState, useEffect }")
    elif f == "src/pages/Settings/SettingsLayout.tsx":
        content = content.replace("import React from 'react';\n", "")
        
    with open(f, "w", encoding="utf-8") as file:
        file.write(content)
