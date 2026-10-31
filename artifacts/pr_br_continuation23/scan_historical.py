"""Read-only scan of saved PR-BR artifacts. No model calls. No game imports."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "historical_scan.json"

TARGETS = [
    ROOT / "artifacts" / "pr_br_full_gate" / "20261002T021950Z",
    ROOT / "artifacts" / "pr_br_independent_smoke" / "20261002T012905Z",
    ROOT / "artifacts" / "pr_br_continuation21",
    ROOT / "artifacts" / "pr_br_continuation21b",
    ROOT / "artifacts" / "pr_br_continuation21c",
    ROOT / "artifacts" / "pr_br_continuation22",
]


def _contract(resolution: dict) -> dict:
    meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    contract = meta.get("resolution_contract") if isinstance(meta.get("resolution_contract"), dict) else {}
    return contract


def _summarize_log_row(row: dict, source: str) -> dict:
    resolution = row.get("resolution") if isinstance(row.get("resolution"), dict) else {}
    contract = _contract(resolution)
    meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    route = meta.get("intent_route_debug") if isinstance(meta.get("intent_route_debug"), dict) else {}
    gm = row.get("gm_output") if isinstance(row.get("gm_output"), dict) else {}
    gm_meta = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
    accepted = gm_meta.get("accepted_response") if isinstance(gm_meta.get("accepted_response"), dict) else {}
    text = str(row.get("player_input") or "")
    return {
        "source": source,
        "player_input": text[:240],
        "kind": resolution.get("kind"),
        "route_reason": route.get("route_reason"),
        "canonical_entry_reason": meta.get("canonical_entry_reason"),
        "contract": bool(contract.get("contract_id") or contract.get("operation")),
        "operation": contract.get("operation"),
        "accepted": bool(accepted.get("text")),
        "visible": str(gm.get("player_facing_text") or "")[:180],
        "gpt_called": row.get("gpt_called"),
    }


def _summarize_turn_file(payload: dict, source: str) -> dict:
    text = str(payload.get("player_text") or payload.get("player_input") or "")
    contract = payload.get("resolution_contract") if isinstance(payload.get("resolution_contract"), dict) else {}
    if not contract:
        nested = payload.get("resolution") if isinstance(payload.get("resolution"), dict) else {}
        contract = _contract(nested)
    return {
        "source": source,
        "player_input": text[:240],
        "kind": payload.get("resolution_kind") or payload.get("operation") or (payload.get("resolution") or {}).get("kind")
        if isinstance(payload.get("resolution"), dict)
        else payload.get("operation"),
        "contract": bool(contract.get("contract_id") or contract.get("operation") or payload.get("operation")),
        "operation": contract.get("operation") or payload.get("operation"),
        "accepted": bool(payload.get("accepted_response_text") or payload.get("accepted_text")),
        "visible": str(payload.get("final_emitted_response") or payload.get("final_emitted_response") or "")[:180],
        "fast_path_used": payload.get("fast_path_used"),
        "manual_pass": payload.get("manual_pass"),
        "route_reason": None,
    }


def main() -> None:
    rows: list[dict] = []
    for base in TARGETS:
        if not base.exists():
            continue
        for path in base.rglob("session_log.jsonl"):
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not str(row.get("player_input") or "").strip() and row.get("request", {}).get("start_campaign"):
                    continue
                rows.append(_summarize_log_row(row, str(path.relative_to(ROOT))))
        for path in base.rglob("turns.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            items = payload if isinstance(payload, list) else payload.get("turns") if isinstance(payload, dict) else None
            if not isinstance(items, list):
                continue
            for item in items:
                if isinstance(item, dict):
                    rows.append(_summarize_turn_file(item, str(path.relative_to(ROOT))))

    bypass = [
        row
        for row in rows
        if row.get("kind") == "adjudication_query" or row.get("route_reason", "") and str(row.get("route_reason")).startswith("procedural_")
    ]
    missing = [row for row in rows if row.get("contract") is False and row.get("player_input")]
    OUT.write_text(
        json.dumps(
            {
                "rows": len(rows),
                "adjudication_or_procedural": bypass,
                "missing_contract_sample": missing[:80],
                "missing_contract_count": len(missing),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"rows={len(rows)} adjudication={len(bypass)} missing_contract={len(missing)}")


if __name__ == "__main__":
    main()
