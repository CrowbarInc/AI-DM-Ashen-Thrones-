"""Transcript gauntlet: campaign boundaries, persisted scene/journal reset, and lead→travel sequencing.

Single-turn social routing, minimum-actionable-lead helpers, and declared-switch behavior are covered
elsewhere (``test_social_target_authority_regressions``, ``test_social_lead_landing``,
``test_directed_social_routing``, ``test_turn_pipeline_shared``). This module keeps **multi-turn**
chat transcripts that would be awkward to express as isolated unit tests.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Callable

import pytest

from game import storage
from game.affordances import _affordance_passes_conditions
from game.api import chat
from game.campaign_reset import apply_new_campaign_hard_reset
from game.campaign_state import create_fresh_session_document
from game.defaults import default_scene, default_world
from game.journal import build_player_journal
from game.models import ChatRequest
from game.storage import get_world_flag
from game.utils import slugify
from tests.helpers.transcript_runner import (
    compact_snapshot_summary,
    format_turn_debug,
    latest_target_id,
    latest_target_source,
    patch_transcript_storage,
    snapshot_from_chat_payload,
    write_default_bootstrap_scenes,
)

pytestmark = [pytest.mark.transcript, pytest.mark.slow]

LEAD_CLUE_ID = "lead_gauntlet_missing_patrol"
LEAD_TEXT_MARKER = "GAUNTLET_LEAD_MISSING_PATROL"
CONSEQUENCE_FLAG_KEY = "patrol_route_known"


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
    for t in turns:
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


def _setup_frontier_patrol_lead_scene(tmp_path: Path, monkeypatch: Any) -> None:
    patch_transcript_storage(monkeypatch, tmp_path)
    write_default_bootstrap_scenes()
    path = storage.scene_path("old_milestone")
    if not path.exists():
        storage._save_json(path, default_scene("old_milestone"))
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")

    fg = copy.deepcopy(default_scene("frontier_gate"))
    scene = fg.setdefault("scene", {})
    clues = scene.setdefault("discoverable_clues", [])
    clues.append(
        {
            "id": LEAD_CLUE_ID,
            "text": f"{LEAD_TEXT_MARKER} The posted warning names the east road and the old milestone as the patrol's last known direction.",
        }
    )
    scene["interactables"] = [
        {
            "id": "notice_board",
            "type": "investigate",
            "reveals_clue": LEAD_CLUE_ID,
        }
    ]
    for ex in scene.get("exits") or []:
        if isinstance(ex, dict) and (ex.get("target_scene_id") or "").strip() == "old_milestone":
            ex["conditions"] = {"requires_clues": [LEAD_CLUE_ID]}
            ex["world_updates_on_transition"] = {"set_flags": {CONSEQUENCE_FLAG_KEY: True}}
            break
    storage._save_json(storage.scene_path("frontier_gate"), fg)


def _patrol_exit_action_template(scene_envelope: dict[str, Any]) -> dict[str, Any] | None:
    scene = scene_envelope.get("scene") if isinstance(scene_envelope.get("scene"), dict) else {}
    for ex in scene.get("exits") or []:
        if not isinstance(ex, dict):
            continue
        if (ex.get("target_scene_id") or "").strip() != "old_milestone":
            continue
        label = str(ex.get("label") or "Travel").strip() or "Travel"
        short_label = label if len(label) <= 44 else label[:41] + "..."

        return {
            "id": slugify(f"Leave for {short_label}") or "leave",
            "label": f"Leave for {short_label}",
            "type": "scene_transition",
            "prompt": f"I leave for {label}.",
            "targetSceneId": "old_milestone",
            "conditions": ex.get("conditions") if isinstance(ex.get("conditions"), dict) else {},
        }
    return None


def _collect_clue_markers(session: dict[str, Any]) -> dict[str, Any]:
    ck = session.get("clue_knowledge") if isinstance(session.get("clue_knowledge"), dict) else {}
    clue_ids = sorted(ck.keys()) if isinstance(ck, dict) else []
    runtime_ids: list[str] = []
    rt = session.get("scene_runtime") if isinstance(session.get("scene_runtime"), dict) else {}
    for _sid, blob in rt.items():
        if isinstance(blob, dict):
            for cid in blob.get("discovered_clue_ids") or []:
                if isinstance(cid, str) and cid.strip():
                    runtime_ids.append(cid.strip())
    return {"clue_knowledge_ids": clue_ids, "runtime_discovered_clue_ids": sorted(set(runtime_ids))}


def _journal_blob(journal: Any) -> str:
    return json.dumps(journal, default=str) if journal is not None else ""


def _fail_report(msg: str, turns: list[str], payloads: list[dict[str, Any]]) -> None:
    lines = [msg, "", "transcript_turns:", json.dumps(turns, indent=2), ""]
    sid_row = []
    tgt_row = []
    for i, pl in enumerate(payloads):
        snap = snapshot_from_chat_payload(i, turns[i] if i < len(turns) else "", pl)
        sid_row.append(snap.get("scene_id"))
        tgt_row.append({"id": latest_target_id(snap), "source": latest_target_source(snap)})
    lines.append(f"scene_ids_by_turn: {json.dumps(sid_row, default=str)}")
    lines.append(f"target_ids_by_turn: {json.dumps(tgt_row, default=str)}")
    lines.append("")
    lines.append("per_turn:")
    graph = storage.load_active_scene()
    world = storage.load_world()
    for i, pl in enumerate(payloads):
        snap = snapshot_from_chat_payload(i, turns[i] if i < len(turns) else "", pl)
        lines.append(f"--- turn {i} ---")
        lines.append(compact_snapshot_summary(snap))
        lines.append(format_turn_debug(snap))
        sess = pl.get("session") if isinstance(pl.get("session"), dict) else {}
        lines.append(f"  clue_markers: {json.dumps(_collect_clue_markers(sess), default=str)}")
        j = pl.get("journal") if isinstance(pl.get("journal"), dict) else {}
        lines.append(
            f"  journal_summary: known_facts={len(j.get('known_facts') or [])} "
            f"clues={len(j.get('discovered_clues') or [])} leads={len(j.get('unresolved_leads') or [])}"
        )
        lines.append(f"  journal_tail_blob: {_journal_blob(j)[-400:]}")
        ev = (pl.get("world") or {}).get("event_log") if isinstance(pl.get("world"), dict) else []
        if isinstance(ev, list):
            lines.append(f"  event_log_tail: {json.dumps(ev[-5:], default=str)}")
    lines.append("")
    lines.append(f"storage_session_markers: {json.dumps(_collect_clue_markers(storage.load_session()), default=str)}")
    lines.append(f"world_flag {CONSEQUENCE_FLAG_KEY!r}: {get_world_flag(world, CONSEQUENCE_FLAG_KEY)!r}")
    lines.append(f"active_scene_id: {graph.get('scene', {}).get('id')!r}")
    pytest.fail("\n".join(lines))


def test_new_campaign_clears_social_then_runner_turn_rebinds(tmp_path: Path, monkeypatch: Any) -> None:
    """After hard reset, no stale interlocutor; a fresh explicit Runner address must bind tavern_runner (not prior guard)."""
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
        replies_campaign_b=[_gm_ok("Tavern Runner", "Stew is hot; rumors are hotter.")],
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
    turns_b = ["Begin.", "Runner, what are you selling today?"]
    payloads_b = _run_chat_turns(turns_b)
    _assert_session_social_baseline(
        payloads_b[0].get("session") if isinstance(payloads_b[0].get("session"), dict) else {},
        label="campaign B after Begin (social layer only)",
    )
    snap_b0 = snapshot_from_chat_payload(0, turns_b[0], payloads_b[0])
    assert snap_b0.get("current_interlocutor") in (None, "")
    res0 = payloads_b[0].get("resolution")
    soc0 = res0.get("social") if isinstance(res0, dict) else None
    assert not isinstance(soc0, dict) or not str(soc0.get("npc_id") or "").strip(), res0

    soc_b = payloads_b[1].get("resolution", {}).get("social") if isinstance(payloads_b[1].get("resolution"), dict) else {}
    assert soc_b.get("npc_id") == "tavern_runner", soc_b
    assert soc_b.get("target_source") in ("explicit_target", "spoken_vocative", "vocative"), soc_b
    assert soc_b.get("npc_id") != "guard_captain", soc_b
    snap_b1 = snapshot_from_chat_payload(1, turns_b[1], payloads_b[1])
    assert snap_b1.get("current_interlocutor") == "tavern_runner"
    assert snap_b1.get("social_resolution", {}).get("npc_id") == "tavern_runner"


def test_new_campaign_resets_journal_scene_runtime_and_template(tmp_path: Path, monkeypatch: Any) -> None:
    """One prior campaign dirties journal + frontier_gate runtime; after reset, Begin. yields seed-only journal and clean runtime."""
    _setup_frontier_with_notice_interactable(tmp_path, monkeypatch)
    switch_to_b = _install_gpt_two_campaigns(
        monkeypatch,
        replies_campaign_a=[
            _gm_ok("Guard Captain", "Crowd noise rises; a clerk updates the board."),
            _gm_ok("The notice board", "Names and dates blur in the rain; one line stands out."),
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
        "Guard Captain, is the board current?",
        "Investigate the notice board.",
        "Guard Captain, state the curfew.",
        "Runner, sell me a rumor.",
        "Guard Captain, hold the line.",
        "Runner, any word on the road?",
    ]
    payloads_a = _run_chat_turns(turns_a)
    j_a = payloads_a[2].get("journal") if isinstance(payloads_a[2].get("journal"), dict) else {}
    clues_a = j_a.get("discovered_clues") if isinstance(j_a.get("discovered_clues"), list) else []
    assert "GAUNTLET_JOURNAL_CLUE_LINE" in " ".join(str(c) for c in clues_a)

    s_a = storage.load_session()
    rt_a = s_a.get("scene_runtime") if isinstance(s_a.get("scene_runtime"), dict) else {}
    fg_a = rt_a.get("frontier_gate") if isinstance(rt_a.get("frontier_gate"), dict) else {}
    assert bool(fg_a) and (
        fg_a.get("last_description_hash")
        or int(fg_a.get("momentum_exchanges_since") or 0) > 0
        or (fg_a.get("discovered_clues") and len(fg_a.get("discovered_clues") or []) > 0)
        or (fg_a.get("topic_pressure") and len(fg_a.get("topic_pressure") or {}) > 0)
    ), f"campaign A should mutate scene_runtime: {fg_a!r}"

    apply_new_campaign_hard_reset()
    _assert_session_social_baseline(
        storage.load_session(), label="post-reset pre-Begin", require_empty_scene_runtime=True
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

    s_b = payloads_b[0].get("session") if isinstance(payloads_b[0].get("session"), dict) else {}
    rt_b = s_b.get("scene_runtime") if isinstance(s_b.get("scene_runtime"), dict) else {}
    fg_b = rt_b.get("frontier_gate") if isinstance(rt_b.get("frontier_gate"), dict) else {}
    assert (fg_b.get("discovered_clues") or []) == []
    assert (fg_b.get("discovered_clue_ids") or []) == []

    scene_payload = payloads_b[0].get("scene") if isinstance(payloads_b[0].get("scene"), dict) else {}
    inner = scene_payload.get("scene") if isinstance(scene_payload.get("scene"), dict) else {}
    template = default_scene("frontier_gate")["scene"]
    assert inner.get("visible_facts") == template.get("visible_facts")
    assert inner.get("journal_seed_facts") == template.get("journal_seed_facts")
    ss_b = s_b.get("scene_state") if isinstance(s_b.get("scene_state"), dict) else {}
    assert ss_b.get("active_scene_id") == "frontier_gate"


def test_transcript_lead_unlocks_travel_scene_and_world_flag_then_reset_clears(tmp_path: Path, monkeypatch: Any) -> None:
    """Sequencing: clue gates exit → follow affordance → milestone + flag; new campaign does not inherit structured lead."""
    _setup_frontier_patrol_lead_scene(tmp_path, monkeypatch)

    idx = {"n": 0}
    filler = _gm_ok("The world", "Rain, ink, and road-mud; the fiction advances without stalling.")

    def call_gpt(_messages: list[dict[str, str]]) -> dict[str, Any]:
        i = idx["n"]
        idx["n"] += 1
        if i == 0:
            return _gm_ok(
                "The rain",
                "The gate crowd presses in; the notice board gleams wet in the torchlight.",
            )
        return filler

    _patch_call_gpt(monkeypatch, call_gpt)

    apply_new_campaign_hard_reset()
    storage.activate_scene("frontier_gate")

    turns = [
        "Begin.",
        "Investigate the notice board.",
        "I follow the missing patrol rumor.",
    ]
    payloads: list[dict[str, Any]] = []
    snaps: list[dict[str, Any]] = []

    frontier_env = storage.load_scene("frontier_gate")
    tpl0 = _patrol_exit_action_template(frontier_env)
    assert tpl0 is not None
    assert not _affordance_passes_conditions(
        tpl0, "frontier_gate", storage.load_session(), storage.load_world()
    ), "patrol exit should stay gated before the lead is discovered"

    for t in turns:
        pl = chat(ChatRequest(text=t))
        payloads.append(pl)
        snaps.append(snapshot_from_chat_payload(len(snaps), t, pl))

    sess_after_lead = payloads[1].get("session") if isinstance(payloads[1].get("session"), dict) else {}
    markers = _collect_clue_markers(sess_after_lead)
    j1 = payloads[1].get("journal") if isinstance(payloads[1].get("journal"), dict) else {}
    journal_hits_lead = LEAD_TEXT_MARKER in _journal_blob(j1)
    event_log = (payloads[1].get("world") or {}).get("event_log") if isinstance(payloads[1].get("world"), dict) else []
    event_hits = isinstance(event_log, list) and LEAD_TEXT_MARKER.lower() in json.dumps(event_log, default=str).lower()

    lead_surfaced = (
        LEAD_CLUE_ID in markers["clue_knowledge_ids"]
        or LEAD_CLUE_ID in markers["runtime_discovered_clue_ids"]
        or journal_hits_lead
        or event_hits
    )
    try:
        assert lead_surfaced
    except AssertionError as e:
        _fail_report(str(e), turns, payloads)

    tpl1 = _patrol_exit_action_template(storage.load_scene("frontier_gate"))
    try:
        assert tpl1 is not None
        assert _affordance_passes_conditions(tpl1, "frontier_gate", sess_after_lead, payloads[1].get("world") or {})
    except AssertionError as e:
        _fail_report(str(e), turns, payloads)

    final_pl = payloads[-1]
    scene_inner = (final_pl.get("scene") or {}).get("scene") if isinstance(final_pl.get("scene"), dict) else {}
    world_final = final_pl.get("world") if isinstance(final_pl.get("world"), dict) else {}
    try:
        assert scene_inner.get("id") == "old_milestone"
        assert scene_inner.get("mode") == "exploration"
        assert get_world_flag(world_final, CONSEQUENCE_FLAG_KEY) is True
    except AssertionError as e:
        _fail_report(str(e), turns, payloads)

    j_final = final_pl.get("journal") if isinstance(final_pl.get("journal"), dict) else {}
    try:
        assert LEAD_TEXT_MARKER in _journal_blob(j_final)
    except AssertionError as e:
        _fail_report(str(e), turns, payloads)

    apply_new_campaign_hard_reset()
    storage.activate_scene("frontier_gate")
    idx["n"] = 0
    fresh_pl = chat(ChatRequest(text="Begin."))
    sess_new = fresh_pl.get("session") if isinstance(fresh_pl.get("session"), dict) else {}
    world_new = fresh_pl.get("world") if isinstance(fresh_pl.get("world"), dict) else {}
    env_new = fresh_pl.get("scene") if isinstance(fresh_pl.get("scene"), dict) else {}
    baseline = build_player_journal(sess_new, world_new, env_new)
    try:
        assert LEAD_CLUE_ID not in _collect_clue_markers(sess_new)["clue_knowledge_ids"]
        assert get_world_flag(world_new, CONSEQUENCE_FLAG_KEY) is not True
        assert LEAD_TEXT_MARKER not in json.dumps(baseline, default=str)
    except AssertionError as e:
        _fail_report(
            str(e),
            turns + ["Begin."],
            payloads + [fresh_pl],
        )

    assert all(s.get("scene_id") for s in snaps)
