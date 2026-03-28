"""Transcript-level gauntlet: actor binding, generic addressing, continuity (real chat turns)."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Callable

import pytest

from game import storage
from game.api import chat
from game.defaults import default_scene
from game.models import ChatRequest
from tests.helpers.transcript_runner import (
    format_turn_debug,
    patch_transcript_storage,
    run_transcript_turns,
    write_default_bootstrap_scenes,
)


def _gm_ok(speaker: str, line: str) -> dict[str, Any]:
    """Minimal strict-social-safe reply (quoted speech)."""
    return {
        "player_facing_text": f'{speaker} nods. "{line}"',
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }


def _gm_opening() -> dict[str, Any]:
    return _gm_ok("The rain", "The gate crowd presses in; voices and wagon wheels fill the mud.")


def _patch_call_gpt(monkeypatch: Any, fn: Callable[..., dict[str, Any]]) -> None:
    monkeypatch.setattr("game.api.call_gpt", fn)


def _run_transcript_with_payloads(
    tmp_path: Path,
    monkeypatch: Any,
    turns: list[str],
    *,
    chat_fn: Callable[[ChatRequest], dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    patch_transcript_storage(monkeypatch, tmp_path)
    write_default_bootstrap_scenes()
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")
    payloads: list[dict[str, Any]] = []

    def capture(req: ChatRequest) -> dict[str, Any]:
        p = chat_fn(req)
        payloads.append(p)
        return p

    snaps = run_transcript_turns(turns, starting_scene_id="frontier_gate", chat_fn=capture)
    return snaps, payloads


def _actor_struct_from_snap(snap: dict[str, Any], payload: dict[str, Any] | None = None) -> dict[str, Any]:
    soc = snap.get("social_resolution") if isinstance(snap.get("social_resolution"), dict) else {}
    ctx = snap.get("interaction_context") if isinstance(snap.get("interaction_context"), dict) else {}
    gm = payload.get("gm_output") if isinstance(payload, dict) and isinstance(payload.get("gm_output"), dict) else {}
    meta = gm.get("_final_emission_meta") if isinstance(gm.get("_final_emission_meta"), dict) else {}
    return {
        "target_id": (str(soc.get("npc_id") or "").strip() or None),
        "target_source": (str(soc.get("target_source") or "").strip() or None),
        "target_resolved": soc.get("target_resolved"),
        "current_interlocutor": snap.get("current_interlocutor"),
        "active_interaction_target_id": (str(ctx.get("active_interaction_target_id") or "").strip() or None),
        "final_route": meta.get("final_route"),
        "final_emitted_source": meta.get("final_emitted_source"),
    }


def latest_target_not_null_after_bind(snap: dict[str, Any], payload: dict[str, Any] | None) -> bool:
    st = _actor_struct_from_snap(snap, payload)
    return bool(st["target_id"] and st["target_source"] and st["current_interlocutor"])


def _fail_transcript(msg: str, snaps: list[dict[str, Any]], payloads: list[dict[str, Any]] | None = None) -> None:
    blocks: list[str] = [msg, "", "Per-turn summary:", ""]
    for i, snap in enumerate(snaps):
        pl = payloads[i] if payloads and i < len(payloads) else None
        blocks.append(format_turn_debug(snap))
        if pl is not None:
            st = _actor_struct_from_snap(snap, pl)
            blocks.append(f"  structured: {json.dumps(st, default=str)}")
        blocks.append("---")
    pytest.fail("\n".join(blocks))


def _assert_social_turn(
    snap: dict[str, Any],
    payload: dict[str, Any] | None,
    *,
    expected_target: str,
    allowed_sources: tuple[str, ...],
    interlocutor: str | None = None,
    interlocutor_not: str | None = None,
    require_resolved: bool = True,
    snaps: list[dict[str, Any]] | None = None,
    payloads: list[dict[str, Any]] | None = None,
) -> None:
    soc = snap.get("social_resolution") if isinstance(snap.get("social_resolution"), dict) else {}
    st = _actor_struct_from_snap(snap, payload)
    try:
        assert st["target_id"] == expected_target, st
        if require_resolved:
            assert soc.get("target_resolved") is True, soc
        assert st["target_source"] in allowed_sources, st
        if "continuity" not in allowed_sources and st["target_source"] == "continuity":
            raise AssertionError(f"unexpected continuity win: {st}")
        if interlocutor is not None:
            assert snap.get("current_interlocutor") == interlocutor, snap
        if interlocutor_not is not None:
            assert snap.get("current_interlocutor") != interlocutor_not, snap
    except AssertionError:
        _fail_transcript(
            f"Assertion failed for turn_index={snap.get('turn_index')!r}",
            snaps or [snap],
            payloads,
        )


@pytest.fixture
def mock_gpt_chain(monkeypatch: Any) -> Callable[[list[str]], None]:
    """Install call_gpt that returns opening text for Begin., then lines from *replies* in order."""

    def install(replies: list[str]) -> None:
        opening = _gm_opening()
        idx = {"n": 0}

        def call_gpt(_messages: list[dict[str, str]]) -> dict[str, Any]:
            i = idx["n"]
            idx["n"] += 1
            if i == 0:
                return opening
            li = i - 1
            if li < len(replies):
                return json.loads(replies[li])
            return _gm_ok(speaker="Someone", line="I hear you.")

        _patch_call_gpt(monkeypatch, call_gpt)

    return install


def test_guard_followup_preserves_target(tmp_path, monkeypatch, mock_gpt_chain):
    replies = [
        json.dumps(_gm_ok("Guard Captain", "Tax notices and a warning about the patrol.")),
        json.dumps(_gm_ok("Guard Captain", "Folk say they vanished past the old crossroads.")),
    ]
    mock_gpt_chain(replies)
    turns = [
        "Begin.",
        "Guard Captain, what is posted on the notice board?",
        "What about the patrol rumor?",
    ]
    snaps, payloads = _run_transcript_with_payloads(tmp_path, monkeypatch, turns, chat_fn=chat)

    _assert_social_turn(
        snaps[1],
        payloads[1],
        expected_target="guard_captain",
        allowed_sources=("explicit_target", "spoken_vocative", "vocative"),
        interlocutor="guard_captain",
        snaps=snaps,
        payloads=payloads,
    )
    _assert_social_turn(
        snaps[2],
        payloads[2],
        expected_target="guard_captain",
        allowed_sources=("continuity", "explicit_target"),
        interlocutor="guard_captain",
        snaps=snaps,
        payloads=payloads,
    )
    for i in (1, 2):
        assert latest_target_not_null_after_bind(snaps[i], payloads[i]), _actor_struct_from_snap(
            snaps[i], payloads[i]
        )


def test_generic_guard_address_overrides_runner(tmp_path, monkeypatch, mock_gpt_chain):
    replies = [
        json.dumps(_gm_ok("Tavern Runner", "Stew and whispers—both cost coin.")),
        json.dumps(_gm_ok("Guard Captain", "Captain's inside the gatehouse today.")),
    ]
    mock_gpt_chain(replies)
    turns = [
        "Begin.",
        "Tavern Runner, what are you selling today?",
        "You, watchman. Where is your Captain?",
    ]
    snaps, payloads = _run_transcript_with_payloads(tmp_path, monkeypatch, turns, chat_fn=chat)

    _assert_social_turn(
        snaps[1],
        payloads[1],
        expected_target="tavern_runner",
        allowed_sources=("explicit_target", "spoken_vocative", "vocative"),
        interlocutor="tavern_runner",
        snaps=snaps,
        payloads=payloads,
    )
    _assert_social_turn(
        snaps[2],
        payloads[2],
        expected_target="guard_captain",
        allowed_sources=("explicit_target", "generic_role", "spoken_vocative", "vocative"),
        interlocutor="guard_captain",
        snaps=snaps,
        payloads=payloads,
    )
    grb = (snaps[2].get("social_resolution") or {}).get("generic_role_rebind")
    if isinstance(grb, dict):
        assert grb.get("continuity_overridden") is True, grb


def test_generic_runner_address_overrides_guard(tmp_path, monkeypatch, mock_gpt_chain):
    replies = [
        json.dumps(_gm_ok("Guard Captain", "Sundown to dawn, no exceptions.")),
        json.dumps(_gm_ok("Tavern Runner", "Word is the patrol never came back from the east road.")),
    ]
    mock_gpt_chain(replies)
    turns = [
        "Begin.",
        "Guard Captain, what are the curfew hours?",
        "Runner, what rumor are you selling?",
    ]
    snaps, payloads = _run_transcript_with_payloads(tmp_path, monkeypatch, turns, chat_fn=chat)

    _assert_social_turn(
        snaps[1],
        payloads[1],
        expected_target="guard_captain",
        allowed_sources=("explicit_target", "spoken_vocative", "vocative"),
        interlocutor="guard_captain",
        snaps=snaps,
        payloads=payloads,
    )
    _assert_social_turn(
        snaps[2],
        payloads[2],
        expected_target="tavern_runner",
        allowed_sources=("explicit_target", "spoken_vocative", "vocative", "generic_role"),
        interlocutor="tavern_runner",
        snaps=snaps,
        payloads=payloads,
    )


def test_generic_stranger_does_not_fall_back_to_guard(tmp_path, monkeypatch, mock_gpt_chain):
    replies = [
        json.dumps(_gm_ok("Guard Captain", "Stay alert; we have orders.")),
        json.dumps(_gm_ok("Ragged stranger", "I only know what the crowd mutters.")),
    ]
    mock_gpt_chain(replies)
    turns = [
        "Begin.",
        "Guard Captain, any word on the gate wait?",
        "Stranger, heard anything about the missing patrol?",
    ]
    snaps, payloads = _run_transcript_with_payloads(tmp_path, monkeypatch, turns, chat_fn=chat)

    _assert_social_turn(
        snaps[2],
        payloads[2],
        expected_target="refugee",
        allowed_sources=("explicit_target", "spoken_vocative", "vocative", "generic_role"),
        interlocutor_not="guard_captain",
        snaps=snaps,
        payloads=payloads,
    )
    assert snaps[2].get("social_resolution", {}).get("npc_id") != "guard_captain"
    # Transcript quirk: scene_actor-only targets may clear session current_interlocutor while
    # resolution.social still binds the correct addressee — do not require interlocutor == refugee.


def test_explicit_address_never_gets_wiped_by_later_validation(tmp_path, monkeypatch):
    """Explicit bind: response payload must keep resolution.social target fields (see also unit emission test)."""

    idx = {"n": 0}

    def call_gpt(_messages: list[dict[str, str]]) -> dict[str, Any]:
        i = idx["n"]
        idx["n"] += 1
        if i == 0:
            return _gm_opening()
        # Bad candidate: upstream retry/npc-contract may rewrite visible text; payload resolution must keep target.
        return {
            "player_facing_text": "For a breath, the scene holds still while the guard studies you.",
            "tags": [],
            "scene_update": None,
            "activate_scene_id": None,
            "new_scene_draft": None,
            "world_updates": None,
            "suggested_action": None,
            "debug_notes": "test_illegal_social_candidate",
        }

    _patch_call_gpt(monkeypatch, call_gpt)
    turns = [
        "Begin.",
        "Guard Captain, where was the patrol last seen?",
    ]
    snaps, payloads = _run_transcript_with_payloads(tmp_path, monkeypatch, turns, chat_fn=chat)

    soc = payloads[1].get("resolution", {}).get("social", {})
    try:
        assert soc.get("npc_id") == "guard_captain", soc
        assert soc.get("target_source") in ("explicit_target", "spoken_vocative", "vocative"), soc
        assert soc.get("target_resolved") is True, soc
        assert snaps[1].get("current_interlocutor") == "guard_captain"
        assert latest_target_not_null_after_bind(snaps[1], payloads[1])
    except AssertionError:
        _fail_transcript("explicit bind + emission fallback metadata check failed", snaps, payloads)


def test_generic_stranger_unresolved_clean_when_not_authored(tmp_path, monkeypatch):
    """If no stranger actor exists, resolution must not attribute the line to guard via continuity."""

    def call_gpt(_messages: list[dict[str, str]]) -> dict[str, Any]:
        # Only used for Begin + guard line + fallback narrator line
        if not hasattr(call_gpt, "_i"):
            call_gpt._i = 0  # type: ignore[attr-defined]
        i = call_gpt._i  # type: ignore[attr-defined]
        call_gpt._i = i + 1  # type: ignore[attr-defined]
        if i == 0:
            return _gm_opening()
        if i == 1:
            return _gm_ok("Guard Captain", "Move along when you can.")
        return _gm_ok("The crowd", "No one meets your eye.")

    _patch_call_gpt(monkeypatch, call_gpt)

    patch_transcript_storage(monkeypatch, tmp_path)
    write_default_bootstrap_scenes()
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")

    base = default_scene("frontier_gate")
    scene = copy.deepcopy(base)
    addr = scene.get("scene", {}).get("addressables")
    assert isinstance(addr, list)
    scene["scene"]["addressables"] = [a for a in addr if isinstance(a, dict) and a.get("id") != "refugee"]
    path = storage.scene_path("frontier_gate")
    storage._save_json(path, scene)

    turns = [
        "Begin.",
        "Guard Captain, is the queue slow today?",
        # Avoid "you" in the clause: pronoun continuation can otherwise snap to the prior interlocutor
        # when no stranger actor exists (find_addressed_npc_id_for_turn).
        "Stranger, heard anything about the missing patrol?",
    ]
    snaps, payloads = _run_transcript_with_payloads(tmp_path, monkeypatch, turns, chat_fn=chat)

    soc = snaps[2].get("social_resolution") if isinstance(snaps[2].get("social_resolution"), dict) else {}
    try:
        assert soc.get("npc_id") != "guard_captain"
        assert soc.get("target_resolved") is not True
        assert soc.get("target_source") in (None, "", "none") or soc.get("target_source") == "none"
    except AssertionError:
        _fail_transcript("unresolved stranger branch failed", snaps, payloads)

    src = str(soc.get("target_source") or "").strip().lower()
    assert src != "continuity", soc
