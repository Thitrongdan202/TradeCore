import urllib.request
import urllib.parse
import json
import sys

BASE = "http://localhost:8000"

def test_login(username, password):
    data = urllib.parse.urlencode({"username": username, "password": password}).encode()
    req = urllib.request.Request(
        f"{BASE}/api/v1/auth/login",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as r:
            resp = json.loads(r.read())
            return True, resp.get("access_token", "")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return False, f"HTTP {e.code}: {body}"
    except Exception as e:
        return False, str(e)

def test_me(token):
    req = urllib.request.Request(
        f"{BASE}/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        method="GET"
    )
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

users = ["admin", "quanly01", "kinhdoanh01", "muahang01", "kho01", "xnk01"]
tokens = {}

print("=== LOGIN TEST ===")
all_pass = True
for u in users:
    ok, result = test_login(u, "tradecore123")
    if ok:
        tokens[u] = result
        print(f"[OK]  {u}: login succeeded")
    else:
        print(f"[FAIL] {u}: {result}")
        all_pass = False

print()
print("=== /me TEST (admin) ===")
if "admin" in tokens:
    me = test_me(tokens["admin"])
    print(json.dumps(me, indent=2, ensure_ascii=True))
else:
    print("No admin token - skipping /me test")

print()
print("=== SUMMARY ===")
print("All logins passed:", all_pass)
