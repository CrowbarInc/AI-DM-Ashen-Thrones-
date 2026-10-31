"""Dump preserved-gate codes after the lexical-scope repair. No model calls."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from game.gm_resolution_decision import (  # noqa: E402
    _authored_corpus,
    audit_realization_envelope_against_decision,
)

EVIDENCE = ROOT / "artifacts" / "pr_bu_pr_bt_final_repaired_chain_micro_live" / "evidence"


def _raw(name: str) -> dict:
    payload = json.loads((EVIDENCE / name).read_text(encoding="utf-8"))
    return json.loads(payload["parsed"]["raw_output"])


def _codes(audit: dict) -> list[str]:
    found: list[str] = []
    for key in ("violations", "claim_results"):
        for row in audit.get(key) or []:
            if isinstance(row, dict):
                found.extend(row.get("reason_codes") or [])
    declaration = audit.get("declaration_validation") or {}
    for key in ("violations", "rejected_claims", "accepted_claims"):
        for row in declaration.get(key) or []:
            if isinstance(row, dict):
                found.extend(row.get("reason_codes") or [])
    ordered: list[str] = []
    for code in found:
        if code not in ordered:
            ordered.append(code)
    return ordered


def main() -> None:
    rows = []
    for label, decision_name, scene_name, raw_name in (
        ("P1_retry", "P1/gm_resolution_decision.json", "P1/isolated/data/scenes/chapel_belfry.json", "P1/raw_generation_attempt_2.json"),
        ("P1_initial", "P1/gm_resolution_decision.json", "P1/isolated/data/scenes/chapel_belfry.json", "P1/raw_generation_attempt_1.json"),
        ("P2_initial", "P2/gm_resolution_decision.json", "P2/isolated/data/scenes/bread_stall.json", "P2/raw_generation_attempt_1.json"),
        ("P3_initial", "P3/gm_resolution_decision.json", "P3/isolated/data/scenes/chapel_belfry.json", "P3/raw_generation_attempt_1.json"),
    ):
        decision = json.loads((EVIDENCE / decision_name).read_text(encoding="utf-8"))
        scene = json.loads((EVIDENCE / scene_name).read_text(encoding="utf-8"))
        envelope = _raw(raw_name)
        audit = audit_realization_envelope_against_decision(
            narration=envelope.get("narration"),
            declared_claims=envelope.get("declared_claims") or [],
            decision=decision,
            authored_corpus=_authored_corpus(scene, {}),
        )
        rows.append(
            {
                "label": label,
                "hard_valid": audit["hard_valid"],
                "reason_codes": _codes(audit),
                "narration_validation_set": audit.get("narration_validation") is not None,
            }
        )
    out = Path(__file__).resolve().parent / "preserved_gate_after.json"
    out.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
