import json
from pathlib import Path

rows = json.loads(Path("review_sheet.json").read_text(encoding="utf-8"))
lines = []
for row in rows:
    if "n" not in row:
        continue
    a1 = (row["a1"] or "").strip()
    emit = (row["emitted"] or "").strip()
    acc = (row["accepted"] or "").strip()
    if a1 != emit or acc != emit:
        lines.append(
            f"{row['persona']} {row['n']} prov={row['prov']} exact={row['exact']} a1_eq_emit={a1==emit} acc_eq_emit={acc==emit} a1_len={len(a1)} emit_len={len(emit)} acc_len={len(acc)}"
        )
Path("mismatch_scan.txt").write_text("\n".join(lines) or "NONE", encoding="utf-8")
print(Path("mismatch_scan.txt").read_text(encoding="utf-8"))
