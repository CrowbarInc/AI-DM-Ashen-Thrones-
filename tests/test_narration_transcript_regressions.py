"""Transcript regression harness for narration-adjacent gate and routing paths.

Add a case in ~10–20 lines by constructing a :class:`NarrationTranscriptScenario` and calling
:func:`run_gate_level_case` or :func:`run_pipeline_route_case` / :func:`run_pipeline_intent_case`.

- **Gate-level**: feed a synthetic GM candidate through :func:`apply_final_emission_gate`.
- **Pipeline-level**: exercise ``choose_interaction_route`` and/or ``parse_freeform_to_action``
  when failures originate before the final gate.

**Block 4 (18a) integration regressions** — deterministic, monkeypatched failure paths that lock the
repaired chain (upstream social-lock escape → strict-social terminal fallback → grounded-speaker
first-mention safety). These are not live API / quota failure tests.

**Block 4 (18b / Objective #20) integration regressions** — transcript-level locks for the full repair
chain: embedded vocative direct-address recovery → mid-scene anti-reset (no opener replay) →
bounded-partial substance through the final gate (including ambiguity safety). Prefer substring /
meta flags over copy-paste narration.

**Block 4 (Objective #21) integration regressions** — follow-up recovery into social routing (not
local-observation misroute), post-emission speaker adoption, stale-anchor invalidation without
``active_interlocutor_followup`` binding to the wrong NPC, forced terminal fallback anchoring to the
current canonical speaker, and safety (anonymous crowd / ambiguous multi-speaker). Prefer route,
``resolve_directed_social_entry``, interaction state, and stable meta over narration prose.

Production code is not patched except where a test passes ``patch_final_emission_helpers`` for
determinism (mirrors other transcript regression tests), or uses small targeted monkeypatches for
forced fallback / retry exhaustion (same spirit as ``test_strict_social_emergency_fallback_dialogue``).

Prompt-contract semantics stay owned by ``tests/test_prompt_context.py``. This module may consume
shipped prompt contracts inside transcript fixtures, but only as regression evidence for
cross-layer routing / gate behavior, not as the primary prompt-contract authority.
"""
from __future__ import annotations

import json
import random
from dataclasses import dataclass, field, replace
from typing import Any, Callable, Mapping

import pytest

import game.final_emission_gate as _feg
from game.interaction_routing import choose_interaction_route
from game.defaults import default_scene, default_session, default_world
from game.final_emission_gate import apply_final_emission_gate
from game.intent_parser import parse_freeform_to_action
from game.interaction_context import (
    inspect as inspect_interaction_context,
    rebuild_active_scene_entities,
    resolve_directed_social_entry,
    set_social_target,
)
from game.gm import force_terminal_retry_fallback
from game.post_emission_speaker_adoption import (
    apply_post_emission_speaker_adoption,
    apply_stale_interlocutor_invalidation_after_emission,
)
from game.prompt_context import canonical_interaction_target_npc_id
from game.storage import load_scene
import game.social_exchange_emission as _sse
from game.social_exchange_emission import build_final_strict_social_response

from tests.test_turn_pipeline_shared import _patch_storage
from tests.test_fallback_behavior_gate import _fallback_contract, _answer_contract, _response_type_contract

pytestmark = [pytest.mark.regression, pytest.mark.transcript]


# --- Scenario schema ---------------------------------------------------------


@dataclass(frozen=True)
class NarrationTranscriptAssertions:
    """Focused checks — prefer route/speaker/meta over long exact strings."""

    required_substrings: tuple[str, ...] = ()
    forbidden_substrings: tuple[str, ...] = ()
    #: If set, compared (case-insensitive) to normalized player-facing text.
    forbidden_normalized_substrings: tuple[str, ...] = (
        "as an ai",
        "the system cannot",
        "there is insufficient context",
    )
    #: Exact matches on ``_final_emission_meta`` keys when the value is not ``...`` (ellipsis = skip).
    meta_exact: Mapping[str, Any] = field(default_factory=dict)
    #: Each fragment must appear in ``str(_final_emission_meta.get(key) or "")``.
    meta_value_fragments: Mapping[str, str] = field(default_factory=dict)
    #: Substring match anywhere in the JSON-ish string form of ``_final_emission_meta`` (stable flags).
    meta_json_fragments: tuple[str, ...] = ()
    expected_speaker_id: str | None = None
    #: Human-readable note for expected repair/route behavior (optional; see ``meta_exact`` for real checks).
    expected_route_or_repair: str | None = None


@dataclass(frozen=True)
class NarrationTranscriptScenario:
    """Single transcript fixture: inputs, deterministic seeds, and assertions."""

    id: str
    player_text: str
    raw_or_model_output: str
    #: Resolution passed into the gate (``kind`` should match the turn).
    resolution: Mapping[str, Any]
    session_seed: int = 0xDEADBEEF
    scene_seed: int = 0xC0FFEE
    world_seed: int = 0xBADC0DE
    scene_id: str = "frontier_gate"
    session: Mapping[str, Any] | None = None
    world: Mapping[str, Any] | None = None
    #: Optional scene envelope for pipeline intent parsing (defaults from ``default_scene``).
    scene_envelope: Mapping[str, Any] | None = None
    tags: tuple[str, ...] = ()
    assertions: NarrationTranscriptAssertions = field(default_factory=NarrationTranscriptAssertions)
    #: Optional scene envelope passed to :func:`apply_final_emission_gate` as ``scene=`` (visibility / grounding).
    emission_scene: Mapping[str, Any] | None = None
    #: Expected ``choose_interaction_route`` result when running pipeline routing.
    route_kind: str | None = None
    #: Expected ``parse_freeform_to_action`` ``type`` when parser returns an action.
    intent_kind: str | None = None
    patch_visibility_enforcement: bool = True
    use_tmp_storage: bool = False


# --- Helpers -----------------------------------------------------------------


def normalize_transcript_text(text: str) -> str:
    """Collapse whitespace and lower-case for stable substring checks."""
    return " ".join(str(text or "").lower().split())


def apply_transcript_seeds(scenario: NarrationTranscriptScenario) -> None:
    """Deterministic RNG for any code path that consults ``random`` during a case."""
    mixed = (scenario.session_seed ^ (scenario.scene_seed << 1) ^ (scenario.world_seed << 2)) & 0xFFFFFFFFFFFFFFFF
    random.seed(mixed)


def attach_seed_markers(
    session: dict[str, Any],
    world: dict[str, Any],
    scene_envelope: dict[str, Any],
    scenario: NarrationTranscriptScenario,
) -> None:
    """Record seeds for debugging without affecting production behavior."""
    session["_transcript_seed"] = scenario.session_seed
    world["_transcript_seed"] = scenario.world_seed
    scene = scene_envelope.setdefault("scene", {})
    if isinstance(scene, dict):
        scene["_transcript_seed"] = scenario.scene_seed


def build_default_minimal_scene_envelope(scene_id: str) -> dict[str, Any]:
    env = default_scene(scene_id)
    if isinstance(env, dict) and isinstance(env.get("scene"), dict):
        env["scene"]["id"] = scene_id
    return env


def seed_minimal_play_context(
    scenario: NarrationTranscriptScenario,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], str]:
    """In-memory session/world/scene for gate or pipeline cases (no disk I/O)."""
    session = dict(scenario.session) if scenario.session is not None else default_session()
    world = dict(scenario.world) if scenario.world is not None else default_world()
    sid = str(scenario.scene_id or "frontier_gate").strip() or "frontier_gate"
    session["active_scene_id"] = sid
    if not session.get("visited_scene_ids"):
        session["visited_scene_ids"] = [sid]
    scene_envelope = (
        dict(scenario.scene_envelope) if scenario.scene_envelope is not None else build_default_minimal_scene_envelope(sid)
    )
    attach_seed_markers(session, world, scene_envelope, scenario)
    return session, world, scene_envelope, sid


def maybe_patch_storage_tmp(scenario: NarrationTranscriptScenario, tmp_path: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    if scenario.use_tmp_storage:
        _patch_storage(tmp_path, monkeypatch)


def patch_final_emission_helpers(
    monkeypatch: pytest.MonkeyPatch,
    *,
    patch_visibility: bool = True,
    visibility_hook: Callable[..., Any] | None = None,
) -> None:
    """Optional stability hooks (same spirit as ``test_anti_railroading_transcript_regressions``)."""
    hook = visibility_hook or (lambda out, **kwargs: out)
    if patch_visibility:
        monkeypatch.setattr(_feg, "_apply_visibility_enforcement", hook)


def assert_narration_transcript_outcome(gm_out: Mapping[str, Any], assertions: NarrationTranscriptAssertions) -> None:
    text = str(gm_out.get("player_facing_text") or "")
    norm = normalize_transcript_text(text)
    for sub in assertions.required_substrings:
        assert sub.lower() in norm, f"missing required substring {sub!r} in {norm!r}"
    for sub in assertions.forbidden_substrings:
        assert sub.lower() not in norm, f"forbidden substring {sub!r} present in {norm!r}"
    for sub in assertions.forbidden_normalized_substrings:
        if sub:
            assert sub.lower() not in norm, f"forbidden normalized substring {sub!r} in {norm!r}"
    meta = gm_out.get("_final_emission_meta")
    meta_dict = meta if isinstance(meta, dict) else {}
    meta_blob = json.dumps(meta_dict, sort_keys=True, default=str)
    for fragment in assertions.meta_json_fragments:
        assert fragment in meta_blob, f"meta fragment {fragment!r} not in {meta_blob}"
    for key, expected in assertions.meta_exact.items():
        if expected is ...:
            continue
        assert meta_dict.get(key) == expected, f"_final_emission_meta[{key!r}] got {meta_dict.get(key)!r} expected {expected!r}"
    for key, frag in assertions.meta_value_fragments.items():
        bucket = str(meta_dict.get(key) or "")
        assert frag in bucket, f"_final_emission_meta[{key!r}] missing fragment {frag!r}: {bucket!r}"
    if assertions.expected_speaker_id:
        got = (
            str(meta_dict.get("active_interlocutor_id") or "").strip()
            or str(meta_dict.get("npc_id") or "").strip()
            or str((meta_dict.get("speaker_selection") or {}).get("speaker_id") or "").strip()
        )
        assert got == assertions.expected_speaker_id, f"speaker id {got!r} != {assertions.expected_speaker_id!r}"


def run_gate_level_case(
    scenario: NarrationTranscriptScenario,
    monkeypatch: pytest.MonkeyPatch,
    *,
    tmp_path: Any | None = None,
) -> dict[str, Any]:
    """Run ``apply_final_emission_gate`` on ``raw_or_model_output`` with scenario resolution/context."""
    apply_transcript_seeds(scenario)
    if scenario.use_tmp_storage and tmp_path is not None:
        maybe_patch_storage_tmp(scenario, tmp_path, monkeypatch)
    patch_final_emission_helpers(monkeypatch, patch_visibility=scenario.patch_visibility_enforcement)
    session, world, _scene_env, sid = seed_minimal_play_context(scenario)
    gm: dict[str, Any] = {"player_facing_text": scenario.raw_or_model_output, "tags": list(scenario.tags)}
    gate_scene = dict(scenario.emission_scene) if scenario.emission_scene is not None else None
    out = apply_final_emission_gate(
        gm,
        resolution=dict(scenario.resolution),
        session=session,
        scene_id=sid,
        world=world,
        scene=gate_scene,
    )
    assert_narration_transcript_outcome(out, scenario.assertions)
    return out


def run_pipeline_route_case(scenario: NarrationTranscriptScenario) -> str:
    """Return ``choose_interaction_route`` for ``player_text`` under seeded session/world/scene."""
    apply_transcript_seeds(scenario)
    session, world, scene_envelope, _sid = seed_minimal_play_context(scenario)
    route = choose_interaction_route(
        scenario.player_text,
        scene=scene_envelope,
        session=session,
        world=world,
    )
    if scenario.route_kind is not None:
        assert route == scenario.route_kind, f"route {route!r} != expected {scenario.route_kind!r}"
    return route


def run_pipeline_intent_case(scenario: NarrationTranscriptScenario) -> dict[str, Any] | None:
    """Return ``parse_freeform_to_action`` result when the parser can classify the turn."""
    apply_transcript_seeds(scenario)
    session, world, scene_envelope, _sid = seed_minimal_play_context(scenario)
    action = parse_freeform_to_action(
        scenario.player_text,
        scene_envelope,
        session=session,
        world=world,
    )
    if scenario.intent_kind is not None:
        assert action is not None, "parse_freeform_to_action returned None"
        assert action.get("type") == scenario.intent_kind, f"intent type {action.get('type')!r} != {scenario.intent_kind!r}"
    return action


# --- Phantom entity regressions (strict-social gate) -------------------------


def _session_engaged_tavern_runner() -> dict[str, Any]:
    s = default_session()
    s["interaction_context"] = {
        "active_interaction_target_id": "tavern_runner",
        "active_interaction_kind": "social",
        "interaction_mode": "social",
        "engagement_level": "engaged",
    }
    return s


def _resolution_question_to_runner(prompt: str) -> dict[str, Any]:
    return {
        "kind": "question",
        "prompt": prompt,
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "tavern_runner",
            "npc_name": "Tavern Runner",
            "npc_reply_expected": True,
            "reply_kind": "answer",
            "target_resolved": True,
        },
    }


def _resolution_persuade_to_runner(prompt: str) -> dict[str, Any]:
    return {
        "kind": "persuade",
        "prompt": prompt,
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "tavern_runner",
            "npc_name": "Tavern Runner",
            "npc_reply_expected": True,
            "reply_kind": "answer",
            "target_resolved": True,
        },
    }


def assert_output_excludes_player_prompt_fingerprint(player_line: str, gm_text: str, *, min_len: int = 28) -> None:
    """Block near-verbatim recycling of a long player prompt inside the final emission."""
    p = normalize_transcript_text(player_line)
    t = normalize_transcript_text(gm_text)
    if len(p) < min_len:
        return
    assert p[:min_len] not in t, f"player prompt fingerprint {p[:min_len]!r} leaked into emission: {t!r}"


def _session_engaged_runner_at_scene(*, runner_id: str = "runner") -> dict[str, Any]:
    s = default_session()
    s["interaction_context"] = {
        "active_interaction_target_id": runner_id,
        "active_interaction_kind": "social",
        "interaction_mode": "social",
        "engagement_level": "engaged",
    }
    return s


def _world_with_runner_at_scene(scene_id: str, *, runner_id: str = "runner", name: str = "Tavern Runner") -> dict[str, Any]:
    w = default_world()
    w["npcs"] = [{"id": runner_id, "name": name, "location": scene_id}]
    return w


def _dialogue_contract_strict_social_resolution(prompt: str) -> dict[str, Any]:
    """Strict-social resolution with an engine dialogue contract (for grounded-speaker exemption meta)."""
    return {
        "kind": "question",
        "prompt": prompt,
        "metadata": {"response_type_contract": {"required_response_type": "dialogue"}},
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "tavern_runner",
            "npc_name": "Tavern Runner",
            "npc_reply_expected": True,
            "reply_kind": "answer",
            "target_resolved": True,
        },
    }


def _grounded_runner_session_world_scene(*, scene_id: str = "frontier_gate") -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Session/world/scene aligned with strict-social grounded-interlocutor gate tests (no disk I/O)."""
    session = default_session()
    world = default_world()
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, scene_id)
    ic = dict(session.get("interaction_context") or {})
    ic["engagement_level"] = "focused"
    session["interaction_context"] = ic
    emission_scene = default_scene(scene_id)
    return session, world, emission_scene


# --- Objective #21 Block 4: integration helpers (scene_investigate + runner topic pressure) ---


def _obj21_scene_world_investigate() -> tuple[dict[str, Any], dict[str, Any]]:
    scene = default_scene("scene_investigate")
    scene["scene"]["id"] = "scene_investigate"
    world = default_world()
    world["npcs"] = [
        {"id": "tavern_runner", "name": "Tavern Runner", "location": "scene_investigate", "topics": []},
        {"id": "gate_guard", "name": "Gate Guard", "location": "scene_investigate", "topics": []},
    ]
    return scene, world


def _obj21_session_runner_crossroads_topic(*, last_answer: str = "Old crossroads—that way.") -> dict[str, Any]:
    session = default_session()
    session["active_scene_id"] = "scene_investigate"
    session["visited_scene_ids"] = ["scene_investigate"]
    session["interaction_context"] = {
        "active_interaction_target_id": "tavern_runner",
        "active_interaction_kind": "social",
        "interaction_mode": "social",
        "engagement_level": "engaged",
    }
    session["scene_runtime"] = {
        "scene_investigate": {
            "topic_pressure_last_topic_key": "crossroads_incident",
            "topic_pressure_current": {
                "speaker_key": "tavern_runner",
                "topic_key": "crossroads_incident",
            },
            "topic_pressure": {
                "crossroads_incident": {
                    "last_answer": last_answer,
                    "last_turn": 3,
                }
            },
        }
    }
    return session


def _obj21_scenario_crossroads_followup_recovery() -> NarrationTranscriptScenario:
    scene, world = _obj21_scene_world_investigate()
    session = _obj21_session_runner_crossroads_topic()
    return NarrationTranscriptScenario(
        id="obj21_crossroads_followup_not_local_observation",
        player_text="What's going on at the old crossroads?",
        raw_or_model_output="",
        resolution={"kind": "question", "prompt": "What's going on at the old crossroads?"},
        session_seed=0x02140101,
        scene_seed=0x02140102,
        world_seed=0x02140103,
        scene_id="scene_investigate",
        session=session,
        world=world,
        scene_envelope=scene,
        route_kind="dialogue",
    )


def _obj21_resolution_stale_runner_dialogue_contract(prompt: str) -> dict[str, Any]:
    """Stale engine npc_id (runner) while session may already reflect guard — for fallback-anchor tests."""
    return {
        "kind": "question",
        "prompt": prompt,
        "metadata": {"response_type_contract": {"required_response_type": "dialogue"}},
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "tavern_runner",
            "npc_name": "Tavern Runner",
            "npc_reply_expected": True,
            "reply_kind": "answer",
            "target_resolved": True,
        },
    }


def _assert_obj21_crossroads_followup_recovery_chain(scenario: NarrationTranscriptScenario) -> None:
    run_pipeline_route_case(scenario)
    apply_transcript_seeds(scenario)
    session, world, scene_envelope, _ = seed_minimal_play_context(scenario)
    entry = resolve_directed_social_entry(
        session=session,
        scene=scene_envelope,
        world=world,
        segmented_turn=None,
        raw_text=scenario.player_text,
    )
    assert entry.get("should_route_social") is True
    assert entry.get("target_actor_id") == "tavern_runner"
    assert entry.get("reason") != "local_scene_observation_query"
    act = parse_freeform_to_action(
        scenario.player_text,
        scene_envelope,
        session=session,
        world=world,
    )
    assert act is None or act.get("type") != "observe"


def _assert_obj21_guard_adoption_updates_interlocutor() -> None:
    scene, world = _obj21_scene_world_investigate()
    session = _obj21_session_runner_crossroads_topic()
    rebuild_active_scene_entities(session, world, "scene_investigate", scene_envelope=scene)
    out = apply_post_emission_speaker_adoption(
        session,
        world,
        scene,
        {"player_facing_text": 'Gate Guard says, "Halt—papers, now."'},
        resolution={"kind": "observe"},
        scene_changed=False,
    )
    assert out.get("adopted") is True
    assert session["interaction_context"]["active_interaction_target_id"] == "gate_guard"
    assert (session.get("scene_state") or {}).get("current_interlocutor") == "gate_guard"
    aid = str(inspect_interaction_context(session).get("active_interaction_target_id") or "").strip()
    assert canonical_interaction_target_npc_id(session, aid) == "gate_guard"


def _assert_obj21_stale_anchor_cleared_followup_not_runner() -> None:
    scene, world = _obj21_scene_world_investigate()
    session = _obj21_session_runner_crossroads_topic()
    rebuild_active_scene_entities(session, world, "scene_investigate", scene_envelope=scene)
    gm = {"player_facing_text": 'Gate Guard says, "The gate closes at dusk."'}
    adopt = apply_post_emission_speaker_adoption(
        session,
        world,
        scene,
        gm,
        resolution={"kind": "observe"},
        scene_changed=False,
    )
    assert adopt.get("adopted") is False
    inv = apply_stale_interlocutor_invalidation_after_emission(
        session,
        world,
        scene,
        gm,
        resolution={"kind": "observe"},
        scene_changed=False,
        adoption_debug=adopt,
    )
    assert inv.get("cleared") is True
    nxt = resolve_directed_social_entry(
        session=session,
        scene=scene,
        world=world,
        segmented_turn=None,
        raw_text="Why close it so early?",
    )
    assert nxt.get("reason") != "active_interlocutor_followup"
    assert nxt.get("target_actor_id") != "tavern_runner"


def _assert_obj21_force_terminal_fallback_uses_guard_not_stale_runner(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("game.gm.apply_social_exchange_retry_fallback_gm", lambda *a, **k: {})
    scene, world = _obj21_scene_world_investigate()
    session = _obj21_session_runner_crossroads_topic()
    rebuild_active_scene_entities(session, world, "scene_investigate", scene_envelope=scene)
    apply_post_emission_speaker_adoption(
        session,
        world,
        scene,
        {"player_facing_text": 'Gate Guard says, "Halt—papers, now."'},
        resolution={"kind": "observe"},
        scene_changed=False,
    )
    res_stale = _obj21_resolution_stale_runner_dialogue_contract("What did you hear last night?")
    out = force_terminal_retry_fallback(
        session=session,
        original_text="",
        failure={"failure_class": "scene_stall", "reasons": ["stall"]},
        player_text="What did you hear last night?",
        scene_envelope=scene,
        world=world,
        resolution=res_stale,
        base_gm={
            "player_facing_text": "",
            "tags": [],
            "response_policy": {"response_type_contract": {"required_response_type": "dialogue"}},
        },
    )
    text = normalize_transcript_text(str(out.get("player_facing_text") or ""))
    assert "gate guard" in text
    assert "tavern runner" not in text


def _assert_obj21_safety_crowd_and_ambiguous() -> None:
    scene, world = _obj21_scene_world_investigate()
    session = _obj21_session_runner_crossroads_topic()
    rebuild_active_scene_entities(session, world, "scene_investigate", scene_envelope=scene)
    apply_post_emission_speaker_adoption(
        session,
        world,
        scene,
        {"player_facing_text": 'Someone in the crowd shouts, "Fire!" and panic ripples.'},
        resolution=None,
        scene_changed=False,
    )
    assert session["interaction_context"]["active_interaction_target_id"] == "tavern_runner"
    ambiguous = {
        "player_facing_text": (
            'Gate Guard says, "Halt."\n'
            'Tavern Runner says, "Wait—the papers are in order."\n'
            '"Fine," the Gate Guard says, "move along."'
        )
    }
    ad = apply_post_emission_speaker_adoption(
        session,
        world,
        scene,
        ambiguous,
        resolution=None,
        scene_changed=False,
    )
    assert ad.get("reason") == "ambiguous_multi_speaker"
    inv = apply_stale_interlocutor_invalidation_after_emission(
        session,
        world,
        scene,
        ambiguous,
        resolution=None,
        scene_changed=False,
        adoption_debug=ad,
    )
    assert inv.get("cleared") is not True
    assert inspect_interaction_context(session).get("active_interaction_target_id") == "tavern_runner"


# --- Objective #20 (18b Block 4): integrated repair-chain regressions -----------------

# Stock opener / scene-establishment overlap (frontier_gate) — must not replay mid-exchange.
_FORBIDDEN_SCENE_INTRO_MARKERS = (
    "rain spatters soot-dark stone",
    "you take in the scene",
    "what surrounds you resolves into focus",
)


def _session_world_scene_frontier_gate_cleared_embedded_vocative() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """frontier_gate roster + addressables; no continuity pin (embedded vocative must bind)."""
    world: dict[str, Any] = {"npcs": []}
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    session["interaction_context"] = {}
    scene_envelope = load_scene("frontier_gate")
    st = session["scene_state"]
    if isinstance(st, dict):
        st = dict(st)
        st["active_scene_id"] = "frontier_gate"
        st["active_entities"] = [
            "guard_captain",
            "tavern_runner",
            "refugee",
            "threadbare_watcher",
        ]
        session["scene_state"] = st
        scene_envelope["scene_state"] = dict(st)
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene_envelope)
    return session, world, scene_envelope


def _run_object20_bounded_gate_case(
    scenario: NarrationTranscriptScenario,
    monkeypatch: pytest.MonkeyPatch,
    *,
    with_answer_contract: bool,
) -> dict[str, Any]:
    """Full gate with fallback_behavior (+ optional answer contract) for Objective #20 substance rows."""
    gm: dict[str, Any] = {
        "player_facing_text": scenario.raw_or_model_output,
        "tags": [],
        "response_policy": (
            {
                "response_type_contract": _response_type_contract("answer"),
                "answer_completeness": _answer_contract(),
                "fallback_behavior": _fallback_contract(),
            }
            if with_answer_contract
            else {"fallback_behavior": _fallback_contract()}
        ),
    }
    apply_transcript_seeds(scenario)
    patch_final_emission_helpers(monkeypatch, patch_visibility=scenario.patch_visibility_enforcement)
    session, world, _, sid = seed_minimal_play_context(scenario)
    out = apply_final_emission_gate(
        gm,
        resolution=dict(scenario.resolution),
        session=session,
        scene_id=sid,
        world=world,
        scene={},
    )
    assert_narration_transcript_outcome(out, scenario.assertions)
    return out


@pytest.mark.routing
def test_integration_embedded_direct_address_keeps_dialogue_and_binds_tavern_runner(monkeypatch: pytest.MonkeyPatch) -> None:
    """Embedded ``tell me runner, …`` must route socially and bind the scene runner (no targetless drift)."""
    _ = monkeypatch
    session, world, scene_envelope = _session_world_scene_frontier_gate_cleared_embedded_vocative()
    scenario = NarrationTranscriptScenario(
        id="obj20_embedded_vocative_tell_me_runner_watch",
        player_text='Tell me runner, who runs the watch?',
        raw_or_model_output="",
        resolution={"kind": "question", "prompt": 'Tell me runner, who runs the watch?'},
        session_seed=0x20B40101,
        scene_seed=0x20B40102,
        world_seed=0x20B40103,
        scene_id="frontier_gate",
        session=session,
        world=world,
        scene_envelope=scene_envelope,
        route_kind="dialogue",
    )
    run_pipeline_route_case(scenario)
    apply_transcript_seeds(scenario)
    session2, world2, scene2, _ = seed_minimal_play_context(scenario)
    entry = resolve_directed_social_entry(
        session=session2,
        scene=scene2,
        world=world2,
        segmented_turn=None,
        raw_text=scenario.player_text,
    )
    assert entry.get("should_route_social") is True, entry
    assert entry.get("target_actor_id") == "tavern_runner", entry


@pytest.mark.emission
def test_gate_integration_anti_reset_no_opener_on_forced_non_social_replace(monkeypatch: pytest.MonkeyPatch) -> None:
    """Established mid-scene exchange + forced replace: local continuation, no stock scene-opener replay."""
    monkeypatch.setattr(_feg, "strict_social_emission_will_apply", lambda *a, **k: False)
    session = default_session()
    session["turn_counter"] = 4
    session["interaction_context"] = {
        "active_interaction_target_id": "tavern_runner",
        "active_interaction_kind": "social",
        "interaction_mode": "social",
        "engagement_level": "engaged",
    }
    scenario = NarrationTranscriptScenario(
        id="obj20_anti_reset_mid_scene_forced_replace",
        player_text="Look around for a certain answer.",
        raw_or_model_output="From here, no certain answer presents itself.",
        resolution={
            "kind": "observe",
            "prompt": "look around",
            "social": {
                "social_intent_class": "social_exchange",
                "npc_id": "tavern_runner",
                "npc_name": "Tavern Runner",
            },
        },
        session_seed=0x20A20101,
        scene_seed=0x20A20102,
        world_seed=0x20A20103,
        scene_id="frontier_gate",
        session=session,
        emission_scene=default_scene("frontier_gate"),
        patch_visibility_enforcement=False,
        assertions=NarrationTranscriptAssertions(
            meta_exact={
                "final_emitted_source": "anti_reset_local_continuation_fallback",
                "anti_reset_intro_suppressed": True,
            },
            forbidden_substrings=_FORBIDDEN_SCENE_INTRO_MARKERS,
        ),
    )
    run_gate_level_case(scenario, monkeypatch)


@pytest.mark.emission
def test_gate_integration_bounded_partial_thin_line_repaired_full_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """Thin identity line fails substance checks; repair yields known edge + uncertainty + next lead; not global fallback."""
    scenario = NarrationTranscriptScenario(
        id="obj20_bounded_partial_unresolved_buyer_question",
        player_text="Who was the buyer, exactly?",
        raw_or_model_output="No name comes clear from what shows.",
        resolution={"kind": "adjudication_query", "prompt": "Who was the buyer, exactly?"},
        session_seed=0x20B00101,
        scene_seed=0x20B00102,
        world_seed=0x20B00103,
        scene_id="frontier_gate",
        patch_visibility_enforcement=False,
        assertions=NarrationTranscriptAssertions(
            required_substrings=("hearsay", "sergeant"),
            forbidden_substrings=("no name comes clear from what shows.",),
            meta_exact={
                "fallback_behavior_repaired": True,
                "fallback_behavior_failed": False,
                "final_emitted_source": "bounded_partial",
            },
            meta_value_fragments={
                "fallback_behavior_repair_mode": "bounded_partial",
            },
        ),
    )
    out = _run_object20_bounded_gate_case(scenario, monkeypatch, with_answer_contract=True)
    meta = out.get("_final_emission_meta") if isinstance(out.get("_final_emission_meta"), dict) else {}
    assert meta.get("final_emitted_source") != "global_scene_fallback"


@pytest.mark.emission
def test_gate_integration_bounded_partial_safety_no_invented_culprit_or_signer(monkeypatch: pytest.MonkeyPatch) -> None:
    """Synthesis from thin partial must not assert a specific unsupported identity or guilt."""
    scenario = NarrationTranscriptScenario(
        id="obj20_bounded_partial_safety_who_signed",
        player_text="Who signed the order?",
        raw_or_model_output="No name comes clear from what shows.",
        resolution={"kind": "adjudication_query", "prompt": "Who signed the order?"},
        session_seed=0x205A0101,
        scene_seed=0x205A0102,
        world_seed=0x205A0103,
        scene_id="frontier_gate",
        patch_visibility_enforcement=False,
        assertions=NarrationTranscriptAssertions(
            forbidden_substrings=(
                "verrick",
                "culprit was",
                "signed by",
                "the order was signed by",
            ),
            meta_exact={"fallback_behavior_repaired": True, "fallback_behavior_failed": False},
        ),
    )
    _ = _run_object20_bounded_gate_case(scenario, monkeypatch, with_answer_contract=False)


# --- Objective #21 Block 4: full repaired chain (integration; compact vs Block 1/2/3 suites) ---


@pytest.mark.routing
def test_integration_obj21_runner_crossroads_followup_routes_dialogue_not_observe(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tavern Runner surfaced old crossroads; 'what's going on…' follow-up stays social (not local observation)."""
    _ = monkeypatch
    _assert_obj21_crossroads_followup_recovery_chain(_obj21_scenario_crossroads_followup_recovery())


@pytest.mark.routing
def test_integration_obj21_visible_guard_takeover_adopts_interaction_context() -> None:
    """Grounded guard interruption: post-emission adoption updates carried interlocutor (stable fields)."""
    _assert_obj21_guard_adoption_updates_interlocutor()


@pytest.mark.routing
def test_integration_obj21_guard_visible_without_adoption_clears_stale_runner_followup() -> None:
    """Visible grounded other speaker without takeover → stale continuity cleared; next turn not runner follow-up."""
    _assert_obj21_stale_anchor_cleared_followup_not_runner()


@pytest.mark.emission
def test_integration_obj21_force_terminal_fallback_reconciles_stale_resolution_to_adopted_guard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Retry exhaustion: effective strict-social speaker follows session (guard), not stale resolution npc_id."""
    _assert_obj21_force_terminal_fallback_uses_guard_not_stale_runner(monkeypatch)


@pytest.mark.routing
def test_integration_obj21_safety_anonymous_crowd_and_ambiguous_multi_speaker() -> None:
    """Anonymous crowd does not become interlocutor; ambiguous multi-speaker does not steal continuity."""
    _assert_obj21_safety_crowd_and_ambiguous()


# --- 18a Block 4: full-chain integration (deterministic; not live API failures) ---


@pytest.mark.routing
def test_route_upstream_inspect_escapes_social_dialogue_lock(monkeypatch: pytest.MonkeyPatch) -> None:
    """Lightweight upstream check: explicit inspect of an NPC-tied object is not dialogue-routed."""
    _ = monkeypatch
    sid = "scene_investigate"
    scenario = NarrationTranscriptScenario(
        id="chain_upstream_inspect_stew_not_dialogue",
        player_text="Galinor inspects the tavern runner's stew.",
        raw_or_model_output="",
        resolution={"kind": "observe", "prompt": "Galinor inspects the tavern runner's stew."},
        session_seed=0xE5C40101,
        scene_seed=0xE5C40102,
        world_seed=0xE5C40103,
        scene_id=sid,
        session=_session_engaged_runner_at_scene(runner_id="tavern_runner"),
        world=_world_with_runner_at_scene(sid, runner_id="tavern_runner"),
        scene_envelope={"scene": {"id": sid}},
    )
    route = run_pipeline_route_case(scenario)
    assert route != "dialogue"


@pytest.mark.emission
def test_gate_chain_strict_social_forced_fallback_grounded_speaker_and_dialogue(monkeypatch: pytest.MonkeyPatch) -> None:
    """Forced strict-social terminal fallback: dialogue-valid output, phantom cleared, grounded FM exemption stable."""
    prompt = "What did you hear last night?"
    session, world, emission_scene = _grounded_runner_session_world_scene()
    scenario = NarrationTranscriptScenario(
        id="chain_forced_fallback_grounded_speaker_dialogue",
        player_text=prompt,
        raw_or_model_output='Magistrate Kell leans in. "They moved the wagons east," she murmurs.',
        resolution=_dialogue_contract_strict_social_resolution(prompt),
        session_seed=0xFA11B401,
        scene_seed=0xFA11B402,
        world_seed=0xFA11B403,
        scene_id="frontier_gate",
        session=session,
        world=world,
        emission_scene=emission_scene,
        patch_visibility_enforcement=False,
        assertions=NarrationTranscriptAssertions(
            required_substrings=("tavern runner",),
            forbidden_substrings=("magistrate", "starts to answer", "shouting breaks out", "crowd murmurs"),
            expected_speaker_id="tavern_runner",
            meta_exact={"final_emitted_source": "minimal_social_emergency_fallback"},
        ),
    )
    out = run_gate_level_case(scenario, monkeypatch)
    text = str(out.get("player_facing_text") or "")
    assert '"' in text, "forced fallback must retain dialogue presence"
    meta = out.get("_final_emission_meta") if isinstance(out.get("_final_emission_meta"), dict) else {}
    assert meta.get("first_mention_strict_social_grounded_speaker_exemption_entity_id") == "tavern_runner"
    assert meta.get("first_mention_validation_passed") is True
    assert meta.get("first_mention_replacement_applied") is False


@pytest.mark.emission
def test_gate_chain_phantom_speaker_not_accepted_via_grounding_exemption(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exemption id stays the grounded interlocutor; invented authority is not treated as the exempt speaker."""
    prompt = "Who signed the order?"
    session, world, emission_scene = _grounded_runner_session_world_scene()
    scenario = NarrationTranscriptScenario(
        id="chain_phantom_not_merged_into_exemption",
        player_text=prompt,
        raw_or_model_output='Magistrate Kell leans in. "Not my signature," she says, watching you.',
        resolution=_dialogue_contract_strict_social_resolution(prompt),
        session_seed=0xFA4F001,
        scene_seed=0xFA4F002,
        world_seed=0xFA4F003,
        scene_id="frontier_gate",
        session=session,
        world=world,
        emission_scene=emission_scene,
        patch_visibility_enforcement=False,
        assertions=NarrationTranscriptAssertions(
            required_substrings=("tavern runner",),
            forbidden_substrings=("magistrate",),
            expected_speaker_id="tavern_runner",
            meta_exact={"final_emitted_source": "minimal_social_emergency_fallback"},
        ),
    )
    out = run_gate_level_case(scenario, monkeypatch)
    meta = out.get("_final_emission_meta") if isinstance(out.get("_final_emission_meta"), dict) else {}
    assert meta.get("first_mention_strict_social_grounded_speaker_exemption_entity_id") == "tavern_runner"


@pytest.mark.emission
def test_gate_chain_familiarity_violation_still_fails_where_unearned(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unearned familiarity still fails first-mention enforcement (observe beat; not masked by social rewrite)."""
    scenario = NarrationTranscriptScenario(
        id="chain_familiarity_unearned_still_rejected",
        player_text="I study the gate.",
        raw_or_model_output="Guard Captain stands near the gate; you recognize him immediately.",
        resolution={"kind": "observe", "prompt": "I study the gate."},
        session_seed=0xF401A001,
        scene_seed=0xF401A002,
        world_seed=0xF401A003,
        scene_id="frontier_gate",
        session=default_session(),
        world=default_world(),
        emission_scene=default_scene("frontier_gate"),
        patch_visibility_enforcement=False,
        assertions=NarrationTranscriptAssertions(
            meta_json_fragments=("first_mention_unearned_familiarity",),
            forbidden_substrings=("you recognize him immediately",),
        ),
    )
    run_gate_level_case(scenario, monkeypatch)


@pytest.mark.emission
def test_integration_strict_social_forced_fallback_stable_under_duplicate_emissions(monkeypatch: pytest.MonkeyPatch) -> None:
    """With forced internal fallback, identical inputs yield identical emissions (no silent drift).

    Progression / repeat-guard thresholds are covered more directly in ``test_strict_social_emergency_fallback_dialogue``.
    """
    _orig_hr = _sse.hard_reject_social_exchange_text

    def _augment_hard_reject(*args: Any, **kwargs: Any) -> list[str]:
        reasons = _orig_hr(*args, **kwargs)
        return list(reasons) + ["integration_test_force_internal_fallback"]

    monkeypatch.setattr(_sse, "hard_reject_social_exchange_text", _augment_hard_reject)
    sid = "frontier_gate"
    session, world, _scene = _grounded_runner_session_world_scene(scene_id=sid)
    res = _dialogue_contract_strict_social_resolution("What did you hear?")
    bad = "Candidate line that would otherwise pass."
    t1, m1 = build_final_strict_social_response(
        bad, resolution=res, session=session, world=world, scene_id=sid, tags=[]
    )
    t2, m2 = build_final_strict_social_response(
        bad, resolution=res, session=session, world=world, scene_id=sid, tags=[]
    )
    assert m1.get("used_internal_fallback") is True
    assert m2.get("used_internal_fallback") is True
    assert normalize_transcript_text(t1) == normalize_transcript_text(t2)


@pytest.mark.emission
def test_gate_phantom_named_speaker_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """Model attributes a line to an invented authority figure; gate keeps the grounded interlocutor."""
    prompt = "What happened to the patrol?"
    scenario = NarrationTranscriptScenario(
        id="phantom_named_speaker_magistrate",
        player_text=prompt,
        raw_or_model_output=(
            'Magistrate Kell leans in. "The patrol vanished east," she says, watching you.'
        ),
        resolution=_resolution_question_to_runner(prompt),
        session_seed=0x5A11FADE,
        scene_seed=0x5A11C0DE,
        world_seed=0x5A11EED0,
        scene_id="frontier_gate",
        session=_session_engaged_tavern_runner(),
        # Full visibility: patched-off visibility can leave partially repaired phantom lines without the grounded speaker.
        patch_visibility_enforcement=False,
        assertions=NarrationTranscriptAssertions(
            required_substrings=("tavern runner",),
            forbidden_substrings=("magistrate kell", "magistrate"),
            expected_speaker_id="tavern_runner",
            meta_exact={"final_emitted_source": "minimal_social_emergency_fallback"},
            expected_route_or_repair="strict-social emergency fallback strips phantom attributed speaker",
        ),
    )
    run_gate_level_case(scenario, monkeypatch)


@pytest.mark.emission
def test_gate_phantom_crowd_watcher_insertion_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sparse engagement turn must not accept invented crowd pressure as established scene truth."""
    prompt = "What do you hear about the patrol?"
    scenario = NarrationTranscriptScenario(
        id="phantom_crowd_onlookers_and_guard",
        player_text=prompt,
        raw_or_model_output=(
            "The crowd murmurs agreement; a guard steps closer as onlookers stare at your questions."
        ),
        resolution=_resolution_question_to_runner(prompt),
        session_seed=0xC20D51DE,
        scene_seed=0xC20D5C4E,
        world_seed=0xC20D5EED,
        scene_id="frontier_gate",
        session=_session_engaged_tavern_runner(),
        patch_visibility_enforcement=False,
        assertions=NarrationTranscriptAssertions(
            required_substrings=("tavern runner",),
            forbidden_substrings=("onlookers", "murmurs agreement", "guard steps closer"),
            expected_speaker_id="tavern_runner",
            expected_route_or_repair="invented spectacle / crowd pressure removed from strict-social emission",
        ),
    )
    run_gate_level_case(scenario, monkeypatch)


@pytest.mark.emission
def test_gate_phantom_continuity_callback_to_absent_authority_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """Narration invents a prior conversation with a non-grounded figure; gate must not keep it as fact."""
    prompt = "Where are they sending the next wagons?"
    scenario = NarrationTranscriptScenario(
        id="phantom_continuity_magistrate_callback",
        player_text=prompt,
        raw_or_model_output=(
            "Magistrate Kell told you yesterday the patrol went east; the runner just nods along "
            "as if that were still the plan."
        ),
        resolution=_resolution_question_to_runner(prompt),
        session_seed=0xCA11BAC3,
        scene_seed=0xCA115C4E,
        world_seed=0xCA11EED0,
        scene_id="frontier_gate",
        session=_session_engaged_tavern_runner(),
        patch_visibility_enforcement=False,
        assertions=NarrationTranscriptAssertions(
            required_substrings=("tavern runner",),
            forbidden_substrings=("magistrate kell", "magistrate kell told you"),
            expected_speaker_id="tavern_runner",
            expected_route_or_repair="unsupported continuity callback cleared via strict-social replacement",
        ),
    )
    run_gate_level_case(scenario, monkeypatch)


# --- Echo response regressions (strict-social gate) --------------------------


@pytest.mark.emission
def test_gate_echo_direct_question_recycled(monkeypatch: pytest.MonkeyPatch) -> None:
    """GM text parrots the player's question instead of answering; emission must advance past the echo."""
    prompt = "What supplies are still moving through the gate?"
    scenario = NarrationTranscriptScenario(
        id="echo_direct_question_parrot",
        player_text=prompt,
        raw_or_model_output=(
            "Tavern Runner tilts his head and repeats your question back to you word for word: "
            "What supplies are still moving through the gate?"
        ),
        resolution=_resolution_question_to_runner(prompt),
        session_seed=0xEC40E5E1,
        scene_seed=0xEC40C0DE,
        world_seed=0xEC40EED0,
        scene_id="frontier_gate",
        session=_session_engaged_tavern_runner(),
        patch_visibility_enforcement=False,
        assertions=NarrationTranscriptAssertions(
            required_substrings=("tavern runner",),
            forbidden_substrings=("word for word", "what supplies are still moving through the gate"),
            expected_speaker_id="tavern_runner",
            expected_route_or_repair="question-echo candidate replaced with lawful runner continuation",
        ),
    )
    out = run_gate_level_case(scenario, monkeypatch)
    assert_output_excludes_player_prompt_fingerprint(prompt, str(out.get("player_facing_text") or ""))


@pytest.mark.emission
def test_gate_echo_action_paraphrase_stall(monkeypatch: pytest.MonkeyPatch) -> None:
    """GM only restates the player's declared maneuver without consequence; gate must not keep the stall."""
    prompt = "I press a silver coin into his palm and ask him to speak plainly."
    scenario = NarrationTranscriptScenario(
        id="echo_action_mirror_without_advancement",
        player_text=prompt,
        raw_or_model_output=(
            "You press a silver coin into his palm and ask him to speak plainly, mirroring the moment "
            "without advancing it."
        ),
        resolution=_resolution_persuade_to_runner(prompt),
        session_seed=0xAC710E5E,
        scene_seed=0xAC71C0DE,
        world_seed=0xAC71EED0,
        scene_id="frontier_gate",
        session=_session_engaged_tavern_runner(),
        patch_visibility_enforcement=False,
        assertions=NarrationTranscriptAssertions(
            required_substrings=("tavern runner",),
            forbidden_substrings=("mirroring the moment", "without advancing"),
            expected_speaker_id="tavern_runner",
            expected_route_or_repair="action-echo stall replaced with lawful social reply framing",
        ),
    )
    out = run_gate_level_case(scenario, monkeypatch)
    assert_output_excludes_player_prompt_fingerprint(prompt, str(out.get("player_facing_text") or ""))


@pytest.mark.emission
def test_gate_echo_faux_npc_reply_mirrors_player_question(monkeypatch: pytest.MonkeyPatch) -> None:
    """Quoted 'answer' is only the player's question; that faux reply must not survive emission."""
    prompt = "What happened to the patrol?"
    scenario = NarrationTranscriptScenario(
        id="echo_faux_answer_is_player_question",
        player_text=prompt,
        raw_or_model_output=(
            'Tavern Runner meets your eyes and answers flatly: "What happened to the patrol?"'
        ),
        resolution=_resolution_question_to_runner(prompt),
        session_seed=0xFA0E5E1E,
        scene_seed=0xFA0C5C4E,
        world_seed=0xFA0EED00,
        scene_id="frontier_gate",
        session=_session_engaged_tavern_runner(),
        patch_visibility_enforcement=False,
        assertions=NarrationTranscriptAssertions(
            required_substrings=("tavern runner",),
            forbidden_substrings=("what happened to the patrol",),
            expected_speaker_id="tavern_runner",
            expected_route_or_repair="mirrored faux-answer stripped; runner-owned line substituted",
        ),
    )
    out = run_gate_level_case(scenario, monkeypatch)
    assert_output_excludes_player_prompt_fingerprint(prompt, str(out.get("player_facing_text") or ""))


# --- Misrouted intent (pipeline route / intent) --------------------------------


@pytest.mark.routing
def test_route_misroute_directed_social_question_stays_dialogue(monkeypatch: pytest.MonkeyPatch) -> None:
    """Vocative + knowledge question must stay in the dialogue lane (not action/undecided)."""
    _ = monkeypatch
    sid = "scene_investigate"
    scenario = NarrationTranscriptScenario(
        id="misroute_social_vocative_question_not_non_dialogue",
        player_text="Tavern Runner, what did the watch report last night?",
        raw_or_model_output="",
        resolution={"kind": "question", "prompt": "Tavern Runner, what did the watch report last night?"},
        session_seed=0xD1A60001,
        scene_seed=0xD1A60002,
        world_seed=0xD1A60003,
        scene_id=sid,
        session=_session_engaged_runner_at_scene(),
        world=_world_with_runner_at_scene(sid),
        scene_envelope={"scene": {"id": sid}},
        route_kind="dialogue",
    )
    run_pipeline_route_case(scenario)


@pytest.mark.routing
def test_route_misroute_investigation_search_not_social_lane(monkeypatch: pytest.MonkeyPatch) -> None:
    """Forceful search during an engaged exchange must not collapse into dialogue routing."""
    _ = monkeypatch
    sid = "scene_investigate"
    scenario = NarrationTranscriptScenario(
        id="misroute_investigation_search_not_dialogue_lane",
        player_text="I search the crate for contraband.",
        raw_or_model_output="",
        resolution={"kind": "investigate", "prompt": "I search the crate for contraband."},
        session_seed=0x1A73501,
        scene_seed=0x1A73502,
        world_seed=0x1A73503,
        scene_id=sid,
        session=_session_engaged_runner_at_scene(),
        world=_world_with_runner_at_scene(sid),
        scene_envelope={"scene": {"id": sid}},
        route_kind="action",
        intent_kind="investigate",
    )
    run_pipeline_route_case(scenario)
    run_pipeline_intent_case(scenario)


@pytest.mark.routing
def test_route_misroute_manipulation_stays_action_lane(monkeypatch: pytest.MonkeyPatch) -> None:
    """Concrete object manipulation must remain action-routed (not passive narration / dialogue lock)."""
    _ = monkeypatch
    sid = "scene_investigate"
    scenario = NarrationTranscriptScenario(
        id="misroute_pick_up_lantern_stays_action_lane",
        player_text="I pick up the lantern.",
        raw_or_model_output="",
        resolution={"kind": "interact", "prompt": "I pick up the lantern."},
        session_seed=0xAC710001,
        scene_seed=0xAC710002,
        world_seed=0xAC710003,
        scene_id=sid,
        session=_session_engaged_runner_at_scene(),
        world=_world_with_runner_at_scene(sid),
        scene_envelope={"scene": {"id": sid}},
        route_kind="action",
    )
    run_pipeline_route_case(scenario)


def _scenario_mixed_regression_phantom_gate() -> NarrationTranscriptScenario:
    prompt = "What happened to the patrol?"
    return NarrationTranscriptScenario(
        id="table_mixed_phantom_named_speaker",
        player_text=prompt,
        raw_or_model_output=(
            'Magistrate Kell leans in. "The patrol vanished east," she says, watching you.'
        ),
        resolution=_resolution_question_to_runner(prompt),
        session_seed=0x7ABE1001,
        scene_seed=0x7ABE1002,
        world_seed=0x7ABE1003,
        scene_id="frontier_gate",
        session=_session_engaged_tavern_runner(),
        patch_visibility_enforcement=False,
        assertions=NarrationTranscriptAssertions(
            required_substrings=("tavern runner",),
            forbidden_substrings=("magistrate kell", "magistrate"),
            expected_speaker_id="tavern_runner",
            meta_exact={"final_emitted_source": "minimal_social_emergency_fallback"},
        ),
    )


def _scenario_mixed_regression_echo_gate() -> NarrationTranscriptScenario:
    prompt = "What supplies are still moving through the gate?"
    return NarrationTranscriptScenario(
        id="table_mixed_echo_question_parrot",
        player_text=prompt,
        raw_or_model_output=(
            "Tavern Runner tilts his head and repeats your question back to you word for word: "
            "What supplies are still moving through the gate?"
        ),
        resolution=_resolution_question_to_runner(prompt),
        session_seed=0x7ABE2001,
        scene_seed=0x7ABE2002,
        world_seed=0x7ABE2003,
        scene_id="frontier_gate",
        session=_session_engaged_tavern_runner(),
        patch_visibility_enforcement=False,
        assertions=NarrationTranscriptAssertions(
            required_substrings=("tavern runner",),
            forbidden_substrings=("word for word", "what supplies are still moving through the gate"),
            expected_speaker_id="tavern_runner",
        ),
    )


def _scenario_mixed_regression_misroute_route() -> NarrationTranscriptScenario:
    sid = "scene_investigate"
    return NarrationTranscriptScenario(
        id="table_misroute_search_crate_action_lane",
        player_text="I search the crate for contraband.",
        raw_or_model_output="",
        resolution={"kind": "investigate", "prompt": "I search the crate for contraband."},
        session_seed=0x7ABE3001,
        scene_seed=0x7ABE3002,
        world_seed=0x7ABE3003,
        scene_id=sid,
        session=_session_engaged_runner_at_scene(),
        world=_world_with_runner_at_scene(sid),
        scene_envelope={"scene": {"id": sid}},
        route_kind="action",
        intent_kind="investigate",
    )


def _scenario_mixed_upstream_inspect_escape() -> NarrationTranscriptScenario:
    sid = "scene_investigate"
    return NarrationTranscriptScenario(
        id="table_mixed_upstream_inspect_escape",
        player_text="Galinor inspects the tavern runner's stew.",
        raw_or_model_output="",
        resolution={"kind": "observe", "prompt": "Galinor inspects the tavern runner's stew."},
        session_seed=0x7ABE4001,
        scene_seed=0x7ABE4002,
        world_seed=0x7ABE4003,
        scene_id=sid,
        session=_session_engaged_runner_at_scene(runner_id="tavern_runner"),
        world=_world_with_runner_at_scene(sid, runner_id="tavern_runner"),
        scene_envelope={"scene": {"id": sid}},
    )


def _scenario_mixed_chain_forced_fallback_gate() -> NarrationTranscriptScenario:
    prompt = "What did you hear?"
    session, world, emission_scene = _grounded_runner_session_world_scene()
    return NarrationTranscriptScenario(
        id="table_mixed_forced_strict_social_fallback",
        player_text=prompt,
        raw_or_model_output='Magistrate Kell leans in. "They moved the wagons east," she murmurs.',
        resolution=_dialogue_contract_strict_social_resolution(prompt),
        session_seed=0x7ABE5001,
        scene_seed=0x7ABE5002,
        world_seed=0x7ABE5003,
        scene_id="frontier_gate",
        session=session,
        world=world,
        emission_scene=emission_scene,
        patch_visibility_enforcement=False,
        assertions=NarrationTranscriptAssertions(
            required_substrings=("tavern runner",),
            forbidden_substrings=("magistrate",),
            expected_speaker_id="tavern_runner",
            meta_exact={"final_emitted_source": "minimal_social_emergency_fallback"},
        ),
    )


def _scenario_mixed_familiarity_gate() -> NarrationTranscriptScenario:
    return NarrationTranscriptScenario(
        id="table_mixed_familiarity_reject",
        player_text="I study the gate.",
        raw_or_model_output="Guard Captain stands near the gate; you recognize him immediately.",
        resolution={"kind": "observe", "prompt": "I study the gate."},
        session_seed=0x7ABE6001,
        scene_seed=0x7ABE6002,
        world_seed=0x7ABE6003,
        scene_id="frontier_gate",
        session=default_session(),
        world=default_world(),
        emission_scene=default_scene("frontier_gate"),
        patch_visibility_enforcement=False,
        assertions=NarrationTranscriptAssertions(
            meta_json_fragments=("first_mention_unearned_familiarity",),
            forbidden_substrings=("you recognize him immediately",),
        ),
    )


def _scenario_mixed_obj20_embedded_vocative() -> NarrationTranscriptScenario:
    session, world, scene_envelope = _session_world_scene_frontier_gate_cleared_embedded_vocative()
    return NarrationTranscriptScenario(
        id="table_mixed_obj20_embedded_vocative",
        player_text='Tell me runner, who runs the watch?',
        raw_or_model_output="",
        resolution={"kind": "question", "prompt": 'Tell me runner, who runs the watch?'},
        session_seed=0x7ABE7001,
        scene_seed=0x7ABE7002,
        world_seed=0x7ABE7003,
        scene_id="frontier_gate",
        session=session,
        world=world,
        scene_envelope=scene_envelope,
        route_kind="dialogue",
    )


def _scenario_mixed_obj20_anti_reset() -> NarrationTranscriptScenario:
    session = default_session()
    session["turn_counter"] = 4
    session["interaction_context"] = {
        "active_interaction_target_id": "tavern_runner",
        "active_interaction_kind": "social",
        "interaction_mode": "social",
        "engagement_level": "engaged",
    }
    return NarrationTranscriptScenario(
        id="table_mixed_obj20_anti_reset",
        player_text="Look around for a certain answer.",
        raw_or_model_output="From here, no certain answer presents itself.",
        resolution={
            "kind": "observe",
            "prompt": "look around",
            "social": {
                "social_intent_class": "social_exchange",
                "npc_id": "tavern_runner",
                "npc_name": "Tavern Runner",
            },
        },
        session_seed=0x7ABE8001,
        scene_seed=0x7ABE8002,
        world_seed=0x7ABE8003,
        scene_id="frontier_gate",
        session=session,
        emission_scene=default_scene("frontier_gate"),
        patch_visibility_enforcement=False,
        assertions=NarrationTranscriptAssertions(
            meta_exact={
                "final_emitted_source": "anti_reset_local_continuation_fallback",
                "anti_reset_intro_suppressed": True,
            },
            forbidden_substrings=_FORBIDDEN_SCENE_INTRO_MARKERS,
        ),
    )


def _scenario_mixed_obj20_bounded_partial() -> NarrationTranscriptScenario:
    return NarrationTranscriptScenario(
        id="table_mixed_obj20_bounded_partial",
        player_text="Who was the buyer, exactly?",
        raw_or_model_output="No name comes clear from what shows.",
        resolution={"kind": "adjudication_query", "prompt": "Who was the buyer, exactly?"},
        session_seed=0x7ABE9001,
        scene_seed=0x7ABE9002,
        world_seed=0x7ABE9003,
        scene_id="frontier_gate",
        patch_visibility_enforcement=False,
        assertions=NarrationTranscriptAssertions(
            required_substrings=("hearsay", "sergeant"),
            forbidden_substrings=("no name comes clear from what shows.",),
            meta_exact={
                "fallback_behavior_repaired": True,
                "fallback_behavior_failed": False,
                "final_emitted_source": "bounded_partial",
            },
            meta_value_fragments={"fallback_behavior_repair_mode": "bounded_partial"},
        ),
    )


def _scenario_mixed_obj20_safety() -> NarrationTranscriptScenario:
    return NarrationTranscriptScenario(
        id="table_mixed_obj20_safety_ambiguity",
        player_text="Who signed the order?",
        raw_or_model_output="No name comes clear from what shows.",
        resolution={"kind": "adjudication_query", "prompt": "Who signed the order?"},
        session_seed=0x7ABEA001,
        scene_seed=0x7ABEA002,
        world_seed=0x7ABEA003,
        scene_id="frontier_gate",
        patch_visibility_enforcement=False,
        assertions=NarrationTranscriptAssertions(
            forbidden_substrings=(
                "verrick",
                "culprit was",
                "signed by",
                "the order was signed by",
            ),
            meta_exact={"fallback_behavior_repaired": True, "fallback_behavior_failed": False},
        ),
    )


def _scenario_mixed_obj21_followup_recovery() -> NarrationTranscriptScenario:
    return replace(_obj21_scenario_crossroads_followup_recovery(), id="table_mixed_obj21_followup_recovery")


@pytest.mark.parametrize(
    "runner_kind, scenario",
    [
        pytest.param("gate", _scenario_mixed_regression_phantom_gate(), marks=[pytest.mark.emission]),
        pytest.param("gate", _scenario_mixed_regression_echo_gate(), marks=[pytest.mark.emission]),
        pytest.param("pipeline_misroute", _scenario_mixed_regression_misroute_route(), marks=[pytest.mark.routing]),
        pytest.param("pipeline_upstream", _scenario_mixed_upstream_inspect_escape(), marks=[pytest.mark.routing]),
        pytest.param("gate", _scenario_mixed_chain_forced_fallback_gate(), marks=[pytest.mark.emission]),
        pytest.param("gate", _scenario_mixed_familiarity_gate(), marks=[pytest.mark.emission]),
        pytest.param("pipeline_direct_address", _scenario_mixed_obj20_embedded_vocative(), marks=[pytest.mark.routing]),
        pytest.param("gate_anti_reset_obj20", _scenario_mixed_obj20_anti_reset(), marks=[pytest.mark.emission]),
        pytest.param("gate_bounded_partial_obj20", _scenario_mixed_obj20_bounded_partial(), marks=[pytest.mark.emission]),
        pytest.param("gate_safety_obj20", _scenario_mixed_obj20_safety(), marks=[pytest.mark.emission]),
        pytest.param("pipeline_obj21_followup", _scenario_mixed_obj21_followup_recovery(), marks=[pytest.mark.routing]),
        pytest.param("integration_obj21_adoption", _scenario_mixed_obj21_followup_recovery(), marks=[pytest.mark.routing]),
        pytest.param("integration_obj21_stale_anchor", _scenario_mixed_obj21_followup_recovery(), marks=[pytest.mark.routing]),
        pytest.param("integration_obj21_fallback_anchor", _scenario_mixed_obj21_followup_recovery(), marks=[pytest.mark.emission]),
        pytest.param("integration_obj21_ambiguity_safety", _scenario_mixed_obj21_followup_recovery(), marks=[pytest.mark.routing]),
    ],
    ids=[
        "mixed_phantom_gate",
        "mixed_echo_gate",
        "mixed_misroute_pipeline",
        "mixed_upstream_inspect",
        "mixed_forced_strict_fallback",
        "mixed_familiarity_gate",
        "mixed_obj20_embedded_vocative",
        "mixed_obj20_anti_reset",
        "mixed_obj20_bounded_partial",
        "mixed_obj20_safety",
        "mixed_obj21_followup_recovery",
        "mixed_obj21_speaker_adoption",
        "mixed_obj21_stale_anchor",
        "mixed_obj21_fallback_anchor",
        "mixed_obj21_ambiguity_safety",
    ],
)
def test_transcript_mixed_regression_table(
    runner_kind: str,
    scenario: NarrationTranscriptScenario,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Any,
) -> None:
    """Durable entry point: phantom + echo + 18a chain (gate); routing; Objective #20 / #21 integration rows."""
    if runner_kind == "gate":
        run_gate_level_case(scenario, monkeypatch, tmp_path=tmp_path)
    elif runner_kind == "pipeline_misroute":
        run_pipeline_route_case(scenario)
        run_pipeline_intent_case(scenario)
    elif runner_kind == "pipeline_upstream":
        route = run_pipeline_route_case(scenario)
        assert route != "dialogue"
    elif runner_kind == "pipeline_direct_address":
        run_pipeline_route_case(scenario)
        apply_transcript_seeds(scenario)
        session, world, scene_envelope, _ = seed_minimal_play_context(scenario)
        entry = resolve_directed_social_entry(
            session=session,
            scene=scene_envelope,
            world=world,
            segmented_turn=None,
            raw_text=scenario.player_text,
        )
        assert entry.get("should_route_social") is True
        assert entry.get("target_actor_id") == "tavern_runner"
    elif runner_kind == "gate_anti_reset_obj20":
        monkeypatch.setattr(_feg, "strict_social_emission_will_apply", lambda *a, **k: False)
        run_gate_level_case(scenario, monkeypatch, tmp_path=tmp_path)
    elif runner_kind == "gate_bounded_partial_obj20":
        out = _run_object20_bounded_gate_case(scenario, monkeypatch, with_answer_contract=True)
        meta = out.get("_final_emission_meta") if isinstance(out.get("_final_emission_meta"), dict) else {}
        assert meta.get("final_emitted_source") != "global_scene_fallback"
    elif runner_kind == "gate_safety_obj20":
        _ = _run_object20_bounded_gate_case(scenario, monkeypatch, with_answer_contract=False)
    elif runner_kind == "pipeline_obj21_followup":
        _assert_obj21_crossroads_followup_recovery_chain(scenario)
    elif runner_kind == "integration_obj21_adoption":
        assert scenario.id.startswith("table_mixed_obj21")
        _assert_obj21_guard_adoption_updates_interlocutor()
    elif runner_kind == "integration_obj21_stale_anchor":
        assert scenario.id.startswith("table_mixed_obj21")
        _assert_obj21_stale_anchor_cleared_followup_not_runner()
    elif runner_kind == "integration_obj21_fallback_anchor":
        assert scenario.id.startswith("table_mixed_obj21")
        _assert_obj21_force_terminal_fallback_uses_guard_not_stale_runner(monkeypatch)
    elif runner_kind == "integration_obj21_ambiguity_safety":
        assert scenario.id.startswith("table_mixed_obj21")
        _assert_obj21_safety_crowd_and_ambiguous()
    else:
        raise AssertionError(f"unknown runner_kind {runner_kind!r}")


# --- Smoke tests -------------------------------------------------------------


@pytest.mark.emission
def test_harness_gate_level_smoke_hard_constraint_passthrough(monkeypatch: pytest.MonkeyPatch) -> None:
    """Trivial happy-path: concrete scene detail passes without anti-railroad repair."""
    scenario = NarrationTranscriptScenario(
        id="gate_smoke_bridge_constraint",
        player_text="I look for routes.",
        raw_or_model_output="The bridge is out. The alley and the roofline are still open.",
        resolution={"kind": "observe", "prompt": "I look for routes."},
        session_seed=1,
        scene_seed=2,
        world_seed=3,
        assertions=NarrationTranscriptAssertions(
            required_substrings=("bridge", "alley"),
            meta_exact={"anti_railroading_repaired": False},
        ),
    )
    out = run_gate_level_case(scenario, monkeypatch)
    assert out.get("player_facing_text") == scenario.raw_or_model_output


@pytest.mark.routing
def test_harness_pipeline_route_smoke_dialogue_lock(monkeypatch: pytest.MonkeyPatch) -> None:
    """Routing: dialogue lock keeps informational questions in the dialogue lane."""
    _ = monkeypatch  # reserved for future GM/network patches
    scenario = NarrationTranscriptScenario(
        id="pipeline_smoke_dialogue_lock",
        player_text="Who attacked them?",
        raw_or_model_output="",
        resolution={"kind": "observe", "prompt": "Who attacked them?"},
        session_seed=10,
        scene_seed=11,
        world_seed=12,
        scene_id="scene_investigate",
        world={
            "npcs": [
                {"id": "runner", "name": "Tavern Runner", "location": "scene_investigate"},
            ]
        },
        session={
            "interaction_context": {
                "active_interaction_target_id": "runner",
                "active_interaction_kind": "social",
                "interaction_mode": "social",
                "engagement_level": "engaged",
            }
        },
        scene_envelope={"scene": {"id": "scene_investigate"}},
        route_kind="dialogue",
    )
    run_pipeline_route_case(scenario)


@pytest.mark.routing
def test_harness_pipeline_intent_smoke_observe_parse(monkeypatch: pytest.MonkeyPatch) -> None:
    """Intent: deterministic parser classifies a plain observation action."""
    _ = monkeypatch
    scenario = NarrationTranscriptScenario(
        id="pipeline_smoke_observe_intent",
        player_text="I look around.",
        raw_or_model_output="",
        resolution={"kind": "observe", "prompt": "I look around."},
        session_seed=20,
        scene_seed=21,
        world_seed=22,
        intent_kind="observe",
    )
    run_pipeline_intent_case(scenario)
