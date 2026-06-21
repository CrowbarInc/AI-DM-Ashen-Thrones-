"""Regression tests for gm_retry paths that integrate open-social solicitation recovery."""
from __future__ import annotations

from types import SimpleNamespace

import game.social_exchange_emission as social_exchange_emission
from game.campaign_state import create_fresh_session_document
from game.interaction_context import rebuild_active_scene_entities
from game.realization_authority import FALLBACK_FAMILIES
from game.realization_provenance import (
    GATE_TERMINAL_REPAIR,
    REALIZATION_FALLBACK_FAMILY_FIELD,
    RETRY_TERMINAL_FALLBACK,
    UPSTREAM_PREPARED_EMISSION,
)
import game.gm as _gm  # noqa: F401 - primes gm/gm_retry's circular import path for direct retry tests.
from game.social_exchange_emission import apply_social_exchange_retry_fallback_gm
from game.storage import load_scene
import game.gm_retry as gm_retry
from game.final_emission_meta import OPENING_FALLBACK_OWNER_RETRY

import pytest

pytestmark = pytest.mark.unit


def test_gm_binding_exposes_strict_social_resolution_seam():
    """Regression: gm_retry._gm_binding() must resolve strict-social helpers on game.gm."""
    import game.gm as gm

    binding = gm_retry._gm_binding()
    assert callable(getattr(binding, "effective_strict_social_resolution_for_emission", None))
    assert binding.effective_strict_social_resolution_for_emission is gm.effective_strict_social_resolution_for_emission
    assert callable(getattr(binding, "minimal_social_emergency_fallback_line", None))


def _gate_session_scene():
    session = create_fresh_session_document()
    session["active_scene_id"] = "frontier_gate"
    session["scene_state"]["active_scene_id"] = "frontier_gate"
    st = session["scene_state"]
    st["active_entities"] = ["guard_captain", "tavern_runner", "refugee", "threadbare_watcher"]
    st.setdefault("entity_presence", {})
    st["entity_presence"].update({e: "active" for e in st["active_entities"]})
    world = {
        "npcs": [
            {"id": "guard_captain", "name": "Guard Captain", "location": "frontier_gate"},
            {"id": "tavern_runner", "name": "Runner", "location": "frontier_gate"},
        ]
    }
    scene = load_scene("frontier_gate")
    scene["scene_state"] = dict(st)
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene)
    return session, scene, world


def test_apply_social_exchange_retry_fallback_gm_prefers_open_social_recovery(monkeypatch):
    session, scene, world = _gate_session_scene()
    resolution = {
        "kind": "question",
        "prompt": "Anyone listening?",
        "social": {
            "social_intent_class": "open_call",
            "open_social_solicitation": True,
            "candidate_addressable_ids": ["guard_captain", "tavern_runner"],
            "candidate_addressable_count": 2,
            "target_resolved": False,
            "npc_reply_expected": False,
        },
    }

    sentinel = (
        "DETERMINISTIC_SOCIAL_FALLBACK_SENTINEL_XYZ "
        "If this text appears, deterministic_social_fallback_line was used instead of open-social recovery."
    )

    def _boom(*a, **k):
        raise AssertionError("deterministic_social_fallback_line must not run when open-social recovery succeeds")

    monkeypatch.setattr(social_exchange_emission, "deterministic_social_fallback_line", _boom)

    gm = {"player_facing_text": "The square stays vague.", "tags": [], "metadata": {}}
    out = apply_social_exchange_retry_fallback_gm(
        gm,
        player_text="Anyone listening?",
        session=session,
        world=world,
        resolution=resolution,
        scene_id="frontier_gate",
    )
    assert sentinel not in out.get("player_facing_text", "")
    tags = [str(t).lower() for t in (out.get("tags") or []) if isinstance(t, str)]
    assert "open_social_recovery" in tags
    assert "open_social_solicitation_recovery" in tags
    assert "social_exchange_retry_fallback" not in tags
    assert "social_exchange_fallback:" not in " ".join(tags)

    low = str(out.get("player_facing_text") or "").lower()
    assert "guard captain" in low or "tavern runner" in low
    assert low.strip() not in {"no one answers.", "the moment passes.", "nobody steps forward."}

    em = (out.get("metadata") or {}).get("emission_debug") or {}
    assert em.get("open_social_recovery_used") is True
    assert em.get("open_social_recovery_mode") in ("concrete_responder", "concrete_lead")
    assert str(em.get("open_social_recovery_reason") or "").strip()
    assert em.get("open_social_recovery_suppressed_retry_fallback") is True
    assert "retry_fallback:suppressed:social_exchange_template" in str(out.get("debug_notes") or "")


def _retry_fallback_base_inputs():
    return {
        "player_text": "What does the guard know?",
        "scene_envelope": {"scene": {"id": "frontier_gate"}},
        "session": {"active_scene_id": "frontier_gate"},
        "world": {},
        "resolution": {"kind": "question", "prompt": "What does the guard know?"},
    }


def _base_gm_with_metadata(text: str = "Original text."):
    return {
        "player_facing_text": text,
        "tags": ["existing_tag"],
        "metadata": {
            "existing_metadata": "kept",
            "emission_debug": {"existing_debug": True},
        },
        "_final_emission_meta": {"existing_fem": True},
    }


def _install_retry_fallback_harness(monkeypatch, *, strict_route=False, soc_in_scope=True):
    monkeypatch.setattr(
        gm_retry,
        "_gm_binding",
        lambda: SimpleNamespace(
            effective_strict_social_resolution_for_emission=lambda resolution, session, world, scene_id: (
                resolution,
                strict_route,
                None,
            ),
            apply_social_exchange_retry_fallback_gm=lambda gm, **kwargs: {
                **gm,
                "player_facing_text": "The captain answers with a clipped warning.",
                "tags": list(gm.get("tags") or []) + ["strict_social_inner"],
            },
        ),
    )
    monkeypatch.setattr(
        gm_retry,
        "inspect_retry_social_answer_fallback_scope",
        lambda **kwargs: {
            "retry_social_fallback_considered": True,
            "block1_world_action_signal": not soc_in_scope,
            "block1_canonical_continuity_break": False,
            "social_shaped_fallback_in_scope": soc_in_scope,
        },
    )
    monkeypatch.setattr(gm_retry, "_is_valid_player_facing_fallback_answer", lambda *args, **kwargs: True)


def _assert_retry_family(out):
    family = out[REALIZATION_FALLBACK_FAMILY_FIELD]
    assert family in FALLBACK_FAMILIES
    assert family == RETRY_TERMINAL_FALLBACK
    assert family != UPSTREAM_PREPARED_EMISSION
    assert family != GATE_TERMINAL_REPAIR
    assert out["metadata"][REALIZATION_FALLBACK_FAMILY_FIELD] == RETRY_TERMINAL_FALLBACK
    assert out["_final_emission_meta"][REALIZATION_FALLBACK_FAMILY_FIELD] == RETRY_TERMINAL_FALLBACK
    assert out.get("opening_fallback_owner_bucket") == OPENING_FALLBACK_OWNER_RETRY
    assert out["metadata"].get("opening_fallback_owner_bucket") == OPENING_FALLBACK_OWNER_RETRY
    assert out["_final_emission_meta"].get("opening_fallback_owner_bucket") == OPENING_FALLBACK_OWNER_RETRY


def _assert_metadata_preserved(out):
    assert out["metadata"]["existing_metadata"] == "kept"
    assert out["metadata"]["emission_debug"]["existing_debug"] is True
    assert out["_final_emission_meta"]["existing_fem"] is True


def _assert_no_upstream_prepared_assignment(out):
    assert out.get(REALIZATION_FALLBACK_FAMILY_FIELD) != UPSTREAM_PREPARED_EMISSION
    assert out.get(REALIZATION_FALLBACK_FAMILY_FIELD) != GATE_TERMINAL_REPAIR
    assert out["metadata"].get(REALIZATION_FALLBACK_FAMILY_FIELD) != UPSTREAM_PREPARED_EMISSION
    assert out["metadata"].get(REALIZATION_FALLBACK_FAMILY_FIELD) != GATE_TERMINAL_REPAIR
    assert out["_final_emission_meta"].get(REALIZATION_FALLBACK_FAMILY_FIELD) != UPSTREAM_PREPARED_EMISSION
    assert out["_final_emission_meta"].get(REALIZATION_FALLBACK_FAMILY_FIELD) != GATE_TERMINAL_REPAIR
    assert out["metadata"].get("upstream_prepared_emission_used") is not True
    assert out["_final_emission_meta"].get("upstream_prepared_emission_used") is not True


def _install_terminal_retry_harness(
    monkeypatch,
    *,
    social_authority=False,
    social_scope=False,
    strict_lane=False,
    social_text="The captain answers with a clipped warning.",
    illegal_social_text=False,
    emergency_social_text="They answer cautiously, keeping it brief.",
    repair_text=None,
):
    monkeypatch.setattr(gm_retry, "_session_social_authority", lambda session: social_authority)
    monkeypatch.setattr(gm_retry, "_social_answer_fallback_in_scope", lambda **kwargs: social_scope)
    monkeypatch.setattr(
        gm_retry,
        "_gm_binding",
        lambda: SimpleNamespace(
            effective_strict_social_resolution_for_emission=lambda resolution, session, world, scene_id: (
                resolution,
                strict_lane or social_authority,
                None,
            ),
            apply_social_exchange_retry_fallback_gm=lambda gm, **kwargs: {
                **gm,
                "player_facing_text": social_text,
                "tags": list(gm.get("tags") or []) + ["terminal_social_inner"],
            },
            is_route_illegal_global_or_sanitizer_fallback_text=lambda text: illegal_social_text,
            minimal_social_emergency_fallback_line=lambda resolution: emergency_social_text,
            strict_social_emission_will_apply=lambda resolution, session, world, scene_id: strict_lane,
            repair_strict_social_terminal_dialogue_fallback_if_needed=(
                lambda text, **kwargs: (repair_text, True) if repair_text is not None else (text, False)
            ),
        ),
    )


def _terminal_retry_inputs(**overrides):
    base = {
        "session": {"active_scene_id": "frontier_gate"},
        "original_text": "Original failed retry.",
        "failure": {"failure_class": "validator_voice", "reasons": ["empty", "validator_voice"]},
        "retry_failures": [{"failure_class": "validator_voice", "reasons": ["empty"]}],
        "player_text": "What does the guard say?",
        "scene_envelope": {"scene": {"id": "frontier_gate", "visible_facts": []}},
        "world": {"npcs": [{"id": "guard_captain", "name": "Guard Captain"}]},
        "resolution": {
            "kind": "question",
            "prompt": "What does the guard say?",
            "social": {"target_resolved": True, "npc_id": "guard_captain"},
        },
        "base_gm": _base_gm_with_metadata(""),
    }
    base.update(overrides)
    return base


def _assert_terminal_retry_metadata(out, *, expect_failure_debug=True):
    assert out["retry_exhausted"] is True
    assert out["targeted_retry_terminal"] is True
    assert out["retry_failure_class"] == "validator_voice"
    assert out["retry_failure_reasons"] == ["empty", "validator_voice"]
    assert out["retry_failures_snapshot"] == [{"failure_class": "validator_voice", "reasons": ["empty"]}]
    assert "retry_escape_hatch" in out["tags"]
    if expect_failure_debug:
        assert "validator_voice" in out["debug_notes"]
    _assert_retry_family(out)
    _assert_metadata_preserved(out)
    _assert_no_upstream_prepared_assignment(out)


def test_apply_deterministic_retry_fallback_answer_context_branch_labels_retry_family(monkeypatch):
    _install_retry_fallback_harness(monkeypatch, soc_in_scope=True)
    monkeypatch.setattr(gm_retry, "resolve_known_fact_before_uncertainty", lambda *args, **kwargs: None)
    gm = _base_gm_with_metadata()

    out = gm_retry.apply_deterministic_retry_fallback(
        gm,
        failure={
            "failure_class": "answer",
            "known_fact_context": {
                "answer": "The missing ledger is under the blue stone.",
                "source": "social_answer_candidate",
            },
        },
        **_retry_fallback_base_inputs(),
    )

    assert out["player_facing_text"] == "The missing ledger is under the blue stone."
    assert {"question_retry_fallback", "known_fact_guard", "social_answer_retry"} <= set(out["tags"])
    _assert_retry_family(out)
    _assert_metadata_preserved(out)
    _assert_no_upstream_prepared_assignment(out)


def test_apply_deterministic_retry_fallback_known_fact_branch_labels_retry_family(monkeypatch):
    _install_retry_fallback_harness(monkeypatch, soc_in_scope=True)
    monkeypatch.setattr(
        gm_retry,
        "resolve_known_fact_before_uncertainty",
        lambda *args, **kwargs: {
            "text": "The gate bell rang before dawn.",
            "source": "current_scene_state",
            "speaker": {"role": "guard"},
        },
    )
    gm = _base_gm_with_metadata()

    out = gm_retry.apply_deterministic_retry_fallback(
        gm,
        failure={"failure_class": "unresolved_question"},
        **_retry_fallback_base_inputs(),
    )

    assert out["player_facing_text"] == "The gate bell rang before dawn."
    assert {"question_retry_fallback", "known_fact_guard"} <= set(out["tags"])
    _assert_retry_family(out)
    _assert_metadata_preserved(out)
    _assert_no_upstream_prepared_assignment(out)


def test_apply_deterministic_retry_fallback_open_social_branch_labels_retry_family(monkeypatch):
    _install_retry_fallback_harness(monkeypatch, soc_in_scope=True)
    monkeypatch.setattr(gm_retry, "resolve_known_fact_before_uncertainty", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        social_exchange_emission,
        "build_open_social_solicitation_recovery",
        lambda **kwargs: {
            "used": True,
            "text": "The runner looks up first.",
            "mode": "concrete_responder",
            "reason": "test",
        },
    )
    monkeypatch.setattr(
        social_exchange_emission,
        "_merge_open_social_recovery_emission_debug",
        lambda out, rec: out.setdefault("metadata", {})
        .setdefault("emission_debug", {})
        .update({"open_social_recovery_used": True}),
    )
    inputs = _retry_fallback_base_inputs()
    inputs["resolution"] = {
        "kind": "question",
        "social": {"open_social_solicitation": True, "npc_reply_expected": False},
    }
    gm = _base_gm_with_metadata()

    out = gm_retry.apply_deterministic_retry_fallback(
        gm,
        failure={"failure_class": "unresolved_question"},
        **inputs,
    )

    assert out["player_facing_text"] == "The runner looks up first."
    assert {"question_retry_fallback", "open_social_solicitation_recovery", "open_social_recovery"} <= set(out["tags"])
    assert out["metadata"]["emission_debug"]["open_social_recovery_used"] is True
    _assert_retry_family(out)
    _assert_metadata_preserved(out)
    _assert_no_upstream_prepared_assignment(out)


def test_apply_deterministic_retry_fallback_strict_social_branch_labels_retry_family(monkeypatch):
    _install_retry_fallback_harness(monkeypatch, strict_route=True, soc_in_scope=True)
    monkeypatch.setattr(gm_retry, "resolve_known_fact_before_uncertainty", lambda *args, **kwargs: None)
    gm = _base_gm_with_metadata()

    out = gm_retry.apply_deterministic_retry_fallback(
        gm,
        failure={"failure_class": "unresolved_question"},
        **_retry_fallback_base_inputs(),
    )

    assert out["player_facing_text"] == "The captain answers with a clipped warning."
    assert "strict_social_inner" in out["tags"]
    _assert_retry_family(out)
    _assert_metadata_preserved(out)
    _assert_no_upstream_prepared_assignment(out)


def test_apply_deterministic_retry_fallback_uncertainty_branch_labels_retry_family(monkeypatch):
    _install_retry_fallback_harness(monkeypatch, strict_route=False, soc_in_scope=False)
    monkeypatch.setattr(gm_retry, "resolve_known_fact_before_uncertainty", lambda *args, **kwargs: None)
    monkeypatch.setattr(gm_retry, "classify_uncertainty", lambda *args, **kwargs: {"category": "bounded_unknown"})

    def _uncertainty_to_gm(gm, **kwargs):
        out = dict(gm)
        out["player_facing_text"] = "The trail is still uncertain."
        return out

    monkeypatch.setattr(gm_retry, "_apply_uncertainty_to_gm", _uncertainty_to_gm)
    gm = _base_gm_with_metadata()

    out = gm_retry.apply_deterministic_retry_fallback(
        gm,
        failure={"failure_class": "unresolved_question"},
        **_retry_fallback_base_inputs(),
    )

    assert out["player_facing_text"] == "The trail is still uncertain."
    assert "question_retry_fallback" in out["tags"]
    assert "retry_fallback_chosen:nonsocial_uncertainty_pool_after_block1_social_out_of_scope" in out["debug_notes"]
    _assert_retry_family(out)
    _assert_metadata_preserved(out)
    _assert_no_upstream_prepared_assignment(out)


def test_apply_deterministic_retry_fallback_noop_preserves_original_for_unhandled_failure(monkeypatch):
    _install_retry_fallback_harness(monkeypatch)
    gm = _base_gm_with_metadata("Keep this exact line.")

    out = gm_retry.apply_deterministic_retry_fallback(
        gm,
        failure={"failure_class": "validator_voice"},
        **_retry_fallback_base_inputs(),
    )

    assert out is gm
    assert out["player_facing_text"] == "Keep this exact line."
    assert REALIZATION_FALLBACK_FAMILY_FIELD not in out
    assert REALIZATION_FALLBACK_FAMILY_FIELD not in out["metadata"]
    assert out["metadata"]["existing_metadata"] == "kept"


def test_select_deterministic_retry_fallback_line_answer_context_structure_and_purity(monkeypatch):
    _install_retry_fallback_harness(monkeypatch, soc_in_scope=True)
    monkeypatch.setattr(gm_retry, "resolve_known_fact_before_uncertainty", lambda *args, **kwargs: None)
    gm = _base_gm_with_metadata()
    before = {
        "player_facing_text": gm["player_facing_text"],
        "tags": list(gm["tags"]),
        "metadata": dict(gm["metadata"]),
        "_final_emission_meta": dict(gm["_final_emission_meta"]),
    }

    selected = gm_retry.select_deterministic_retry_fallback_line(
        gm,
        failure={
            "failure_class": "answer",
            "known_fact_context": {
                "answer": "The missing ledger is under the blue stone.",
                "source": "social_answer_candidate",
            },
        },
        **_retry_fallback_base_inputs(),
    )

    assert selected["selected"] is True
    assert selected["text"] == "The missing ledger is under the blue stone."
    assert selected["source"] == "answer_context_known_fact"
    assert selected["realization_fallback_family"] == RETRY_TERMINAL_FALLBACK
    assert selected["realization_fallback_family"] in FALLBACK_FAMILIES
    assert selected["debug"]["failure_class"] == "answer"
    assert selected["debug"]["source"] == "social_answer_candidate"
    assert selected["gm_output"]["player_facing_text"] == "The missing ledger is under the blue stone."
    assert selected[REALIZATION_FALLBACK_FAMILY_FIELD] == RETRY_TERMINAL_FALLBACK
    assert REALIZATION_FALLBACK_FAMILY_FIELD not in selected["gm_output"]
    assert REALIZATION_FALLBACK_FAMILY_FIELD not in selected["gm_output"]["metadata"]
    assert REALIZATION_FALLBACK_FAMILY_FIELD not in selected["gm_output"]["_final_emission_meta"]
    assert gm["player_facing_text"] == before["player_facing_text"]
    assert gm["tags"] == before["tags"]
    assert gm["metadata"] == before["metadata"]
    assert gm["_final_emission_meta"] == before["_final_emission_meta"]


def test_select_terminal_retry_fallback_line_returns_structure_without_mutating_base(monkeypatch):
    _install_terminal_retry_harness(monkeypatch, social_authority=False, social_scope=False, strict_lane=False)
    monkeypatch.setattr(gm_retry, "_nonsocial_forced_retry_progress_line", lambda *args, **kwargs: "")
    monkeypatch.setattr(gm_retry, "render_nonsocial_terminal_anchor_line", lambda *args, **kwargs: "A cold bell marks the pause")
    monkeypatch.setattr(gm_retry, "anti_reset_suppresses_intro_style_fallbacks", lambda *args, **kwargs: False)
    base_gm = _base_gm_with_metadata("")
    before = {
        "player_facing_text": base_gm["player_facing_text"],
        "tags": list(base_gm["tags"]),
        "metadata": dict(base_gm["metadata"]),
        "_final_emission_meta": dict(base_gm["_final_emission_meta"]),
    }

    selected = gm_retry.select_terminal_retry_fallback_line(
        session={"active_scene_id": "watch_post"},
        player_text="I wait.",
        scene_envelope={"scene": {"id": "watch_post", "visible_facts": []}},
        world={},
        resolution={"kind": "observe", "prompt": "I wait."},
        base_gm=base_gm,
    )

    assert selected["text"] == "A cold bell marks the pause."
    assert selected["source"] == "nonsocial_terminal_anchor"
    assert selected["realization_fallback_family"] == RETRY_TERMINAL_FALLBACK
    assert selected["realization_fallback_family"] in FALLBACK_FAMILIES
    assert selected["debug"]["use_social_terminal"] is False
    assert selected["debug"]["soc_terminal_in_scope"] is False
    assert selected["debug"]["scene_id"] == "watch_post"
    assert "metadata" not in selected
    assert "_final_emission_meta" not in selected
    assert REALIZATION_FALLBACK_FAMILY_FIELD not in base_gm
    assert REALIZATION_FALLBACK_FAMILY_FIELD not in base_gm["metadata"]
    assert REALIZATION_FALLBACK_FAMILY_FIELD not in base_gm["_final_emission_meta"]
    assert base_gm["player_facing_text"] == before["player_facing_text"]
    assert base_gm["tags"] == before["tags"]
    assert base_gm["metadata"] == before["metadata"]
    assert base_gm["_final_emission_meta"] == before["_final_emission_meta"]


def test_force_terminal_retry_fallback_social_terminal_path_labels_retry_family(monkeypatch):
    _install_terminal_retry_harness(
        monkeypatch,
        social_authority=True,
        social_scope=True,
        social_text="The captain answers with a clipped warning.",
    )

    out = gm_retry.force_terminal_retry_fallback(**_terminal_retry_inputs())

    assert out["player_facing_text"] == "The captain answers with a clipped warning."
    assert out["final_route"] == "forced_retry_fallback"
    assert out["fallback_kind"] == "retry_escape_hatch"
    assert out["accepted_via"] == "forced_fallback"
    assert {"retry_escape_hatch", "forced_retry_fallback", "retry_exhausted"} <= set(out["tags"])
    _assert_terminal_retry_metadata(out)


def test_force_terminal_retry_fallback_nonsocial_terminal_anchor_path_labels_retry_family(monkeypatch):
    _install_terminal_retry_harness(monkeypatch, social_authority=False, social_scope=False, strict_lane=False)
    monkeypatch.setattr(gm_retry, "_nonsocial_forced_retry_progress_line", lambda *args, **kwargs: "")
    monkeypatch.setattr(gm_retry, "render_nonsocial_terminal_anchor_line", lambda *args, **kwargs: "A cold bell marks the pause")
    monkeypatch.setattr(gm_retry, "anti_reset_suppresses_intro_style_fallbacks", lambda *args, **kwargs: False)

    out = gm_retry.force_terminal_retry_fallback(
        **_terminal_retry_inputs(
            session={"active_scene_id": "watch_post"},
            player_text="I wait.",
            scene_envelope={"scene": {"id": "watch_post", "visible_facts": []}},
            world={},
            resolution={"kind": "observe", "prompt": "I wait."},
        )
    )

    assert out["player_facing_text"] == "A cold bell marks the pause."
    assert out["final_route"] == "forced_retry_fallback"
    assert out["fallback_kind"] == "retry_escape_hatch"
    assert out["accepted_via"] == "forced_fallback"
    _assert_terminal_retry_metadata(out)


def test_force_terminal_retry_fallback_empty_social_repair_path_labels_retry_family(monkeypatch):
    _install_terminal_retry_harness(
        monkeypatch,
        social_authority=True,
        social_scope=True,
        social_text="",
        emergency_social_text="",
    )

    def _minimal_social_repair(**kwargs):
        gm = dict(kwargs["gm"])
        gm["player_facing_text"] = "They answer cautiously, keeping it brief."
        gm["final_route"] = "social_fallback_minimal"
        gm["fallback_kind"] = "social_empty_resolution_repair"
        gm["accepted_via"] = "social_resolution_repair"
        gm["targeted_retry_terminal"] = True
        gm["retry_exhausted"] = True
        gm["tags"] = list(gm.get("tags") or []) + ["social_empty_resolution_repair", "retry_exhausted"]
        gm["debug_notes"] = "social_empty_resolution_repair:terminal social resolution repair"
        return gm

    monkeypatch.setattr(gm_retry, "ensure_minimal_social_resolution", _minimal_social_repair)

    out = gm_retry.force_terminal_retry_fallback(**_terminal_retry_inputs())

    assert out["player_facing_text"] == "They answer cautiously, keeping it brief."
    assert out["final_route"] == "social_fallback_minimal"
    assert out["fallback_kind"] == "social_empty_resolution_repair"
    assert out["accepted_via"] == "social_resolution_repair"
    assert "social_empty_resolution_repair" in out["tags"]
    assert "social_empty_resolution_repair:terminal social resolution repair" in out["debug_notes"]
    _assert_terminal_retry_metadata(out, expect_failure_debug=False)
