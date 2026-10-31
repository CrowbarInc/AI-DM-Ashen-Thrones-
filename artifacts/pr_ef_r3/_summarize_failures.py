"""Print a decision-provenance summary for the four R2 holdout failures."""
from __future__ import annotations

import json
from pathlib import Path

SRC = Path(__file__).resolve().parent / "failure_provenance.json"


def walk_keys(obj, prefix="", hits=None, needles=None, depth=0):
    if hits is None:
        hits = []
    if depth > 8 or obj is None:
        return hits
    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{prefix}.{k}" if prefix else k
            lk = k.lower()
            if any(n in lk for n in needles):
                shown = v
                if isinstance(v, (dict, list)):
                    shown = json.dumps(v, ensure_ascii=False)[:600]
                elif isinstance(v, str) and len(v) > 600:
                    shown = v[:600]
                hits.append((path, shown))
            walk_keys(v, path, hits, needles, depth + 1)
    elif isinstance(obj, list) and obj and depth < 6:
        for i, v in enumerate(obj[:6]):
            walk_keys(v, f"{prefix}[{i}]", hits, needles, depth + 1)
    return hits


def main() -> None:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    needles = (
        "recipient",
        "purpose",
        "communication",
        "target",
        "ambigu",
        "unresolved",
        "owner",
        "operation",
        "clarif",
        "route",
        "decision",
        "interloc",
        "authority",
        "effects",
        "time",
        "faction",
        "reply",
        "kind",
        "fallback",
        "safe",
        "correction",
        "mode",
        "status",
    )
    for row in data["rows"]:
        print("=" * 100)
        print("TURN", row["turn"], row["player"])
        print("expected", row["expected"], "actual", row["actual"], "strict", row["strict_pass"], "crit", row["critical"])
        print("response:", row["response"])
        print("calls", row["provider_calls"], "ms", row["elapsed_ms"], "nonmutating", row["nonmutating"])
        print("STATE CHANGES:")
        print(json.dumps(row["state_changes"], ensure_ascii=False)[:2500])
        hits = walk_keys(row, needles=needles)
        # de-dupe very similar
        seen = set()
        for path, shown in hits:
            key = (path, str(shown)[:180])
            if key in seen:
                continue
            seen.add(key)
            print(f"  {path}: {shown}")


if __name__ == "__main__":
    main()
