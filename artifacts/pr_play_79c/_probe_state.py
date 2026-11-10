import json
import urllib.request

body = json.load(urllib.request.urlopen("http://127.0.0.1:8096/api/state", timeout=20))
ui = body.get("public_state", {}).get("ui") or body.get("ui") or {}
# search keys
text = json.dumps(body)
for key in ("campaign_started", "campaign_can_start", "active_scene"):
    idx = text.find(key)
    print(key, text[idx:idx+80] if idx >= 0 else "MISSING")
print("top", list(body)[:12])
