"""Shared final-emission gate harness fixtures (strict-social bundle + opening GM scaffold).

Support residue for gate-adjacent and replay/downstream suites. Block-O opening
attach-then-helper adapters mirror gate entry prep without owning orchestration
semantics. Semantic orchestration ownership remains ``tests/test_final_emission_gate.py``.
"""
from __future__ import annotations

from typing import Any, Mapping

import pytest

import game.final_emission_gate as feg
from game.upstream_response_repairs import maybe_attach_upstream_prepared_opening_fallback_payload
from game.defaults import default_session, default_world
from game.final_emission_gate import apply_final_emission_gate
from game.final_emission_meta import (
    opening_fallback_owner_bucket_from_fields,
    opening_fallback_owner_bucket_from_meta,
    read_final_emission_meta_dict,
)
from game.upstream_response_repairs import OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL
from game.interaction_context import rebuild_active_scene_entities, set_social_target
from game.narrative_authority import build_narrative_authority_contract
from game.social_exchange_emission import effective_strict_social_resolution_for_emission
from game.storage import get_scene_runtime

EXPECTED_FRONTIER_GATE_OPENING_FALLBACK = (
    "Rain spatters soot-dark stone; frayed banners hang above Cinderwatch's eastern gate. "
    "Refugees, wagons, and foot traffic clog the muddy approach; guards hold the choke while the crowd presses in. "
    "A notice board lists new taxes, curfews, and a posted warning about a missing patrol. "
    "You can start with Read the notice board or Approach the guards."
)


def response_type_contract(required: str) -> dict:
    return {
        "required_response_type": required,
        "action_must_preserve_agency": required == "action_outcome",
    }


def opening_validation_context() -> dict:
    facts = [
        "Rain spatters soot-dark stone; frayed banners hang above Cinderwatch's eastern gate.",
        "Refugees, wagons, and foot traffic clog the muddy approach; guards hold the choke while the crowd presses in.",
        "A notice board lists new taxes, curfews, and a posted warning about a missing patrol.",
    ]
    return {
        "location_anchors": ["Cinderwatch Gate District"],
        "visible_facts": facts,
        "actionable_labels": ["Read the notice board", "Approach the guards"],
    }


_DEFAULT_OPENING_HARNESS_RESOLUTION: dict[str, Any] = {"kind": "scene_opening", "prompt": "Start the campaign."}


def opening_gate_attach_then_opening_scene_safe_fallback_tuple(
    gm_output: dict[str, Any],
    *,
    resolution: Mapping[str, Any] | None = None,
) -> tuple[str, str, str, str, str, str, dict[str, Any]]:
    """Run ``maybe_attach_upstream_prepared_opening_fallback_payload`` then ``_opening_scene_safe_fallback_tuple`` (Block O).

    Mirrors the opening-prep sequence at ``apply_final_emission_gate`` entry before opening helper seams. Mutates *gm_output*.
    """
    resolved = dict(resolution) if isinstance(resolution, Mapping) else dict(_DEFAULT_OPENING_HARNESS_RESOLUTION)
    maybe_attach_upstream_prepared_opening_fallback_payload(gm_output, resolution=resolved)
    return feg._opening_scene_safe_fallback_tuple(gm_output)


def opening_gate_attach_then_enforce_response_type_contract(
    candidate_text: str,
    gm_output: dict[str, Any],
    *,
    resolution: Mapping[str, Any] | None = None,
    session: dict[str, Any] | None = None,
    scene_id: str = "frontier_gate",
    world: dict[str, Any] | None = None,
    strict_social_turn: bool = False,
    strict_social_suppressed_non_social_turn: bool = False,
    active_interlocutor: str = "",
) -> tuple[str, dict[str, Any]]:
    """Run ``maybe_attach_upstream_prepared_opening_fallback_payload`` then ``_enforce_response_type_contract`` (Block O).

    Mutates *gm_output* in place like full gate entry.
    """
    resolved = dict(resolution) if isinstance(resolution, Mapping) else dict(_DEFAULT_OPENING_HARNESS_RESOLUTION)
    maybe_attach_upstream_prepared_opening_fallback_payload(gm_output, resolution=resolved)
    return feg._enforce_response_type_contract(
        candidate_text,
        gm_output=gm_output,
        resolution=resolved,
        session=session if session is not None else {},
        scene_id=scene_id,
        world=world if world is not None else {},
        strict_social_turn=strict_social_turn,
        strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        active_interlocutor=active_interlocutor,
    )


def opening_gm_output() -> dict:
    facts = opening_validation_context()["visible_facts"]
    return {
        "response_policy": {"response_type_contract": response_type_contract("scene_opening")},
        "opening_curated_facts": list(facts),
        "metadata": {
            "emission_debug": {
                "opening_curated_facts_present": True,
                "opening_curated_facts_count": len(facts),
                "opening_curated_facts_source": "realization",
            }
        },
        "prompt_context": {
            "opening_inputs_are_curated": True,
            "opening_curated_facts": list(facts),
            "narration_obligations": {"is_opening_scene": True},
            "narrative_plan": {
                "scene_opening": {"location_anchors": ["Cinderwatch Gate District"]},
                "scene_anchors": {"location_anchors": ["Cinderwatch Gate District"]},
                "active_pressures": {},
            },
            "opening_scene_realization": {"contract": {"narration_basis_visible_facts": facts}},
            "narration_visibility": {"visible_facts": facts},
            "scene": {
                "public": {
                    "id": "frontier_gate",
                    "location": "Cinderwatch Gate District",
                    "visible_facts": facts,
                    "actions": [{"label": "Read the notice board"}, {"label": "Approach the guards"}],
                }
            },
        },
    }


def final_emission_meta_from_output(gm_output: Mapping[str, Any]) -> dict[str, Any]:
    """Read normalized FEM from a gate output dict."""
    return read_final_emission_meta_dict(dict(gm_output)) or {}


def assert_final_emission_meta_contains(
    meta: Mapping[str, Any] | None,
    **expected: Any,
) -> dict[str, Any]:
    """Assert exact key matches on FEM/debug metadata already extracted from gate output."""
    fem = dict(meta) if isinstance(meta, Mapping) else {}
    for key, value in expected.items():
        assert fem.get(key) == value, f"{key}: expected {value!r}, got {fem.get(key)!r}"
    return fem


def assert_fallback_owner_bucket(
    expected: str,
    *,
    meta: Mapping[str, Any] | None = None,
    from_fields: Mapping[str, Any] | None = None,
) -> None:
    """Assert opening fallback owner bucket via meta read or explicit field projection."""
    if from_fields is not None:
        got = opening_fallback_owner_bucket_from_fields(**dict(from_fields))
    else:
        got = opening_fallback_owner_bucket_from_meta(meta)
    assert got == expected


def assert_opening_fallback_source(
    meta: Mapping[str, Any] | None,
    *,
    final_emitted_source: str,
    authorship_source: str | None = None,
    owner_bucket: str | None = None,
    forbid_compat_local_authorship: bool = False,
) -> None:
    """Assert canonical opening fallback source/authorship/owner-bucket projection locks."""
    fem = dict(meta) if isinstance(meta, Mapping) else {}
    assert fem.get("final_emitted_source") == final_emitted_source
    if authorship_source is not None:
        assert fem.get("opening_fallback_authorship_source") == authorship_source
    if forbid_compat_local_authorship:
        assert fem.get("opening_fallback_authorship_source") != OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL
    if owner_bucket is not None:
        assert_fallback_owner_bucket(owner_bucket, meta=fem)


def assert_sealed_fallback_owner_bucket(meta: Mapping[str, Any] | None, expected: str) -> None:
    """Assert sealed fallback owner-bucket stamp on FEM/debug metadata."""
    fem = dict(meta) if isinstance(meta, Mapping) else {}
    assert fem.get("sealed_fallback_owner_bucket") == expected


def assert_visibility_pool(
    *,
    fallback_pool: str = "",
    fallback_kind: str = "",
    final_emitted_source: str = "",
    owner_bucket: str | None = None,
) -> None:
    """Assert visibility fallback owner-bucket classification from pool/kind/source signals."""
    import game.final_emission_visibility_fallback as visibility_fallback

    kwargs = {
        "fallback_pool": fallback_pool,
        "fallback_kind": fallback_kind,
        "final_emitted_source": final_emitted_source,
    }
    if owner_bucket is not None:
        assert visibility_fallback.classify_visibility_fallback_owner_bucket(**kwargs) == owner_bucket


def runner_strict_bundle():
    session = default_session()
    world = default_world()
    sid = "scene_investigate"
    world["npcs"] = [
        {
            "id": "runner",
            "name": "Tavern Runner",
            "location": "scene_investigate",
            "topics": [{"id": "lanes", "text": "East lanes.", "clue_id": "east_lanes"}],
        }
    ]
    session["active_scene_id"] = sid
    session["visited_scene_ids"] = [sid]
    set_social_target(session, "runner")
    rebuild_active_scene_entities(session, world, sid)
    ic = dict(session.get("interaction_context") or {})
    ic["engagement_level"] = "engaged"
    session["interaction_context"] = ic
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "Who attacked them?"
    resolution = {
        "kind": "question",
        "prompt": "Who attacked them?",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "runner",
            "npc_name": "Tavern Runner",
        },
    }
    return session, world, sid, resolution


def _na_contract_for_resolution(resolution: dict) -> dict:
    return build_narrative_authority_contract(
        resolution=resolution,
        narration_visibility={},
        scene_state_anchor_contract=None,
        speaker_selection_contract=None,
        session_view=None,
    )


def run_strict_social_motive_overclaim_gate_case(monkeypatch: pytest.MonkeyPatch) -> None:
    """Strict-social: NA is validate-only; motive overclaim remains visible in meta, not silently rewritten."""
    session, world, sid, resolution = runner_strict_bundle()
    eff, route, _ = effective_strict_social_resolution_for_emission(resolution, session, world, sid)
    assert route is True

    na = _na_contract_for_resolution(eff if isinstance(eff, dict) else resolution)
    bad = (
        'Tavern Runner says, "No names yet—only rumors."\n\n'
        "He plans to stall you until the watch arrives."
    )

    stub_details = {
        "used_internal_fallback": False,
        "final_emitted_source": "test_stub",
        "rejection_reasons": [],
        "deterministic_attempted": False,
        "deterministic_passed": False,
        "fallback_pool": "none",
        "fallback_kind": "none",
        "route_illegal_intercepted": False,
    }

    def fake_build(_candidate_text, *, resolution, tags, session, scene_id, world):
        return bad, dict(stub_details)

    monkeypatch.setattr(feg, "build_final_strict_social_response", fake_build)

    out = apply_final_emission_gate(
        {
            "player_facing_text": bad,
            "tags": [],
            "response_policy": {"narrative_authority": na},
        },
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    text = out.get("player_facing_text") or ""
    meta = read_final_emission_meta_dict(out) or {}
    em = (out.get("metadata") or {}).get("emission_debug") or {}
    assert meta.get("narrative_authority_repaired") is False
    assert meta.get("narrative_authority_failed") is True
    assert em.get("narrative_authority_boundary_semantic_repair_disabled") is True
    assert "plans to stall" in text.lower()
    assert "Tavern Runner" in text
    assert meta.get("speaker_contract_enforcement_reason") == "speaker_contract_match"
