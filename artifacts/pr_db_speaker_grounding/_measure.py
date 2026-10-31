"""Deterministic PR-DB measurements. No provider calls."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import game.gm as gm
from game.defaults import default_campaign, default_character, default_combat
from tests.test_pr_db_speaker_grounding import TURN_1, TURN_2, TURN_3, _gate_session_scene, play_turn

OUT = Path(__file__).resolve().parent


def _predicates(payload: dict, envelope: str) -> list[dict]:
    recipe = payload.get("decision_facing_answer_recipe")
    turn_operation = recipe.get("turn_operation") if isinstance(recipe, dict) else None
    decision = payload.get("gm_resolution_decision")
    contract = payload.get("resolution_contract")
    response_policy = payload.get("response_policy")
    speaker_selection = payload.get("speaker_selection")
    active_interlocutor = payload.get("active_interlocutor")
    dialogue_plan = payload.get("dialogue_social_plan")
    scene = payload.get("scene")
    permitted_inference = recipe.get("permitted_inference") if isinstance(recipe, dict) else None
    combat = payload.get("combat")
    mechanical = payload.get("mechanical_resolution")
    metadata = mechanical.get("metadata") if isinstance(mechanical, dict) else None
    social = mechanical.get("social") if isinstance(mechanical, dict) else None
    opening = payload.get("opening_narration_obligations")
    advancement = payload.get("scene_advancement")
    rows = [
        ("payload_is_dict", "dict", type(payload).__name__, isinstance(payload, dict), "projector payload argument"),
        ("provider_response_contract", "narration_only", envelope, envelope == "narration_only", "build_messages selected envelope"),
        ("recipe_is_dict", True, isinstance(recipe, dict), isinstance(recipe, dict), "payload.decision_facing_answer_recipe"),
        ("turn_operation_is_dict", True, isinstance(turn_operation, dict), isinstance(turn_operation, dict), "turn_operation"),
        ("response_operation", "incidental_dialogue", (turn_operation or {}).get("response_operation") if isinstance(turn_operation, dict) else None, isinstance(turn_operation, dict) and turn_operation.get("response_operation") == "incidental_dialogue", "turn_operation.response_operation"),
        ("declaration_expectation", "reply_not_required", (turn_operation or {}).get("declaration_expectation") if isinstance(turn_operation, dict) else None, isinstance(turn_operation, dict) and turn_operation.get("declaration_expectation") == "reply_not_required", "turn_operation.declaration_expectation"),
        ("decision_is_dict", True, isinstance(decision, dict), isinstance(decision, dict), "gm_resolution_decision"),
        ("permitted_state_mutations", [], (decision or {}).get("permitted_state_mutations") if isinstance(decision, dict) else None, isinstance(decision, dict) and decision.get("permitted_state_mutations") == [], "permitted_state_mutations"),
        ("unresolved_qualifiers", [], (decision or {}).get("unresolved_qualifiers") if isinstance(decision, dict) else None, isinstance(decision, dict) and decision.get("unresolved_qualifiers") == [], "unresolved_qualifiers"),
        ("unresolved_content_absent", True, not (recipe or {}).get("unresolved_content") if isinstance(recipe, dict) else False, isinstance(recipe, dict) and not recipe.get("unresolved_content"), "unresolved_content"),
        ("permitted_inference_is_dict", True, isinstance(permitted_inference, dict), isinstance(permitted_inference, dict), "permitted_inference"),
        ("permitted_inference_allowed", False, (permitted_inference or {}).get("allowed") if isinstance(permitted_inference, dict) else None, isinstance(permitted_inference, dict) and permitted_inference.get("allowed") is False, "permitted_inference.allowed"),
        ("contract_is_dict", True, isinstance(contract, dict), isinstance(contract, dict), "resolution_contract"),
        ("contract_operation", "ask", (contract or {}).get("operation") if isinstance(contract, dict) else None, isinstance(contract, dict) and str(contract.get("operation") or "").strip().lower() == "ask", "resolution_contract.operation"),
        ("contract_target_nonempty", True, bool(str((contract or {}).get("target") or "").strip()) if isinstance(contract, dict) else False, isinstance(contract, dict) and bool(str(contract.get("target") or "").strip()), "resolution_contract.target"),
        ("response_policy_is_dict", True, isinstance(response_policy, dict), isinstance(response_policy, dict), "response_policy"),
        ("scene_is_dict", True, isinstance(scene, dict), isinstance(scene, dict), "scene"),
        ("dialogue_plan_is_dict", True, isinstance(dialogue_plan, dict), isinstance(dialogue_plan, dict), "dialogue_social_plan"),
        ("speaker_selection_is_dict", True, isinstance(speaker_selection, dict), isinstance(speaker_selection, dict), "speaker_selection"),
        ("allowed_speaker_ids_is_list", True, isinstance((speaker_selection or {}).get("allowed_speaker_ids"), list) if isinstance(speaker_selection, dict) else False, isinstance(speaker_selection, dict) and isinstance(speaker_selection.get("allowed_speaker_ids"), list), "allowed_speaker_ids"),
        ("exactly_one_allowed_speaker", 1, len((speaker_selection or {}).get("allowed_speaker_ids") or []) if isinstance(speaker_selection, dict) else 0, isinstance(speaker_selection, dict) and isinstance(speaker_selection.get("allowed_speaker_ids"), list) and len(speaker_selection.get("allowed_speaker_ids") or []) == 1, "allowed_speaker_ids length"),
        ("active_interlocutor_is_dict", True, isinstance(active_interlocutor, dict), isinstance(active_interlocutor, dict), "active_interlocutor"),
        ("active_interlocutor_npc_id", "nonempty", (active_interlocutor or {}).get("npc_id") if isinstance(active_interlocutor, dict) else None, isinstance(active_interlocutor, dict) and bool(str(active_interlocutor.get("npc_id") or "").strip()), "active_interlocutor.npc_id"),
        ("speaker_matches_active_interlocutor", True, isinstance(speaker_selection, dict) and isinstance(active_interlocutor, dict) and speaker_selection.get("allowed_speaker_ids") == [active_interlocutor.get("npc_id")] and speaker_selection.get("primary_speaker_id") == active_interlocutor.get("npc_id"), isinstance(speaker_selection, dict) and isinstance(active_interlocutor, dict) and speaker_selection.get("allowed_speaker_ids") == [active_interlocutor.get("npc_id")] and speaker_selection.get("primary_speaker_id") == active_interlocutor.get("npc_id"), "speaker_selection vs active_interlocutor"),
        ("contract_matches_active_interlocutor", True, isinstance(contract, dict) and isinstance(active_interlocutor, dict) and contract.get("interlocutor") == active_interlocutor.get("npc_id"), isinstance(contract, dict) and isinstance(active_interlocutor, dict) and contract.get("interlocutor") == active_interlocutor.get("npc_id"), "resolution_contract.interlocutor"),
        ("selected_resolver_social", "social", (metadata or {}).get("selected_resolver") if isinstance(metadata, dict) else None, isinstance(metadata, dict) and metadata.get("selected_resolver") == "social", "mechanical_resolution.metadata.selected_resolver"),
        ("ordinary_contract_established", True, (metadata or {}).get("ordinary_contract_established") if isinstance(metadata, dict) else None, isinstance(metadata, dict) and metadata.get("ordinary_contract_established") is True, "ordinary_contract_established"),
        ("social_is_dict", True, isinstance(social, dict), isinstance(social, dict), "mechanical_resolution.social"),
        ("social_npc_matches", True, isinstance(social, dict) and isinstance(active_interlocutor, dict) and social.get("npc_id") == active_interlocutor.get("npc_id"), isinstance(social, dict) and isinstance(active_interlocutor, dict) and social.get("npc_id") == active_interlocutor.get("npc_id"), "social.npc_id"),
        ("social_target_resolved", True, (social or {}).get("target_resolved") if isinstance(social, dict) else None, isinstance(social, dict) and social.get("target_resolved") is True, "social.target_resolved"),
        ("reply_plan_kind", "harmless_subjective_response_permitted", (social or {}).get("reply_plan_kind") if isinstance(social, dict) else None, isinstance(social, dict) and social.get("reply_plan_kind") == "harmless_subjective_response_permitted", "social.reply_plan_kind"),
        ("incidental_subjective_allowed", True, (social or {}).get("incidental_subjective_allowed") if isinstance(social, dict) else None, isinstance(social, dict) and social.get("incidental_subjective_allowed") is True, "social.incidental_subjective_allowed"),
        ("objective_world_fact_authority", "none", (social or {}).get("objective_world_fact_authority") if isinstance(social, dict) else None, isinstance(social, dict) and social.get("objective_world_fact_authority") == "none", "social.objective_world_fact_authority"),
        ("npc_speech_authority", "claim_only", (social or {}).get("npc_speech_authority") if isinstance(social, dict) else None, isinstance(social, dict) and social.get("npc_speech_authority") == "claim_only", "social.npc_speech_authority"),
        ("durable_state_mutation_allowed", False, (social or {}).get("durable_state_mutation_allowed") if isinstance(social, dict) else None, isinstance(social, dict) and social.get("durable_state_mutation_allowed") is False, "social.durable_state_mutation_allowed"),
        ("topic_revealed_absent", False, bool((social or {}).get("topic_revealed")) if isinstance(social, dict) else None, isinstance(social, dict) and not social.get("topic_revealed"), "social.topic_revealed"),
        ("skill_check_absent", False, bool((social or {}).get("skill_check")) if isinstance(social, dict) else None, isinstance(social, dict) and not social.get("skill_check"), "social.skill_check"),
        ("requires_check", False, (mechanical or {}).get("requires_check") if isinstance(mechanical, dict) else None, isinstance(mechanical, dict) and mechanical.get("requires_check") is False, "requires_check"),
        ("state_changes_absent", False, bool((mechanical or {}).get("state_changes")) if isinstance(mechanical, dict) else None, isinstance(mechanical, dict) and not mechanical.get("state_changes"), "state_changes"),
        ("world_updates_absent", False, bool((mechanical or {}).get("world_updates")) if isinstance(mechanical, dict) else None, isinstance(mechanical, dict) and not mechanical.get("world_updates"), "world_updates"),
        ("discovered_clues_absent", False, bool((mechanical or {}).get("discovered_clues")) if isinstance(mechanical, dict) else None, isinstance(mechanical, dict) and not mechanical.get("discovered_clues"), "discovered_clues"),
        ("resolved_transition_absent", False, bool((mechanical or {}).get("resolved_transition")) if isinstance(mechanical, dict) else None, isinstance(mechanical, dict) and not mechanical.get("resolved_transition"), "resolved_transition"),
        ("combat_not_active", False, (combat or {}).get("in_combat") if isinstance(combat, dict) else None, isinstance(combat, dict) and combat.get("in_combat") is False, "combat.in_combat"),
        ("opening_mode_false", False, (opening or {}).get("opening_mode") if isinstance(opening, dict) else None, isinstance(opening, dict) and opening.get("opening_mode") is False, "opening_narration_obligations.opening_mode"),
        ("scene_advancement_empty", True, isinstance(advancement, dict) and not any(advancement.values()), isinstance(advancement, dict) and not any(advancement.values()), "scene_advancement"),
    ]
    return [
        {"predicate": name, "required": required, "actual": actual, "pass": bool(ok), "authority_source": source}
        for name, required, actual, ok, source in rows
    ]


def _messages_for(result: dict, session: dict, scene: dict, world: dict, player: str):
    from game.ctir_runtime import SESSION_CTIR_STAMP_KEY, attach_ctir, build_runtime_ctir_for_narration
    from game.narration_plan_bundle import build_narration_plan_bundle, ensure_narration_plan_bundle_for_turn
    from unittest.mock import patch

    resolution = result["resolution"]
    attach_ctir(
        session,
        build_runtime_ctir_for_narration(
            turn_id="pr-db",
            scene_id="frontier_gate",
            player_input=player,
            builder_source="artifacts.pr_db_speaker_grounding",
            resolution=resolution,
            normalized_action={"type": "question", "prompt": player, "label": player},
            combat=default_combat(),
            session=session,
            world=world,
        ),
    )
    session[SESSION_CTIR_STAMP_KEY] = "pr-db"
    with patch.object(gm, "get_effective_scene", return_value=scene):
        kwargs = gm.collect_narration_context_call_kwargs(
            default_campaign(),
            world,
            session,
            default_character(),
            scene,
            default_combat(),
            [],
            player,
            resolution=resolution,
            scene_runtime={},
        )
    bundle_kwargs = dict(kwargs)
    bundle_kwargs.pop("known_answer_hint", None)
    ensure_narration_plan_bundle_for_turn(
        session,
        turn_stamp="pr-db",
        builder=lambda: build_narration_plan_bundle(session=session, narration_context_kwargs=bundle_kwargs),
    )
    return gm.build_messages(
        default_campaign(),
        world,
        session,
        default_character(),
        scene,
        default_combat(),
        [],
        player,
        resolution=resolution,
        scene_runtime={},
        narration_context_call_kwargs=kwargs,
    )


def _payload_from_messages(messages) -> tuple[str, dict | None, str]:
    texts = []
    for item in messages:
        content = item.get("content") if isinstance(item, dict) else None
        if isinstance(content, list):
            for chunk in content:
                if isinstance(chunk, dict) and chunk.get("text"):
                    texts.append(chunk["text"])
        elif isinstance(content, str):
            texts.append(content)
        elif isinstance(item, dict) and isinstance(item.get("text"), str):
            texts.append(item["text"])
    blob = "\n".join(texts)
    payload = None
    start = blob.find("\n{")
    if start < 0:
        start = blob.find("{")
    if start >= 0:
        try:
            payload, _end = json.JSONDecoder().raw_decode(blob[start:].lstrip())
        except json.JSONDecodeError:
            payload = None
    envelope = "narration_only" if "narration_only" in blob else "unknown"
    return blob, payload if isinstance(payload, dict) else None, envelope


def main() -> None:
    session, scene, world = _gate_session_scene()
    turns = []
    for text in (TURN_1, TURN_2, TURN_3):
        result = play_turn(session, scene, world, text)
        turns.append({k: result[k] for k in result if k not in {"resolution", "speaker"}})
        session["turn_counter"] = int(session.get("turn_counter") or 0) + 1
    # Rebuild turn 2 on a fresh continuity state for the provider payload.
    session2, scene2, world2 = _gate_session_scene()
    play_turn(session2, scene2, world2, TURN_1)
    follow = play_turn(session2, scene2, world2, TURN_2)
    scene2 = dict(scene2)
    scene2.pop("_is_canon", None)
    messages = _messages_for(follow, session2, scene2, world2, TURN_2)
    blob, payload, envelope = _payload_from_messages(messages)
    projected = None
    if isinstance(payload, dict):
        projected = gm._project_harmless_social_provider_context(dict(payload), provider_response_contract="narration_only")
    rows = _predicates(payload or {}, "narration_only")
    first_fail = next((row for row in rows if not row["pass"]), None)
    selected = isinstance(projected, dict) and isinstance(projected.get("provider_context_projection"), dict)
    summary = {
        "turns": turns,
        "followup_reply_plan_kind": follow.get("reply_plan_kind"),
        "serialized_chars": len(blob),
        "serialized_bytes": len(blob.encode("utf-8")),
        "sha256": hashlib.sha256(blob.encode("utf-8")).hexdigest(),
        "envelope_marker": envelope,
        "payload_found": isinstance(payload, dict),
        "projection_selected": selected,
        "projection_mode": (projected or {}).get("provider_context_projection", {}).get("mode") if isinstance(projected, dict) else None,
        "first_failing_predicate": first_fail,
        "predicates": rows,
        "speaker_allowed": follow.get("allowed_speaker_ids"),
        "social_npc_id": follow.get("social_npc_id"),
        "active_target_after": follow.get("active_interaction_target_id"),
    }
    (OUT / "_measure.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in summary if k not in {"predicates", "turns"}}, indent=2, default=str))
    print("TURNS")
    print(json.dumps(turns, indent=2, default=str))


if __name__ == "__main__":
    main()
