from __future__ import annotations

from copy import deepcopy

import pytest

import game.api_turn_support as api_turn_support
from game.defaults import default_scene, default_session, default_world
from game.final_emission_gate import (
    _decompress_overpacked_sentences,
    _micro_smooth_post_repair_sentences,
    _repair_fragmentary_participial_splits,
)
from game.interaction_context import rebuild_active_scene_entities, set_social_target
from game.narration_visibility import (
    validate_player_facing_first_mentions,
    validate_player_facing_referential_clarity,
)
from game.storage import get_scene_runtime


pytestmark = pytest.mark.unit

GLOBAL_VISIBILITY_FALLBACK = "For a breath, the scene holds while voices shift around you."
VISIBLE_FACT = "A brazier throws orange sparks over the checkpoint."
DISCOVERABLE_FACT = "The missing patrol was last seen near the old stone bridge."
HIDDEN_FACT = "The checkpoint taxes are funding an Ash Cowl payoff."


def _base_visibility_bundle():
    session = default_session()
    world = default_world()
    world["npcs"].append(
        {
            "id": "lord_aldric",
            "name": "Lord Aldric",
            "location": "castle_keep",
        }
    )
    scene = default_scene("frontier_gate")
    scene["scene"]["visible_facts"] = [VISIBLE_FACT]
    scene["scene"]["discoverable_clues"] = [DISCOVERABLE_FACT]
    scene["scene"]["hidden_facts"] = [HIDDEN_FACT]
    sid = "frontier_gate"
    session["active_scene_id"] = sid
    session["scene_state"]["active_scene_id"] = sid
    rebuild_active_scene_entities(session, world, sid, scene_envelope=scene)
    scene["scene_state"] = dict(session["scene_state"])
    return session, world, scene, sid


def _rich_scene_visibility_bundle():
    session = default_session()
    world = default_world()
    scene = default_scene("frontier_gate")
    sid = "frontier_gate"
    session["active_scene_id"] = sid
    session["scene_state"]["active_scene_id"] = sid
    rebuild_active_scene_entities(session, world, sid, scene_envelope=scene)
    scene["scene_state"] = dict(session["scene_state"])
    return session, world, scene, sid


def _visibility_bundle_with_extra_addressables(*addressables: dict):
    session, world, scene, sid = _base_visibility_bundle()
    scene["scene"]["addressables"].extend(deepcopy(list(addressables)))
    rebuild_active_scene_entities(session, world, sid, scene_envelope=scene)
    scene["scene_state"] = dict(session["scene_state"])
    return session, world, scene, sid


def _finalize_via_turn_support(
    text: str,
    *,
    session: dict,
    world: dict,
    scene: dict,
    resolution: dict | None = None,
) -> dict:
    scene["scene_state"] = dict(session["scene_state"])
    out, _narr_meta = api_turn_support._finalize_player_facing_for_turn(
        {"player_facing_text": text, "tags": []},
        resolution=resolution,
        session=session,
        world=world,
        scene=scene,
    )
    assert out["_player_facing_emission_finalized"] is True
    return out


def _assert_first_mention_default_meta_shape(meta: dict) -> None:
    assert "first_mention_validation_passed" in meta
    assert "first_mention_replacement_applied" in meta
    assert "first_mention_violation_kinds" in meta
    assert "first_mention_checked_entities" in meta
    assert "first_mention_leading_pronoun_detected" in meta
    assert "first_mention_first_explicit_entity_offset" in meta
    assert "first_mention_fallback_strategy" in meta
    assert "first_mention_fallback_candidate_source" in meta
    assert "opening_scene_first_mention_preference_used" in meta


def _assert_referential_clarity_default_meta_shape(meta: dict) -> None:
    assert "referential_clarity_validation_passed" in meta
    assert "referential_clarity_replacement_applied" in meta
    assert "referential_clarity_violation_kinds" in meta
    assert "referential_clarity_checked_entities" in meta
    assert "referential_clarity_violation_sample" in meta
    assert "referential_clarity_local_substitution_attempted" in meta
    assert "referential_clarity_local_substitution_applied" in meta
    assert "referential_clarity_local_substitution_token" in meta
    assert "referential_clarity_local_substitution_replacement" in meta
    assert "referential_clarity_fallback_avoided" in meta
    assert "referential_clarity_fallback_after_failed_local_repair" in meta


def test_pipeline_replaces_offscene_known_npc_reference():
    session, world, scene, _sid = _base_visibility_bundle()

    out = _finalize_via_turn_support(
        "Lord Aldric watches the checkpoint from the square.",
        session=session,
        world=world,
        scene=scene,
    )

    assert out["player_facing_text"] == GLOBAL_VISIBILITY_FALLBACK
    assert out["tags"] == [
        "final_emission_gate_replaced",
        "visibility_enforcement_replaced",
        "visibility_violation:unseen_entity_reference",
    ]
    assert out["_final_emission_meta"]["visibility_validation_passed"] is False
    assert out["_final_emission_meta"]["visibility_replacement_applied"] is True
    assert out["_final_emission_meta"]["visibility_violation_kinds"] == [
        "unseen_entity_reference",
    ]
    assert out["_final_emission_meta"]["visibility_checked_entities"] == [
        {
            "entity_id": "lord_aldric",
            "matched_aliases": ["lord aldric"],
        }
    ]


def test_pipeline_allows_visible_npc_reference():
    session, world, scene, _sid = _base_visibility_bundle()
    candidate = "Guard Captain stands near the gate."

    out = _finalize_via_turn_support(
        candidate,
        session=session,
        world=world,
        scene=scene,
    )

    assert out["player_facing_text"] == candidate
    assert out["tags"] == []
    assert out["_final_emission_meta"]["visibility_validation_passed"] is True
    assert out["_final_emission_meta"]["visibility_replacement_applied"] is False
    assert out["_final_emission_meta"]["visibility_violation_kinds"] == []
    assert out["_final_emission_meta"]["visibility_checked_entities"] == [
        {
            "entity_id": "guard_captain",
            "matched_aliases": ["guard captain"],
        }
    ]


def test_pipeline_allows_active_interlocutor_reference():
    session, world, scene, _sid = _base_visibility_bundle()
    set_social_target(session, "tavern_runner")
    candidate = 'Tavern Runner leans in and says, "Keep your hood up in this rain."'

    out = _finalize_via_turn_support(
        candidate,
        session=session,
        world=world,
        scene=scene,
    )

    assert out["player_facing_text"] == candidate
    assert out["tags"] == []
    assert out["_final_emission_meta"]["active_interlocutor_id"] == "tavern_runner"
    assert out["_final_emission_meta"]["visibility_validation_passed"] is True
    assert out["_final_emission_meta"]["visibility_replacement_applied"] is False
    assert out["_final_emission_meta"]["visibility_checked_entities"] == [
        {
            "entity_id": "tavern_runner",
            "matched_aliases": ["tavern runner"],
        }
    ]


def test_pipeline_replaces_hidden_fact_assertion():
    session, world, scene, _sid = _base_visibility_bundle()

    out = _finalize_via_turn_support(
        HIDDEN_FACT,
        session=session,
        world=world,
        scene=scene,
    )

    assert out["player_facing_text"] == GLOBAL_VISIBILITY_FALLBACK
    assert out["tags"] == [
        "final_emission_gate_replaced",
        "visibility_enforcement_replaced",
        "visibility_violation:undiscovered_fact_assertion",
    ]
    assert out["_final_emission_meta"]["visibility_validation_passed"] is False
    assert out["_final_emission_meta"]["visibility_replacement_applied"] is True
    assert out["_final_emission_meta"]["visibility_violation_kinds"] == [
        "undiscovered_fact_assertion",
    ]
    assert out["_final_emission_meta"]["visibility_checked_facts"] == [
        {
            "kind": "hidden_fact_strings",
            "fact": "the checkpoint taxes are funding an ash cowl payoff",
            "match_kind": "exact",
        }
    ]


def test_pipeline_replaces_discoverable_but_undiscovered_fact_assertion():
    session, world, scene, _sid = _base_visibility_bundle()

    out = _finalize_via_turn_support(
        DISCOVERABLE_FACT,
        session=session,
        world=world,
        scene=scene,
    )

    assert out["player_facing_text"] == GLOBAL_VISIBILITY_FALLBACK
    assert out["tags"] == [
        "final_emission_gate_replaced",
        "visibility_enforcement_replaced",
        "visibility_violation:undiscovered_fact_assertion",
    ]
    assert out["_final_emission_meta"]["visibility_validation_passed"] is False
    assert out["_final_emission_meta"]["visibility_replacement_applied"] is True
    assert out["_final_emission_meta"]["visibility_violation_kinds"] == [
        "undiscovered_fact_assertion",
    ]
    assert out["_final_emission_meta"]["visibility_checked_facts"] == [
        {
            "kind": "discoverable_fact_strings",
            "fact": "the missing patrol was last seen near the old stone bridge",
            "match_kind": "exact",
        }
    ]


def test_pipeline_allows_visible_fact_assertion():
    session, world, scene, _sid = _base_visibility_bundle()

    out = _finalize_via_turn_support(
        VISIBLE_FACT,
        session=session,
        world=world,
        scene=scene,
    )

    assert out["player_facing_text"] == VISIBLE_FACT
    assert out["tags"] == []
    assert out["_final_emission_meta"]["visibility_validation_passed"] is True
    assert out["_final_emission_meta"]["visibility_replacement_applied"] is False
    assert out["_final_emission_meta"]["visibility_violation_kinds"] == []
    assert out["_final_emission_meta"]["visibility_checked_facts"] == [
        {
            "kind": "visible_fact_strings",
            "fact": "a brazier throws orange sparks over the checkpoint",
            "match_kind": "exact",
        }
    ]


def test_pipeline_visibility_metadata_captures_entity_and_fact_matches():
    session, world, scene, _sid = _base_visibility_bundle()

    out = _finalize_via_turn_support(
        f"Lord Aldric says {HIDDEN_FACT}",
        session=session,
        world=world,
        scene=scene,
    )

    meta = out["_final_emission_meta"]
    assert out["player_facing_text"] == GLOBAL_VISIBILITY_FALLBACK
    assert meta["visibility_validation_passed"] is False
    assert meta["visibility_replacement_applied"] is True
    assert meta["visibility_violation_kinds"] == [
        "unseen_entity_reference",
        "undiscovered_fact_assertion",
    ]
    assert meta["visibility_checked_entities"] == [
        {
            "entity_id": "lord_aldric",
            "matched_aliases": ["lord aldric"],
        }
    ]
    assert meta["visibility_checked_facts"] == [
        {
            "kind": "hidden_fact_strings",
            "fact": "the checkpoint taxes are funding an ash cowl payoff",
            "match_kind": "substring",
        }
    ]
    assert [sample["kind"] for sample in meta["visibility_violation_sample"]] == [
        "unseen_entity_reference",
        "undiscovered_fact_assertion",
    ]


def test_pipeline_visibility_enforcement_is_read_only_for_discovery_state(monkeypatch):
    session, world, scene, sid = _base_visibility_bundle()
    runtime = get_scene_runtime(session, sid)
    runtime["discovered_clues"].append("Known clue.")
    runtime["revealed_hidden_facts"].append("Known secret.")
    session["clue_knowledge"] = {
        "known_clue": {
            "text": "Known clue.",
            "source_scene": sid,
        }
    }
    scene["scene"]["visible_facts"].append("The rain has started to ease.")

    monkeypatch.setattr(api_turn_support, "apply_repeated_description_guard", lambda gm, session, scene_id: None)
    monkeypatch.setattr(api_turn_support, "update_scene_momentum_runtime", lambda session, scene_id, gm: {})

    before_session = deepcopy(session)
    before_world = deepcopy(world)
    before_scene = deepcopy(scene)
    before_runtime = deepcopy(get_scene_runtime(session, sid))
    before_clue_knowledge = deepcopy(session["clue_knowledge"])

    out = _finalize_via_turn_support(
        HIDDEN_FACT,
        session=session,
        world=world,
        scene=scene,
    )

    assert out["player_facing_text"] == GLOBAL_VISIBILITY_FALLBACK
    assert get_scene_runtime(session, sid) == before_runtime
    assert session["clue_knowledge"] == before_clue_knowledge
    assert session == before_session
    assert world == before_world
    assert scene == before_scene


def test_pipeline_replaces_pronoun_before_first_explicit_entity():
    session, world, scene, _sid = _base_visibility_bundle()
    candidate = "He leans closer through the rain. Guard Captain studies your face."

    out = _finalize_via_turn_support(candidate, session=session, world=world, scene=scene)

    assert out["player_facing_text"] != candidate
    meta = out["_final_emission_meta"]
    assert meta["first_mention_validation_passed"] is False
    assert meta["first_mention_replacement_applied"] is True
    assert "pronoun_before_first_explicit_entity" in meta["first_mention_violation_kinds"]
    assert meta["first_mention_leading_pronoun_detected"] is True
    assert meta["first_mention_fallback_strategy"] == "composed_visible_scene_intro"
    assert meta["first_mention_fallback_candidate_source"] == "visible_scene_composed_intro"
    assert meta["opening_scene_first_mention_preference_used"] is True
    assert "first_mention_enforcement_replaced" in out["tags"]


def test_pipeline_replaces_unearned_familiarity_first_intro():
    session, world, scene, _sid = _base_visibility_bundle()
    candidate = "Guard Captain stands near the gate; you recognize him immediately."

    out = _finalize_via_turn_support(candidate, session=session, world=world, scene=scene)

    assert out["player_facing_text"] != candidate
    meta = out["_final_emission_meta"]
    assert meta["first_mention_validation_passed"] is False
    assert meta["first_mention_replacement_applied"] is True
    assert "first_mention_unearned_familiarity" in meta["first_mention_violation_kinds"]


def test_pipeline_replaces_first_mention_missing_grounding():
    session, world, scene, _sid = _base_visibility_bundle()
    candidate = "Guard Captain appears."

    out = _finalize_via_turn_support(candidate, session=session, world=world, scene=scene)

    assert out["player_facing_text"] != candidate
    meta = out["_final_emission_meta"]
    assert meta["first_mention_validation_passed"] is False
    assert meta["first_mention_replacement_applied"] is True
    assert "first_mention_missing_grounding" in meta["first_mention_violation_kinds"]


def test_pipeline_allows_grounded_explicit_first_intro():
    session, world, scene, _sid = _base_visibility_bundle()
    candidate = "Guard Captain stands near the gate."

    out = _finalize_via_turn_support(candidate, session=session, world=world, scene=scene)

    assert out["player_facing_text"] == candidate
    meta = out["_final_emission_meta"]
    assert meta["first_mention_validation_passed"] is True
    assert meta["first_mention_replacement_applied"] is False
    assert meta["first_mention_violation_kinds"] == []


def test_pipeline_allows_grounded_active_interlocutor_intro():
    session, world, scene, _sid = _base_visibility_bundle()
    set_social_target(session, "tavern_runner")
    candidate = 'Tavern Runner beside the shuttered bar says, "Keep your hood low."'

    out = _finalize_via_turn_support(candidate, session=session, world=world, scene=scene)

    assert out["player_facing_text"] == candidate
    meta = out["_final_emission_meta"]
    assert meta["first_mention_validation_passed"] is True
    assert meta["first_mention_replacement_applied"] is False
    assert meta["active_interlocutor_id"] == "tavern_runner"


def test_pipeline_allows_opening_scene_composition_with_later_grounded_first_entity_mention():
    session, world, scene, _sid = _base_visibility_bundle()
    candidate = (
        "Nearby, cart wheels hiss over the wet stones while vendors shout under the awning, "
        "and Guard Captain calls for the line to keep moving at the gate."
    )

    out = _finalize_via_turn_support(candidate, session=session, world=world, scene=scene)

    assert out["player_facing_text"] == candidate
    meta = out["_final_emission_meta"]
    assert meta["first_mention_validation_passed"] is True
    assert meta["first_mention_replacement_applied"] is False
    assert meta["first_mention_violation_kinds"] == []


def test_pipeline_first_mention_metadata_records_checked_entities():
    session, world, scene, _sid = _base_visibility_bundle()
    candidate = "Guard Captain appears."

    out = _finalize_via_turn_support(candidate, session=session, world=world, scene=scene)

    meta = out["_final_emission_meta"]
    checked = meta["first_mention_checked_entities"]
    assert isinstance(checked, list)
    assert checked
    first = checked[0]
    assert first["entity_id"] == "guard_captain"
    assert "matched_alias" in first
    assert "first_offset" in first
    assert "grounding_present" in first
    assert "violation_kinds" in first


def test_pipeline_visibility_failure_skips_first_mention_but_keeps_default_meta_shape():
    session, world, scene, _sid = _base_visibility_bundle()
    candidate = "Lord Aldric watches the checkpoint from the square."

    out = _finalize_via_turn_support(candidate, session=session, world=world, scene=scene)

    assert out["player_facing_text"] == GLOBAL_VISIBILITY_FALLBACK
    meta = out["_final_emission_meta"]
    _assert_first_mention_default_meta_shape(meta)
    _assert_referential_clarity_default_meta_shape(meta)
    assert meta["visibility_validation_passed"] is False
    assert meta["visibility_replacement_applied"] is True
    assert meta["first_mention_validation_passed"] is None
    assert meta["first_mention_replacement_applied"] is False
    assert meta["first_mention_violation_kinds"] == []
    assert meta["first_mention_checked_entities"] == []
    assert meta["first_mention_leading_pronoun_detected"] is False
    assert meta["first_mention_first_explicit_entity_offset"] is None
    assert meta["first_mention_fallback_strategy"] is None
    assert meta["first_mention_fallback_candidate_source"] is None
    assert meta["opening_scene_first_mention_preference_used"] is False
    assert meta["referential_clarity_validation_passed"] is None
    assert meta["referential_clarity_replacement_applied"] is False
    assert meta["referential_clarity_violation_kinds"] == []
    assert meta["referential_clarity_checked_entities"] == []
    assert meta["referential_clarity_violation_sample"] == []


def test_pipeline_first_mention_fallback_also_satisfies_gate_when_replacement_needed():
    session, world, scene, _sid = _base_visibility_bundle()
    candidate = "He leans closer through the rain. Guard Captain studies your face."

    out = _finalize_via_turn_support(candidate, session=session, world=world, scene=scene)

    meta = out["_final_emission_meta"]
    assert meta["first_mention_replacement_applied"] is True
    validation = validate_player_facing_first_mentions(
        out["player_facing_text"],
        session=session,
        scene=scene,
        world=world,
    )
    assert validation["ok"] is True


def test_pipeline_opening_scene_pronoun_failure_prefers_grounded_visible_scene_fallback():
    session, world, scene, _sid = _base_visibility_bundle()
    candidate = "He watches the line in silence. Guard Captain studies the press at the gate."

    out = _finalize_via_turn_support(candidate, session=session, world=world, scene=scene)

    meta = out["_final_emission_meta"]
    assert meta["first_mention_replacement_applied"] is True
    assert out["player_facing_text"] != GLOBAL_VISIBILITY_FALLBACK
    assert "guard captain" in out["player_facing_text"].lower()
    assert any(token in out["player_facing_text"].lower() for token in ("gate", "rain", "approach", "crowd"))
    assert meta["first_mention_fallback_strategy"] == "composed_visible_scene_intro"
    assert meta["first_mention_fallback_candidate_source"] == "visible_scene_composed_intro"
    assert meta["final_emitted_source"] == "composed_visible_scene_intro"
    assert meta["opening_scene_first_mention_preference_used"] is True


def test_pipeline_composed_scene_intro_avoids_repeated_trivial_verbs_when_fact_backed_actions_exist():
    session, world, scene, _sid = _rich_scene_visibility_bundle()
    candidate = "He leans closer through the rain. Guard Captain studies your face."

    out = _finalize_via_turn_support(candidate, session=session, world=world, scene=scene)

    text = out["player_facing_text"].lower()
    meta = out["_final_emission_meta"]
    assert meta["first_mention_replacement_applied"] is True
    assert meta["first_mention_fallback_strategy"] == "composed_visible_scene_intro"
    assert meta["final_emitted_source"] == "composed_visible_scene_intro"
    assert any(token in text for token in ("rain", "gate", "muddy", "crowd"))
    assert any(name in text for name in ("guard captain", "tavern runner", "threadbare watcher", "ragged stranger"))
    assert "guard captain shouts, while tavern runner shouts" not in text
    assert text.count(" shouts") <= 1
    validation = validate_player_facing_first_mentions(
        out["player_facing_text"],
        session=session,
        scene=scene,
        world=world,
    )
    assert validation["ok"] is True


def test_pipeline_visibility_and_first_mention_metadata_coexist():
    session, world, scene, _sid = _base_visibility_bundle()
    candidate = "Guard Captain stands near the gate."

    out = _finalize_via_turn_support(candidate, session=session, world=world, scene=scene)

    meta = out["_final_emission_meta"]
    assert "visibility_validation_passed" in meta
    assert "visibility_replacement_applied" in meta
    assert "visibility_violation_kinds" in meta
    _assert_first_mention_default_meta_shape(meta)
    _assert_referential_clarity_default_meta_shape(meta)
    assert meta["visibility_validation_passed"] is True
    assert meta["first_mention_validation_passed"] is True
    assert meta["referential_clarity_validation_passed"] is True


def test_pipeline_referential_clarity_allows_single_named_referent_followed_by_pronoun():
    session, world, scene, _sid = _base_visibility_bundle()
    candidate = "Guard Captain leans closer. He studies your face."

    out = _finalize_via_turn_support(candidate, session=session, world=world, scene=scene)

    assert out["player_facing_text"] == candidate
    meta = out["_final_emission_meta"]
    _assert_referential_clarity_default_meta_shape(meta)
    assert meta["referential_clarity_validation_passed"] is True
    assert meta["referential_clarity_replacement_applied"] is False
    assert meta["referential_clarity_violation_kinds"] == []
    assert "referential_clarity_enforcement_replaced" not in out["tags"]


def test_pipeline_referential_clarity_allows_singular_they_for_single_local_person_referent():
    session, world, scene, _sid = _base_visibility_bundle()
    candidate = "Guard Captain leans closer. Their voice drops to a whisper."

    out = _finalize_via_turn_support(candidate, session=session, world=world, scene=scene)

    assert out["player_facing_text"] == candidate
    meta = out["_final_emission_meta"]
    _assert_referential_clarity_default_meta_shape(meta)
    assert meta["referential_clarity_validation_passed"] is True
    assert meta["referential_clarity_replacement_applied"] is False
    assert meta["referential_clarity_violation_kinds"] == []


def test_pipeline_referential_clarity_replaces_same_sentence_ambiguous_pronoun():
    session, world, scene, _sid = _base_visibility_bundle()
    candidate = "Guard Captain and Tavern Runner trade hard looks. He steps forward."

    out = _finalize_via_turn_support(candidate, session=session, world=world, scene=scene)

    assert out["player_facing_text"] != candidate
    meta = out["_final_emission_meta"]
    assert meta["referential_clarity_validation_passed"] is False
    assert meta["referential_clarity_replacement_applied"] is True
    assert "ambiguous_entity_reference" in meta["referential_clarity_violation_kinds"]
    assert "referential_clarity_enforcement_replaced" in out["tags"]
    assert "referential_clarity_violation:ambiguous_entity_reference" in out["tags"]


def test_pipeline_referential_clarity_replaces_next_sentence_ambiguous_pronoun():
    session, world, scene, _sid = _base_visibility_bundle()
    candidate = "Guard Captain speaks with Tavern Runner near the brazier. He lowers his voice."

    out = _finalize_via_turn_support(candidate, session=session, world=world, scene=scene)

    assert out["player_facing_text"] != candidate
    meta = out["_final_emission_meta"]
    assert meta["referential_clarity_validation_passed"] is False
    assert meta["referential_clarity_replacement_applied"] is True
    assert "ambiguous_entity_reference" in meta["referential_clarity_violation_kinds"]


def test_pipeline_referential_clarity_allows_explicit_reanchor():
    session, world, scene, _sid = _base_visibility_bundle()
    candidate = "Guard Captain and Tavern Runner trade hard looks. Guard Captain steps forward."

    out = _finalize_via_turn_support(candidate, session=session, world=world, scene=scene)

    assert out["player_facing_text"] == candidate
    meta = out["_final_emission_meta"]
    assert meta["referential_clarity_validation_passed"] is True
    assert meta["referential_clarity_replacement_applied"] is False


def test_pipeline_referential_clarity_allows_descriptor_reanchor_when_unique():
    session, world, scene, _sid = _base_visibility_bundle()
    candidate = "Guard Captain and Tavern Runner argue near the gate. The captain steps closer."

    out = _finalize_via_turn_support(candidate, session=session, world=world, scene=scene)

    meta = out["_final_emission_meta"]
    _assert_referential_clarity_default_meta_shape(meta)
    assert out["player_facing_text"] == candidate
    assert meta["referential_clarity_validation_passed"] is True
    assert meta["referential_clarity_replacement_applied"] is False
    assert meta["referential_clarity_violation_kinds"] == []


def test_pipeline_referential_clarity_replaces_ambiguous_descriptor_reanchor():
    session, world, scene, _sid = _visibility_bundle_with_extra_addressables(
        {
            "id": "left_guard",
            "name": "Left Guard",
            "scene_id": "frontier_gate",
            "kind": "scene_actor",
            "addressable": True,
            "address_priority": 4,
            "address_roles": ["guard"],
            "aliases": ["left guard"],
        }
    )
    candidate = "Two guards block the way. The guard taps the pommel of a sheathed sword."

    out = _finalize_via_turn_support(candidate, session=session, world=world, scene=scene)

    meta = out["_final_emission_meta"]
    _assert_referential_clarity_default_meta_shape(meta)
    assert out["player_facing_text"] != candidate
    assert meta["referential_clarity_validation_passed"] is False
    assert meta["referential_clarity_replacement_applied"] is True
    assert "ambiguous_entity_reference" in meta["referential_clarity_violation_kinds"]
    assert "referential_clarity_enforcement_replaced" in out["tags"]


def test_pipeline_referential_clarity_allows_unique_nonperson_pronoun():
    session, world, scene, _sid = _base_visibility_bundle()
    candidate = "Guard Captain stands near the gate holding the lantern. Its light catches the rain."

    out = _finalize_via_turn_support(candidate, session=session, world=world, scene=scene)

    meta = out["_final_emission_meta"]
    _assert_referential_clarity_default_meta_shape(meta)
    assert out["player_facing_text"] == candidate
    assert meta["referential_clarity_validation_passed"] is True
    assert meta["referential_clarity_replacement_applied"] is False


def test_pipeline_referential_clarity_replaces_ambiguous_nonperson_pronoun():
    session, world, scene, _sid = _base_visibility_bundle()
    candidate = "Guard Captain sets the lantern beside the note. It glints in the dark."

    out = _finalize_via_turn_support(candidate, session=session, world=world, scene=scene)

    meta = out["_final_emission_meta"]
    _assert_referential_clarity_default_meta_shape(meta)
    assert out["player_facing_text"] != candidate
    assert meta["referential_clarity_validation_passed"] is False
    assert meta["referential_clarity_replacement_applied"] is True
    assert "ambiguous_entity_reference" in meta["referential_clarity_violation_kinds"]
    assert "referential_clarity_enforcement_replaced" in out["tags"]


def test_pipeline_referential_clarity_replaces_neuter_pronoun_in_person_only_context():
    session, world, scene, _sid = _base_visibility_bundle()
    candidate = "The captain stands near the gate with the courier. It sways in the rain."

    out = _finalize_via_turn_support(candidate, session=session, world=world, scene=scene)

    meta = out["_final_emission_meta"]
    assert out["player_facing_text"] != candidate
    assert meta["referential_clarity_validation_passed"] is False
    assert meta["referential_clarity_replacement_applied"] is True
    assert "ambiguous_entity_reference" in meta["referential_clarity_violation_kinds"]


def test_pipeline_referential_clarity_allows_clear_quoted_speaker_tag():
    session, world, scene, _sid = _base_visibility_bundle()
    candidate = 'Guard Captain stands near the gate. "Open the gate," he says.'

    out = _finalize_via_turn_support(candidate, session=session, world=world, scene=scene)

    meta = out["_final_emission_meta"]
    _assert_referential_clarity_default_meta_shape(meta)
    assert out["player_facing_text"] == candidate
    assert meta["referential_clarity_validation_passed"] is True
    assert meta["referential_clarity_replacement_applied"] is False


def test_pipeline_referential_clarity_replaces_ambiguous_quoted_speaker_tag():
    session, world, scene, _sid = _base_visibility_bundle()
    candidate = 'Guard Captain and Tavern Runner stand near the gate. "Back away," he says.'

    out = _finalize_via_turn_support(candidate, session=session, world=world, scene=scene)

    meta = out["_final_emission_meta"]
    assert out["player_facing_text"] != candidate
    assert meta["referential_clarity_validation_passed"] is False
    assert meta["referential_clarity_replacement_applied"] is True
    assert "ambiguous_entity_reference" in meta["referential_clarity_violation_kinds"]
    assert "referential_clarity_enforcement_replaced" in out["tags"]


def test_pipeline_referential_clarity_replaces_referent_drift_after_new_competitor():
    session, world, scene, _sid = _base_visibility_bundle()
    candidate = "Guard Captain leans closer. Tavern Runner answers from the doorway. He folds his arms."

    out = _finalize_via_turn_support(candidate, session=session, world=world, scene=scene)

    assert out["player_facing_text"] != candidate
    meta = out["_final_emission_meta"]
    assert meta["referential_clarity_validation_passed"] is False
    assert meta["referential_clarity_replacement_applied"] is True
    assert any(kind in meta["referential_clarity_violation_kinds"] for kind in ("referent_drift", "ambiguous_entity_reference"))


def test_pipeline_referential_clarity_replaces_singular_they_with_multiple_active_person_candidates():
    session, world, scene, _sid = _base_visibility_bundle()
    candidate = "Guard Captain and Tavern Runner watch you closely. Their voices stay low."

    out = _finalize_via_turn_support(candidate, session=session, world=world, scene=scene)

    meta = out["_final_emission_meta"]
    _assert_referential_clarity_default_meta_shape(meta)
    assert out["player_facing_text"] != candidate
    assert meta["referential_clarity_validation_passed"] is False
    assert meta["referential_clarity_replacement_applied"] is True
    assert "ambiguous_entity_reference" in meta["referential_clarity_violation_kinds"]
    assert "referential_clarity_enforcement_replaced" in out["tags"]


def test_pipeline_referential_clarity_metadata_shape_always_present_on_pass():
    session, world, scene, _sid = _base_visibility_bundle()
    candidate = "Guard Captain leans closer. He studies your face."

    out = _finalize_via_turn_support(candidate, session=session, world=world, scene=scene)

    meta = out["_final_emission_meta"]
    _assert_referential_clarity_default_meta_shape(meta)
    assert isinstance(meta["referential_clarity_checked_entities"], list)
    assert isinstance(meta["referential_clarity_violation_sample"], list)


def test_validate_player_facing_referential_clarity_records_referent_drift():
    session, world, scene, _sid = _base_visibility_bundle()
    result = validate_player_facing_referential_clarity(
        "Guard Captain leans closer. Tavern Runner answers from the doorway. He folds his arms.",
        session=session,
        scene=scene,
        world=world,
    )

    kinds = [v.get("kind") for v in result["violations"] if isinstance(v, dict)]
    assert "referent_drift" in kinds


def test_validate_player_facing_first_mentions_pronoun_before_explicit_entity():
    session, world, scene, _sid = _base_visibility_bundle()
    result = validate_player_facing_first_mentions(
        "He leans in. Guard Captain watches the road.",
        session=session,
        scene=scene,
        world=world,
    )
    kinds = [v.get("kind") for v in result["violations"] if isinstance(v, dict)]
    assert "pronoun_before_first_explicit_entity" in kinds


def test_validate_player_facing_first_mentions_unearned_familiarity():
    session, world, scene, _sid = _base_visibility_bundle()
    result = validate_player_facing_first_mentions(
        "You recognize Guard Captain immediately.",
        session=session,
        scene=scene,
        world=world,
    )
    kinds = [v.get("kind") for v in result["violations"] if isinstance(v, dict)]
    assert "first_mention_unearned_familiarity" in kinds


def test_validate_player_facing_first_mentions_accepts_grounded_intro():
    session, world, scene, _sid = _base_visibility_bundle()
    result = validate_player_facing_first_mentions(
        "Guard Captain stands near the gate.",
        session=session,
        scene=scene,
        world=world,
    )
    assert result["ok"] is True


def test_validate_player_facing_first_mentions_accepts_opening_scene_sentence_grounded_by_opener_and_action():
    session, world, scene, _sid = _base_visibility_bundle()
    result = validate_player_facing_first_mentions(
        (
            "Nearby, cart wheels hiss over the wet stones while vendors shout under the awning, "
            "and Guard Captain calls for the line to keep moving at the gate."
        ),
        session=session,
        scene=scene,
        world=world,
    )
    assert result["ok"] is True


@pytest.mark.parametrize(
    "candidate",
    [
        "Guard Captain is there.",
        "Tavern Runner is present.",
    ],
)
def test_validate_player_facing_first_mentions_rejects_vague_presence_only_openings(candidate: str):
    session, world, scene, _sid = _base_visibility_bundle()
    result = validate_player_facing_first_mentions(
        candidate,
        session=session,
        scene=scene,
        world=world,
    )
    kinds = [v.get("kind") for v in result["violations"] if isinstance(v, dict)]
    assert "first_mention_missing_grounding" in kinds


def test_sentence_decompression_splits_semicolon_alternatives():
    text = (
        "Off to Galinor's left, two alleyways present themselves; "
        "one is narrow and shadowy, the other wider and lively, leading toward the tavern."
    )
    out = _decompress_overpacked_sentences(text)

    assert "; one is narrow and shadowy" not in out.lower()
    assert out.count(".") >= 3
    assert "two alleyways present themselves" in out.lower()
    assert "narrow and shadowy" in out.lower()
    assert "wider and lively" in out.lower()


def test_sentence_decompression_splits_long_participial_tail():
    text = (
        "Nearby, the tavern runner energetically shouts offers of warm stew above the rain-slick crowd as wagons creak "
        "through the gate, hinting at deeper tensions surrounding the missing patrol."
    )
    out = _decompress_overpacked_sentences(text)

    assert ", hinting at deeper tensions surrounding the missing patrol" not in out.lower()
    assert out.count(".") >= 2
    assert "tavern runner" in out.lower()
    assert "missing patrol" in out.lower()


def test_fragmentary_participial_split_repair_anchors_to_previous_sentence():
    text = (
        "Nearby, a tavern runner calls out urgently. "
        "Offering both warm stew and rumors, their voice cutting through the din."
    )
    repaired, applied = _repair_fragmentary_participial_splits(text)

    assert applied is True
    assert "They offer both warm stew and rumors." in repaired
    assert "Their voice cuts through the din." in repaired


def test_fragmentary_participial_split_repair_uses_sparse_it_subject_for_hinting():
    text = "The rain taps steadily on the awning. Hinting at trouble just beyond the square."
    repaired, applied = _repair_fragmentary_participial_splits(text)

    assert applied is True
    assert "It hints at trouble just beyond the square." in repaired


def test_fragmentary_participial_split_repair_preserves_uncertain_suggesting_clause():
    text = "A stranger watches from the edge of the crowd. Suggesting he knows more than he says."
    repaired, applied = _repair_fragmentary_participial_splits(text)

    assert applied is False
    assert repaired == text


def test_micro_smoothing_merges_short_they_to_they_pair():
    text = "They offer both warm stew and rumors. They gesture toward the tavern."

    smoothed, applied = _micro_smooth_post_repair_sentences(text)

    assert applied is True
    assert smoothed != text
    assert smoothed.count(".") == 1
    assert len(smoothed) <= 140
    assert "They offer both warm stew and rumors" in smoothed
    assert "gesture toward the tavern" in smoothed
    assert "suggesting" not in smoothed.lower()
    assert "implying" not in smoothed.lower()
    assert "revealing" not in smoothed.lower()
    assert "indicating" not in smoothed.lower()


def test_micro_smoothing_merges_short_they_to_their_continuation():
    text = "They offer both warm stew and rumors. Their voice cuts."

    smoothed, applied = _micro_smooth_post_repair_sentences(text)

    assert applied is True
    assert smoothed != text
    assert smoothed.count(".") == 1
    assert "They offer both warm stew and rumors" in smoothed
    assert "their voice cutting" in smoothed.lower()
    assert "suggesting" not in smoothed.lower()
    assert "implying" not in smoothed.lower()
    assert "revealing" not in smoothed.lower()
    assert "indicating" not in smoothed.lower()


def test_micro_smoothing_preserves_when_anchor_changes():
    text = "The tavern runner calls out from the awning. A guard scans the square."

    smoothed, applied = _micro_smooth_post_repair_sentences(text)

    assert applied is False
    assert smoothed == text
    assert smoothed.count(".") == 2


@pytest.mark.parametrize(
    "tail_sentence",
    [
        "Their expression hints at more than they say.",
        "Their expression suggests they know more than they say.",
        "Their expression reveals more than they say.",
        "Their expression indicates more than they say.",
        "Their expression implying more than they say.",
    ],
)
def test_micro_smoothing_preserves_when_second_sentence_is_implication_language(tail_sentence: str):
    text = f"They pause at the gate. {tail_sentence}"

    smoothed, applied = _micro_smooth_post_repair_sentences(text)

    assert applied is False
    assert smoothed == text
    assert smoothed.count(".") == 2
    assert ", their expression" not in smoothed.lower()


def test_micro_smoothing_preserves_dialogue_like_text():
    text = 'They offer both warm stew and rumors. "Keep your hood low," they whisper.'

    smoothed, applied = _micro_smooth_post_repair_sentences(text)

    assert applied is False
    assert smoothed == text


def test_micro_smoothing_does_not_treat_contractions_as_dialogue():
    text = "They don't linger. They scan the road."

    smoothed, applied = _micro_smooth_post_repair_sentences(text)

    assert applied is True
    assert smoothed != text
    assert "don't linger" in smoothed.lower()
    assert smoothed.count(".") == 1


def test_micro_smoothing_allows_simple_list_heavy_sentence_when_otherwise_safe():
    text = "They carry bandages and lamp oil. They wave toward shelter."

    smoothed, applied = _micro_smooth_post_repair_sentences(text)

    assert applied is True
    assert smoothed != text
    assert smoothed.count(".") == 1
    assert "bandages and lamp oil" in smoothed.lower()


def test_micro_smoothing_never_merges_more_than_one_pair_per_passage():
    text = (
        "They offer both warm stew and rumors. "
        "They gesture toward the tavern. "
        "They scan the muddy lane. "
        "They watch the gate."
    )

    smoothed, applied = _micro_smooth_post_repair_sentences(text)

    assert applied is True
    assert smoothed.count(".") == 3
    assert "They scan the muddy lane. They watch the gate." in smoothed


def test_micro_smoothing_respects_combined_length_guardrail():
    text = (
        "They map every alley from the awning to the south culvert and the watch post near the flooded square. "
        "They recount each route marker, shuttered stall, and wagon scar to keep your notes exact."
    )

    smoothed, applied = _micro_smooth_post_repair_sentences(text)

    assert applied is False
    assert smoothed == text
    assert smoothed.count(".") == 2


def test_micro_smoothing_preserves_mechanical_or_combat_text():
    text = "They roll initiative as steel clears leather. They draw and close the distance."

    smoothed, applied = _micro_smooth_post_repair_sentences(text)

    assert applied is False
    assert smoothed == text


def test_micro_smoothing_preserves_already_clean_output_when_no_clear_gain():
    text = "They watch the awning. A guard checks the queue."

    smoothed, applied = _micro_smooth_post_repair_sentences(text)

    assert applied is False
    assert smoothed == text


def test_finalization_pipeline_metadata_for_micro_smoothing():
    session, world, scene, _sid = _base_visibility_bundle()
    repaired_candidate = (
        "Nearby, a tavern runner calls out urgently, offering both warm stew and rumors, their voice cutting."
    )
    repaired_out = _finalize_via_turn_support(
        repaired_candidate,
        session=session,
        world=world,
        scene=scene,
    )
    assert repaired_out["_final_emission_meta"]["sentence_decompression_applied"] is True
    assert repaired_out["_final_emission_meta"]["sentence_fragment_repair_applied"] is True
    assert repaired_out["_final_emission_meta"]["sentence_micro_smoothing_applied"] is True

    plain_out = _finalize_via_turn_support(
        "Guard Captain stands near the gate.",
        session=session,
        world=world,
        scene=scene,
    )
    assert plain_out["_final_emission_meta"]["sentence_decompression_applied"] is False
    assert plain_out["_final_emission_meta"]["sentence_fragment_repair_applied"] is False
    assert plain_out["_final_emission_meta"]["sentence_micro_smoothing_applied"] is False
