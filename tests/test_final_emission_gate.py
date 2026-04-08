"""Integration tests for apply_final_emission_gate speaker-contract enforcement ordering and metadata."""
from __future__ import annotations

import pytest

import game.final_emission_gate as feg
import game.scene_state_anchoring as ssa
from game.defaults import default_session, default_world
from game.final_emission_gate import apply_final_emission_gate, get_speaker_selection_contract
from game.narrative_authority import build_narrative_authority_contract
from game.interaction_context import rebuild_active_scene_entities, set_social_target
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
