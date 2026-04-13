"""Integration tests for apply_final_emission_gate speaker-contract enforcement ordering and metadata."""
from __future__ import annotations

import json

import pytest

import game.final_emission_gate as feg
import game.scene_state_anchoring as ssa
from game.defaults import default_scene, default_session, default_world
from game.final_emission_gate import apply_final_emission_gate, get_speaker_selection_contract
from game.anti_railroading import build_anti_railroading_contract
from game.context_separation import build_context_separation_contract
from game.narrative_authority import build_narrative_authority_contract
from game.interaction_context import rebuild_active_scene_entities, set_social_target
from game.player_facing_narration_purity import build_player_facing_narration_purity_contract
from game.response_policy_contracts import build_social_response_structure_contract
from game.social_exchange_emission import effective_strict_social_resolution_for_emission
from game.storage import get_scene_runtime

pytestmark = pytest.mark.unit


def _runner_strict_bundle():
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


def test_apply_final_emission_gate_runs_response_delta_before_speaker_enforcement(monkeypatch):
    session, world, sid, resolution = _runner_strict_bundle()
    eff, route, _ = effective_strict_social_resolution_for_emission(resolution, session, world, sid)
    assert route is True
    assert isinstance(eff, dict)

    order: list[str] = []
    orig_rd = feg._apply_response_delta_layer
    orig_enf = feg.enforce_emitted_speaker_with_contract

    def rd(*args, **kwargs):
        order.append("response_delta")
        return orig_rd(*args, **kwargs)

    def enf(*args, **kwargs):
        order.append("speaker_contract")
        return orig_enf(*args, **kwargs)

    monkeypatch.setattr(feg, "_apply_response_delta_layer", rd)
    monkeypatch.setattr(feg, "enforce_emitted_speaker_with_contract", enf)

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

    def fake_build(candidate_text, *, resolution, tags, session, scene_id, world):
        return 'Tavern Runner says, "No names, only rumors."', dict(stub_details)

    monkeypatch.setattr(feg, "build_final_strict_social_response", fake_build)

    out = apply_final_emission_gate(
        {"player_facing_text": 'Tavern Runner says, "No names, only rumors."', "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    assert order.index("response_delta") < order.index("speaker_contract")
    em = (out.get("metadata") or {}).get("emission_debug") or {}
    assert "speaker_contract_enforcement" in em
    reason = (out.get("_final_emission_meta") or {}).get("speaker_contract_enforcement_reason")
    assert reason == em["speaker_contract_enforcement"]["final_reason_code"]


def test_apply_final_emission_gate_strict_social_contract_missing_skips_tightening(monkeypatch):
    """Legacy / missing contract: enforcement must not invent a stricter policy."""
    session, world, sid, resolution = _runner_strict_bundle()
    empty_contract = get_speaker_selection_contract(None, None, None)
    assert empty_contract["debug"].get("contract_missing") is True

    monkeypatch.setattr(feg, "get_speaker_selection_contract", lambda *a, **kw: empty_contract)

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

    def fake_build(candidate_text, *, resolution, tags, session, scene_id, world):
        # Would be forbidden repair if a real contract were present.
        return 'Ragged stranger says, "Pay me."', dict(stub_details)

    monkeypatch.setattr(feg, "build_final_strict_social_response", fake_build)

    out = apply_final_emission_gate(
        {"player_facing_text": 'Ragged stranger says, "Pay me."', "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    text = out.get("player_facing_text") or ""
    assert "Ragged stranger" in text
    assert (out.get("_final_emission_meta") or {}).get("speaker_contract_enforcement_reason") == "speaker_contract_match"
    payload = ((out.get("metadata") or {}).get("emission_debug") or {}).get("speaker_contract_enforcement") or {}
    assert payload.get("validation", {}).get("details", {}).get("skipped") == "no_contract"


def test_apply_final_emission_gate_non_strict_path_does_not_attach_speaker_enforcement():
    out = apply_final_emission_gate(
        {"player_facing_text": "Rain drums on the slate roof.", "tags": []},
        resolution={"kind": "observe", "prompt": "I listen to the rain."},
        session={},
        scene_id="scene_investigate",
        world={},
    )
    em = (out.get("metadata") or {}).get("emission_debug") or {}
    assert "speaker_contract_enforcement" not in em


def test_apply_final_emission_gate_runs_scene_state_anchor_after_speaker_enforcement(monkeypatch):
    """Objective #8 layer is ordered after speaker contract enforcement on strict-social turns."""
    session, world, sid, resolution = _runner_strict_bundle()
    order: list[str] = []
    orig_enf = feg.enforce_emitted_speaker_with_contract
    orig_ssa = feg._apply_scene_state_anchor_layer

    def enf(*args, **kwargs):
        order.append("speaker_contract")
        return orig_enf(*args, **kwargs)

    def ssa(*args, **kwargs):
        order.append("scene_state_anchor")
        return orig_ssa(*args, **kwargs)

    monkeypatch.setattr(feg, "enforce_emitted_speaker_with_contract", enf)
    monkeypatch.setattr(feg, "_apply_scene_state_anchor_layer", ssa)

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

    def fake_build(candidate_text, *, resolution, tags, session, scene_id, world):
        return 'Tavern Runner says, "No names, only rumors."', dict(stub_details)

    monkeypatch.setattr(feg, "build_final_strict_social_response", fake_build)

    apply_final_emission_gate(
        {"player_facing_text": 'Tavern Runner says, "No names, only rumors."', "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    assert order.index("speaker_contract") < order.index("scene_state_anchor")


def test_apply_final_emission_gate_scene_state_anchor_location_repair_non_strict():
    """Floating narration is minimally tethered when the shipped contract supplies location tokens."""
    contract = {
        "enabled": True,
        "required_any_of": ["location", "actor", "player_action"],
        "minimum_anchor_hits": 1,
        "scene_id": "frontier_gate",
        "scene_location_label": "Frontier Checkpoint",
        "location_tokens": ["checkpoint", "frontier gate"],
        "actor_tokens": [],
        "player_action_tokens": [],
        "preferred_repair_order": ["actor", "player_action", "location"],
        "debug_reason": "test",
        "debug_sources": {},
    }
    raw = "The air tastes of iron and distant smoke."
    out = apply_final_emission_gate(
        {
            "player_facing_text": raw,
            "tags": [],
            "scene_state_anchor_contract": contract,
        },
        resolution={"kind": "observe", "prompt": "I look around."},
        session=None,
        scene_id="frontier_gate",
        world={},
    )
    text = out.get("player_facing_text") or ""
    assert "checkpoint" in text.lower() or "frontier" in text.lower()
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("scene_state_anchor_repaired") is True
    assert meta.get("scene_state_anchor_repair_mode") in {"location_rebind", "narrator_neutral_scene_rebind"}
    assert meta.get("scene_state_anchor_passed") is True


def _ssa_contract(**overrides):
    base = {
        "enabled": True,
        "required_any_of": ["location", "actor", "player_action"],
        "minimum_anchor_hits": 1,
        "scene_id": "frontier_gate",
        "scene_location_label": None,
        "location_tokens": [],
        "actor_tokens": [],
        "player_action_tokens": [],
        "preferred_repair_order": ["actor", "player_action", "location"],
        "debug_reason": "test",
        "debug_sources": {},
    }
    base.update(overrides)
    return base


def test_strict_social_preserves_speaker_repair_then_applies_anchor_repair(monkeypatch):
    """After speaker enforcement rewrites to the canonical NPC line, SSA may still tether floating tails."""
    session, world, sid, resolution = _runner_strict_bundle()

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

    def fake_build(candidate_text, *, resolution, tags, session, scene_id, world):
        return 'A stranger says, "Fine."', dict(stub_details)

    monkeypatch.setattr(feg, "build_final_strict_social_response", fake_build)

    def fake_enforce(text, *, gm_output, resolution, eff_resolution, world, scene_id):
        fixed = 'Tavern Runner says, "Fine."'
        payload = {
            "contract_present": True,
            "final_reason_code": "local_rebind",
            "validation": {"ok": True},
            "repair": {"mode": "local_rebind"},
        }
        return fixed, payload

    monkeypatch.setattr(feg, "enforce_emitted_speaker_with_contract", fake_enforce)

    contract = _ssa_contract(
        scene_id=sid,
        location_tokens=["investigate", "scene investigate"],
        actor_tokens=[],
        player_action_tokens=[],
    )
    out = apply_final_emission_gate(
        {
            "player_facing_text": 'A stranger says, "Fine."',
            "tags": [],
            "scene_state_anchor_contract": contract,
        },
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    text = (out.get("player_facing_text") or "").lower()
    assert "tavern runner" in text
    assert "investigate" in text or "scene" in text
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("scene_state_anchor_repaired") is True
    assert meta.get("scene_state_anchor_repair_mode") == "location_rebind"


def test_non_strict_runs_answer_completeness_and_response_delta_before_scene_state_anchor(monkeypatch):
    order: list[str] = []
    orig_ac = feg._apply_answer_completeness_layer
    orig_rd = feg._apply_response_delta_layer
    orig_ssa = feg._apply_scene_state_anchor_layer

    def ac(*args, **kwargs):
        order.append("answer_completeness")
        return orig_ac(*args, **kwargs)

    def rd(*args, **kwargs):
        order.append("response_delta")
        return orig_rd(*args, **kwargs)

    def ssa_layer(*args, **kwargs):
        order.append("scene_state_anchor")
        return orig_ssa(*args, **kwargs)

    monkeypatch.setattr(feg, "_apply_answer_completeness_layer", ac)
    monkeypatch.setattr(feg, "_apply_response_delta_layer", rd)
    monkeypatch.setattr(feg, "_apply_scene_state_anchor_layer", ssa_layer)

    apply_final_emission_gate(
        {
            "player_facing_text": "Rain drums on the slate roof.",
            "tags": [],
            "scene_state_anchor_contract": _ssa_contract(
                scene_location_label="Frontier Checkpoint",
                location_tokens=["checkpoint"],
            ),
        },
        resolution={"kind": "observe", "prompt": "I listen."},
        session={},
        scene_id="frontier_gate",
        world={},
    )
    ix_ac = order.index("answer_completeness")
    ix_rd = order.index("response_delta")
    ix_ssa = order.index("scene_state_anchor")
    assert ix_ac < ix_ssa and ix_rd < ix_ssa


def test_non_strict_scene_state_anchor_does_not_strip_prior_objective_repairs(monkeypatch):
    """Anchor repair prepends/tethers without removing answer-completeness or response-delta markers."""

    def fake_ac(text, **kwargs):
        meta = {
            "answer_completeness_checked": False,
            "answer_completeness_failed": False,
            "answer_completeness_failure_reasons": [],
            "answer_completeness_repaired": True,
            "answer_completeness_repair_mode": "inject_resolution_gate_phrase",
            "answer_completeness_expected_voice": None,
            "answer_completeness_skip_reason": None,
        }
        return text + " |AC_OK|", meta, []

    def fake_rd(text, **kwargs):
        meta = feg._default_response_delta_meta()
        meta["response_delta_repaired"] = True
        meta["response_delta_repair_mode"] = "boundary_echo_trim"
        return text + " |RD_OK|", meta, []

    monkeypatch.setattr(feg, "_apply_answer_completeness_layer", fake_ac)
    monkeypatch.setattr(feg, "_apply_response_delta_layer", fake_rd)

    out = apply_final_emission_gate(
        {
            "player_facing_text": "The wind shifts.",
            "tags": [],
            "scene_state_anchor_contract": _ssa_contract(
                scene_location_label="Frontier Checkpoint",
                location_tokens=["checkpoint"],
            ),
        },
        resolution={"kind": "observe", "prompt": "I listen."},
        session={},
        scene_id="frontier_gate",
        world={},
    )
    text = out.get("player_facing_text") or ""
    assert "|AC_OK|" in text
    assert "|RD_OK|" in text
    assert "checkpoint" in text.lower()
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("answer_completeness_repaired") is True
    assert meta.get("response_delta_repaired") is True
    assert meta.get("scene_state_anchor_repaired") is True


def test_scene_state_anchor_pass_path_flags_and_matched_kinds():
    """Use location-only anchors so visibility enforcement does not replace the line (no unseen NPC names)."""
    contract = _ssa_contract(
        location_tokens=["granite", "slate"],
    )
    raw = "Granite steps wear smooth under the slate roof."
    out = apply_final_emission_gate(
        {
            "player_facing_text": raw,
            "tags": [],
            "scene_state_anchor_contract": contract,
        },
        resolution={"kind": "observe", "prompt": "I listen for routes."},
        session=None,
        scene_id="frontier_gate",
        world={},
    )
    assert out.get("player_facing_text") == raw
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("scene_state_anchor_checked") is True
    assert meta.get("scene_state_anchor_passed") is True
    assert meta.get("scene_state_anchor_failed") is False
    assert meta.get("scene_state_anchor_repaired") is False
    assert meta.get("scene_state_anchor_skip_reason") is None
    assert "location" in (meta.get("scene_state_anchor_matched_kinds") or [])


def test_scene_state_anchor_actor_rebind_repair_metadata():
    contract = _ssa_contract(actor_tokens=["mara the smith"])
    text, meta = feg._apply_scene_state_anchor_layer(
        "The hammer rings once.",
        gm_output={"scene_state_anchor_contract": contract},
        strict_social_details=None,
    )
    assert "Mara" in text or "mara" in text.lower()
    assert meta.get("scene_state_anchor_repaired") is True
    assert meta.get("scene_state_anchor_repair_mode") == "actor_rebind"
    assert meta.get("scene_state_anchor_passed") is True


def test_scene_state_anchor_action_rebind_repair_metadata():
    contract = _ssa_contract(
        actor_tokens=[],
        player_action_tokens=["north gate", "question"],
    )
    text, meta = feg._apply_scene_state_anchor_layer(
        "The guards exchange a look.",
        gm_output={"scene_state_anchor_contract": contract},
        strict_social_details=None,
    )
    assert "—" in text
    assert "north gate" in text.lower()
    assert meta.get("scene_state_anchor_repair_mode") == "action_rebind"
    assert meta.get("scene_state_anchor_passed") is True


def test_scene_state_anchor_location_rebind_repair_metadata():
    contract = _ssa_contract(
        scene_location_label="Stone Quay",
        location_tokens=["quay", "stone"],
    )
    text, meta = feg._apply_scene_state_anchor_layer(
        "Gulls wheel overhead.",
        gm_output={"scene_state_anchor_contract": contract},
        strict_social_details=None,
    )
    assert text.lower().startswith("at ")
    assert "quay" in text.lower()
    assert meta.get("scene_state_anchor_repair_mode") == "location_rebind"
    assert meta.get("scene_state_anchor_passed") is True


def test_scene_state_anchor_narrator_neutral_only_when_location_rebind_unavailable(monkeypatch):
    """If `location_rebind` cannot run, the ladder may still reach narrator-neutral scene rebind."""

    def no_location_opening(*args, **kwargs):
        return None, None

    monkeypatch.setattr(feg, "_repair_location_opening", no_location_opening)
    contract = _ssa_contract(
        scene_location_label="Ash Harbor",
        location_tokens=["harbor"],
    )
    text, meta = feg._apply_scene_state_anchor_layer(
        "Salt stings the air.",
        gm_output={"scene_state_anchor_contract": contract},
        strict_social_details=None,
    )
    assert text.lower().startswith("here at ")
    assert meta.get("scene_state_anchor_repair_mode") == "narrator_neutral_scene_rebind"
    assert meta.get("scene_state_anchor_passed") is True


def test_scene_state_anchor_unrecoverable_preserves_text_and_records_failure():
    contract = _ssa_contract(
        enabled=True,
        location_tokens=[],
        actor_tokens=[],
        player_action_tokens=[],
        scene_location_label=None,
    )
    raw = "Untethered prose with no hooks."
    text, meta = feg._apply_scene_state_anchor_layer(
        raw,
        gm_output={"scene_state_anchor_contract": contract},
        strict_social_details=None,
    )
    assert text == raw
    assert meta.get("scene_state_anchor_failed") is True
    assert meta.get("scene_state_anchor_repaired") is False
    assert meta.get("scene_state_anchor_repair_mode") is None
    assert meta.get("scene_state_anchor_passed") is False
    assert "no_anchor_match" in (meta.get("scene_state_anchor_failure_reasons") or [])


def test_scene_state_anchor_fast_fallback_neutral_prefers_location_rebind_over_actor_prefix():
    contract = _ssa_contract(
        scene_location_label="Frontier Gate",
        location_tokens=["frontier gate", "gate"],
        actor_tokens=["emergent lord aldric"],
    )
    text, meta = feg._apply_scene_state_anchor_layer(
        "Several patrons exchange furtive glances.",
        gm_output={
            "scene_state_anchor_contract": contract,
            "tags": ["forced_retry_fallback", "upstream_api_fast_fallback"],
        },
        strict_social_details=None,
    )
    assert "emergent lord aldric several" not in text.lower()
    assert text.lower().startswith("at frontier gate")
    assert meta.get("scene_state_anchor_repair_mode") == "location_rebind"
    assert meta.get("scene_state_anchor_passed") is True


def test_apply_final_emission_gate_repairs_malformed_opening_fast_fallback_composition():
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    session["active_scene_id"] = sid
    session["scene_state"]["active_scene_id"] = sid
    session["turn_counter"] = 0
    session["visited_scene_ids"] = [sid]
    scene = default_scene(sid)
    scene["scene"]["location"] = "Frontier Gate"
    scene["scene"]["summary"] = "A rain-soaked checkpoint holds a nervous crowd at the gate."
    scene["scene"]["visible_facts"] = [
        "Several patrons exchange furtive glances.",
        "A notice board lists a missing patrol.",
        "Rain darkens the flagstones around the checkpoint.",
    ]
    rebuild_active_scene_entities(session, world, sid, scene_envelope=scene)
    scene["scene_state"] = dict(session["scene_state"])

    out = apply_final_emission_gate(
        {
            "player_facing_text": (
                "Emergent Lord Aldric Several patrons exchange furtive glances. "
                "The rain holds; beside it, a notice board lists a missing patrol."
            ),
            "tags": ["forced_retry_fallback", "upstream_api_fast_fallback"],
            "scene_state_anchor_contract": _ssa_contract(
                scene_id=sid,
                scene_location_label="Frontier Gate",
                location_tokens=["frontier gate", "gate", "checkpoint"],
                actor_tokens=["emergent lord aldric"],
            ),
        },
        resolution={"kind": "observe", "prompt": "Begin."},
        session=session,
        scene_id=sid,
        scene=scene,
        world=world,
    )

    text = str(out.get("player_facing_text") or "")
    low = text.lower()
    meta = out.get("_final_emission_meta") or {}
    assert "emergent lord aldric several" not in low
    assert "holds; beside it" not in low
    assert any(token in low for token in ("checkpoint", "gate", "patrol", "rain"))
    assert meta.get("fast_fallback_neutral_composition_repaired") is True
    assert meta.get("fast_fallback_neutral_composition_repair_mode") == "opening_scene_template"
    assert meta.get("final_emitted_source") == "opening_scene_template"


def test_ssa_layer_skip_reasons_direct():
    assert feg._skip_scene_state_anchor_layer(
        "x",
        None,
        strict_social_details=None,
    ) == "missing_contract"

    assert feg._skip_scene_state_anchor_layer(
        "x",
        _ssa_contract(enabled=False),
        strict_social_details=None,
    ) == "contract_disabled"

    assert feg._skip_scene_state_anchor_layer(
        "",
        _ssa_contract(),
        strict_social_details=None,
    ) == "empty_text"

    assert feg._skip_scene_state_anchor_layer(
        None,
        _ssa_contract(),
        strict_social_details=None,
    ) == "non_string_text"

    assert feg._skip_scene_state_anchor_layer(
        "x",
        _ssa_contract(),
        strict_social_details={"used_internal_fallback": True},
    ) == "strict_social_authoritative_internal_fallback"

    assert feg._skip_scene_state_anchor_layer(
        "x",
        _ssa_contract(),
        strict_social_details={"final_emitted_source": "neutral_reply_speaker_grounding_bridge"},
    ) == "strict_social_structured_or_bridge_source"

    assert feg._skip_scene_state_anchor_layer(
        "x",
        _ssa_contract(),
        strict_social_details=None,
        response_type_debug={"response_type_candidate_ok": False},
    ) == "response_type_contract_failed"


def test_final_emission_meta_and_emission_debug_merge_scene_state_anchor(monkeypatch):
    upstream = {"enabled": True, "scene_id": "frontier_gate", "counts": {"location": 2, "actor": 1, "player_action": 0}}
    gm_out = {
        "player_facing_text": "The wind shifts.",
        "tags": [],
        "scene_state_anchor_contract": _ssa_contract(location_tokens=["checkpoint"]),
        "metadata": {
            "emission_debug": {
                "scene_state_anchor": dict(upstream),
                "prior_debug_counts": {"x": 1},
            }
        },
    }
    out = apply_final_emission_gate(
        gm_out,
        resolution={"kind": "observe", "prompt": "I look."},
        session={},
        scene_id="frontier_gate",
        world={},
    )
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("scene_state_anchor_checked") is True
    assert meta.get("scene_state_anchor_upstream_debug") == upstream
    em = (out.get("metadata") or {}).get("emission_debug") or {}
    merged = em.get("scene_state_anchor") or {}
    assert merged.get("counts") == {"location": 2, "actor": 1, "player_action": 0}
    assert em.get("scene_state_anchor_passed") is True or em.get("scene_state_anchor_repaired") is True
    assert em.get("prior_debug_counts") == {"x": 1}
    flat_ok = any(k.startswith("scene_state_anchor_") for k in em.keys())
    assert flat_ok


def test_validate_scene_state_anchoring_invoked_and_reinvoked_on_repair(monkeypatch):
    calls: list[str] = []

    def tracking_validate(t, c):
        calls.append(str(t))
        if len(calls) == 1:
            return {
                "checked": True,
                "passed": False,
                "matched_anchor_kinds": [],
                "failure_reasons": ["no_anchor_match"],
            }
        return {
            "checked": True,
            "passed": True,
            "matched_anchor_kinds": ["location"],
            "failure_reasons": [],
        }

    monkeypatch.setattr(feg, "validate_scene_state_anchoring", tracking_validate)
    contract = _ssa_contract(location_tokens=["beacon"])
    out = apply_final_emission_gate(
        {
            "player_facing_text": "Fog rolls in.",
            "tags": [],
            "scene_state_anchor_contract": contract,
        },
        resolution={"kind": "observe", "prompt": "I watch."},
        session={},
        scene_id="beacon_yard",
        world={},
    )
    assert len(calls) >= 2
    assert calls[0] == "Fog rolls in."
    assert "beacon" in calls[1].lower()
    assert out.get("_final_emission_meta", {}).get("scene_state_anchor_passed") is True


def test_gate_never_invokes_build_scene_state_anchor_contract(monkeypatch):
    def boom(*_a, **_kw):
        raise AssertionError("build_scene_state_anchor_contract must not be called from final emission gate")

    monkeypatch.setattr(ssa, "build_scene_state_anchor_contract", boom)
    out = apply_final_emission_gate(
        {
            "player_facing_text": "Stable air, cold iron.",
            "tags": [],
            "scene_state_anchor_contract": _ssa_contract(location_tokens=["stable"]),
        },
        resolution={"kind": "observe", "prompt": "I look."},
        session={},
        scene_id="frontier_gate",
        world={},
    )
    assert "stable" in (out.get("player_facing_text") or "").lower()


_contract_rope = _ssa_contract(location_tokens=["rope_bridge"])


@pytest.mark.parametrize(
    "attach_key,attach_payload",
    [
        ("scene_state_anchor_contract", _contract_rope),
        ("narration_payload", {"scene_state_anchor_contract": _contract_rope}),
        ("prompt_payload", {"scene_state_anchor_contract": _contract_rope}),
        ("_narration_payload", {"scene_state_anchor_contract": _contract_rope}),
        ("metadata", {"scene_state_anchor_contract": _contract_rope}),
        ("trace", {"scene_state_anchor_contract": _contract_rope}),
    ],
)
def test_contract_resolution_from_gm_output_nested_paths(attach_key, attach_payload):
    gm = {"player_facing_text": "Wind rises.", "tags": []}
    if attach_key == "scene_state_anchor_contract":
        gm["scene_state_anchor_contract"] = attach_payload
    else:
        gm[attach_key] = attach_payload
    out = apply_final_emission_gate(
        gm,
        resolution={"kind": "observe", "prompt": "I steady myself."},
        session={},
        scene_id="rope_bridge",
        world={},
    )
    assert "rope" in (out.get("player_facing_text") or "").lower()


def test_strict_social_npc_line_with_actor_token_passes_without_anchor_rewrite(monkeypatch):
    session, world, sid, resolution = _runner_strict_bundle()
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

    def fake_build(candidate_text, *, resolution, tags, session, scene_id, world):
        return 'Tavern Runner says, "East lanes."', dict(stub_details)

    monkeypatch.setattr(feg, "build_final_strict_social_response", fake_build)

    contract = _ssa_contract(actor_tokens=["tavern runner"])
    out = apply_final_emission_gate(
        {
            "player_facing_text": 'Tavern Runner says, "East lanes."',
            "tags": [],
            "scene_state_anchor_contract": contract,
        },
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("scene_state_anchor_repaired") is False
    assert meta.get("scene_state_anchor_passed") is True


def test_floating_narration_silence_line_fails_until_repaired():
    raw = "The silence stretches for a moment."
    out = apply_final_emission_gate(
        {
            "player_facing_text": raw,
            "tags": [],
            "scene_state_anchor_contract": _ssa_contract(
                scene_location_label="Frontier Checkpoint",
                location_tokens=["checkpoint"],
            ),
        },
        resolution={"kind": "observe", "prompt": "I wait."},
        session={},
        scene_id="frontier_gate",
        world={},
    )
    assert out.get("player_facing_text") != raw
    assert out.get("_final_emission_meta", {}).get("scene_state_anchor_repaired") is True


def test_contract_actor_only_player_action_only_location_only():
    for tokens, kind in (
        ({"actor_tokens": ["yrsa"]}, "actor"),
        ({"player_action_tokens": ["barter check", "question"]}, "player_action"),
        ({"location_tokens": ["granary"], "scene_location_label": "Old Granary"}, "location"),
    ):
        c = _ssa_contract(**tokens)
        out = apply_final_emission_gate(
            {
                "player_facing_text": "Dust motes drift.",
                "tags": [],
                "scene_state_anchor_contract": c,
            },
            resolution={"kind": "question", "prompt": "I look."},
            session={},
            scene_id="granary_scene",
            world={},
        )
        meta = out.get("_final_emission_meta") or {}
        assert meta.get("scene_state_anchor_passed") is True
        assert kind in (meta.get("scene_state_anchor_matched_kinds") or [])


def test_scene_transition_prefers_location_when_no_actor_tokens():
    out = apply_final_emission_gate(
        {
            "player_facing_text": "The road bends without a name.",
            "tags": [],
            "scene_state_anchor_contract": _ssa_contract(
                actor_tokens=[],
                player_action_tokens=[],
                location_tokens=["crossroads"],
                scene_location_label="The Crossroads",
            ),
        },
        resolution={"kind": "observe", "prompt": "I follow the road."},
        session={},
        scene_id="crossroads",
        world={},
    )
    m = out.get("_final_emission_meta") or {}
    assert m.get("scene_state_anchor_repair_mode") == "location_rebind"


def test_scene_location_label_used_when_location_tokens_sparse():
    """``scene_location_label`` drives the repair phrase; sparse ``location_tokens`` still validate the tether."""
    contract = _ssa_contract(
        location_tokens=["salt"],
        scene_location_label="Salt Docks",
    )
    text, meta = feg._apply_scene_state_anchor_layer(
        "Ropes creak.",
        gm_output={"scene_state_anchor_contract": contract},
        strict_social_details=None,
    )
    assert "salt" in text.lower()
    assert meta.get("scene_state_anchor_repair_mode") == "location_rebind"


def test_repaired_output_excludes_hidden_bucket_strings():
    gm_out = {
        "player_facing_text": "Stillness.",
        "tags": [],
        "scene_state_anchor_contract": _ssa_contract(location_tokens=["watchtower"]),
        "gm_only_hidden_facts": ["SECRET_CULT_LEADER_NAME_XYZ"],
        "metadata": {"emission_debug": {"scene_state_anchor": {"counts": {"location": 1, "actor": 0, "player_action": 0}}}},
    }
    out = apply_final_emission_gate(
        gm_out,
        resolution={"kind": "observe", "prompt": "I listen."},
        session={},
        scene_id="watchtower",
        world={},
    )
    assert "SECRET_CULT" not in (out.get("player_facing_text") or "")


def test_short_npc_line_grounded_by_actor_token_passes_without_rewrite():
    out = apply_final_emission_gate(
        {
            "player_facing_text": 'Kara says, "No."',
            "tags": [],
            "scene_state_anchor_contract": _ssa_contract(actor_tokens=["kara"]),
        },
        resolution={"kind": "question", "prompt": "Did they leave?"},
        session=None,
        scene_id="lane_scene",
        world={},
    )
    assert "Kara" in (out.get("player_facing_text") or "")
    m = out.get("_final_emission_meta") or {}
    assert m.get("scene_state_anchor_repaired") is False
    assert m.get("scene_state_anchor_passed") is True


def test_observational_follow_up_grounded_by_player_action_token():
    out = apply_final_emission_gate(
        {
            "player_facing_text": "You study the latch; rust flakes away.",
            "tags": [],
            "scene_state_anchor_contract": _ssa_contract(
                actor_tokens=[],
                player_action_tokens=["study", "latch", "investigate"],
            ),
        },
        resolution={"kind": "investigate", "prompt": "I study the latch."},
        session=None,
        scene_id="storeroom",
        world={},
    )
    m = out.get("_final_emission_meta") or {}
    assert m.get("scene_state_anchor_passed") is True
    assert "player_action" in (m.get("scene_state_anchor_matched_kinds") or [])


def test_strict_and_non_strict_repair_sync_metadata():
    contract = _ssa_contract(location_tokens=["pier"])
    non_strict = apply_final_emission_gate(
        {
            "player_facing_text": "Fog.",
            "tags": [],
            "scene_state_anchor_contract": contract,
        },
        resolution={"kind": "observe", "prompt": "I smell salt."},
        session={},
        scene_id="pier",
        world={},
    )
    ns = non_strict.get("_final_emission_meta") or {}
    em_ns = (non_strict.get("metadata") or {}).get("emission_debug") or {}
    assert ns.get("scene_state_anchor_repaired") is True
    assert em_ns.get("scene_state_anchor_repaired") is True

    text, layer_meta = feg._apply_scene_state_anchor_layer(
        "Fog.",
        gm_output={"scene_state_anchor_contract": contract},
        strict_social_details=None,
    )
    merged = {}
    feg._merge_scene_state_anchor_meta(merged, layer_meta)
    assert merged.get("scene_state_anchor_repaired") is True
    assert merged.get("scene_state_anchor_repair_mode") == "location_rebind"


def _iter_narration_constraint_strings(value):
    if isinstance(value, str):
        yield value
        return
    if isinstance(value, dict):
        for child in value.values():
            yield from _iter_narration_constraint_strings(child)
        return
    if isinstance(value, list):
        for child in value:
            yield from _iter_narration_constraint_strings(child)


def _assert_narration_constraint_payload_is_compact(payload: dict) -> None:
    assert set(payload) == {"response_type", "visibility", "speaker_selection"}
    assert set(payload["response_type"]) == {
        "required",
        "contract_source",
        "candidate_ok",
        "repair_used",
        "repair_kind",
    }
    assert set(payload["visibility"]) == {
        "contract_present",
        "decision_mode",
        "visible_entity_count",
        "withheld_fact_count",
        "reason_codes",
    }
    assert set(payload["speaker_selection"]) == {
        "speaker_id",
        "speaker_name",
        "selection_source",
        "reason_code",
        "binding_confident",
    }
    assert isinstance(payload["visibility"]["reason_codes"], list)
    assert len(payload["visibility"]["reason_codes"]) <= 5
    assert payload["visibility"]["visible_entity_count"] is None or isinstance(
        payload["visibility"]["visible_entity_count"], int
    )
    assert payload["visibility"]["withheld_fact_count"] is None or isinstance(
        payload["visibility"]["withheld_fact_count"], int
    )
    for text in _iter_narration_constraint_strings(payload):
        assert len(text) <= 120


def _assert_payload_omits_sentinels(payload: dict, *sentinels: str) -> None:
    blob = json.dumps(payload, sort_keys=True)
    for sentinel in sentinels:
        assert sentinel not in blob


def test_narration_constraint_debug_default_shape_is_stable():
    assert feg._default_narration_constraint_debug() == {
        "response_type": {
            "required": None,
            "contract_source": None,
            "candidate_ok": None,
            "repair_used": False,
            "repair_kind": None,
        },
        "visibility": {
            "contract_present": False,
            "decision_mode": None,
            "visible_entity_count": None,
            "withheld_fact_count": None,
            "reason_codes": [],
        },
        "speaker_selection": {
            "speaker_id": None,
            "speaker_name": None,
            "selection_source": None,
            "reason_code": None,
            "binding_confident": None,
        },
    }


def test_narration_constraint_debug_builder_and_merge_are_null_safe():
    payload = feg._build_narration_constraint_debug(
        response_type_debug={
            "response_type_required": "dialogue",
            "response_type_contract_source": "resolution.metadata",
            "response_type_candidate_ok": True,
            "response_type_repair_used": False,
            "response_type_repair_kind": None,
        },
        narration_visibility={
            "visible_entity_ids": ["runner", "guard"],
            "hidden_fact_strings": ["hidden one", "hidden two"],
        },
        visibility_meta={
            "visibility_validation_passed": False,
            "visibility_replacement_applied": True,
            "visibility_violation_kinds": [
                "hidden_fact_reference",
                "unseen_entity_reference",
                "hidden_fact_reference",
                "offscene_reference",
                "continuity_bleed",
                "should_not_fit",
            ],
        },
        speaker_selection_contract={
            "primary_speaker_id": "runner",
            "primary_speaker_name": "Tavern Runner",
            "primary_speaker_source": "continuity",
            "continuity_locked": True,
            "speaker_switch_allowed": False,
            "debug": {"grounding_reason_code": "grounded_in_scene_npc"},
        },
        speaker_contract_enforcement={
            "final_reason_code": "speaker_contract_match",
            "validation": {
                "reason_code": "speaker_contract_match",
                "details": {"signature": {"confidence": "high"}},
            },
        },
    )

    assert payload == {
        "response_type": {
            "required": "dialogue",
            "contract_source": "resolution.metadata",
            "candidate_ok": True,
            "repair_used": False,
            "repair_kind": None,
        },
        "visibility": {
            "contract_present": True,
            "decision_mode": "replaced",
            "visible_entity_count": 2,
            "withheld_fact_count": 2,
            "reason_codes": [
                "hidden_fact_reference",
                "unseen_entity_reference",
                "offscene_reference",
                "continuity_bleed",
                "should_not_fit",
            ],
        },
        "speaker_selection": {
            "speaker_id": "runner",
            "speaker_name": "Tavern Runner",
            "selection_source": "continuity",
            "reason_code": "speaker_contract_match",
            "binding_confident": True,
        },
    }

    metadata = {
        "other_key": 7,
        "emission_debug": {
            "speaker_contract_enforcement": {"final_reason_code": "speaker_contract_match"},
            "narration_constraint_debug": {
                "speaker_selection": {
                    "speaker_id": "runner",
                    "selection_source": "existing_source",
                }
            },
        },
    }
    feg._merge_narration_constraint_debug_meta(
        metadata,
        {
            "response_type": {"required": "dialogue"},
            "speaker_selection": {"speaker_name": "Tavern Runner"},
        },
    )

    merged = metadata["emission_debug"]["narration_constraint_debug"]
    assert metadata["other_key"] == 7
    assert metadata["emission_debug"]["speaker_contract_enforcement"]["final_reason_code"] == "speaker_contract_match"
    assert merged["response_type"]["required"] == "dialogue"
    assert merged["response_type"]["repair_used"] is False
    assert merged["speaker_selection"]["speaker_id"] == "runner"
    assert merged["speaker_selection"]["selection_source"] == "existing_source"
    assert merged["speaker_selection"]["speaker_name"] == "Tavern Runner"
    assert merged["visibility"]["reason_codes"] == []


def test_narration_constraint_debug_excludes_sensitive_and_verbose_inputs():
    hidden_fact = "The cult leader's name is Marrow Vale."
    unpublished_clue = "The ledger under the chapel floor names Iven as the courier."
    raw_prompt = "Player prompt fragment: tell me the secret name from the hidden ledger right now."
    candidate_generation = (
        'Candidate generation: Tavern Runner says, "The ledger under the chapel floor names Iven as the courier."'
    )
    contract_dump = (
        'Contract dump: {"allowed_speaker_ids":["runner","guard"],"debug":{"authoritative_source":"prompt"}}'
    )
    roster_dump = "Scene roster: Tavern Runner, Gate Guard, Harbor Priest, Smuggler Lookout, Dock Clerk."
    long_narration = " ".join(["Rain hammers the slate roof while the harbor bells answer the wind."] * 8)

    payload = feg._build_narration_constraint_debug(
        response_type_debug={
            "response_type_required": "dialogue",
            "response_type_contract_source": raw_prompt,
            "response_type_candidate_ok": True,
            "response_type_repair_used": True,
            "response_type_repair_kind": candidate_generation,
        },
        narration_visibility={
            "visible_entity_ids": ["runner", "guard", "priest"],
            "hidden_fact_strings": [hidden_fact, unpublished_clue],
        },
        visibility_meta={
            "visibility_validation_passed": False,
            "visibility_violation_kinds": [
                hidden_fact,
                unpublished_clue,
                raw_prompt,
                candidate_generation,
                contract_dump,
                roster_dump,
                long_narration,
            ],
        },
        speaker_selection_contract={
            "primary_speaker_id": "runner",
            "primary_speaker_name": roster_dump,
            "primary_speaker_source": raw_prompt,
            "debug": {
                "grounding_reason_code": contract_dump,
                "authoritative_source": roster_dump,
            },
        },
        speaker_contract_enforcement={
            "final_reason_code": candidate_generation,
            "validation": {
                "reason_code": unpublished_clue,
                "canonical_speaker_name": long_narration,
                "details": {"signature": {"confidence": "high"}},
            },
        },
        speaker_binding_bridge={
            "speaker_reason_code": contract_dump,
            "malformed_attribution_detected": False,
        },
    )

    assert payload["response_type"]["required"] == "dialogue"
    assert payload["visibility"]["contract_present"] is True
    assert payload["visibility"]["visible_entity_count"] == 3
    assert payload["visibility"]["withheld_fact_count"] == 2
    _assert_narration_constraint_payload_is_compact(payload)
    _assert_payload_omits_sentinels(
        payload,
        hidden_fact,
        unpublished_clue,
        raw_prompt,
        candidate_generation,
        contract_dump,
        roster_dump,
        long_narration,
    )


def test_narration_constraint_debug_speaker_fallback_reason_codes_are_stable():
    explicit = feg._build_narration_constraint_debug(
        speaker_selection_contract={
            "primary_speaker_id": "runner",
            "primary_speaker_name": "Tavern Runner",
            "primary_speaker_source": "explicit_target",
        }
    )
    assert explicit["speaker_selection"]["reason_code"] == "speaker_from_explicit_target"

    continuity = feg._build_narration_constraint_debug(
        speaker_selection_contract={
            "primary_speaker_id": "runner",
            "primary_speaker_name": "Tavern Runner",
            "primary_speaker_source": "continuity",
        }
    )
    assert continuity["speaker_selection"]["reason_code"] == "speaker_from_continuity"

    unresolved = feg._build_narration_constraint_debug()
    assert unresolved["speaker_selection"]["reason_code"] == "speaker_unresolved"


def test_narration_constraint_debug_prefers_grounded_speaker_reason_code_over_fallbacks():
    payload = feg._build_narration_constraint_debug(
        speaker_selection_contract={
            "primary_speaker_id": "runner",
            "primary_speaker_name": "Tavern Runner",
            "primary_speaker_source": "continuity",
            "debug": {"grounding_reason_code": "speaker_from_continuity"},
        },
        speaker_contract_enforcement={
            "final_reason_code": "local_rebind",
            "validation": {"details": {"signature": {"confidence": "high"}}},
        },
        speaker_binding_bridge={"speaker_reason_code": "speaker_from_explicit_target"},
    )
    assert payload["speaker_selection"]["reason_code"] == "local_rebind"


def test_narration_constraint_debug_missing_speaker_inputs_do_not_emit_noisy_values():
    noisy = "Malformed prompt fragment that should never surface in narration_constraint_debug output."
    payload = feg._build_narration_constraint_debug(
        speaker_selection_contract={
            "primary_speaker_source": noisy,
            "debug": {
                "grounding_reason_code": noisy,
                "authoritative_source": noisy,
            },
        },
        speaker_contract_enforcement={
            "validation": {"reason_code": noisy},
        },
        speaker_binding_bridge={"speaker_reason_code": noisy},
    )

    assert payload["speaker_selection"]["speaker_id"] is None
    assert payload["speaker_selection"]["speaker_name"] is None
    assert payload["speaker_selection"]["reason_code"] == "speaker_unresolved"
    _assert_payload_omits_sentinels(payload, noisy)


def test_merge_narration_constraint_debug_into_outputs_is_null_safe_and_preserves_metadata(monkeypatch):
    out = {
        "player_facing_text": "Rain drums on the slate roof.",
        "_final_emission_meta": {"visibility_validation_passed": True},
        "metadata": {
            "top_level_keep": {"ok": True},
            "emission_debug": {
                "existing_out_debug": {"count": 1},
            },
        },
    }
    resolution = {
        "kind": "observe",
        "prompt": "I listen.",
        "metadata": {
            "resolution_keep": {"source": "original"},
            "emission_debug": {"existing_resolution_debug": {"count": 2}},
        },
    }
    eff_resolution = {
        "kind": "observe",
        "metadata": {
            "effective_keep": {"source": "effective"},
            "emission_debug": {"existing_effective_debug": {"count": 3}},
        },
    }

    monkeypatch.setattr(feg, "get_speaker_selection_contract", lambda *a, **kw: None)

    feg._merge_narration_constraint_debug_into_outputs(
        out,
        resolution,
        eff_resolution,
        session=None,
        scene=None,
        world=None,
        response_type_debug={"response_type_required": "neutral_narration"},
        speaker_contract_enforcement=None,
    )

    out_payload = ((out.get("metadata") or {}).get("emission_debug") or {}).get("narration_constraint_debug")
    res_payload = ((resolution.get("metadata") or {}).get("emission_debug") or {}).get("narration_constraint_debug")
    eff_payload = ((eff_resolution.get("metadata") or {}).get("emission_debug") or {}).get("narration_constraint_debug")

    assert out["metadata"]["top_level_keep"] == {"ok": True}
    assert out["metadata"]["emission_debug"]["existing_out_debug"] == {"count": 1}
    assert resolution["metadata"]["resolution_keep"] == {"source": "original"}
    assert resolution["metadata"]["emission_debug"]["existing_resolution_debug"] == {"count": 2}
    assert eff_resolution["metadata"]["effective_keep"] == {"source": "effective"}
    assert eff_resolution["metadata"]["emission_debug"]["existing_effective_debug"] == {"count": 3}
    assert out_payload == res_payload == eff_payload
    assert out_payload["response_type"]["required"] == "neutral_narration"
    assert out_payload["speaker_selection"]["reason_code"] == "speaker_unresolved"
    _assert_narration_constraint_payload_is_compact(out_payload)


def test_apply_final_emission_gate_tolerates_missing_gm_output_for_narration_constraint_debug():
    assert apply_final_emission_gate(
        None,
        resolution=None,
        session=None,
        scene_id="scene_investigate",
        world=None,
    ) is None


def test_apply_final_emission_gate_surfaces_narration_constraint_debug_in_metadata(monkeypatch):
    session, world, sid, resolution = _runner_strict_bundle()
    speaker_contract = {
        "primary_speaker_id": "runner",
        "primary_speaker_name": "Tavern Runner",
        "primary_speaker_source": "continuity",
        "allowed_speaker_ids": ["runner"],
        "continuity_locked": True,
        "speaker_switch_allowed": False,
        "debug": {"grounding_reason_code": "grounded_in_scene_npc"},
    }
    monkeypatch.setattr(feg, "get_speaker_selection_contract", lambda *a, **kw: dict(speaker_contract))

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

    def fake_build(candidate_text, *, resolution, tags, session, scene_id, world):
        return 'Tavern Runner says, "East lanes."', dict(stub_details)

    monkeypatch.setattr(feg, "build_final_strict_social_response", fake_build)

    out = apply_final_emission_gate(
        {
            "player_facing_text": 'Tavern Runner says, "East lanes."',
            "tags": [],
            "response_policy": {"response_type_contract": _response_type_contract("dialogue")},
        },
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )

    payload = ((out.get("metadata") or {}).get("emission_debug") or {}).get("narration_constraint_debug") or {}
    assert payload["response_type"]["required"] == "dialogue"
    assert payload["response_type"]["candidate_ok"] is True
    assert payload["visibility"]["contract_present"] is True
    assert isinstance(payload["visibility"]["visible_entity_count"], int)
    assert payload["speaker_selection"] == {
        "speaker_id": "runner",
        "speaker_name": "Tavern Runner",
        "selection_source": "continuity",
        "reason_code": "speaker_contract_match",
        "binding_confident": True,
    }

    res_payload = ((resolution.get("metadata") or {}).get("emission_debug") or {}).get("narration_constraint_debug") or {}
    assert res_payload == payload


def test_apply_final_emission_gate_narration_constraint_debug_stays_compact_after_gate_pass(monkeypatch):
    session, world, sid, resolution = _runner_strict_bundle()
    speaker_contract = {
        "primary_speaker_id": "runner",
        "primary_speaker_name": "Tavern Runner",
        "primary_speaker_source": "continuity",
        "allowed_speaker_ids": ["runner"],
        "continuity_locked": True,
        "speaker_switch_allowed": False,
        "debug": {"grounding_reason_code": "grounded_in_scene_npc"},
    }
    monkeypatch.setattr(feg, "get_speaker_selection_contract", lambda *a, **kw: dict(speaker_contract))

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

    def fake_build(candidate_text, *, resolution, tags, session, scene_id, world):
        return 'Tavern Runner says, "East lanes."', dict(stub_details)

    monkeypatch.setattr(feg, "build_final_strict_social_response", fake_build)

    secret_fact = "The sealed ledger under the chapel floor names Iven as the courier."
    prompt_fragment = "Player prompt fragment: reveal the sealed ledger courier by name."
    candidate_generation = (
        'Candidate generation: Tavern Runner says, "The sealed ledger under the chapel floor names Iven as the courier."'
    )

    out = apply_final_emission_gate(
        {
            "player_facing_text": 'Tavern Runner says, "East lanes."',
            "tags": [],
            "gm_only_hidden_facts": [secret_fact],
            "metadata": {
                "top_level_keep": {"ok": True},
                "emission_debug": {
                    "existing_debug": {"count": 1},
                    "raw_prompt_fragment": prompt_fragment,
                    "candidate_generations": [candidate_generation],
                },
            },
            "response_policy": {"response_type_contract": _response_type_contract("dialogue")},
        },
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )

    payload = ((out.get("metadata") or {}).get("emission_debug") or {}).get("narration_constraint_debug") or {}
    assert payload["response_type"]["required"] == "dialogue"
    assert "response_type" in payload
    assert "visibility" in payload
    assert "speaker_selection" in payload
    assert (out.get("metadata") or {}).get("top_level_keep") == {"ok": True}
    assert ((out.get("metadata") or {}).get("emission_debug") or {}).get("existing_debug") == {"count": 1}
    _assert_narration_constraint_payload_is_compact(payload)
    _assert_payload_omits_sentinels(payload, secret_fact, prompt_fragment, candidate_generation)

# --- Narrative authority (Objective #9 Block 3 contract resolution + strict-social slice) ---------


def _na_contract_for_resolution(resolution: dict) -> dict:
    return build_narrative_authority_contract(
        resolution=resolution,
        narration_visibility={},
        scene_state_anchor_contract=None,
        speaker_selection_contract=None,
        session_view=None,
    )


def _response_type_debug(*, candidate_ok: bool | None = True) -> dict:
    return {
        "response_type_required": None,
        "response_type_contract_source": None,
        "response_type_candidate_ok": candidate_ok,
        "response_type_repair_used": False,
        "response_type_repair_kind": None,
        "response_type_rejection_reasons": [],
        "non_hostile_escalation_blocked": False,
    }


def test_resolve_narrative_authority_full_contract_from_response_policy():
    res = {"kind": "observe", "prompt": "I listen."}
    na = _na_contract_for_resolution(res)
    gm = {"response_policy": {"narrative_authority": na}}
    full = feg._resolve_narrative_authority_contract(gm)
    assert full is na
    assert feg._is_shipped_full_narrative_authority_contract(full) is True


def test_resolve_narrative_authority_slim_prompt_debug_is_not_full_contract():
    slim = {"enabled": True, "authoritative_outcome_available": False}
    gm = {"prompt_debug": {"narrative_authority": slim}}
    assert feg._is_shipped_full_narrative_authority_contract(slim) is False
    assert feg._resolve_narrative_authority_contract(gm) is None


def test_resolve_narrative_authority_full_contract_from_narration_payload():
    res = {"kind": "observe", "prompt": "I listen."}
    na = _na_contract_for_resolution(res)
    gm = {"narration_payload": {"narrative_authority": na}}
    assert feg._resolve_narrative_authority_contract(gm) is na


def test_resolve_narrative_authority_full_contract_from_prompt_payload():
    res = {"kind": "observe", "prompt": "I listen."}
    na = _na_contract_for_resolution(res)
    gm = {"prompt_payload": {"narrative_authority": na}}
    assert feg._resolve_narrative_authority_contract(gm) is na


def test_resolve_narrative_authority_full_contract_from_trace_response_policy():
    res = {"kind": "observe", "prompt": "I listen."}
    na = _na_contract_for_resolution(res)
    gm = {"trace": {"response_policy": {"narrative_authority": na}}}
    assert feg._resolve_narrative_authority_contract(gm) is na


def test_resolve_narrative_authority_full_contract_from_narration_payload_mirror_key():
    res = {"kind": "observe", "prompt": "I listen."}
    na = _na_contract_for_resolution(res)
    gm = {"_narration_payload": {"response_policy": {"narrative_authority": na}}}
    assert feg._resolve_narrative_authority_contract(gm) is na


def test_skip_narrative_authority_when_forbid_unjustified_is_false():
    res = {"kind": "observe", "prompt": "I listen."}
    na = _na_contract_for_resolution(res)
    gm = {
        "response_policy": {
            "forbid_unjustified_narrative_authority": False,
            "narrative_authority": na,
        }
    }
    text, meta, _ = feg._apply_narrative_authority_layer(
        "The lock clicks open.",
        gm_output=gm,
        resolution=res,
        strict_social_details=None,
        response_type_debug=_response_type_debug(),
        answer_completeness_meta={},
        session={},
        scene_id="s",
    )
    assert meta["narrative_authority_skip_reason"] == "narrative_authority_policy_disabled"
    assert meta["narrative_authority_checked"] is False
    assert text == "The lock clicks open."


def test_skip_narrative_authority_when_contract_enabled_false():
    res = {"kind": "observe", "prompt": "I listen."}
    base = _na_contract_for_resolution(res)
    na = {**base, "enabled": False}
    gm = {"response_policy": {"narrative_authority": na}}
    text, meta, _ = feg._apply_narrative_authority_layer(
        "The lock clicks open.",
        gm_output=gm,
        resolution=res,
        strict_social_details=None,
        response_type_debug=_response_type_debug(),
        answer_completeness_meta={},
        session={},
        scene_id="s",
    )
    assert meta["narrative_authority_skip_reason"] == "contract_disabled"
    assert meta["narrative_authority_checked"] is False


def test_skip_narrative_authority_when_response_type_candidate_not_ok():
    res = {"kind": "observe", "prompt": "I listen."}
    na = _na_contract_for_resolution(res)
    gm = {"response_policy": {"narrative_authority": na}}
    text, meta, _ = feg._apply_narrative_authority_layer(
        "The lock clicks open.",
        gm_output=gm,
        resolution=res,
        strict_social_details=None,
        response_type_debug=_response_type_debug(candidate_ok=False),
        answer_completeness_meta={},
        session={},
        scene_id="s",
    )
    assert meta["narrative_authority_skip_reason"] == "response_type_contract_failed"
    assert meta["narrative_authority_checked"] is False


def test_skip_narrative_authority_only_slim_prompt_debug_no_validation():
    res = {"kind": "observe", "prompt": "I look."}
    slim = {"enabled": True, "authoritative_outcome_available": False}
    gm = {"prompt_debug": {"narrative_authority": slim}, "response_policy": {}}
    text, meta, _ = feg._apply_narrative_authority_layer(
        "The lock clicks open.",
        gm_output=gm,
        resolution=res,
        strict_social_details=None,
        response_type_debug=_response_type_debug(),
        answer_completeness_meta={},
        session={},
        scene_id="s",
    )
    assert meta["narrative_authority_skip_reason"] == "no_full_contract"
    assert meta["narrative_authority_checked"] is False
    assert text == "The lock clicks open."


def test_apply_na_with_full_contract_validates_normally():
    res = {"kind": "observe", "prompt": "I look at the moss."}
    na = _na_contract_for_resolution(res)
    gm = {"response_policy": {"narrative_authority": na}}
    text, meta, _ = feg._apply_narrative_authority_layer(
        "Rain brightens the moss; nothing is decided yet.",
        gm_output=gm,
        resolution=res,
        strict_social_details=None,
        response_type_debug=_response_type_debug(),
        answer_completeness_meta={},
        session={},
        scene_id="s",
    )
    assert meta["narrative_authority_skip_reason"] is None
    assert meta["narrative_authority_checked"] is True
    assert meta["narrative_authority_failed"] is False
    assert text == "Rain brightens the moss; nothing is decided yet."


def test_strict_social_gate_repairs_motive_overclaim_and_keeps_speaker(monkeypatch):
    """Slice: strict-social path runs NA before speaker enforcement; repair preserves NPC line."""
    session, world, sid, resolution = _runner_strict_bundle()
    eff, route, _ = effective_strict_social_resolution_for_emission(resolution, session, world, sid)
    assert route is True

    na = _na_contract_for_resolution(eff if isinstance(eff, dict) else resolution)
    # Newline so intent lives in its own sentence (quoted periods are masked and can
    # prevent splitting; one merged sentence would replace the whole NPC line on repair).
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
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("narrative_authority_repaired") is True
    assert "plans to stall" not in text.lower()
    assert "Tavern Runner" in text
    assert meta.get("speaker_contract_enforcement_reason") == "speaker_contract_match"


def test_final_emission_gate_marks_non_hostile_escalation_blocked_on_tone_writer_overshoot() -> None:
    """When pre-repair text violates shipped tone policy, legacy meta records the overshoot."""
    ctr = {
        "enabled": True,
        "scene_id": "hall",
        "base_tone": "neutral",
        "max_allowed_tone": "guarded",
        "allow_guarded_refusal": True,
        "allow_verbal_pressure": False,
        "allow_explicit_threat": False,
        "allow_physical_hostility": False,
        "allow_combat_initiation": False,
        "justification_flags": {},
        "justification_reasons": [],
        "debug_inputs": {"scene_id": "hall"},
        "debug_flags": {},
    }
    out = apply_final_emission_gate(
        {
            "player_facing_text": "Out of nowhere, chaos erupts through the hall.",
            "tags": [],
            "response_policy": {"tone_escalation": ctr},
        },
        resolution={"kind": "observe", "prompt": "I listen."},
        session={},
        scene_id="hall",
        world={},
    )
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("non_hostile_escalation_blocked") is True
    assert meta.get("tone_escalation_violation_before_repair") is True


# --- Anti-railroading (Objective Block 3) -------------------------------------------------------


def _ar_contract(**kwargs):
    return build_anti_railroading_contract(
        resolution=kwargs.get("resolution"),
        prompt_leads=kwargs.get("prompt_leads"),
        player_text=kwargs.get("player_text"),
    )


def test_anti_railroading_gate_passes_clean_leads_and_constraints():
    for raw in (
        "Two leads stand out: the lighthouse keeper and the customs office.",
        "The bridge is out. The alley and the roofline are still open.",
        "If you want an immediate answer, confronting the priest publicly is one option.",
    ):
        out = apply_final_emission_gate(
            {"player_facing_text": raw, "tags": [], "anti_railroading_contract": _ar_contract()},
            resolution={"kind": "observe", "prompt": "I look around."},
            session={},
            scene_id="dock",
            world={},
        )
        assert out.get("player_facing_text") == raw
        meta = out.get("_final_emission_meta") or {}
        assert meta.get("anti_railroading_repaired") is False
        em = (out.get("metadata") or {}).get("emission_debug") or {}
        assert em.get("anti_railroading", {}).get("validation", {}).get("passed") is True


def test_anti_railroading_gate_repairs_forced_pathing():
    out = apply_final_emission_gate(
        {"player_facing_text": "You head straight to the archive.", "tags": []},
        resolution={"kind": "observe", "prompt": "I look."},
        session={},
        scene_id="s",
        world={},
    )
    text = out.get("player_facing_text") or ""
    assert "you could head there" in text.lower()
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("anti_railroading_repaired") is True


def test_anti_railroading_gate_repairs_exclusive_and_meta_hooks():
    for raw in (
        "The only real lead is the archive.",
        "This is where the story wants you to go.",
        "It's obvious now that you must follow the priest.",
        "Everything points to Greywake, so you go there.",
    ):
        out = apply_final_emission_gate(
            {"player_facing_text": raw, "tags": []},
            resolution={"kind": "observe", "prompt": "I listen."},
            session={},
            scene_id="s",
            world={},
        )
        meta = out.get("_final_emission_meta") or {}
        assert meta.get("anti_railroading_repaired") is True, raw
        assert (out.get("player_facing_text") or "").strip() != raw.strip()


def test_anti_railroading_resolved_transition_allows_arrival_language():
    res = {"kind": "travel", "resolved_transition": True, "prompt": "I enter the ward."}
    c = _ar_contract(resolution=res)
    raw = "You step through the arch into the lower ward, noise washing over you."
    out = apply_final_emission_gate(
        {"player_facing_text": raw, "tags": [], "anti_railroading_contract": c},
        resolution=res,
        session={},
        scene_id="ward",
        world={},
    )
    assert out.get("player_facing_text") == raw
    assert (out.get("_final_emission_meta") or {}).get("anti_railroading_repaired") is False


def test_anti_railroading_commitment_echo_allowed_when_player_committed():
    pt = "I'll head to the archives and check the register."
    c = _ar_contract(player_text=pt)
    raw = "You head toward the archives, letting the crowd carry you a block at a time."
    out = apply_final_emission_gate(
        {"player_facing_text": raw, "tags": [], "anti_railroading_contract": c},
        resolution={"kind": "observe", "prompt": pt},
        session={"scene_runtime": {"test_scene": {"last_player_action_text": pt}}},
        scene_id="test_scene",
        world={},
    )
    assert out.get("player_facing_text") == raw


def test_anti_railroading_quoted_dialogue_not_spuriously_flagged():
    raw = 'The clerk mutters, "You head straight to the archive." Then the door clicks.'
    out = apply_final_emission_gate(
        {"player_facing_text": raw, "tags": []},
        resolution={"kind": "observe", "prompt": "I listen."},
        session={},
        scene_id="s",
        world={},
    )
    assert '"' in (out.get("player_facing_text") or "")
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("anti_railroading_repaired") is False


def test_anti_railroading_prompt_context_contract_resolution():
    c = _ar_contract()
    out = apply_final_emission_gate(
        {
            "player_facing_text": "You head straight to the pier.",
            "tags": [],
            "prompt_context": {"anti_railroading_contract": c},
        },
        resolution={"kind": "observe", "prompt": "I walk."},
        session={},
        scene_id="pier",
        world={},
    )
    assert (out.get("_final_emission_meta") or {}).get("anti_railroading_repaired") is True
    assert (out.get("_final_emission_meta") or {}).get("anti_railroading_contract_resolution_source") == "shipped"


def test_anti_railroading_coexists_with_narrative_authority_and_tone():
    na = build_narrative_authority_contract(
        resolution={"kind": "observe", "prompt": "I look."},
        narration_visibility={},
        scene_state_anchor_contract=None,
        speaker_selection_contract=None,
        session_view=None,
    )
    ctr = {
        "enabled": True,
        "scene_id": "hall",
        "base_tone": "neutral",
        "max_allowed_tone": "tense",
        "allow_guarded_refusal": True,
        "allow_verbal_pressure": True,
        "allow_explicit_threat": False,
        "allow_physical_hostility": False,
        "allow_combat_initiation": False,
        "justification_flags": {},
        "justification_reasons": [],
        "debug_inputs": {"scene_id": "hall"},
        "debug_flags": {},
    }
    out = apply_final_emission_gate(
        {
            "player_facing_text": "The only real lead is the cellar door.",
            "tags": [],
            "response_policy": {"narrative_authority": na, "tone_escalation": ctr},
        },
        resolution={"kind": "observe", "prompt": "I listen."},
        session={},
        scene_id="hall",
        world={},
    )
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("narrative_authority_checked") is True
    assert meta.get("tone_escalation_checked") is True
    assert meta.get("anti_railroading_repaired") is True
    em = (out.get("metadata") or {}).get("emission_debug") or {}
    assert "narrative_authority_checked" in em
    assert "tone_escalation_checked" in em
    assert em.get("anti_railroading", {}).get("validation", {}).get("checked") is True


def test_non_strict_gate_runs_anti_railroading_after_na_before_scene_state_anchor(monkeypatch):
    order: list[str] = []
    orig_na = feg._apply_narrative_authority_layer
    orig_ar = feg._apply_anti_railroading_layer
    orig_cs = feg._apply_context_separation_layer
    orig_pur = feg._apply_player_facing_narration_purity_layer
    orig_asp = feg._apply_answer_shape_primacy_layer
    orig_ssa = feg._apply_scene_state_anchor_layer

    def na(*args, **kwargs):
        order.append("narrative_authority")
        return orig_na(*args, **kwargs)

    def ar(*args, **kwargs):
        order.append("anti_railroading")
        return orig_ar(*args, **kwargs)

    def cs(*args, **kwargs):
        order.append("context_separation")
        return orig_cs(*args, **kwargs)

    def pur(*args, **kwargs):
        order.append("player_facing_narration_purity")
        return orig_pur(*args, **kwargs)

    def asp(*args, **kwargs):
        order.append("answer_shape_primacy")
        return orig_asp(*args, **kwargs)

    def ssa(*args, **kwargs):
        order.append("scene_state_anchor")
        return orig_ssa(*args, **kwargs)

    monkeypatch.setattr(feg, "_apply_narrative_authority_layer", na)
    monkeypatch.setattr(feg, "_apply_anti_railroading_layer", ar)
    monkeypatch.setattr(feg, "_apply_context_separation_layer", cs)
    monkeypatch.setattr(feg, "_apply_player_facing_narration_purity_layer", pur)
    monkeypatch.setattr(feg, "_apply_answer_shape_primacy_layer", asp)
    monkeypatch.setattr(feg, "_apply_scene_state_anchor_layer", ssa)

    cs_contract = build_context_separation_contract(
        player_text="I watch.",
        resolution={"kind": "observe"},
    )
    apply_final_emission_gate(
        {
            "player_facing_text": "Fog rolls in.",
            "tags": [],
            "context_separation_contract": cs_contract,
            "scene_state_anchor_contract": _ssa_contract(location_tokens=["granite"]),
        },
        resolution={"kind": "observe", "prompt": "I watch."},
        session={},
        scene_id="frontier_gate",
        world={},
    )
    assert order.index("narrative_authority") < order.index("anti_railroading")
    assert order.index("anti_railroading") < order.index("context_separation")
    assert order.index("context_separation") < order.index("player_facing_narration_purity")
    assert order.index("player_facing_narration_purity") < order.index("answer_shape_primacy")
    assert order.index("answer_shape_primacy") < order.index("scene_state_anchor")


def test_anti_railroading_surfaced_lead_mandatory_repair(monkeypatch):
    """Surfaced-lead mandatory framing is repaired before visibility enforcement (isolate AR)."""
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    c = _ar_contract(prompt_leads=[{"id": "h1", "title": "Harbor warehouse"}])
    raw = "The Harbor warehouse lead isn't optional; you're going there now."
    out = apply_final_emission_gate(
        {"player_facing_text": raw, "tags": [], "anti_railroading_contract": c},
        resolution={"kind": "observe", "prompt": "I look."},
        session={},
        scene_id="s",
        world={},
    )
    assert (out.get("_final_emission_meta") or {}).get("anti_railroading_repaired") is True
    low = (out.get("player_facing_text") or "").lower()
    assert "pressure" in low or "option" in low


def test_apply_final_emission_gate_runs_context_separation_before_scene_state_anchor(monkeypatch):
    order: list[str] = []
    orig_cs = feg._apply_context_separation_layer
    orig_pur = feg._apply_player_facing_narration_purity_layer
    orig_asp = feg._apply_answer_shape_primacy_layer
    orig_ssa = feg._apply_scene_state_anchor_layer

    def cs(*args, **kwargs):
        order.append("context_separation")
        return orig_cs(*args, **kwargs)

    def pur(*args, **kwargs):
        order.append("player_facing_narration_purity")
        return orig_pur(*args, **kwargs)

    def asp(*args, **kwargs):
        order.append("answer_shape_primacy")
        return orig_asp(*args, **kwargs)

    def ssa(*args, **kwargs):
        order.append("scene_state_anchor")
        return orig_ssa(*args, **kwargs)

    monkeypatch.setattr(feg, "_apply_context_separation_layer", cs)
    monkeypatch.setattr(feg, "_apply_player_facing_narration_purity_layer", pur)
    monkeypatch.setattr(feg, "_apply_answer_shape_primacy_layer", asp)
    monkeypatch.setattr(feg, "_apply_scene_state_anchor_layer", ssa)

    cs_contract = build_context_separation_contract(
        player_text="I look around.",
        resolution={"kind": "observe"},
    )
    apply_final_emission_gate(
        {
            "player_facing_text": "Fog rolls in low over the gate.",
            "tags": [],
            "context_separation_contract": cs_contract,
            "scene_state_anchor_contract": _ssa_contract(location_tokens=["granite"]),
        },
        resolution={"kind": "observe", "prompt": "I look around."},
        session={},
        scene_id="frontier_gate",
        world={},
    )
    assert order.index("context_separation") < order.index("player_facing_narration_purity")
    assert order.index("player_facing_narration_purity") < order.index("answer_shape_primacy")
    assert order.index("answer_shape_primacy") < order.index("scene_state_anchor")


def test_gate_context_separation_pass_brief_pressure_after_direct_answer(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    pt = "What does the loaf cost today?"
    cs = build_context_separation_contract(player_text=pt, resolution={"kind": "barter"})
    text = (
        'She names a price flatly. "Two coppers," she says. '
        "The ward's tense tonight—patrols everywhere—but bread is still bread."
    )
    out = apply_final_emission_gate(
        {"player_facing_text": text, "tags": [], "context_separation_contract": cs},
        resolution={"kind": "barter", "prompt": pt},
        session=None,
        scene_id="market_stall",
        world={},
    )
    em = (out.get("metadata") or {}).get("emission_debug") or {}
    assert em.get("context_separation", {}).get("validation", {}).get("passed") is True
    assert (out.get("_final_emission_meta") or {}).get("final_route") == "accept_candidate"


def test_gate_context_separation_pass_crisis_scene_pressure_focus(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    pt = "Where is the exit?"
    cs = build_context_separation_contract(
        player_text=pt,
        scene_summary="A raid tears through the lower ward; panic and smoke choke the alleys.",
        resolution={"kind": "travel"},
    )
    text = (
        "A guardsman points past a splintered door. "
        "The crackdown is still rolling house to house; you move or you are moved."
    )
    out = apply_final_emission_gate(
        {"player_facing_text": text, "tags": [], "context_separation_contract": cs},
        resolution={"kind": "travel", "prompt": pt},
        session=None,
        scene_id="ward_raid",
        world={},
    )
    em = (out.get("metadata") or {}).get("emission_debug") or {}
    assert em.get("context_separation", {}).get("validation", {}).get("passed") is True


def test_gate_context_separation_pass_player_asks_danger(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    pt = "Is it safe to linger here with the patrols?"
    cs = build_context_separation_contract(player_text=pt, resolution={"kind": "social_probe"})
    text = (
        "He doesn't laugh. 'Safe is a small word for a big war,' he says. "
        "Unrest has the factions eyeing each other; tonight, nowhere feels clean."
    )
    out = apply_final_emission_gate(
        {"player_facing_text": text, "tags": [], "context_separation_contract": cs},
        resolution={"kind": "social_probe", "prompt": pt},
        session=None,
        scene_id="street",
        world={},
    )
    em = (out.get("metadata") or {}).get("emission_debug") or {}
    assert em.get("context_separation", {}).get("validation", {}).get("passed") is True


def test_gate_context_separation_repair_drops_pressure_lead_in(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    pt = "What does the loaf cost today?"
    cs = build_context_separation_contract(player_text=pt, resolution={"kind": "barter"})
    text = (
        "The war along the border has everyone on edge, and coin means nothing next to survival. "
        'She still says, "Two coppers," flat as slate.'
    )
    out = apply_final_emission_gate(
        {"player_facing_text": text, "tags": [], "context_separation_contract": cs},
        resolution={"kind": "barter", "prompt": pt},
        session=None,
        scene_id="market_stall",
        world={},
    )
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("context_separation_repaired") is True
    assert "drop_lead" in str(meta.get("context_separation_repair_mode") or "")
    assert "two coppers" in (out.get("player_facing_text") or "").lower()
    em = (out.get("metadata") or {}).get("emission_debug") or {}
    assert em.get("context_separation_passed_after_repair") is True


def test_gate_context_separation_fail_pressure_monologue_replaces_non_social(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    pt = "What does the loaf cost today?"
    cs = build_context_separation_contract(player_text=pt, resolution={"kind": "barter"})
    text = (
        "The war along the border has everyone on edge, and coin means nothing next to survival. "
        "Factions trade rumors faster than grain, and the capital's politics swallow small questions whole."
    )
    out = apply_final_emission_gate(
        {"player_facing_text": text, "tags": [], "context_separation_contract": cs},
        resolution={"kind": "barter", "prompt": pt},
        session=None,
        scene_id="market_stall",
        world={},
    )
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("context_separation_failed") is True
    assert meta.get("final_route") == "replaced"


def test_gate_context_separation_tone_escalation_with_city_pressure_fails(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    pt = "Good morning. A loaf, please."
    cs = build_context_separation_contract(
        player_text=pt,
        resolution={"kind": "barter"},
        tone_escalation_contract={"allow_verbal_pressure": False, "allow_explicit_threat": False},
    )
    text = (
        "The city is on edge tonight, so back off and drop it—this is not the time for questions."
    )
    out = apply_final_emission_gate(
        {"player_facing_text": text, "tags": [], "context_separation_contract": cs},
        resolution={"kind": "barter", "prompt": pt},
        session=None,
        scene_id="market_stall",
        world={},
    )
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("context_separation_failed") is True
    assert "ambient_pressure_forced_tone_shift" in (meta.get("context_separation_failure_reasons") or [])


def test_gate_context_separation_substitution_fail_then_replace(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    pt = "What is the price today?"
    cs = build_context_separation_contract(player_text=pt, resolution={"kind": "barter"})
    text = (
        "It is impossible to say with the unrest what the price is; "
        "any answer is swallowed by the instability of the war."
    )
    out = apply_final_emission_gate(
        {"player_facing_text": text, "tags": [], "context_separation_contract": cs},
        resolution={"kind": "barter", "prompt": pt},
        session=None,
        scene_id="market_stall",
        world={},
    )
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("context_separation_failed") is True
    assert meta.get("final_route") == "replaced"


def test_gate_context_separation_pressure_overweight_replaces(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    pt = "What is your name?"
    cs = build_context_separation_contract(player_text=pt, resolution={"kind": "social_probe"})
    text = (
        "The border war reshapes every oath. "
        "Unrest makes factions bold and the crown brittle. "
        "Invasion rumors outrun truth, and politics turns markets into maps. "
        "Empire scouts watch the passes, and the realm tears at its seams."
    )
    out = apply_final_emission_gate(
        {"player_facing_text": text, "tags": [], "context_separation_contract": cs},
        resolution={"kind": "social_probe", "prompt": pt},
        session=None,
        scene_id="scene",
        world={},
    )
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("context_separation_failed") is True
    assert "pressure_overweighting" in (meta.get("context_separation_failure_reasons") or [])


# --- Player-facing narration purity + answer-shape primacy (Block 3) ------------------------------


def _purity_contract(**kwargs):
    return build_player_facing_narration_purity_contract(**kwargs)


def _response_type_contract(required: str) -> dict:
    return {
        "required_response_type": required,
        "action_must_preserve_agency": required == "action_outcome",
    }


def test_resolve_player_facing_narration_purity_contract_from_response_policy():
    c = _purity_contract()
    gm = {"response_policy": {"player_facing_narration_purity": c}}
    got, src = feg._resolve_player_facing_narration_purity_contract(gm)
    assert got is c
    assert src == "response_policy"


def test_gate_purity_and_asp_pass_clean_observation(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    out = apply_final_emission_gate(
        {
            "player_facing_text": "Rain hammers the slate roof; torchlight shivers in the gutter below.",
            "tags": [],
            "player_facing_narration_purity_contract": _purity_contract(),
            "response_policy": {"response_type_contract": _response_type_contract("neutral_narration")},
        },
        resolution={"kind": "observe", "prompt": "I look around the street."},
        session={},
        scene_id="market_lane",
        world={},
    )
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("player_facing_narration_purity_failed") is False
    assert meta.get("answer_shape_primacy_failed") is False
    assert "Rain" in (out.get("player_facing_text") or "")


def test_gate_purity_and_asp_pass_scene_transition_arrival(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    out = apply_final_emission_gate(
        {
            "player_facing_text": (
                "You emerge into the lower ward—smoke, shouted names, the harbor's brine on the wind."
            ),
            "tags": [],
            "player_facing_narration_purity_contract": _purity_contract(),
            "response_policy": {"response_type_contract": _response_type_contract("neutral_narration")},
        },
        resolution={
            "kind": "travel",
            "prompt": "I take the postern into the ward.",
            "resolved_transition": True,
        },
        session={},
        scene_id="lower_ward",
        world={},
    )
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("answer_shape_primacy_failed") is False
    assert "emerge" in (out.get("player_facing_text") or "").lower()


def test_gate_purity_pass_npc_quoted_command_in_observe(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    text = (
        'The sergeant does not raise her voice. "Move toward the gate, now," she says, '
        "and the line stiffens as if pulled by a single wire."
    )
    out = apply_final_emission_gate(
        {
            "player_facing_text": text,
            "tags": [],
            "player_facing_narration_purity_contract": _purity_contract(),
            "response_policy": {"response_type_contract": _response_type_contract("neutral_narration")},
        },
        resolution={"kind": "observe", "prompt": "I watch the line."},
        session={},
        scene_id="gate_yard",
        world={},
    )
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("player_facing_narration_purity_failed") is False
    assert "gate" in (out.get("player_facing_text") or "").lower()


def test_gate_purity_and_asp_pass_action_outcome_then_brief_consequence(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    text = (
        "You thumb the latch; it gives with a dry snap. "
        "Patrol whistles tighten two streets over, a thin urgent sound against the rain."
    )
    out = apply_final_emission_gate(
        {
            "player_facing_text": text,
            "tags": [],
            "player_facing_narration_purity_contract": _purity_contract(),
            "response_policy": {"response_type_contract": _response_type_contract("action_outcome")},
        },
        resolution={"kind": "interact", "prompt": "I try the latch on the side door."},
        session={},
        scene_id="alley_door",
        world={},
    )
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("answer_shape_primacy_failed") is False
    assert "latch" in (out.get("player_facing_text") or "").lower()


def test_gate_purity_repairs_scaffold_header_leak(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    raw = "Consequence / Opportunity:\nThe patrol's torchlight sweeps the far arch."
    out = apply_final_emission_gate(
        {
            "player_facing_text": raw,
            "tags": [],
            "player_facing_narration_purity_contract": _purity_contract(),
            "response_policy": {"response_type_contract": _response_type_contract("neutral_narration")},
        },
        resolution={"kind": "observe", "prompt": "I glance up the street."},
        session={},
        scene_id="arch_lane",
        world={},
    )
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("player_facing_narration_purity_repaired") is True
    low = (out.get("player_facing_text") or "").lower()
    assert "consequence" not in low
    assert "torchlight" in low or "arch" in low


def test_gate_purity_repairs_coaching_language(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    raw = "You weigh what you just tried near the checkpoint; rain drums on the slate roof."
    out = apply_final_emission_gate(
        {
            "player_facing_text": raw,
            "tags": [],
            "player_facing_narration_purity_contract": _purity_contract(),
            "response_policy": {"response_type_contract": _response_type_contract("neutral_narration")},
        },
        resolution={"kind": "observe", "prompt": "I listen at the checkpoint."},
        session={},
        scene_id="frontier_gate",
        world={},
    )
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("player_facing_narration_purity_repaired") is True
    assert "weigh what you just tried" not in (out.get("player_facing_text") or "").lower()


def test_gate_purity_repairs_ui_label_leak(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    raw = "Take the exit labeled North and you smell cold river air beyond the arch."
    out = apply_final_emission_gate(
        {
            "player_facing_text": raw,
            "tags": [],
            "player_facing_narration_purity_contract": _purity_contract(),
            "response_policy": {"response_type_contract": _response_type_contract("neutral_narration")},
        },
        resolution={"kind": "observe", "prompt": "I scan for a way out."},
        session={},
        scene_id="river_arch",
        world={},
    )
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("player_facing_narration_purity_repaired") is True
    assert "labeled" not in (out.get("player_facing_text") or "").lower()


def test_gate_asp_repairs_observe_when_pressure_leads_concrete_observation(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    raw = (
        "The ward's tension mounts; confrontation feels inevitable. "
        "You hear boots on wet cobbles to your left, uneven and hurried."
    )
    out = apply_final_emission_gate(
        {
            "player_facing_text": raw,
            "tags": [],
            "player_facing_narration_purity_contract": _purity_contract(),
            "response_policy": {"response_type_contract": _response_type_contract("neutral_narration")},
        },
        resolution={"kind": "observe", "prompt": "I listen for movement."},
        session={},
        scene_id="lower_ward",
        world={},
    )
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("answer_shape_primacy_repaired") is True
    text = out.get("player_facing_text") or ""
    assert text.lower().strip().startswith("you hear")


def test_gate_purity_strips_transition_scaffold_on_travel(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    raw = "The next beat is yours. You emerge onto the quay, ropes creaking, gulls wheeling overhead."
    out = apply_final_emission_gate(
        {
            "player_facing_text": raw,
            "tags": [],
            "player_facing_narration_purity_contract": _purity_contract(),
            "response_policy": {"response_type_contract": _response_type_contract("neutral_narration")},
        },
        resolution={"kind": "travel", "prompt": "I head down to the quay.", "resolved_transition": True},
        session={},
        scene_id="stone_quay",
        world={},
    )
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("player_facing_narration_purity_repaired") is True
    assert "next beat" not in (out.get("player_facing_text") or "").lower()
    assert "quay" in (out.get("player_facing_text") or "").lower()


def test_gate_asp_triggers_replace_when_no_observation_payload(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    raw = (
        "Unrest makes factions bold and the crown brittle. "
        "Invasion rumors outrun truth, and politics turns markets into maps."
    )
    out = apply_final_emission_gate(
        {
            "player_facing_text": raw,
            "tags": [],
            "player_facing_narration_purity_contract": _purity_contract(),
            "response_policy": {"response_type_contract": _response_type_contract("neutral_narration")},
        },
        resolution={"kind": "observe", "prompt": "What do I see on the street?"},
        session={},
        scene_id="market_square",
        world={},
    )
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("answer_shape_primacy_failed") is True
    assert meta.get("final_route") == "replaced"


# --- Social response structure (orchestration + metadata) ----------------------------------------


def _monoblob_dialogue_quote() -> str:
    core = " ".join(f"w{i}" for i in range(110))
    return f'Tavern Runner says "{core}."'


def _dialogue_response_policy_with_social_structure(**srs_overrides):
    rtc = _response_type_contract("dialogue")
    srs = build_social_response_structure_contract(rtc)
    srs.update(srs_overrides)
    return {"response_type_contract": rtc, "social_response_structure": srs}


def test_social_response_structure_layer_runs_after_response_delta_and_before_tone_escalation(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    order: list[str] = []
    orig_rd = feg._apply_response_delta_layer
    orig_srs = feg._apply_social_response_structure_layer
    orig_te = feg._apply_tone_escalation_layer

    def rd(*args, **kwargs):
        order.append("response_delta")
        return orig_rd(*args, **kwargs)

    def srs(*args, **kwargs):
        order.append("social_response_structure")
        return orig_srs(*args, **kwargs)

    def te(*args, **kwargs):
        order.append("tone_escalation")
        return orig_te(*args, **kwargs)

    monkeypatch.setattr(feg, "_apply_response_delta_layer", rd)
    monkeypatch.setattr(feg, "_apply_social_response_structure_layer", srs)
    monkeypatch.setattr(feg, "_apply_tone_escalation_layer", te)

    pol = _dialogue_response_policy_with_social_structure()
    apply_final_emission_gate(
        {
            "player_facing_text": 'Sergeant says "East gate is two hundred feet south."',
            "tags": [],
            "response_policy": pol,
        },
        resolution={"kind": "question", "prompt": "Where is the east gate?"},
        session=None,
        scene_id="gate_yard",
        world={},
    )
    assert order.index("response_delta") < order.index("social_response_structure") < order.index(
        "tone_escalation"
    )


def test_non_strict_social_failed_repair_adds_unsatisfied_after_repair_reason(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    bad = _monoblob_dialogue_quote()
    pol = _dialogue_response_policy_with_social_structure()
    out = apply_final_emission_gate(
        {"player_facing_text": bad, "tags": [], "response_policy": pol},
        resolution={"kind": "observe", "prompt": "What does the runner say?"},
        session=None,
        scene_id="checkpoint",
        world={},
    )
    meta = out.get("_final_emission_meta") or {}
    dbg = out.get("debug_notes") or ""
    assert "social_response_structure_unsatisfied_after_repair" in dbg
    assert meta.get("final_route") == "replaced"
    assert "social_response_structure_unsatisfied_after_repair" in (meta.get("rejection_reasons_sample") or [])


def test_strict_social_failed_repair_does_not_add_unsatisfied_after_repair_reason(monkeypatch):
    session, world, sid, resolution = _runner_strict_bundle()
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
    bad = _monoblob_dialogue_quote()

    def fake_build(candidate_text, *, resolution, tags, session, scene_id, world):
        return bad, dict(stub_details)

    monkeypatch.setattr(feg, "build_final_strict_social_response", fake_build)
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    pol = _dialogue_response_policy_with_social_structure()
    out = apply_final_emission_gate(
        {"player_facing_text": bad, "tags": [], "response_policy": pol},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    meta = out.get("_final_emission_meta") or {}
    txt = out.get("player_facing_text") or ""
    assert "w0" in txt and "w50" in txt
    assert meta.get("social_response_structure_passed") is False
    assert meta.get("social_response_structure_repair_passed") is False
    ins = meta.get("social_response_structure_inspect")
    assert isinstance(ins, dict) and ins.get("failed") is True
    assert "final_emission_gate_replaced" not in (out.get("tags") or [])
    assert "social_response_structure_unsatisfied_after_repair" not in (meta.get("rejection_reasons_sample") or [])


def test_successful_social_response_structure_repair_updates_final_emitted_source(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    pol = _dialogue_response_policy_with_social_structure()
    bullet = '- "East gate is two hundred feet south," he says.\n- "Patrols chart that lane nightly."'
    out = apply_final_emission_gate(
        {"player_facing_text": bullet, "tags": [], "response_policy": pol},
        resolution={"kind": "question", "prompt": "Where is the east gate?"},
        session=None,
        scene_id="gate_yard",
        world={},
    )
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("social_response_structure_repair_applied") is True
    assert meta.get("social_response_structure_passed") is True
    assert meta.get("final_emitted_source") == "flatten_list_like_dialogue"
    out_txt = out.get("player_facing_text") or ""
    assert "east gate" in out_txt.lower() and "patrols" in out_txt.lower()
    assert not any(ln.lstrip().startswith("-") for ln in out_txt.splitlines() if ln.strip())


def test_social_response_structure_metadata_merged_on_layer_execution(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    pol = _dialogue_response_policy_with_social_structure()
    out = apply_final_emission_gate(
        {
            "player_facing_text": 'Watchman says "East road bends past the mill."',
            "tags": [],
            "response_policy": pol,
        },
        resolution={"kind": "question", "prompt": "Which way?"},
        session=None,
        scene_id="lane",
        world={},
    )
    meta = out.get("_final_emission_meta") or {}
    for key in (
        "social_response_structure_checked",
        "social_response_structure_applicable",
        "social_response_structure_passed",
        "social_response_structure_failure_reasons",
        "social_response_structure_repair_applied",
        "social_response_structure_repair_changed_text",
        "social_response_structure_repair_passed",
        "social_response_structure_repair_mode",
        "social_response_structure_skip_reason",
        "social_response_structure_inspect",
    ):
        assert key in meta
    assert meta.get("social_response_structure_checked") is True
    assert meta.get("social_response_structure_applicable") is True
    assert meta.get("social_response_structure_passed") is True


def test_social_response_structure_skip_path_records_skip_reason_on_answer_completeness_failed():
    rtc = _response_type_contract("dialogue")
    srs = build_social_response_structure_contract(rtc)
    gm = {"response_policy": {"response_type_contract": rtc, "social_response_structure": srs}}
    raw = '- "East gate is south," he says.\n- "Patrols watch it nightly."'
    text, meta, extra = feg._apply_social_response_structure_layer(
        raw,
        gm_output=gm,
        strict_social_details=None,
        response_type_debug={"response_type_candidate_ok": True},
        answer_completeness_meta={"answer_completeness_failed": True},
        strict_social_path=False,
    )
    assert text == raw
    assert extra == []
    assert meta.get("social_response_structure_skip_reason") == "answer_completeness_failed"
    assert meta.get("social_response_structure_checked") is False


def test_response_type_failure_skips_social_response_structure_layer(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    pol = _dialogue_response_policy_with_social_structure()
    raw = "The lane stays quiet under the lamps without a direct reply."
    out = apply_final_emission_gate(
        {"player_facing_text": raw, "tags": [], "response_policy": pol},
        resolution={"kind": "observe", "prompt": "What do I hear?"},
        session=None,
        scene_id="lane",
        world={},
    )
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("social_response_structure_skip_reason") == "response_type_contract_failed"
    assert meta.get("social_response_structure_checked") is False
    assert meta.get("final_route") == "replaced"


def test_action_outcome_turn_social_response_structure_not_applicable(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    rtc = _response_type_contract("action_outcome")
    srs = build_social_response_structure_contract(rtc)
    raw = "You lift the bar; it groans, and the side door eases open a finger's width."
    out = apply_final_emission_gate(
        {"player_facing_text": raw, "tags": [], "response_policy": {"response_type_contract": rtc, "social_response_structure": srs}},
        resolution={"kind": "interact", "prompt": "I try the side door."},
        session=None,
        scene_id="alley",
        world={},
    )
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("social_response_structure_applicable") is False
    assert meta.get("social_response_structure_failure_reasons") == []


def test_social_response_structure_coexists_with_tone_escalation_layer(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    order: list[str] = []
    orig_srs = feg._apply_social_response_structure_layer
    orig_te = feg._apply_tone_escalation_layer

    def srs(*args, **kwargs):
        order.append("social_response_structure")
        return orig_srs(*args, **kwargs)

    def te(*args, **kwargs):
        order.append("tone_escalation")
        return orig_te(*args, **kwargs)

    monkeypatch.setattr(feg, "_apply_social_response_structure_layer", srs)
    monkeypatch.setattr(feg, "_apply_tone_escalation_layer", te)
    pol = _dialogue_response_policy_with_social_structure()
    out = apply_final_emission_gate(
        {
            "player_facing_text": 'Clerk says "East ledger is closed until dawn."',
            "tags": [],
            "response_policy": pol,
        },
        resolution={"kind": "question", "prompt": "When does the east ledger open?"},
        session=None,
        scene_id="hall",
        world={},
    )
    assert order.index("social_response_structure") < order.index("tone_escalation")
    meta = out.get("_final_emission_meta") or {}
    assert "tone_escalation_checked" in meta
    assert meta.get("candidate_validation_passed") is True


# --- Appended global-visibility stock: last-mile owner is _finalize_emission_output (not sanitizer-only). ---


def test_strip_appended_global_visibility_stock_multi_sentence_trailing():
    raw = (
        "The clerk taps the ledger. "
        "For a breath, the scene holds while voices shift around you."
    )
    stripped = feg._strip_appended_route_illegal_contamination_sentences(raw)
    assert stripped == "The clerk taps the ledger."


def test_strip_appended_global_visibility_stock_alt_sentence_variant():
    raw = "Fog hugs the river tents. For a breath, the scene stays still."
    assert feg._strip_appended_route_illegal_contamination_sentences(raw) == "Fog hugs the river tents."


def test_strip_placeholder_stock_single_sentence_output_unchanged():
    solo = "For a breath, the scene stays still."
    assert feg._strip_appended_route_illegal_contamination_sentences(solo) == solo


def test_strip_preserves_dialogue_sentence_containing_for_a_breath_stock_phrase():
    text = 'The runner shrugs. "For a breath, the scene stays still," she adds with a smirk.'
    assert feg._strip_appended_route_illegal_contamination_sentences(text) == text


def test_strip_preserves_interruption_setup_strips_only_trailing_stock_sentence():
    intr = (
        "The clerk starts to answer, but a shout from the square cuts across the room. "
        "For a breath, the scene holds while voices shift around you."
    )
    out = feg._strip_appended_route_illegal_contamination_sentences(intr)
    assert "shout from the square" in out.lower()
    assert "voices shift around you" not in out.lower()


def test_strip_preserves_paragraph_break_when_stripping_within_second_block():
    raw = "First block line.\n\nSecond block body. For a breath, the scene stays still."
    got = feg._strip_appended_route_illegal_contamination_sentences(raw)
    assert "\n\n" in got
    assert "First block line." in got
    assert "Second block body." in got
    assert "scene stays still" not in got.lower()


def test_strip_does_not_remove_unrelated_multi_sentence_atmosphere():
    raw = (
        "Mist threads between the tents. "
        "Somewhere a dog barks once, and the sound thins in damp air."
    )
    assert feg._strip_appended_route_illegal_contamination_sentences(raw) == raw


def test_finalize_emission_output_post_containment_reseals_appended_stock(monkeypatch):
    """Block I containment can revert to selector text after exit fingerprinting; stock strip must still win."""
    selector = (
        "Rain drums steady on the slate roof above. "
        "For a breath, the scene stays still."
    )
    out = {
        "player_facing_text": selector,
        "_final_emission_meta": {"final_route": "accept_candidate"},
        "tags": [],
        "metadata": {},
    }

    def _simulate_containment_revert(o: dict, **kwargs):
        o["player_facing_text"] = selector
        return False

    monkeypatch.setattr(feg, "_finalize_upstream_fallback_overwrite_containment", _simulate_containment_revert)
    pre = feg._normalize_text(selector)
    finalized = feg._finalize_emission_output(out, pre_gate_text=pre, fast_path=True)
    pft = (finalized.get("player_facing_text") or "").lower()
    assert "rain drums" in pft
    assert "scene stays still" not in pft
