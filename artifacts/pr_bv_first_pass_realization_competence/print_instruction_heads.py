import json
from pathlib import Path

root = Path("artifacts/pr_bv_first_pass_realization_competence")
for probe in ("P1", "P2"):
    removed = json.loads((root / f"{probe}_removed_instructions.json").read_text(encoding="utf-8"))
    added = json.loads((root / f"{probe}_added_instructions.json").read_text(encoding="utf-8"))
    print(f"\n===== {probe} REMOVED {len(removed)} =====")
    for index, item in enumerate(removed):
        text = item["text"].replace("\n", " | ")
        print(f"[{index}] {item['chars']}c :: {text[:280]}")
    print(f"\n===== {probe} ADDED {len(added)} =====")
    for index, item in enumerate(added):
        text = item["text"].replace("\n", " | ")
        print(f"[{index}] {item['chars']}c :: {text[:280]}")
