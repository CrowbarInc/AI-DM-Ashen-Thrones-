"""Write the PR-BY retry matrix and the PR-BX feedback snapshot. No model calls."""
from __future__ import annotations

import json
from pathlib import Path

from game.gm import _safe_json
from game.immutable_valid_response import regeneration_feedback
from tests.test_pr_by_narration_only_retry_contract import (
    BAKER_NARRATION,
    _capture_retry,
    _load,
    _p2,
    _resolution,
)

OUT = Path(__file__).resolve().parent
MARKERS = ("declared_claims", "structured_envelope_schema", "structured envelope")


def _measured(feedback: str) -> dict:
    lowered = feedback.lower()
    payload = json.loads(feedback.split("AUTHORITATIVE RETRY CONTEXT ", 1)[1])
    narration_schema = payload.get("narration_only_response_schema")
    structured_schema = payload.get("structured_envelope_schema")
    if isinstance(narration_schema, dict):
        keys = sorted(narration_schema)
        envelope = "narration_only"
    elif isinstance(structured_schema, dict):
        keys = sorted(structured_schema)
        envelope = "structured_realization"
    else:
        keys = []
        envelope = "unspecified"
    return {
        "retry_envelope": envelope,
        "declared_claims_exposed": "declared_claims" in lowered,
        "structured_schema_exposed": "structured_envelope_schema" in feedback,
        "structured_envelope_phrase": "structured envelope" in lowered,
        "expected_provider_keys": keys,
        "result": "preserved",
    }


def main() -> None:
    decision, contract, resolution = _p2()
    rows = []

    rows.append(
        {
            "case": "P2 initial narration-only contract",
            "initial_envelope": "narration_only",
            "failure_reason": None,
            "retry_envelope": "narration_only",
            "declared_claims_exposed": False,
            "structured_schema_exposed": False,
            "expected_provider_keys": ["narration"],
            "result": "preserved",
        }
    )

    audit = {
        "violations": [
            {"reason_codes": ["unowned_stateful_world_assertion"], "text": "Best you choose your own favorites from the loaves here."},
            {"reason_codes": ["unauthorized_evidential_relation"], "text": "Their tone holds a guarded edge, unwilling to reveal personal preference."},
        ],
        "declaration_validation": {"hard_valid": True, "rejected_claims": []},
    }
    pr_bx = regeneration_feedback(
        ["unauthorized_resolution_decision_fact"],
        resolution=resolution,
        audit=audit,
        provider_response_contract="narration_only",
    )
    pr_bx_row = {
        "case": "PR-BX unauthorized_resolution_decision_fact",
        "initial_envelope": "narration_only",
        "failure_reason": "unauthorized_resolution_decision_fact",
        **_measured(pr_bx),
    }
    rows.append(pr_bx_row)

    for reason in (
        "ungrounded_authoritative_rule",
        "wrong_interlocutor",
        "unsolicited_npc_speech",
        "structured_envelope",
        "malformed_or_truncated",
        "hidden_information",
        "interaction_incomplete",
        "consequential_invention",
        "mechanical_contradiction",
    ):
        feedback = regeneration_feedback([reason], resolution=resolution, provider_response_contract="narration_only")
        rows.append(
            {
                "case": f"P2 narration validation branch {reason}",
                "initial_envelope": "narration_only",
                "failure_reason": reason,
                **_measured(feedback),
            }
        )

    malformed = _safe_json('{"narration":', require_structured_claims=True, provider_response_contract="narration_only")
    malformed_feedback = _capture_retry(malformed, resolution)
    rows.append(
        {
            "case": "malformed narration-only JSON",
            "initial_envelope": "narration_only",
            "failure_reason": "structured_contract_failure",
            **_measured(malformed_feedback),
        }
    )

    smuggled = _safe_json(
        json.dumps({"declared_claims": [{"declaration_mode": "propose", "text": "The baker prefers rye."}], "narration": "The baker prefers rye."}),
        require_structured_claims=True,
        provider_response_contract="narration_only",
    )
    smuggled_feedback = _capture_retry(smuggled, resolution)
    rows.append(
        {
            "case": "smuggled declared_claims on narration-only output",
            "initial_envelope": "narration_only",
            "failure_reason": "unexpected_declared_claims",
            **_measured(smuggled_feedback),
        }
    )

    for probe, reason in (("P1", "unauthorized_resolution_decision_fact"), ("P3", "malformed_or_truncated")):
        selected_decision = _load(probe, "gm_resolution_decision.json")
        selected_contract = _load(probe, "resolution_contract.json")
        feedback = regeneration_feedback(
            [reason],
            resolution=_resolution(selected_decision, selected_contract),
            provider_response_contract="structured_realization",
        )
        rows.append(
            {
                "case": f"{probe} structured retry",
                "initial_envelope": "structured_realization",
                "failure_reason": reason,
                **_measured(feedback),
            }
        )

    baker = _safe_json(json.dumps({"narration": BAKER_NARRATION}), require_structured_claims=True, provider_response_contract="narration_only")
    baker_feedback = _capture_retry(baker, resolution)
    rows.append(
        {
            "case": "P2 baker narration through run_preserve_if_valid",
            "initial_envelope": "narration_only",
            "failure_reason": "unauthorized_resolution_decision_fact",
            **_measured(baker_feedback),
        }
    )

    (OUT / "PR-BY_retry_contract_matrix.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    snapshot = {
        "source": "regeneration_feedback for unauthorized_resolution_decision_fact on the P2 narration-only envelope",
        "live_calls": 0,
        "declared_claims_exposed": "declared_claims" in pr_bx.lower(),
        "structured_envelope_schema_exposed": "structured_envelope_schema" in pr_bx,
        "structured_envelope_phrase": "structured envelope" in pr_bx.lower(),
        "expected_provider_keys": ["narration"],
        "feedback": pr_bx,
        "baker_run_preserve_if_valid_feedback": baker_feedback,
    }
    (OUT / "pr_bx_retry_feedback_snapshot.json").write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    bad = [row["case"] for row in rows if row["initial_envelope"] == "narration_only" and (row["declared_claims_exposed"] or row["structured_schema_exposed"] or row["retry_envelope"] != "narration_only")]
    bad += [row["case"] for row in rows if row["initial_envelope"] == "structured_realization" and row["retry_envelope"] != "structured_realization"]
    if bad:
        raise SystemExit("matrix mismatch: " + ", ".join(bad))
    print(f"cases={len(rows)}")


if __name__ == "__main__":
    main()
