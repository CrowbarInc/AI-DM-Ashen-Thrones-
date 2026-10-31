"""Development-only checks that New Campaign / hard reset cleared *runtime* residue.

Bootstrap seed (campaign.json, character sheet, scene templates, static world rows) may
remain; this module flags *stale playthrough* state: interaction locks, scene_runtime
(topic pressure, momentum, passive streaks), clue memory, engine caches, and world
event/project append lists. Reset correctness depends on replacing the session root
(``session.clear()`` + fresh graph), clearing world playthrough fields, combat, and the
transcript — not on partially mutating old dicts in place.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Mapping, Optional

from game.campaign_state import (
    DEFAULT_STARTING_SCENE_ID,
    create_fresh_combat_state,
    create_fresh_session_document,
)

_log = logging.getLogger(__name__)

# Enable post-reset verification in dev: set ASHEN_THRONES_DEV_VERIFY=1
_DEV_VERIFY_ENV = "ASHEN_THRONES_DEV_VERIFY"
# Optional: raise RuntimeError on any violation (e.g. CI / strict local)
_STRICT_ENV = "ASHEN_THRONES_DEV_VERIFY_STRICT"


def dev_verification_enabled() -> bool:
    return os.environ.get(_DEV_VERIFY_ENV, "").strip().lower() in ("1", "true", "yes")


def dev_verification_strict() -> bool:
    return os.environ.get(_STRICT_ENV, "").strip().lower() in ("1", "true", "yes")


def _expected_session_template() -> Dict[str, Any]:
    return create_fresh_session_document()


def collect_fresh_campaign_violations(
    session: Mapping[str, Any] | None,
    world: Mapping[str, Any] | None,
    combat: Mapping[str, Any] | None,
    *,
    log_entries: Optional[List[Any]] = None,
) -> List[str]:
    """Return human-readable violation strings with field paths. Empty list means OK."""
    violations: List[str] = []
    tmpl = _expected_session_template()
    expected_top = set(tmpl.keys()) | {"last_saved_at"}

    if not isinstance(session, dict):
        violations.append("session: expected dict, got " + type(session).__name__)
        return violations

    for key in session.keys():
        if key not in expected_top:
            violations.append(f"session.{key}: unexpected top-level key (stale engine field?)")

    ic = session.get("interaction_context")
    if not isinstance(ic, dict):
        violations.append("session.interaction_context: must be a dict")
    else:
        exp_ic = tmpl["interaction_context"]
        for k in exp_ic.keys():
            if k not in ic:
                violations.append(f"session.interaction_context.{k}: missing")
        for k in ic.keys():
            if k not in exp_ic:
                violations.append(f"session.interaction_context.{k}: unexpected key")
        if ic.get("active_interaction_target_id") not in (None, ""):
            violations.append(
                "session.interaction_context.active_interaction_target_id: "
                f"expected null, got {ic.get('active_interaction_target_id')!r}"
            )
        # Alias for prompt/social: "active interlocutor" is this id in this codebase.
        if ic.get("active_interaction_kind") not in (None, ""):
            violations.append(
                "session.interaction_context.active_interaction_kind: "
                f"expected cleared, got {ic.get('active_interaction_kind')!r}"
            )
        if str(ic.get("interaction_mode") or "").strip().lower() != "none":
            violations.append(
                "session.interaction_context.interaction_mode: "
                f"expected 'none' after reset, got {ic.get('interaction_mode')!r}"
            )
        if str(ic.get("engagement_level") or "").strip().lower() != "none":
            violations.append(
                "session.interaction_context.engagement_level: "
                f"expected 'none' after reset, got {ic.get('engagement_level')!r}"
            )

    ss = session.get("scene_state")
    if not isinstance(ss, dict):
        violations.append("session.scene_state: must be a dict")
    else:
        exp_ss = tmpl["scene_state"]
        if ss.get("current_interlocutor") not in (None, ""):
            violations.append(
                "session.scene_state.current_interlocutor: "
                f"expected null, got {ss.get('current_interlocutor')!r}"
            )
        for k in exp_ss.keys():
            if k not in ss:
                violations.append(f"session.scene_state.{k}: missing")

    sr = session.get("scene_runtime")
    if sr != {}:
        if not isinstance(sr, dict):
            violations.append("session.scene_runtime: must be an empty dict after reset")
        elif sr:
            # Per-scene dicts hold scene_momentum counters, topic_pressure, passive streaks, etc.
            violations.append(
                "session.scene_runtime: expected {{}}, found keys "
                f"{list(sr.keys())!r} (momentum / pressure / discovery residue)"
            )

    if session.get("clue_knowledge") not in ({}, None):
        if not isinstance(session.get("clue_knowledge"), dict) or session["clue_knowledge"]:
            violations.append("session.clue_knowledge: expected empty dict")

    if session.get("npc_runtime") not in ({}, None):
        if not isinstance(session.get("npc_runtime"), dict) or session["npc_runtime"]:
            violations.append("session.npc_runtime: expected empty dict")

    if session.get("debug_traces") not in ([], None):
        violations.append("session.debug_traces: expected empty list")

    if session.get("last_action_debug") is not None:
        violations.append("session.last_action_debug: expected null (no stale GM/debug payload)")

    if session.get("flags") not in ({}, None):
        if not isinstance(session.get("flags"), dict) or session["flags"]:
            violations.append("session.flags: expected empty dict")

    if session.get("chat_history") not in ([], None):
        violations.append("session.chat_history: expected empty list")

    if int(session.get("turn_counter", -1) or 0) != 0:
        violations.append(f"session.turn_counter: expected 0, got {session.get('turn_counter')!r}")

    vs = session.get("visited_scene_ids")
    if vs != [DEFAULT_STARTING_SCENE_ID]:
        violations.append(
            "session.visited_scene_ids: expected bootstrap opening scene only, "
            f"got {vs!r}"
        )

    fresh_combat = create_fresh_combat_state()
    if not isinstance(combat, dict):
        violations.append("combat: expected dict")
    elif combat != fresh_combat:
        violations.append(f"combat: expected fresh idle state {fresh_combat!r}, got {dict(combat)!r}")

    if not isinstance(world, dict):
        violations.append("world: expected dict")
    else:
        if world.get("event_log") not in ([], None):
            violations.append("world.event_log: expected empty after playthrough clear")
        if world.get("projects") not in ([], None):
            violations.append("world.projects: expected empty after playthrough clear")
        if world.get("world_flags") not in ([], None):
            violations.append("world.world_flags: expected empty after playthrough clear")
        if world.get("assets") not in ([], None):
            violations.append("world.assets: expected empty after playthrough clear")
        ws = world.get("world_state")
        if ws != {"flags": {}, "counters": {}, "clocks": {}}:
            violations.append(
                "world.world_state: expected empty flags/counters/clocks shell, "
                f"got {ws!r}"
            )

    if log_entries is not None and log_entries != []:
        violations.append(f"session log: expected empty, got {len(log_entries)} entries")

    return violations


def verify_fresh_campaign_runtime(
    session: Mapping[str, Any] | None,
    world: Mapping[str, Any] | None,
    combat: Mapping[str, Any] | None,
    *,
    log_entries: Optional[List[Any]] = None,
    strict: Optional[bool] = None,
) -> Dict[str, Any]:
    """Run checks; log warnings; optionally raise in strict mode. Returns {ok, violations}."""
    violations = collect_fresh_campaign_violations(
        session, world, combat, log_entries=log_entries
    )
    use_strict = dev_verification_strict() if strict is None else strict
    if violations:
        msg = "; ".join(violations)
        _log.warning("[FRESH_CAMPAIGN_VERIFY] failed: %s", msg)
        if use_strict:
            raise RuntimeError(f"Fresh campaign verification failed: {msg}")
    return {"ok": len(violations) == 0, "violations": violations}


def summarize_post_reset_for_dev_log(
    *,
    campaign_run_id: Any,
    session_id: Any,
    violations: List[str],
) -> str:
    """One compact line for server console when dev verification runs."""
    clean = len(violations) == 0
    return (
        "[NEW_CAMPAIGN_DEV] "
        f"run_id={campaign_run_id!s} session_id={session_id!s} "
        f"bootstrap_scene={DEFAULT_STARTING_SCENE_ID} "
        f"runtime_clean={'yes' if clean else 'NO'} "
        f"n_issues={len(violations)}"
    )
