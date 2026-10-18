"""PR-BY narration-only retry contract preservation. Deterministic. No model calls."""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from game.gm import (
    NARRATION_ONLY_RESPONSE_CONTRACT,
    NARRATION_ONLY_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    _provider_response_contract_from_payload,
    _safe_json,
)
from game.gm_resolution_decision import (
    DECISION_METADATA_KEY,
    PROVIDER_ENVELOPE_NARRATION_ONLY,
    PROVIDER_ENVELOPE_STRUCTURED,
    select_provider_response_envelope,
    validate_declared_claims_against_decision,
)
from game.immutable_valid_response import regeneration_feedback, run_preserve_if_valid

LIVE = Path("artifacts/pr_bv_turn_operation_projection_micro_live/evidence")
BAKER_NARRATION = (
    "The baker glances around briefly before muttering, “I’m afraid that’s "
    "not something I share lightly. Best you choose your own favorites from "
    "the loaves here.” Their tone holds a guarded edge, unwilling to reveal "
    "personal preference."
)
_DECLARATION_MARKERS = (
    "declared_claims",
    "structured_envelope_schema",
    "structured envelope",
    "rejected_declarations",
    "declaration_mode",
)
_OTHER_NARRATION_REASONS = (
    "ungrounded_authoritative_rule",
    "wrong_interlocutor",
    "unsolicited_npc_speech",
    "structured_envelope",
    "malformed_or_truncated",
    "hidden_information",
    "player_text_splice",
    "interaction_incomplete",
    "locate_present_interlocutor",
    "consequential_invention",
    "mechanical_contradiction",
    "impossible_entity_state",
)


def _load(probe: str, name: str) -> dict:
    return json.loads((LIVE / probe / name).read_text(encoding="utf-8"))


def _resolution(decision: dict, contract: dict) -> dict:
    return {
        "kind": "question",
        "metadata": {
            "resolution_contract": deepcopy(contract),
            DECISION_METADATA_KEY: deepcopy(decision),
        },
    }


def _p2() -> tuple[dict, dict, dict]:
    decision = _load("P2", "gm_resolution_decision.json")
    contract = _load("P2", "resolution_contract.json")
    return decision, contract, _resolution(decision, contract)


def _scene() -> dict:
    return {"scene": {"id": "bread_stall", "visible_facts": ["A baker stands beside loaves at a bread stall."]}}


def _assert_narration_only_feedback(feedback: str) -> None:
    lowered = feedback.lower()
    for marker in _DECLARATION_MARKERS:
        assert marker not in lowered, marker
    assert '{"narration": "player-facing response"}' in feedback
    assert "narration_only_response_schema" in feedback
    payload = json.loads(feedback.split("AUTHORITATIVE RETRY CONTEXT ", 1)[1])
    assert set(payload["narration_only_response_schema"]) == {"narration"}
    assert "structured_envelope_schema" not in payload
    assert "rejected_declarations" not in payload


def _assert_structured_feedback(feedback: str) -> None:
    assert "declared_claims" in feedback
    assert "structured_envelope_schema" in feedback
    assert "declared_claims plus narration" in feedback or "declared_claims and narration" in feedback
    assert "narration_only_response_schema" not in feedback
    payload = json.loads(feedback.split("AUTHORITATIVE RETRY CONTEXT ", 1)[1])
    assert "declared_claims" in payload["structured_envelope_schema"]
    assert "narration" in payload["structured_envelope_schema"]


def _capture_retry(candidate: dict, resolution: dict, *, scene: dict | None = None) -> str:
    captured: list[str] = []

    def _regenerate(feedback: str) -> dict:
        captured.append(feedback)
        return _safe_json(
            json.dumps({"narration": "The baker says, \"I keep that to myself.\""}),
            require_structured_claims=True,
            provider_response_contract="narration_only",
        )

    run_preserve_if_valid(
        candidate,
        regenerate=_regenerate,
        resolution=resolution,
        player_text=str((resolution.get("metadata") or {}).get("resolution_contract", {}).get("raw_input") or ""),
        scene=scene if scene is not None else _scene(),
    )
    assert captured, "expected a regeneration"
    return captured[0]


def test_t1_narration_only_initial_contract() -> None:
    decision, contract, _resolution_row = _p2()
    selected = select_provider_response_envelope(decision, contract)
    assert selected["selected_envelope"] == PROVIDER_ENVELOPE_NARRATION_ONLY
    assert selected["response_operation"] == "incidental_dialogue"
    assert selected["declaration_expectation"] == "reply_not_required"
    assert selected["consequential_realization_required"] is False

    payload = {"gm_resolution_decision": decision, "resolution_contract": contract}
    assert _provider_response_contract_from_payload(payload) == PROVIDER_ENVELOPE_NARRATION_ONLY
    assert '{"narration": "player-facing response"}' in NARRATION_ONLY_RESPONSE_CONTRACT
    assert "declared_claims" not in NARRATION_ONLY_RESPONSE_CONTRACT
    assert "declared_claims" not in NARRATION_ONLY_SYSTEM_PROMPT
    assert "structured_envelope_schema" not in NARRATION_ONLY_SYSTEM_PROMPT
    assert "declared_claims" in SYSTEM_PROMPT


def test_t2_narration_rejection_retry_stays_narration_only() -> None:
    decision, _contract, resolution = _p2()
    raw = json.dumps({"narration": BAKER_NARRATION})
    parsed = _safe_json(raw, require_structured_claims=True, provider_response_contract="narration_only")
    envelope = parsed["metadata"]["realization_envelope"]
    assert envelope["declared_claims"] == []
    assert envelope["declaration_authorship"] is False
    declaration = validate_declared_claims_against_decision([], decision=decision)
    assert declaration["hard_valid"] is True

    feedback = _capture_retry(parsed, resolution)
    assert parsed["metadata"]["provider_response_contract"] == PROVIDER_ENVELOPE_NARRATION_ONLY
    _assert_narration_only_feedback(feedback)
    assert "unauthorized_resolution_decision_fact" in feedback


def test_t3_pr_bx_unauthorized_resolution_decision_fact_preserves_narration_only() -> None:
    _decision, _contract, resolution = _p2()
    audit = {
        "violations": [
            {
                "reason_codes": ["unowned_stateful_world_assertion"],
                "text": "Best you choose your own favorites from the loaves here.",
            },
            {
                "reason_codes": ["unauthorized_evidential_relation"],
                "text": "Their tone holds a guarded edge, unwilling to reveal personal preference.",
            },
        ],
        "declaration_validation": {"hard_valid": True, "rejected_claims": []},
    }
    feedback = regeneration_feedback(
        ["unauthorized_resolution_decision_fact"],
        resolution=resolution,
        audit=audit,
        provider_response_contract=PROVIDER_ENVELOPE_NARRATION_ONLY,
    )
    _assert_narration_only_feedback(feedback)
    assert "unauthorized_resolution_decision_fact" in feedback
    assert "unowned_stateful_world_assertion" in feedback
    assert "unauthorized_evidential_relation" in feedback


@pytest.mark.parametrize("reason", _OTHER_NARRATION_REASONS)
def test_t4_other_narration_failure_reasons_stay_narration_only(reason: str) -> None:
    _decision, _contract, resolution = _p2()
    feedback = regeneration_feedback(
        [reason],
        resolution=resolution,
        provider_response_contract=PROVIDER_ENVELOPE_NARRATION_ONLY,
    )
    _assert_narration_only_feedback(feedback)
    assert reason in feedback


def test_t4_mixed_reasons_do_not_reintroduce_declarations() -> None:
    _decision, _contract, resolution = _p2()
    feedback = regeneration_feedback(
        ["ungrounded_authoritative_rule", "unauthorized_resolution_decision_fact", "consequential_invention"],
        resolution=resolution,
        provider_response_contract=PROVIDER_ENVELOPE_NARRATION_ONLY,
    )
    _assert_narration_only_feedback(feedback)


def test_t5_malformed_narration_only_output_retries_narration_only() -> None:
    _decision, _contract, resolution = _p2()
    for raw in ('{"narration":', "{}", '{"narration": ""}', "The baker shrugs."):
        parsed = _safe_json(raw, require_structured_claims=True, provider_response_contract="narration_only")
        assert parsed["metadata"]["structured_contract_failure"] is True
        assert parsed["metadata"]["provider_response_contract"] == PROVIDER_ENVELOPE_NARRATION_ONLY
        feedback = _capture_retry(parsed, resolution)
        _assert_narration_only_feedback(feedback)
        assert "structured_contract_failure" in feedback


def test_t6_smuggled_declarations_stay_rejected_and_retry_stays_narration_only() -> None:
    _decision, _contract, resolution = _p2()
    raw = json.dumps(
        {
            "declared_claims": [{"declaration_mode": "propose", "text": "The baker prefers rye."}],
            "narration": "The baker prefers rye.",
        }
    )
    parsed = _safe_json(raw, require_structured_claims=True, provider_response_contract="narration_only")
    assert parsed["player_facing_text"] == ""
    assert parsed["metadata"]["structured_contract_reason"] == "unexpected_declared_claims"
    assert parsed["metadata"].get("realization_envelope") is None
    feedback = _capture_retry(parsed, resolution)
    _assert_narration_only_feedback(feedback)
    assert "structured_contract_failure" in feedback


def test_t7_structured_retry_keeps_declaration_machinery() -> None:
    decision = _load("P1", "gm_resolution_decision.json")
    contract = _load("P1", "resolution_contract.json")
    selected = select_provider_response_envelope(decision, contract)
    assert selected["selected_envelope"] == PROVIDER_ENVELOPE_STRUCTURED
    feedback = regeneration_feedback(
        ["unauthorized_resolution_decision_fact"],
        resolution=_resolution(decision, contract),
        provider_response_contract=selected["selected_envelope"],
    )
    _assert_structured_feedback(feedback)

    p3_decision = _load("P3", "gm_resolution_decision.json")
    p3_contract = _load("P3", "resolution_contract.json")
    p3_selected = select_provider_response_envelope(p3_decision, p3_contract)
    assert p3_selected["selected_envelope"] == PROVIDER_ENVELOPE_STRUCTURED
    p3_feedback = regeneration_feedback(
        ["malformed_or_truncated"],
        resolution=_resolution(p3_decision, p3_contract),
        provider_response_contract=p3_selected["selected_envelope"],
    )
    assert "declared_claims" in p3_feedback
    assert "structured_envelope_schema" in p3_feedback
    assert "narration_only_response_schema" not in p3_feedback


def test_t8_consequential_realization_stays_structured_across_retry() -> None:
    decision = {
        "contract_id": "rc_by_consequential",
        "outcome_classification": "state_mutation",
        "realization_claims": [
            {
                "claim_id": "rc_by_gate",
                "text": "The gate is barred.",
                "provenance": "authored_world_fact",
                "authority": "world_truth",
                "epistemic_status": "established",
                "realization_role": "MUST_STATE",
                "relation_kind": "ordinary_predicate",
                "premise_claim_ids": [],
                "source_ref": "resolution.state_changes.gate",
            }
        ],
        "epistemic_acts": [],
        "permitted_state_mutations": [{"type": "state_change", "key": "gate", "value": "barred"}],
        "executable_obligations": {"mutation_owner": "resolution"},
        "unresolved_qualifiers": [],
        "proposed_facts": [],
    }
    contract = {"contract_id": "rc_by_consequential", "operation": "ask", "interlocutor_id": "warden", "raw_input": "Bar the gate."}
    selected = select_provider_response_envelope(decision, contract)
    assert selected["selected_envelope"] == PROVIDER_ENVELOPE_STRUCTURED
    assert selected["response_operation"] == "consequential_realization"
    assert selected["consequential_realization_required"] is True
    raw = json.dumps(
        {
            "declared_claims": [{"declaration_mode": "propose", "text": "The storm broke the gate.", "relation_kind": "causal"}],
            "narration": "The storm broke the gate.",
        }
    )
    parsed = _safe_json(
        raw,
        require_structured_claims=True,
        provider_response_contract=selected["selected_envelope"],
    )
    assert parsed["metadata"]["provider_response_contract"] == PROVIDER_ENVELOPE_STRUCTURED
    captured: list[str] = []

    def _regenerate(feedback: str) -> dict:
        captured.append(feedback)
        return _safe_json(
            json.dumps(
                {
                    "declared_claims": [
                        {
                            "declaration_mode": "realize",
                            "source_claim_id": "rc_by_gate",
                            "text": "The gate is barred.",
                        }
                    ],
                    "narration": "The gate is barred.",
                }
            ),
            require_structured_claims=True,
            provider_response_contract=PROVIDER_ENVELOPE_STRUCTURED,
        )

    run_preserve_if_valid(
        parsed,
        regenerate=_regenerate,
        resolution=_resolution(decision, contract),
        player_text="Bar the gate.",
        scene={"scene": {"visible_facts": ["The gate is barred."]}},
    )
    assert captured
    _assert_structured_feedback(captured[0])
    assert select_provider_response_envelope(decision, contract)["selected_envelope"] == PROVIDER_ENVELOPE_STRUCTURED


def test_t9_selected_envelope_is_invariant_across_retry() -> None:
    cases = (
        ("P2", PROVIDER_ENVELOPE_NARRATION_ONLY, json.dumps({"narration": BAKER_NARRATION})),
        (
            "P1",
            PROVIDER_ENVELOPE_STRUCTURED,
            json.dumps(
                {
                    "declared_claims": [{"declaration_mode": "propose", "text": "The storm caused the crack."}],
                    "narration": "The storm caused the crack.",
                }
            ),
        ),
    )
    for probe, expected, raw in cases:
        decision = _load(probe, "gm_resolution_decision.json")
        contract = _load(probe, "resolution_contract.json")
        before_decision = deepcopy(decision)
        before = select_provider_response_envelope(decision, contract)["selected_envelope"]
        assert before == expected
        parsed = _safe_json(raw, require_structured_claims=True, provider_response_contract=before)
        resolution = _resolution(decision, contract)
        feedback = _capture_retry(parsed, resolution)
        after = select_provider_response_envelope(decision, contract)["selected_envelope"]
        assert after == before == parsed["metadata"]["provider_response_contract"]
        assert decision == before_decision
        if expected == PROVIDER_ENVELOPE_NARRATION_ONLY:
            _assert_narration_only_feedback(feedback)
        else:
            _assert_structured_feedback(feedback)


def test_t10_retry_construction_does_not_reclassify_the_turn(monkeypatch: pytest.MonkeyPatch) -> None:
    import game.gm_resolution_decision as decision_mod

    decision, contract, resolution = _p2()
    selected = select_provider_response_envelope(decision, contract)
    calls = {"select": 0, "project": 0}
    real_select = decision_mod.select_provider_response_envelope
    real_project = decision_mod.project_turn_local_operation

    def _select(*args, **kwargs):
        calls["select"] += 1
        return real_select(*args, **kwargs)

    def _project(*args, **kwargs):
        calls["project"] += 1
        return real_project(*args, **kwargs)

    monkeypatch.setattr(decision_mod, "select_provider_response_envelope", _select)
    monkeypatch.setattr(decision_mod, "project_turn_local_operation", _project)
    feedback = regeneration_feedback(
        ["unauthorized_resolution_decision_fact"],
        resolution=resolution,
        provider_response_contract=selected["selected_envelope"],
    )
    _assert_narration_only_feedback(feedback)
    assert calls == {"select": 0, "project": 0}
