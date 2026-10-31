"""Read-only extraction of PR-EF-R2 failure provenance. Investigation only."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "artifacts" / "pr_ef_r2" / "behavior_1.json"
OUT = Path(__file__).resolve().parent / "failure_provenance.json"

OMIT = {
    "state_before",
    "state_after",
    "scene",
    "world",
    "transcript",
    "history",
    "prompt",
    "messages",
    "system",
    "full_state",
    "campaign",
}


def slim(obj, depth=0, maxd=6):
    if depth > maxd:
        return "<depth>"
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in OMIT:
                n = len(v) if hasattr(v, "__len__") else None
                out[k] = f"<omitted {type(v).__name__} len={n}>"
            else:
                out[k] = slim(v, depth + 1, maxd)
        return out
    if isinstance(obj, list):
        items = [slim(x, depth + 1, maxd) for x in obj[:12]]
        if len(obj) > 12:
            items.append(f"<+{len(obj) - 12} more>")
        return items
    if isinstance(obj, str) and len(obj) > 1200:
        return obj[:1200] + f"...<+{len(obj) - 1200} chars>"
    return obj


def main() -> None:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    wanted = {26, 27, 31, 33}
    rows = []
    for row in data["rows"]:
        if row["turn"] not in wanted:
            continue
        rows.append(
            {
                "turn": row["turn"],
                "player": row["player"],
                "expected": row.get("expected"),
                "actual": row.get("actual"),
                "strict_pass": row.get("strict_pass"),
                "behavior_pass": row.get("behavior_pass"),
                "critical": row.get("critical"),
                "response": row.get("response"),
                "provider_calls": row.get("provider_calls"),
                "elapsed_ms": row.get("elapsed_ms"),
                "nonmutating": row.get("nonmutating"),
                "state_changes": row.get("state_changes"),
                "isolated_interpretation": slim(row.get("isolated_interpretation")),
                "wire": slim(row.get("wire"), maxd=5),
                "deterministic_decision": slim(row.get("deterministic_decision")),
                "resolution": slim(row.get("resolution")),
                "gm_output_keys": list((row.get("gm_output") or {}).keys())
                if isinstance(row.get("gm_output"), dict)
                else None,
                "gm_metadata": slim((row.get("gm_output") or {}).get("metadata") if isinstance(row.get("gm_output"), dict) else None),
            }
        )
    payload = {
        "mode": data.get("mode"),
        "fresh_provider": data.get("fresh_provider"),
        "replay_source": data.get("replay_source"),
        "behavior_transport": data.get("behavior_transport"),
        "provider_summary": {
            k: data.get("provider", {}).get(k)
            for k in ("requests", "input_tokens", "output_tokens", "total_tokens")
        },
        "rows": rows,
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(OUT, OUT.stat().st_size)


if __name__ == "__main__":
    main()
