import json
from pathlib import Path

rows = json.loads(Path("review_sheet.json").read_text(encoding="utf-8"))
lines = []
for row in rows:
    if "n" not in row:
        continue
    a2 = (row["a2"] or "").strip()
    emit = (row["emitted"] or "").strip()
    if row["prov"] == "regeneration":
        lines.append(f"{row['persona']} {row['n']} a2_eq_emit={a2==emit} a2_len={len(a2)} emit_len={len(emit)}")
Path("retry_match.txt").write_text("\n".join(lines), encoding="utf-8")
print(Path("retry_match.txt").read_text(encoding="utf-8"))
