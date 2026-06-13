from __future__ import annotations

import game.final_emission_gate as feg
from game.final_emission_text import _normalize_text
from tests.helpers.emission_smoke_assertions import final_emission_meta_from_output
from tests.helpers.objective7_referent_fixtures import (
    minimal_full_referent_artifact,
    referent_compact_mirror,
)

import pytest

from game.interaction_context import rebuild_active_scene_entities
from game.narration_visibility import (
    _THIRD_PERSON_PRONOUN_RE,
    _build_visible_referential_candidates,
    _detect_explicit_entity_mentions,
    _is_player_character_local_pronoun_reference,
    _normalize_visibility_text,
    _split_visibility_sentences,
    build_narration_visibility_contract,
    validate_player_facing_referential_clarity,
)
from tests.test_final_emission_visibility import _base_visibility_bundle, _finalize_via_turn_support

pytestmark = pytest.mark.unit


def _bundle_with_galinor():
    session, world, scene, sid = _base_visibility_bundle()
    session["character_name"] = "Galinor"
    rebuild_active_scene_entities(session, world, sid, scene_envelope=scene)
    scene["scene_state"] = dict(session["scene_state"])
    return session, world, scene, sid


def _pronoun_start_in_sentence(*, normalized_text: str, sentence_index: int, token: str = "he") -> tuple[int, int]:
    sentences = _split_visibility_sentences(normalized_text)
    s = sentences[sentence_index]
    st = int(s["start"])
    sent_text = str(s["text"] or "")
    for m in _THIRD_PERSON_PRONOUN_RE.finditer(sent_text):
        if m.group(0).lower() == token:
            return st, st + int(m.start())
    raise AssertionError(f"no pronoun {token!r} in sentence {sentence_index}")


def test_pc_local_continuation_passes_two_he_spans():
    session, world, scene, _ = _bundle_with_galinor()
    text = _normalize_visibility_text(
        "Galinor walks down the narrow alley, and as he peers into the gloom, he spots two weathered doorways."
    )
    r = validate_player_facing_referential_clarity(text, session=session, scene=scene, world=world)
    assert r["ok"] is True
    assert r.get("violations") == []
    assert r.get("referential_clarity_player_coref_safe_harbor_used") is True
    assert r.get("referential_clarity_player_coref_safe_harbor_tokens") == ["he", "he"]


def test_pc_reflexive_and_followup_he_passes():
    session, world, scene, _ = _bundle_with_galinor()
    text = _normalize_visibility_text("Galinor steadies himself before he pushes the door.")
    r = validate_player_facing_referential_clarity(text, session=session, scene=scene, world=world)
    assert r["ok"] is True
    assert r.get("referential_clarity_player_coref_safe_harbor_used") is True


def test_ambiguous_npc_chain_still_fails():
    session, world, scene, _ = _bundle_with_galinor()
    text = _normalize_visibility_text(
        "The tavern runner looks at the guard captain, and he nods."
    )
    r = validate_player_facing_referential_clarity(text, session=session, scene=scene, world=world)
    assert r["ok"] is False
    kinds = [v.get("kind") for v in r.get("violations") or [] if isinstance(v, dict)]
    assert "ambiguous_entity_reference" in kinds
    assert r.get("referential_clarity_player_coref_safe_harbor_used") is not True


def test_pronoun_first_sentence_still_fails_referential_clarity():
    session, world, scene, _ = _bundle_with_galinor()
    text = _normalize_visibility_text("He walks down the alley.")
    r = validate_player_facing_referential_clarity(text, session=session, scene=scene, world=world)
    assert r["ok"] is False


def test_competing_person_between_pc_and_pronoun_disables_helper():
    session, world, scene, _ = _bundle_with_galinor()
    text = _normalize_visibility_text("Galinor looks toward the guard captain as he enters the alley.")
    contract = build_narration_visibility_contract(session=session, scene=scene, world=world)
    cands = _build_visible_referential_candidates(contract)
    candidates_by_id = {
        str(c.get("entity_id") or "").strip(): c
        for c in cands
        if isinstance(c, dict) and str(c.get("entity_id") or "").strip()
    }
    mentions = _detect_explicit_entity_mentions(text, cands)
    sentence_start, pronoun_start = _pronoun_start_in_sentence(normalized_text=text, sentence_index=0)
    assert (
        _is_player_character_local_pronoun_reference(
            normalized_text=text,
            sentence_start=sentence_start,
            pronoun_start=pronoun_start,
            pronoun_token="he",
            session=session,
            contract=contract,
            candidates_by_id=candidates_by_id,
            sentence_mentions=mentions,
        )
        is False
    )


def test_session_pronoun_constraint_blocks_mismatched_pronoun():
    session, world, scene, _ = _bundle_with_galinor()
    session["character_pronouns"] = "she"
    text = _normalize_visibility_text(
        "Galinor walks down the narrow alley, and as he peers into the gloom, he spots two doorways."
    )
    r = validate_player_facing_referential_clarity(text, session=session, scene=scene, world=world)
    assert r["ok"] is False
    assert r.get("referential_clarity_player_coref_safe_harbor_used") is not True


def test_integration_exploration_alley_doorways_not_replaced():
    session, world, scene, _ = _bundle_with_galinor()
    candidate = (
        "Galinor walks down the narrow, shadowy alleyway, and as he peers into the gloom, "
        "he spots two weathered doorways set deep in the stone."
    )
    out = _finalize_via_turn_support(candidate, session=session, world=world, scene=scene)
    assert out["player_facing_text"] == candidate
    assert "doorway" in out["player_facing_text"].lower()
    meta = final_emission_meta_from_output(out)
    assert meta.get("referential_clarity_validation_passed") is True
    assert meta.get("referential_clarity_replacement_applied") is False


def test_referent_clarity_pre_finalize_merges_fem_and_tracks_input_source():
    art = minimal_full_referent_artifact(referential_ambiguity_class="none", ambiguity_risk=5)
    out = {
        "player_facing_text": "They halt.",
        "prompt_context": {"referent_tracking": art},
        "_gate_turn_packet_cache": {
            "referent_tracking_compact": referent_compact_mirror(
                referential_ambiguity_class="ambiguous_singular",
                ambiguity_risk=40,
            )
        },
        "_final_emission_meta": {"final_route": "accept_candidate", "tone_escalation": {"lane": "stub"}},
    }
    feg._apply_referent_clarity_pre_finalize(out, pre_gate_text="They halt.")
    fem = final_emission_meta_from_output(out)
    assert fem["referent_validation_input_source"] == "full_artifact"
    assert fem["referent_validation_ran"] is True
    assert fem["referent_repair_applied"] is False
    assert fem.get("referent_boundary_semantic_repair_disabled") is True
    assert out["player_facing_text"] == "They halt."
    assert fem.get("tone_escalation") == {"lane": "stub"}
    gtxt = _normalize_text(out["player_facing_text"])
    preview = (gtxt[:120] + "…") if len(gtxt) > 120 else gtxt
    assert fem.get("final_text_preview") == preview
    assert fem.get("post_gate_mutation_detected") is False


def test_referent_clarity_pre_finalize_four_gate_exit_paths_all_use_same_hook():
    """Documentation-by-test: referent pre-finalize is invoked from each finalize branch."""
    import inspect

    src = inspect.getsource(feg.apply_final_emission_gate)
    assert src.count("_apply_referent_clarity_pre_finalize") == 4
