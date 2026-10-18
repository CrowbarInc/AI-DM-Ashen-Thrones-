"""PR-BT provider policy/instruction deduplication. Deterministic; no model calls."""
from __future__ import annotations

import json

from game.gm import _provider_response_contract_from_payload, _safe_json
from game.gm_resolution_decision import (
    PROVIDER_ENVELOPE_NARRATION_ONLY,
    PROVIDER_ENVELOPE_STRUCTURED,
    validate_declared_claims_against_decision,
)
from tools.measure_pr_bt_policy_instruction_payloads import BEFORE, PROBES, reconstruct_probe


def _rows() -> list[dict]:
    return [reconstruct_probe(probe_id, player) for probe_id, _scene, player in PROBES]


def _request(probe: str) -> tuple[list[dict], str, dict]:
    path = (
        "artifacts/pr_bt_policy_instruction_deduplication/evidence/"
        f"{probe}/provider_request_generation_1.json"
    )
    request = json.load(open(path, encoding="utf-8"))
    system = ""
    payload: dict = {}
    for msg in request["provider_input"]:
        if msg.get("role") == "system":
            system = str(msg.get("content") or "")
        elif msg.get("role") == "user":
            parsed = json.loads(str(msg.get("content") or "{}"))
            if isinstance(parsed, dict):
                payload = parsed
    return request["provider_input"], system, payload


def test_pr_bt_reconstructed_provider_requests_keep_required_rule_presence() -> None:
    for row in _rows():
        messages, system, payload = _request(row["probe"])
        contract = _provider_response_contract_from_payload(payload)
        if contract == PROVIDER_ENVELOPE_NARRATION_ONLY:
            recipe = payload["decision_facing_answer_recipe"]
            turn = recipe["turn_operation"]
            assert row["probe"] == "P2"
            assert "NARRATION-ONLY RESPONSE CONTRACT" in system
            assert '{"narration": "player-facing response"}' in system
            assert "declared_claims" not in system
            assert turn["response_operation"] == "incidental_dialogue"
            assert turn["declaration_expectation"] == "reply_not_required"
            assert "Do not declare that reply as a world fact" in turn["instruction"]
            assert "durable preference or history" in turn["instruction"]
            assert "not authored world truth" in recipe["incidental_improvisation_guidance"]
            assert row["rule_presence"]["authority_decision_claims_constrain_realization"] is True
            assert row["rule_presence"]["recipe_cannot_grant_authority"] is True
            assert row["rule_presence"]["invalid_output_no_prose_escape"] is True
            assert len(messages) == 2
            continue
        missing = [name for name, present in row["rule_presence"].items() if not present]
        assert missing == [], f"{row['probe']} missing provider-visible rules: {missing}"
        assert contract == PROVIDER_ENVELOPE_STRUCTURED


def test_pr_bt_provider_requests_remove_duplicate_instruction_payload_without_arbitrary_size_gate() -> None:
    for row in _rows():
        probe = row["probe"]
        after = row["measurements"]["total_provider_chars"]
        _messages, system, payload = _request(probe)
        instructions = [item for item in payload.get("instructions") or [] if isinstance(item, str)]
        assert BEFORE[probe]["total"] > after
        assert BEFORE[probe]["instructions"] > row["measurements"]["instructions_chars"]
        assert [item for item in instructions if item.strip() and item in system] == []
        assert isinstance(payload.get("response_policy"), dict)
        assert isinstance(payload.get("decision_facing_answer_recipe"), dict)


def test_pr_bt_policy_objects_and_recipe_remain_provider_visible() -> None:
    for row in _rows():
        probe = row["probe"]
        path = (
            "artifacts/pr_bt_policy_instruction_deduplication/evidence/"
            f"{probe}/provider_request_generation_1.json"
        )
        request = json.load(open(path, encoding="utf-8"))
        payload = json.loads(request["provider_input"][1]["content"])
        policy = payload.get("response_policy")
        assert isinstance(policy, dict)
        for key in (
            "answer_completeness",
            "narrative_authority",
            "fallback_behavior",
            "anti_railroading",
            "context_separation",
            "player_facing_narration_purity",
        ):
            assert isinstance(policy.get(key), dict), f"{probe} missing response_policy.{key}"
        assert isinstance(payload.get("decision_facing_answer_recipe"), dict)
        assert isinstance(payload.get("turn_packet"), dict)


def test_pr_bt_narration_only_dialogue_rejects_raw_json_and_unauthorized_declarations() -> None:
    _messages, _system, payload = _request("P2")
    decision = payload["gm_resolution_decision"]
    raw = json.dumps({"declared_claims": [], "narration": "The baker says no."})
    parsed = _safe_json(raw, require_structured_claims=True, provider_response_contract="narration_only")
    assert parsed["player_facing_text"] == ""
    assert parsed["metadata"]["structured_contract_reason"] == "unexpected_declared_claims"

    smuggled_preference = [
        {
            "declaration_mode": "propose",
            "text": "The baker prefers rye.",
            "provenance_requested": "authored_world_fact",
            "epistemic_status": "established",
            "modality": "established",
            "relation_kind": "ordinary_predicate",
        }
    ]
    verdict = validate_declared_claims_against_decision(smuggled_preference, decision=decision)
    assert verdict["hard_valid"] is False
    assert verdict["rejected_claims"]


def test_pr_bt_valid_harmless_narration_only_dialogue_survives() -> None:
    raw = json.dumps({"narration": 'The baker gives a small shrug. "Depends on the morning."'})
    parsed = _safe_json(raw, require_structured_claims=True, provider_response_contract="narration_only")
    assert parsed["player_facing_text"] == 'The baker gives a small shrug. "Depends on the morning."'
    envelope = parsed["metadata"]["realization_envelope"]
    assert envelope["declared_claims"] == []
    assert envelope["declaration_authorship"] is False
