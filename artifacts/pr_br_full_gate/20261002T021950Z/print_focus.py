import json
from pathlib import Path

rows = json.loads(Path("review_sheet.json").read_text(encoding="utf-8"))
want = {
    ("persona_a", 4),
    ("persona_a", 5),
    ("persona_a", 9),
    ("persona_a", 10),
    ("persona_b", 2),
    ("persona_b", 3),
    ("persona_b", 6),
    ("persona_b", 9),
    ("persona_b", 10),
    ("persona_c", 2),
    ("persona_c", 4),
    ("persona_c", 8),
    ("persona_c", 10),
    ("persona_d", 1),
    ("persona_d", 3),
    ("persona_d", 6),
    ("persona_d", 10),
}
lines = []
for row in rows:
    if "n" not in row:
        continue
    key = (row["persona"], row["n"])
    if key not in want and not row["regen"] and row["prov"] != "safe_nonresolution":
        continue
    lines.append("=" * 20 + f" {row['persona']} {row['n']} prov={row['prov']} h1={row['a1_hard']} reasons={row['a1_reasons']} h2={row['a2_hard']} r2={row['a2_reasons']}")
    lines.append("PLAYER: " + (row["player"] or ""))
    lines.append("A1: " + (row["a1"] or ""))
    lines.append("A2: " + (row["a2"] or ""))
    lines.append("EMIT: " + (row["emitted"] or ""))
    lines.append("UNAUTH_G: " + json.dumps(row["unauth_gen"]))
    lines.append("UNAUTH_R: " + json.dumps(row["unauth_retry"]))
    lines.append("UNAUTH_E: " + json.dumps(row["unauth_emit"]))
Path("focus.txt").write_text("\n".join(lines), encoding="utf-8")
print("chars", Path("focus.txt").stat().st_size)
