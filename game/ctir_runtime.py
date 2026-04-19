"""Runtime seam: attach, retrieve, and build canonical CTIR for one narration invocation.

**Authority:** CTIR is the canonical *resolved-turn meaning object* for one narration attempt (bounded, no
prose). Canonical engine/session/scene state remains owned by engine modules; CTIR only carries explicit
slices passed into :func:`game.ctir.build_ctir`.

**Lifecycle (see docs/ctir_prompt_adapter_architecture.md):** :func:`game.api._run_resolved_turn_pipeline`
detaches stale CTIR, applies authoritative mutation, then :func:`game.api._build_gpt_narration_from_authoritative_state`
runs resolution-facing hygiene, snapshotted by :func:`ensure_ctir_for_turn` / :func:`build_runtime_ctir_for_narration`,
and attaches CTIR + stamp on ``session`` for reuse across GPT retries.

**Consumers:** :mod:`game.prompt_context` must read via :func:`get_attached_ctir` and map through its adapter
helpers; it must not reconstruct CTIR or call :func:`game.ctir.build_ctir`. :mod:`game.turn_packet` stays a
separate contracts/debug packet—do not duplicate CTIR into the packet.
"""

from __future__ import annotations

from collections.abc import Callable, MutableMapping
from typing import Any

from game import ctir

SESSION_CTIR_KEY = "_runtime_canonical_ctir_v1"
SESSION_CTIR_STAMP_KEY = "_runtime_canonical_ctir_stamp_v1"


def attach_ctir(container: MutableMapping[str, Any], ctir_obj: dict[str, Any]) -> None:
    """Store *ctir_obj* on *container* (typically ``session``)."""
    container[SESSION_CTIR_KEY] = ctir_obj


def get_attached_ctir(container: MutableMapping[str, Any] | None) -> dict[str, Any] | None:
    """Return attached CTIR dict or ``None``."""
    if not isinstance(container, MutableMapping):
        return None
    raw = container.get(SESSION_CTIR_KEY)
    return raw if isinstance(raw, dict) else None


def detach_ctir(container: MutableMapping[str, Any] | None) -> None:
    """Remove CTIR attachment and stamp from *container*."""
    if not isinstance(container, MutableMapping):
        return
    container.pop(SESSION_CTIR_KEY, None)
    container.pop(SESSION_CTIR_STAMP_KEY, None)


def narration_ctir_turn_stamp(
    *,
    session: MutableMapping[str, Any],
    resolution: dict | None,
    user_text: str,
) -> str:
    """Stable stamp for one resolved narration attempt (object identity + session turn + text)."""
    tc = session.get("turn_counter")
    rid = id(resolution) if isinstance(resolution, dict) else 0
    h = hash(user_text) & 0xFFFFFFFF
    return f"{tc!s}:{rid:x}:{h:x}"


def ensure_ctir_for_turn(
    container: MutableMapping[str, Any],
    *,
    turn_stamp: str,
    builder: Callable[[], dict[str, Any]],
) -> dict[str, Any]:
    """Return existing CTIR when *turn_stamp* matches; otherwise build via *builder* and attach."""
    existing = get_attached_ctir(container)
    stamp_ok = str(container.get(SESSION_CTIR_STAMP_KEY) or "") == turn_stamp
    if existing is not None and stamp_ok:
        return existing
    built = builder()
    attach_ctir(container, built)
    container[SESSION_CTIR_STAMP_KEY] = turn_stamp
    return built


def _slice_intent(*, player_input: str, normalized_action: dict | None) -> dict[str, Any]:
    out: dict[str, Any] = {"raw_text": player_input}
    if not isinstance(normalized_action, dict):
        return out
    lab = normalized_action.get("labels")
    if isinstance(lab, (list, tuple)) and lab:
        out["labels"] = list(lab)
    t = str(normalized_action.get("type") or "").strip() or None
    if t:
        out["normalized_kind"] = t
        out["classified_action"] = t
        out["mode"] = t
    aid = str(normalized_action.get("id") or "").strip()
    if aid and not out.get("classified_action"):
        out["classified_action"] = aid
    targets: list[Any] = []
    for key in ("target_scene_id", "targetSceneId", "target_id"):
        v = normalized_action.get(key)
        if v is not None and str(v).strip():
            targets.append(str(v).strip())
    if targets:
        out["targets"] = targets
    return out


def _slice_resolution(resolution: dict | None) -> dict[str, Any]:
    if not isinstance(resolution, dict):
        return {}
    out: dict[str, Any] = {"kind": resolution.get("kind")}
    if "outcome_type" in resolution:
        out["outcome_type"] = resolution.get("outcome_type")
    if "success" in resolution:
        out["success_state"] = "success" if resolution.get("success") else "failure"
    sc = resolution.get("state_changes")
    if isinstance(sc, dict):
        keys = sorted(str(k) for k in sc.keys())[:32]
        out["consequences"] = keys
    elif isinstance(sc, (list, tuple)):
        out["consequences"] = list(sc)[:32]
    auth: dict[str, Any] = {}
    for k in ("action_id", "target_scene_id", "resolved_transition", "originating_scene_id", "clue_id"):
        if k in resolution and resolution.get(k) is not None:
            auth[k] = resolution.get(k)
    if auth:
        out["authoritative_outputs"] = auth
    soc = resolution.get("social")
    if isinstance(soc, dict):
        slim = {k: soc[k] for k in ("npc_reply_expected", "reply_kind", "gated_information", "information_gate") if k in soc}
        if slim:
            out["social"] = slim
    sc = resolution.get("state_changes")
    if isinstance(sc, dict):
        sub = {
            k: bool(sc[k])
            for k in ("scene_transition_occurred", "arrived_at_scene", "new_scene_context_available")
            if k in sc
        }
        if sub:
            out["state_changes"] = sub
    if "requires_check" in resolution:
        out["requires_check"] = bool(resolution.get("requires_check"))
    cr = resolution.get("check_request")
    if isinstance(cr, dict):
        out["check_request"] = cr
    sk = resolution.get("skill_check")
    if isinstance(sk, dict):
        out["skill_check"] = sk
    md = resolution.get("metadata")
    if isinstance(md, dict):
        keep = {k: md[k] for k in ("human_adjacent_intent_family", "implicit_focus_resolution") if k in md}
        if keep:
            out["metadata"] = keep
    for k in ("label", "action_id", "prompt"):
        if k in resolution and resolution.get(k) is not None:
            out[k] = resolution.get(k)
    return out


def _slice_state_mutations(
    *,
    scene_id: str | None,
    resolution: dict | None,
    combat: dict | None,
    session: dict | None,
) -> dict[str, Any]:
    scene_block: dict[str, Any] = {}
    if scene_id:
        scene_block["scene_id"] = scene_id
    if isinstance(resolution, dict):
        if resolution.get("resolved_transition") and resolution.get("target_scene_id"):
            scene_block["activate_scene_id"] = str(resolution.get("target_scene_id") or "").strip() or None
    session_block: dict[str, Any] = {}
    if isinstance(session, dict):
        aid = str(session.get("active_scene_id") or "").strip()
        if aid:
            session_block["scene_id"] = aid
    combat_block: dict[str, Any] = {}
    if isinstance(combat, dict):
        combat_block["combat_active"] = bool(combat.get("in_combat"))
        if "round" in combat:
            combat_block["round"] = combat.get("round")
        if combat.get("phase") is not None:
            combat_block["phase"] = combat.get("phase")
    return {
        "scene": scene_block,
        "session": session_block,
        "combat": combat_block,
        "clues_leads": {},
    }


def _slice_interaction(session: dict | None) -> dict[str, Any]:
    if not isinstance(session, dict):
        return {}
    ctx = session.get("interaction_context")
    if not isinstance(ctx, dict):
        return {}
    out: dict[str, Any] = {}
    mode = str(ctx.get("interaction_mode") or "").strip()
    if mode:
        out["interaction_mode"] = mode
    at = str(session.get("active_interaction_target_id") or "").strip()
    if at:
        out["active_target_id"] = at
    ak = ctx.get("active_interaction_kind")
    if isinstance(ak, str) and ak.strip():
        out["interaction_kind"] = str(ak).strip()
    return out


def _slice_world(resolution: dict | None) -> dict[str, Any]:
    if not isinstance(resolution, dict):
        return {}
    ev = resolution.get("world_tick_events")
    if isinstance(ev, list) and ev:
        return {"events": list(ev)[:32]}
    return {}


def build_runtime_ctir_for_narration(
    *,
    turn_id: Any,
    scene_id: str | None,
    player_input: str,
    builder_source: str,
    resolution: dict | None,
    normalized_action: dict | None,
    combat: dict | None,
    session: dict | None,
) -> dict[str, Any]:
    """Assemble explicit bounded kwargs for :func:`game.ctir.build_ctir`."""
    return ctir.build_ctir(
        turn_id=turn_id,
        scene_id=scene_id,
        player_input=player_input,
        builder_source=builder_source,
        intent=_slice_intent(player_input=player_input, normalized_action=normalized_action),
        resolution=_slice_resolution(resolution),
        state_mutations=_slice_state_mutations(
            scene_id=scene_id,
            resolution=resolution,
            combat=combat,
            session=session,
        ),
        interaction=_slice_interaction(session),
        world=_slice_world(resolution),
        narrative_anchors=None,
        source_modules=("game.ctir_runtime", "game.api"),
        signals_used=None,
        retry_safe_flags=None,
        provenance_extras=None,
    )
