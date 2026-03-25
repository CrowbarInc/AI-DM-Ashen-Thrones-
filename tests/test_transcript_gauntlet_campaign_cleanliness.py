"""Transcript gauntlet: new campaigns do not inherit prior interlocutor, journal, scene runtime, or social targets."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Callable

import pytest

from game import storage
from game.api import chat
from game.campaign_reset import apply_new_campaign_hard_reset
from game.campaign_state import create_fresh_session_document
from game.defaults import default_scene, default_world
from game.journal import build_player_journal
from game.models import ChatRequest
from tests.helpers.transcript_runner import (
    latest_target_id,
    patch_transcript_storage,
    snapshot_from_chat_payload,
    write_default_bootstrap_scenes,
)


def _gm_ok(speaker: str, line: str, **extra: Any) -> dict[str, Any]:
    base = {
        "player_facing_text": f'{speaker} nods. "{line}"',
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    base.update(extra)
    return base


def _gm_opening() -> dict[str, Any]:
    return _gm_ok("The rain", "The gate crowd presses in; voices and wagon wheels fill the mud.")


def _patch_call_gpt(monkeypatch: Any, fn: Callable[..., dict[str, Any]]) -> None:
    monkeypatch.setattr("game.api.call_gpt", fn)


def _install_gpt_two_campaigns(
    monkeypatch: Any,
    replies_campaign_a: list[dict[str, Any]],
    replies_campaign_b: list[dict[str, Any]],
) -> Callable[[], None]:
    """Opening + *replies_campaign_a*; after ``switch_to_b()``, opening + *replies_campaign_b*."""

    phase = {"name": "a", "idx": 0}
    sequence_a = [_gm_opening(), *replies_campaign_a]
    sequence_b = [_gm_opening(), *replies_campaign_b]

    def call_gpt(_messages: list[dict[str, str]]) -> dict[str, Any]:
        seq = sequence_a if phase["name"] == "a" else sequence_b
        i = phase["idx"]
        phase["idx"] = i + 1
        if i < len(seq):
            return seq[i]
        return _gm_ok("Someone", "I hear you.")

    _patch_call_gpt(monkeypatch, call_gpt)

    def switch_to_b() -> None:
        phase["name"] = "b"
        phase["idx"] = 0

    return switch_to_b


def _setup_frontier_with_notice_interactable(tmp_path: Path, monkeypatch: Any) -> None:
    patch_transcript_storage(monkeypatch, tmp_path)
    write_default_bootstrap_scenes()
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")
    fg = copy.deepcopy(default_scene("frontier_gate"))
    scene = fg.setdefault("scene", {})
    clues = scene.setdefault("discoverable_clues", [])
    clues.append(
        {
            "id": "gauntlet_notice_clue",
            "text": "GAUNTLET_JOURNAL_CLUE_LINE notice-board detail only for cleanliness test.",
        }
    )
    scene["interactables"] = [
        {
            "id": "notice_board",
            "type": "investigate",
            "reveals_clue": "gauntlet_notice_clue",
        }
    ]
    storage._save_json(storage.scene_path("frontier_gate"), fg)


def _run_chat_turns(turns: list[str]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i, t in enumerate(turns):
        p = chat(ChatRequest(text=t))
        if not isinstance(p, dict):
            raise TypeError("chat must return dict")
        out.append(p)
    return out


def _expected_baseline_journal() -> dict[str, Any]:
    sess = create_fresh_session_document()
    world = default_world()
    env = default_scene("frontier_gate")
    return build_player_journal(sess, world, env)


def _assert_session_social_baseline(
    sess: dict[str, Any], *, label: str, require_empty_scene_runtime: bool = False
) -> None:
    ic = sess.get("interaction_context") if isinstance(sess.get("interaction_context"), dict) else {}
    ss = sess.get("scene_state") if isinstance(sess.get("scene_state"), dict) else {}
    sr = sess.get("scene_runtime")
    ck = sess.get("clue_knowledge")
    assert str(ic.get("active_interaction_target_id") or "").strip() == "", f"{label}: active_interaction_target_id"
    assert str(ic.get("active_interaction_kind") or "").strip() == "", f"{label}: active_interaction_kind"
    assert str(ic.get("interaction_mode") or "").strip().lower() == "none", f"{label}: interaction_mode"
    assert ss.get("current_interlocutor") in (None, ""), f"{label}: current_interlocutor"
    if require_empty_scene_runtime:
        assert sr == {}, f"{label}: scene_runtime {sr!r}"
    assert ck in ({}, None) or ck == {}, f"{label}: clue_knowledge"


def test_new_campaign_has_no_prior_interlocutor(tmp_path: Path, monkeypatch: Any) -> None:
    patch_transcript_storage(monkeypatch, tmp_path)
    write_default_bootstrap_scenes()
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")

    switch_to_b = _install_gpt_two_campaigns(
        monkeypatch,
        replies_campaign_a=[
            _gm_ok("Guard Captain", "Posted taxes, curfew, missing patrol."),
            _gm_ok("Tavern Runner", "Stew costs coin; rumors cost more."),
            _gm_ok("Ragged stranger", "The crowd mutters when guards look away."),
        ],
        replies_campaign_b=[],
    )

    apply_new_campaign_hard_reset()
    turns_a = [
        "Begin.",
        "Guard Captain, what is on the notice board?",
        "Runner, how much for the stew?",
        "Stranger, heard anything useful?",
    ]
    payloads_a = _run_chat_turns(turns_a)
    snap_guard_a = snapshot_from_chat_payload(1, turns_a[1], payloads_a[1])
    soc_guard = (
        payloads_a[1].get("resolution", {}).get("social") if isinstance(payloads_a[1].get("resolution"), dict) else {}
    )
    assert soc_guard.get("npc_id") == "guard_captain", "campaign A should bind guard on explicit address turn"
    assert latest_target_id(snap_guard_a) == "guard_captain"

    apply_new_campaign_hard_reset()
    _assert_session_social_baseline(
        storage.load_session(), label="campaign B immediately after hard reset", require_empty_scene_runtime=True
    )
    switch_to_b()
    turns_b = ["Begin."]
    payloads_b = _run_chat_turns(turns_b)
    sess_b = payloads_b[0].get("session") if isinstance(payloads_b[0].get("session"), dict) else {}
    _assert_session_social_baseline(sess_b, label="campaign B after Begin (social layer only)")

    snap_b0 = snapshot_from_chat_payload(0, turns_b[0], payloads_b[0])
    assert snap_b0.get("current_interlocutor") in (None, "")
    assert not str((snap_b0.get("interaction_context") or {}).get("active_interaction_target_id") or "").strip()
    res = payloads_b[0].get("resolution")
    soc = res.get("social") if isinstance(res, dict) else None
    assert not isinstance(soc, dict) or not str(soc.get("npc_id") or "").strip(), res


def test_new_campaign_has_clean_journal_seed_only(tmp_path: Path, monkeypatch: Any) -> None:
    _setup_frontier_with_notice_interactable(tmp_path, monkeypatch)
    switch_to_b = _install_gpt_two_campaigns(
        monkeypatch,
        replies_campaign_a=[
            _gm_ok("Guard Captain", "Crowd noise rises; a clerk updates the board."),
            _gm_ok("The notice board", "Names and dates blur in the rain; one line stands out."),
        ],
        replies_campaign_b=[],
    )

    apply_new_campaign_hard_reset()
    turns_a = [
        "Begin.",
        "Guard Captain, is the board current?",
        "Investigate the notice board.",
    ]
    payloads_a = _run_chat_turns(turns_a)
    j_a = payloads_a[-1].get("journal") if isinstance(payloads_a[-1].get("journal"), dict) else {}
    clues_a = j_a.get("discovered_clues") if isinstance(j_a.get("discovered_clues"), list) else []
    joined_clues = " ".join(str(c) for c in clues_a)
    assert "GAUNTLET_JOURNAL_CLUE_LINE" in joined_clues, "campaign A should discover structured clue via investigate"

    apply_new_campaign_hard_reset()
    _assert_session_social_baseline(
        storage.load_session(), label="journal test post-reset pre-Begin", require_empty_scene_runtime=True
    )
    switch_to_b()
    payloads_b = _run_chat_turns(["Begin."])
    j_b = payloads_b[0].get("journal") if isinstance(payloads_b[0].get("journal"), dict) else {}
    expected = _expected_baseline_journal()

    assert j_b.get("known_facts") == expected["known_facts"], (j_b.get("known_facts"), expected["known_facts"])
    assert j_b.get("discovered_clues") in ([],), j_b.get("discovered_clues")
    assert j_b.get("unresolved_leads") in ([],), j_b.get("unresolved_leads")
    assert j_b.get("projects") == [], j_b.get("projects")
    blob_b = json.dumps(j_b, default=str)
    assert "GAUNTLET_JOURNAL_CLUE_LINE" not in blob_b
    for ev in j_b.get("recent_events") or []:
        assert "GAUNTLET_JOURNAL_CLUE_LINE" not in json.dumps(ev, default=str)


def test_new_campaign_scene_bootstrap_is_clean(tmp_path: Path, monkeypatch: Any) -> None:
    patch_transcript_storage(monkeypatch, tmp_path)
    write_default_bootstrap_scenes()
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")

    # Narration without scene_momentum tags increments momentum_exchanges_since each turn.
    switch_to_b = _install_gpt_two_campaigns(
        monkeypatch,
        replies_campaign_a=[
            _gm_ok("Guard Captain", "Curfew is strict."),
            _gm_ok("Tavern Runner", "Rumors come dear."),
            _gm_ok("Guard Captain", "Move when called."),
            _gm_ok("Tavern Runner", "East road whispers return."),
        ],
        replies_campaign_b=[],
    )

    apply_new_campaign_hard_reset()
    turns_a = [
        "Begin.",
        "Guard Captain, state the curfew.",
        "Runner, sell me a rumor.",
        "Guard Captain, hold the line.",
        "Runner, any word on the road?",
    ]
    _run_chat_turns(turns_a)
    s_a = storage.load_session()
    rt_a = s_a.get("scene_runtime") if isinstance(s_a.get("scene_runtime"), dict) else {}
    fg_a = rt_a.get("frontier_gate") if isinstance(rt_a.get("frontier_gate"), dict) else {}
    has_runtime_residue = bool(fg_a) and (
        fg_a.get("last_description_hash")
        or int(fg_a.get("momentum_exchanges_since") or 0) > 0
        or (fg_a.get("discovered_clues") and len(fg_a.get("discovered_clues") or []) > 0)
        or (fg_a.get("topic_pressure") and len(fg_a.get("topic_pressure") or {}) > 0)
    )
    assert has_runtime_residue, f"campaign A should mutate scene_runtime: {fg_a!r}"

    apply_new_campaign_hard_reset()
    assert storage.load_session().get("scene_runtime") == {}
    switch_to_b()
    payloads_b = _run_chat_turns(["Begin."])
    s_b = payloads_b[0].get("session") if isinstance(payloads_b[0].get("session"), dict) else {}
    rt_b = s_b.get("scene_runtime") if isinstance(s_b.get("scene_runtime"), dict) else {}
    fg_b = rt_b.get("frontier_gate") if isinstance(rt_b.get("frontier_gate"), dict) else {}
    assert "A patrol went missing near the old milestone." not in (fg_b.get("discovered_clues") or [])
    assert "Hot stew and rumors for coin." not in (fg_b.get("discovered_clues") or [])

    scene_payload = payloads_b[0].get("scene") if isinstance(payloads_b[0].get("scene"), dict) else {}
    inner = scene_payload.get("scene") if isinstance(scene_payload.get("scene"), dict) else {}
    template = default_scene("frontier_gate")["scene"]
    assert inner.get("visible_facts") == template.get("visible_facts")
    assert inner.get("journal_seed_facts") == template.get("journal_seed_facts")
    ss_b = s_b.get("scene_state") if isinstance(s_b.get("scene_state"), dict) else {}
    assert ss_b.get("active_scene_id") == "frontier_gate"


def test_explicit_target_in_campaign_a_does_not_influence_campaign_b(tmp_path: Path, monkeypatch: Any) -> None:
    patch_transcript_storage(monkeypatch, tmp_path)
    write_default_bootstrap_scenes()
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")

    switch_to_b = _install_gpt_two_campaigns(
        monkeypatch,
        replies_campaign_a=[
            _gm_ok("Guard Captain", "Patrol routes are not for strangers."),
            _gm_ok("Guard Captain", "East gate, dawn shift—remember that."),
        ],
        replies_campaign_b=[
            _gm_ok("Tavern Runner", "Stew is hot; rumors are hotter."),
        ],
    )

    apply_new_campaign_hard_reset()
    payloads_a = _run_chat_turns(
        [
            "Begin.",
            "Guard Captain, who may pass?",
            "What about the dawn watch?",
        ]
    )
    soc_a = payloads_a[-1].get("resolution", {}).get("social") if isinstance(payloads_a[-1].get("resolution"), dict) else {}
    assert soc_a.get("npc_id") == "guard_captain", soc_a

    apply_new_campaign_hard_reset()
    switch_to_b()
    payloads_b = _run_chat_turns(
        [
            "Begin.",
            "Runner, what are you selling today?",
        ]
    )
    soc_b = payloads_b[-1].get("resolution", {}).get("social") if isinstance(payloads_b[-1].get("resolution"), dict) else {}
    assert soc_b.get("npc_id") == "tavern_runner", soc_b
    assert soc_b.get("target_source") in ("explicit_target", "vocative"), soc_b
    assert soc_b.get("npc_id") != "guard_captain", soc_b

    snap_b = snapshot_from_chat_payload(1, "Runner, what are you selling today?", payloads_b[-1])
    assert snap_b.get("current_interlocutor") == "tavern_runner"
    assert snap_b.get("social_resolution", {}).get("npc_id") == "tavern_runner"
