"""PR-CW harmless social context projection tests. No provider calls."""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest
import game.gm as gm
from tools.measure_pr_bt_policy_instruction_payloads import PROBES, reconstruct_probe

_REAL_PROJECTOR = gm._project_harmless_social_provider_context


def social_request(player: str, *, npc_id: str = "guard_captain", history=None):
    """Current resolver artifacts, with no provider or storage writes."""
    from game.defaults import default_campaign, default_character, default_combat, default_scene, default_session, default_world
    from game.live_resolution import attach_interaction_obligation
    from game.social import resolve_social_action

    world = default_world()
    scene = default_scene("frontier_gate")
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    session["turn_counter"] = 2
    session.pop("chat_history", None)
    if npc_id == "baker":
        world["npcs"] = [{"id": "baker", "name": "Baker", "role": "baker", "location": "frontier_gate", "disposition": "neutral", "topics": []}]
        scene["scene"]["visible_facts"] = ["A baker stands beside loaves at the gate."]
        scene["scene"]["addressables"] = [{"id": "baker", "name": "Baker", "addressable": True}]
    history = deepcopy(history or [])
    action = {"id": "cw_question", "label": player, "type": "question", "prompt": player, "target_id": npc_id}
    resolution = resolve_social_action(scene, session, world, action, raw_player_text=player, character=default_character(), turn_counter=2)
    attach_interaction_obligation(resolution, player_text=player, session=session, normalized_action=action, scene_id="frontier_gate", scene=scene, world=world, visible_turns=history, enable_model_interpretation=False)
    from game.ordinary_semantic_ownership import select_ordinary_resolver
    metadata = resolution["metadata"]
    metadata["selected_resolver"], _ = select_ordinary_resolver(metadata["resolution_contract"])
    metadata["ordinary_contract_established"] = True
    from game.ctir_runtime import attach_ctir, build_runtime_ctir_for_narration
    attach_ctir(session, build_runtime_ctir_for_narration(turn_id="pr-cw", scene_id="frontier_gate", player_input=player, builder_source="tests.test_pr_cw_social_context_projection", resolution=resolution, normalized_action=action, combat=default_combat(), session=session, world=world))
    from game.ctir_runtime import SESSION_CTIR_STAMP_KEY
    from game.narration_plan_bundle import build_narration_plan_bundle, ensure_narration_plan_bundle_for_turn
    session[SESSION_CTIR_STAMP_KEY] = "pr-cw"
    from unittest.mock import patch
    with patch.object(gm, "get_effective_scene", return_value=scene):
        kwargs = gm.collect_narration_context_call_kwargs(default_campaign(), world, session, default_character(), scene, default_combat(), history, player, resolution=resolution, scene_runtime={})
    bundle_kwargs = dict(kwargs)
    bundle_kwargs.pop("known_answer_hint", None)
    ensure_narration_plan_bundle_for_turn(session, turn_stamp="pr-cw", builder=lambda: build_narration_plan_bundle(session=session, narration_context_kwargs=bundle_kwargs))
    messages = gm.build_messages(default_campaign(), world, session, default_character(), scene, default_combat(), history, player, resolution=resolution, scene_runtime={}, narration_context_call_kwargs=kwargs)
    return messages, resolution, scene, world, session


POSITIVE_CONTROLS = (
    ("captain_preference", "guard_captain", "Guard Captain, do you prefer standing watch in the rain, or somewhere dry?", []),
    ("baker_preference", "baker", "Baker, which loaf do you usually keep for yourself?", []),
    ("subjective_opinion", "guard_captain", "Guard Captain, which view of the square do you like best?", []),
    ("followup", "baker", "Baker, which loaf would you recommend to me?", [{"log_meta": {"player_input": "Baker, which loaf do you like?"}, "gm_output": {"player_facing_text": 'The baker says, "I like the plain loaf."'}}]),
    ("recent_history", "guard_captain", "Guard Captain, which weather do you prefer for a watch?", [{"log_meta": {"player_input": "Captain, the rain is cold."}, "gm_output": {"player_facing_text": 'The captain says, "It certainly is."'}}]),
)


def _request(
    probe_id: str,
    *,
    out_dir: Path,
    projection_enabled: bool = True,
    monkeypatch,
) -> tuple[str, dict, list[dict]]:
    player = next(player for pid, _scene, player in PROBES if pid == probe_id)
    if not projection_enabled:
        monkeypatch.setattr(
            gm,
            "_project_harmless_social_provider_context",
            lambda payload, *, provider_response_contract: payload,
        )
    else:
        monkeypatch.setattr(gm, "_project_harmless_social_provider_context", _REAL_PROJECTOR)
    reconstruct_probe(probe_id, player, out_dir=out_dir)
    raw = json.loads(
        (out_dir / "evidence" / probe_id / "provider_request_generation_1.json").read_text(
            encoding="utf-8"
        )
    )
    messages = raw["provider_input"]
    payload = json.loads(messages[1]["content"])
    return messages[0]["content"], payload, messages


def _sha_messages(messages: list[dict]) -> str:
    return hashlib.sha256(
        json.dumps(messages, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


@pytest.mark.parametrize("label,npc_id,player,history", POSITIVE_CONTROLS)
def test_pr_cw_harmless_incidental_dialogue_uses_reduced_context(label, npc_id, player, history, monkeypatch) -> None:
    monkeypatch.setattr(gm, "_project_harmless_social_provider_context", lambda payload, **kwargs: payload)
    baseline_messages, *_ = social_request(player, npc_id=npc_id, history=history)
    monkeypatch.setattr(gm, "_project_harmless_social_provider_context", _REAL_PROJECTOR)
    reduced_messages, resolution, scene, world, session = social_request(player, npc_id=npc_id, history=history)
    system, system_after = baseline_messages[0]["content"], reduced_messages[0]["content"]
    baseline, reduced = (json.loads(m[1]["content"]) for m in (baseline_messages, reduced_messages))

    assert system_after == system
    assert "NARRATION-ONLY RESPONSE CONTRACT" in system_after
    assert reduced["provider_context_projection"]["selected"] is True
    assert reduced["decision_facing_answer_recipe"] == baseline["decision_facing_answer_recipe"]
    assert reduced["gm_resolution_decision"] == baseline["gm_resolution_decision"]
    assert reduced["resolution_contract"] == baseline["resolution_contract"]
    assert reduced["response_policy"] == baseline["response_policy"]
    assert reduced["scene"] == baseline["scene"]
    assert reduced["active_interlocutor"] == baseline["active_interlocutor"]
    assert reduced["dialogue_social_plan"] == baseline["dialogue_social_plan"]
    assert reduced["selected_conversational_memory"] == baseline["selected_conversational_memory"]
    assert reduced["recent_log"] == baseline["recent_log"]
    for entry in history:
        assert entry["log_meta"]["player_input"] in json.dumps(reduced["recent_log"])
        assert entry["gm_output"]["player_facing_text"] in " ".join(row["gm_snippet"] for row in reduced["recent_log"])
    assert reduced["active_interlocutor"]["npc_id"] == npc_id
    assert reduced["decision_facing_answer_recipe"]["turn_operation"]["response_operation"] == "incidental_dialogue"
    assert "declared_claims" not in system_after
    assert len(reduced_messages[1]["content"].encode("utf-8")) < len(
        baseline_messages[1]["content"].encode("utf-8")
    )
    from game.immutable_valid_response import run_preserve_if_valid
    text = ('The baker says, "I prefer the plain loaf."' if npc_id == "baker" else 'The guard captain says, "I prefer a dry watch."')
    candidate = gm._safe_json(json.dumps({"narration": text}), require_structured_claims=True, provider_response_contract="narration_only")
    sealed = run_preserve_if_valid(candidate, regenerate=None, resolution=resolution, player_text=player, scene=scene, world=world, session=session)
    assert sealed["metadata"]["hard_validation_attempt_1"]["hard_valid"] is True
    assert sealed["player_facing_text"] == text


def test_pr_cw_ineligible_prompt_payloads_are_unchanged(tmp_path, monkeypatch) -> None:
    for probe_id in ("P1", "P2", "P3"):
        _system, _baseline, baseline_messages = _request(
            probe_id,
            out_dir=tmp_path / f"{probe_id}_baseline",
            projection_enabled=False,
            monkeypatch=monkeypatch,
        )
        _system_after, reduced, reduced_messages = _request(
            probe_id,
            out_dir=tmp_path / f"{probe_id}_after",
            projection_enabled=True,
            monkeypatch=monkeypatch,
        )
        assert "provider_context_projection" not in reduced
        assert _sha_messages(reduced_messages) == _sha_messages(baseline_messages)


def test_pr_cw_negative_control_requires_single_grounded_addressee(monkeypatch) -> None:
    payload = {
        "decision_facing_answer_recipe": {
            "turn_operation": {
                "response_operation": "incidental_dialogue",
                "declaration_expectation": "reply_not_required",
            }
        },
        "gm_resolution_decision": {"permitted_state_mutations": []},
        "resolution_contract": {"operation": "ask", "target": "guard"},
        "response_policy": {},
        "scene": {},
        "dialogue_social_plan": {},
        "speaker_selection": {"allowed_speaker_ids": ["guard", "captain"]},
        "active_interlocutor": {"npc_id": "guard"},
    }
    out = gm._project_harmless_social_provider_context(
        payload,
        provider_response_contract="narration_only",
    )
    assert out is payload


NEGATIVE_CONTROLS = (
    ("authored_knowledge", ("mechanical_resolution", "social", "topic_revealed"), {"text": "A patrol went missing."}),
    ("hidden_knowledge", ("mechanical_resolution", "social", "reply_plan_kind"), "genuine_refusal"),
    ("ambiguous_addressee", ("speaker_selection", "allowed_speaker_ids"), ["guard_captain", "baker"]),
    ("persuasion", ("mechanical_resolution", "social", "skill_check"), {"dc": 15}),
    ("coercion", ("mechanical_resolution", "social", "reply_plan_kind"), "consequential_information_request"),
    ("physical_action", ("resolution_contract", "operation"), "act"),
    ("exploration", ("mechanical_resolution", "metadata", "selected_resolver"), "exploration"),
    ("observation", ("decision_facing_answer_recipe", "turn_operation", "response_operation"), "direct_observation"),
    ("combat", ("mechanical_resolution", "metadata", "selected_resolver"), "combat"),
    ("active_combat", ("combat", "in_combat"), True),
    ("world_mutation", ("gm_resolution_decision", "permitted_state_mutations"), [{"kind": "world_update"}]),
    ("hypothesis", ("gm_resolution_decision", "unresolved_qualifiers"), ["cause unknown"]),
    ("uncertain", ("mechanical_resolution", "social", "incidental_subjective_allowed"), None),
    ("malformed_inference", ("decision_facing_answer_recipe", "permitted_inference"), "unknown"),
    ("mechanical_adjudication", ("mechanical_resolution", "requires_check"), True),
    ("restricted_information", ("mechanical_resolution", "social", "objective_world_fact_authority"), "authored_context_required"),
    ("mismatched_speaker", ("active_interlocutor", "npc_id"), "baker"),
    ("opening", ("opening_narration_obligations", "opening_mode"), True),
    ("scene_transition", ("scene_advancement", "arrived_at_scene"), True),
)


@pytest.mark.parametrize("label,path,value", NEGATIVE_CONTROLS)
def test_pr_cw_authority_negative_controls_preserve_exact_payload(label, path, value, monkeypatch):
    monkeypatch.setattr(gm, "_project_harmless_social_provider_context", lambda payload, **kwargs: payload)
    messages, *_ = social_request(POSITIVE_CONTROLS[0][2])
    payload = json.loads(messages[1]["content"])
    payload.pop("provider_context_projection", None)
    parent = payload
    for key in path[:-1]:
        parent = parent[key]
    parent[path[-1]] = value
    before = json.dumps(payload, ensure_ascii=False)
    assert _REAL_PROJECTOR(payload, provider_response_contract="narration_only") is payload
    assert json.dumps(payload, ensure_ascii=False) == before


@pytest.mark.parametrize("player", [
    "Captain, what do you know about the missing patrol?",
    "Guard Captain, which secret guard schedule do you prefer?",
    "Guard Captain, which suspect do you think committed the murder?",
    "Guard Captain, which restricted entrance would you choose?",
])
def test_pr_cw_real_factual_and_restricted_requests_keep_full_context(player, monkeypatch):
    monkeypatch.setattr(gm, "_project_harmless_social_provider_context", lambda payload, **kwargs: payload)
    before, *_ = social_request(player)
    monkeypatch.setattr(gm, "_project_harmless_social_provider_context", _REAL_PROJECTOR)
    after, *_ = social_request(player)
    assert before == after


ADVERSARIAL_OUTPUTS = (
    ("biography", "The guard captain was born in Blackharbor and served for twenty years.", False),
    ("geography", "The old milestone lies east beyond the trading crossroads.", False),
    ("objective_fact", "The gate tax is five silver coins for every traveler.", False),
    ("hidden_information", "A secret tunnel runs beneath the gate into the keep.", False),
    ("npc_action", "The captain unlocks the gate and lets you pass.", False),
    ("certainty", "The captain confirms that bandits murdered the missing patrol.", False),
    ("discovery", "You discover a hidden map beneath the notice board.", False),
    ("state_change", "The captain gives you ten gold coins and a signed entry permit.", False),
)


@pytest.mark.parametrize("label,text,inherited_hard_valid", ADVERSARIAL_OUTPUTS)
def test_pr_cw_adversarial_validation_matches_full_context(label, text, inherited_hard_valid, monkeypatch):
    from game.immutable_valid_response import run_preserve_if_valid
    audits = []
    for enabled in (False, True):
        monkeypatch.setattr(gm, "_project_harmless_social_provider_context", _REAL_PROJECTOR if enabled else lambda payload, **kwargs: payload)
        messages, resolution, scene, world, session = social_request(POSITIVE_CONTROLS[0][2])
        if enabled:
            assert "provider_context_projection" in json.loads(messages[1]["content"])
        candidate = gm._safe_json(json.dumps({"narration": text}), require_structured_claims=True, provider_response_contract="narration_only")
        sealed = run_preserve_if_valid(candidate, regenerate=None, resolution=resolution, player_text=POSITIVE_CONTROLS[0][2], scene=scene, world=world, session=session)
        audit = sealed["metadata"]["hard_validation_attempt_1"]
        assert audit["hard_valid"] is inherited_hard_valid, (label, audit)
        if not inherited_hard_valid:
            assert sealed["player_facing_text"] != text
        audits.append(audit)
    assert audits[0] == audits[1]


def test_pr_cw_smuggled_declarations_rejected():
    parsed = gm._safe_json(json.dumps({"narration": "The captain nods.", "declared_claims": [{"text": "The captain gives you ten gold coins."}]}), require_structured_claims=True, provider_response_contract="narration_only")
    assert parsed["metadata"]["structured_output_rejected"] is True
    assert parsed["metadata"]["structured_contract_reason"] == "unexpected_declared_claims"
