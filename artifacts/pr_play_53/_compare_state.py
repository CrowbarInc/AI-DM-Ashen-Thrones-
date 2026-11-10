"""One-off state comparison. Does not call a provider."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS = Path(__file__).resolve().parent / "tmp_runs"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def scrub(value):
    if isinstance(value, dict):
        return {
            key: scrub(item)
            for key, item in value.items()
            if not any(part in str(key) for part in ("timestamp", "latency", "stamp", "last_saved"))
            and str(key) not in {
                "run_id", "trace_id", "campaign_run_id", "session_id",
                "canonical_gm_object_id", "debug_traces", "interpretation_telemetry",
            }
        }
    if isinstance(value, list):
        return [scrub(item) for item in value]
    return value


def diff(left, right, path="$"):
    if type(left) is not type(right):
        return [f"{path}: type {type(left).__name__} != {type(right).__name__}"]
    if isinstance(left, dict):
        rows = []
        for key in sorted(set(left) | set(right)):
            if key not in left or key not in right:
                rows.append(f"{path}.{key}: present {key in left} vs {key in right}")
            else:
                rows.extend(diff(left[key], right[key], f"{path}.{key}"))
        return rows
    if isinstance(left, list):
        if len(left) != len(right):
            return [f"{path}: len {len(left)} != {len(right)}"]
        rows = []
        for index, (a, b) in enumerate(zip(left, right)):
            rows.extend(diff(a, b, f"{path}[{index}]"))
        return rows
    if left != right:
        return [f"{path}: differ"]
    return []


def main() -> None:
    report = {}
    for pair in (("a_base", "a_live"), ("b_base", "b_live"), ("a_base", "c_fault")):
        left = RUNS / pair[0] / "data"
        right = RUNS / pair[1] / "data"
        pair_rows = {}
        for name in ("session.json", "world.json", "character.json", "combat.json", "conditions.json"):
            pair_rows[name] = diff(scrub(load(left / name)), scrub(load(right / name)))
        report["__".join(pair)] = {name: rows for name, rows in pair_rows.items() if rows}
    out = Path(__file__).resolve().parent / "state_comparison.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: {name: len(rows) for name, rows in value.items()} for key, value in report.items()}, indent=2))

    needles = []
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8-sig").splitlines():
            if "=" not in line or line.lstrip().startswith("#"):
                continue
            key, value = line.split("=", 1)
            value = value.strip().strip("\"'")
            if len(value) > 8 and any(part in key.lower() for part in ("key", "secret", "token", "password")):
                needles.append(value.encode())
    canaries = (
        b"CANARY_UNDISCOVERED_CLUE",
        b"CANARY_GM_NOTE",
        b"CANARY_NPC_MOTIVE",
        b"CANARY_HIDDEN_DESTINATION",
        b"CANARY_QUEST_TWIST",
        b"An agent of a noble house",
    )
    for path in Path(__file__).resolve().parent.rglob("*"):
        if not path.is_file() or "tmp_runs" in path.parts or "__pycache__" in path.parts:
            continue
        blob = path.read_bytes()
        hits = [item.decode() for item in canaries if item in blob]
        secret = any(item in blob for item in needles)
        if hits or secret:
            print("HIT", path.name, hits, secret)


if __name__ == "__main__":
    main()
