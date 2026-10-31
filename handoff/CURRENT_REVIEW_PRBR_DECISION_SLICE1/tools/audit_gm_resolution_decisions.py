"""Static PR-BR GM resolution-decision auditor.

Usage:
    python tools/audit_gm_resolution_decisions.py path/to/capture.json [more...]

The input may be a turn capture object, a list of turns, or plain text. JSON
objects are searched for ``player_facing_text`` plus ``gm_resolution_decision``.
Plain text is audited with an empty decision, which still exposes targeted
consequential proposition families.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from game.gm_resolution_decision import DECISION_METADATA_KEY, audit_narration_against_decision


def _walk(value: Any) -> Iterable[Any]:
    yield value
    if isinstance(value, Mapping):
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _text_from(row: Mapping[str, Any]) -> str:
    for key in ("player_facing_text", "final_output", "response", "generation_attempt_1", "text"):
        val = row.get(key)
        if isinstance(val, str) and val.strip():
            return val
    gm = row.get("gm_output")
    if isinstance(gm, Mapping):
        return _text_from(gm)
    return ""


def _decision_from(row: Mapping[str, Any]) -> dict[str, Any]:
    md = row.get("metadata") if isinstance(row.get("metadata"), Mapping) else {}
    if isinstance(md.get(DECISION_METADATA_KEY), Mapping):
        return dict(md[DECISION_METADATA_KEY])
    resolution = row.get("resolution") if isinstance(row.get("resolution"), Mapping) else {}
    res_md = resolution.get("metadata") if isinstance(resolution.get("metadata"), Mapping) else {}
    if isinstance(res_md.get(DECISION_METADATA_KEY), Mapping):
        return dict(res_md[DECISION_METADATA_KEY])
    gm = row.get("gm_output") if isinstance(row.get("gm_output"), Mapping) else {}
    gm_md = gm.get("metadata") if isinstance(gm.get("metadata"), Mapping) else {}
    if isinstance(gm_md.get(DECISION_METADATA_KEY), Mapping):
        return dict(gm_md[DECISION_METADATA_KEY])
    return {}


def audit_payload(payload: Any, *, source: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for node in _walk(payload):
        if not isinstance(node, Mapping):
            continue
        text = _text_from(node)
        if not text:
            continue
        decision = _decision_from(node)
        result = audit_narration_against_decision(text, decision=decision, authored_corpus="")
        if result["proposed_facts"] or result["violations"]:
            rows.append({"source": source, "text": text[:500], **result})
    return rows


def audit_file(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    try:
        payload = json.loads(raw)
        rows = audit_payload(payload, source=str(path))
    except json.JSONDecodeError:
        rows = [
            {
                "source": str(path),
                "text": raw[:500],
                **audit_narration_against_decision(raw, decision={}, authored_corpus=""),
            }
        ]
    return {
        "path": str(path),
        "checked": len(rows),
        "violations": [row for row in rows if not row.get("hard_valid")],
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--output", "-o", default="")
    args = parser.parse_args()
    report = {"files": [audit_file(Path(p)) for p in args.paths]}
    report["violation_count"] = sum(len(item["violations"]) for item in report["files"])
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 1 if report["violation_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
