import json
from pathlib import Path
p = Path("artifacts/pr_play_79c/browser_data/session.json")
text = p.read_text(encoding="utf-8")
print("mtime bytes", p.stat().st_size)
for needle in ("last_publication", "last_background", "Hello, Gate Guard", "Gate Guard says"):
    print(needle, text.find(needle))
