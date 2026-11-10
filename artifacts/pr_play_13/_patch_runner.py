from pathlib import Path

path = Path("tools/playtest/runner.py")
text = path.read_text(encoding="utf-8")
old = """            path = run/'diagnostics/ready.json'
            if path.exists():
                ready = json.loads(path.read_text(encoding='utf-8'))
"""
new = """            path = run/'diagnostics/ready.json'
            if path.exists():
                try:
                    ready = json.loads(path.read_text(encoding='utf-8'))
                except (OSError, json.JSONDecodeError):
                    time.sleep(.05)
                    continue
"""
if old not in text:
    raise SystemExit("pattern missing")
temp = path.with_suffix(".py.tmp")
temp.write_bytes(text.replace(old, new, 1).encode("utf-8"))
temp.replace(path)
print("patched")
