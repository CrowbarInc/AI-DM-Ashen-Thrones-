"""PR-CT safe prompt deduplication contract tests. No provider calls."""
from __future__ import annotations

import json

from game.gm import (
    NO_VALIDATOR_VOICE_RULE,
    RULE_PRIORITY_COMPACT_INSTRUCTION,
)
from tools.measure_pr_bt_policy_instruction_payloads import PROBES, reconstruct_probe

_SYSTEM_OWNED_DUPLICATES = (
    RULE_PRIORITY_COMPACT_INSTRUCTION,
    "Always answer the player. Prefer partial truth over refusal. Never output meta explanations.",
    NO_VALIDATOR_VOICE_RULE,
)


def _provider_request(probe_id: str, player: str) -> tuple[str, dict]:
    reconstruct_probe(probe_id, player)
    with open(
        f"artifacts/pr_bt_policy_instruction_deduplication/evidence/{probe_id}/provider_request_generation_1.json",
        encoding="utf-8",
    ) as f:
        request = json.load(f)
    system = request["provider_input"][0]["content"]
    payload = json.loads(request["provider_input"][1]["content"])
    return system, payload


def test_pr_ct_exact_system_owned_instruction_duplicates_removed_from_payload() -> None:
    for probe_id, _scene, player in PROBES:
        system, payload = _provider_request(probe_id, player)
        instructions = payload.get("instructions")
        assert isinstance(instructions, list)
        for duplicate in _SYSTEM_OWNED_DUPLICATES:
            if duplicate in system:
                assert duplicate not in instructions, probe_id


def test_pr_ct_provider_payload_retains_required_contract_surfaces() -> None:
    for probe_id, _scene, player in PROBES:
        system, payload = _provider_request(probe_id, player)
        assert payload.get("player_input") == player
        assert isinstance(payload.get("scene"), dict), probe_id
        assert isinstance(payload.get("session"), dict), probe_id
        assert isinstance(payload.get("turn_packet"), dict), probe_id
        assert isinstance(payload.get("response_policy"), dict), probe_id
        assert isinstance(payload.get("narration_visibility"), dict), probe_id
        assert isinstance(payload.get("decision_facing_answer_recipe"), dict), probe_id
        assert isinstance(payload.get("gm_resolution_decision"), dict), probe_id
        assert isinstance(payload.get("resolution_contract"), dict), probe_id
        assert "Return valid JSON only" in system


def test_pr_ct_authority_sensitive_policy_objects_stay_provider_visible() -> None:
    for probe_id, _scene, player in PROBES:
        _system, payload = _provider_request(probe_id, player)
        policy = payload.get("response_policy")
        assert isinstance(policy, dict), probe_id
        for key in (
            "answer_completeness",
            "narrative_authority",
            "fallback_behavior",
            "anti_railroading",
            "context_separation",
            "player_facing_narration_purity",
            "conversational_memory_window",
        ):
            assert isinstance(policy.get(key), dict), f"{probe_id} missing response_policy.{key}"
        decision = payload["gm_resolution_decision"]
        assert isinstance(decision.get("realization_claims"), list), probe_id
        assert isinstance(decision.get("permitted_state_mutations"), (dict, list)), probe_id
