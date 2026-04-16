"""Authoritative New Campaign hard reset.

A single entry point replaces runtime session (root dict replacement via ``reset_session_state``),
replaces combat with ``create_fresh_combat_state``, clears the transcript, and strips world
playthrough residue. Bootstrap JSON files (campaign, character, scene templates) are not deleted;
``compose_state`` then syncs character name and other intentional bootstrap fields from disk.

Set ``ASHEN_THRONES_DEV_VERIFY=1`` to reload persisted state after reset and run
:func:`game.fresh_campaign_verify.verify_fresh_campaign_runtime` (warnings to log + concise
``print``). ``ASHEN_THRONES_DEV_VERIFY_STRICT=1`` turns failures into ``RuntimeError`` (e.g. CI).
"""
from __future__ import annotations

from typing import Any, Dict

from game.campaign_state import create_fresh_combat_state
from game.session import reset_session_state
from game.storage import (
    clear_log,
    load_combat,
    load_log,
    load_session,
    load_world,
    save_combat,
    save_session,
    save_world,
)
from game.world import reset_world_playthrough_state


def apply_new_campaign_hard_reset() -> Dict[str, Any]:
    """Perform full New Campaign reset: session root replacement, fresh combat, world runtime clear, empty log.

    Session must be replaced before applying bootstrap-derived sync (e.g. clocks init in
    ``compose_state`` / ``get_or_init_clocks``); world playthrough state must be cleared
    or ``world.json`` would re-contaminate prompts (event log, faction ticks, flags).
    """
    session = load_session()
    # Root replacement: stale keys from older engines cannot survive.
    reset_session_state(session)
    save_session(session)

    world = load_world()
    reset_world_playthrough_state(world)
    save_world(world)

    combat = load_combat()
    combat.clear()
    combat.update(create_fresh_combat_state())
    save_combat(combat)

    clear_log()
    # Invariant (NC2): New Campaign is a silent reset — no persisted transcript rows until a turn runs.
    tail = load_log()
    if tail:
        clear_log()
        tail = load_log()
    if tail:
        raise RuntimeError(
            "New Campaign invariant violated: session transcript is non-empty immediately after clear_log()."
        )
    meta: Dict[str, Any] = {
        "campaign_run_id": session.get("campaign_run_id"),
        "session_id": session.get("session_id"),
        # Operator/debug only (HTTP JSON for /api/new_campaign); proves reset + empty transcript.
        "transcript_entry_count_after_reset": 0,
        "silent_reset_no_implicit_transcript": True,
    }

    # Development-only: reload persisted state and assert runtime residue is gone (see
    # ``game.fresh_campaign_verify``). Bootstrap files are unchanged; session/world
    # playthrough layers must be clean.
    from game.fresh_campaign_verify import (
        dev_verification_enabled,
        dev_verification_strict,
        summarize_post_reset_for_dev_log,
        verify_fresh_campaign_runtime,
    )

    if dev_verification_enabled():
        v = verify_fresh_campaign_runtime(
            load_session(),
            load_world(),
            load_combat(),
            log_entries=load_log(),
            strict=dev_verification_strict(),
        )
        meta["dev_verify_ok"] = v["ok"]
        meta["dev_verify_violations"] = v["violations"]
        print(
            summarize_post_reset_for_dev_log(
                campaign_run_id=meta.get("campaign_run_id"),
                session_id=meta.get("session_id"),
                violations=v["violations"],
            )
        )
        if v["violations"]:
            print("[NEW_CAMPAIGN_DEV] " + "; ".join(v["violations"]))

    return meta
