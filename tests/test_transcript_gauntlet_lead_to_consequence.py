"""Transcript gauntlet: lead surfaces from observation, gates a travel affordance, then persists consequences.

Uses the frontier_gate → old_milestone patrol thread with minimal extra scene data (test-local JSON),
mirroring :mod:`tests.test_transcript_gauntlet_campaign_cleanliness`.
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
from game.defaults import default_scene
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

# Stable markers (structure / ids / substrings — not full prose).
LEAD_CLUE_ID = "lead_gauntlet_missing_patrol"
LEAD_TEXT_MARKER = "GAUNTLET_LEAD_MISSING_PATROL"
CONSEQUENCE_FLAG_KEY = "patrol_route_known"

# Social transcript slice: NPC topic → structured clue / pending lead / event / journal.
SOCIAL_VEREVIN_CLUE_ID = "gauntlet_social_house_verevin"
SOCIAL_VEREVIN_MARKER = "GAUNTLET_SOCIAL_VEREVIN_LEAD"


def _gm_ok(speaker: str, line: str) -> dict[str, Any]:
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
    return _gm_ok("The rain", "The gate crowd presses in; the notice board gleams wet in the torchlight.")


def _patch_call_gpt(monkeypatch: Any, fn: Callable[..., dict[str, Any]]) -> None:
    monkeypatch.setattr("game.api.call_gpt", fn)


def _setup_frontier_social_verevin_topic(tmp_path: Path, monkeypatch: Any) -> None:
    """Frontier gate + tavern_runner topic (House Verevin / crossroads style) for social lead landing."""
    patch_transcript_storage(monkeypatch, tmp_path)
    write_default_bootstrap_scenes()
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def _seed_world_runner_verevin_topic() -> None:
    world = storage.load_world()
    npcs = world.setdefault("npcs", [])
    if not isinstance(npcs, list):
        return
    for npc in npcs:
        if isinstance(npc, dict) and str(npc.get("id") or "").strip() == "tavern_runner":
            npc["topics"] = [
                {
                    "id": "verevin_stronghold",
                    "text": (
                        f"{SOCIAL_VEREVIN_MARKER} House Verevin keeps a walled manor past the old trading crossroads—"
                        "same line travelers use toward the milestone."
                    ),
                    "clue_id": SOCIAL_VEREVIN_CLUE_ID,
                    "leads_to_scene": "old_milestone",
                }
            ]
            break
    storage.save_world(world)


def _setup_frontier_patrol_lead_scene(tmp_path: Path, monkeypatch: Any) -> None:
    patch_transcript_storage(monkeypatch, tmp_path)
    write_default_bootstrap_scenes()
    for sid in ("old_milestone",):
        path = storage.scene_path(sid)
        if not path.exists():
            storage._save_json(path, default_scene(sid))
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
            # default_scene("frontier_gate") omits this; shipped JSON has it — restore for consequence assertion.
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
        lines.append(f"  journal_summary: known_facts={len(j.get('known_facts') or [])} clues={len(j.get('discovered_clues') or [])} leads={len(j.get('unresolved_leads') or [])}")
        lines.append(f"  journal_tail_blob: {_journal_blob(j)[-400:]}")
        ev = (pl.get("world") or {}).get("event_log") if isinstance(pl.get("world"), dict) else []
        if isinstance(ev, list):
            lines.append(f"  event_log_tail: {json.dumps(ev[-5:], default=str)}")
    lines.append("")
    lines.append(f"storage_session_markers: {json.dumps(_collect_clue_markers(storage.load_session()), default=str)}")
    lines.append(f"world_flag {CONSEQUENCE_FLAG_KEY!r}: {get_world_flag(world, CONSEQUENCE_FLAG_KEY)!r}")
    lines.append(f"active_scene_id: {graph.get('scene', {}).get('id')!r}")
    pytest.fail("\n".join(lines))


def test_transcript_lead_surfaces_actionable_travel_and_persists_consequence(tmp_path: Path, monkeypatch: Any) -> None:
    """Full slice: clean campaign → read notice (structured clue) → gated travel unlocks → milestone + flag → reset is clean."""
    _setup_frontier_patrol_lead_scene(tmp_path, monkeypatch)

    idx = {"n": 0}
    # Opening turn uses i==0; later turns may invoke GPT multiple times (retries) — use one safe line for all post-opening.
    filler = _gm_ok("The world", "Rain, ink, and road-mud; the fiction advances without stalling.")

    def call_gpt(_messages: list[dict[str, str]]) -> dict[str, Any]:
        i = idx["n"]
        idx["n"] += 1
        if i == 0:
            return _gm_opening()
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

    # --- A: Lead surfaced (structured) ---
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

    # --- B: Lead is actionable (condition layer; see note on MAX_RETURNED_AFFORDANCES vs exits) ---
    tpl1 = _patrol_exit_action_template(storage.load_scene("frontier_gate"))
    try:
        assert tpl1 is not None
        assert _affordance_passes_conditions(tpl1, "frontier_gate", sess_after_lead, payloads[1].get("world") or {})
    except AssertionError as e:
        _fail_report(str(e), turns, payloads)

    # --- C: Consequence (scene + world flag from exit world_updates_on_transition) ---
    final_pl = payloads[-1]
    scene_inner = (final_pl.get("scene") or {}).get("scene") if isinstance(final_pl.get("scene"), dict) else {}
    world_final = final_pl.get("world") if isinstance(final_pl.get("world"), dict) else {}
    try:
        assert scene_inner.get("id") == "old_milestone"
        assert scene_inner.get("mode") == "exploration"
        assert get_world_flag(world_final, CONSEQUENCE_FLAG_KEY) is True
    except AssertionError as e:
        _fail_report(str(e), turns, payloads)

    # --- D: Persistence lands; new campaign does not inherit ---
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

    # Smoke: transcript harness fields remain usable for debugging regressions.
    assert all(s.get("scene_id") for s in snaps)


def test_transcript_social_reveal_lands_structured_markers_and_survives_followup(tmp_path: Path, monkeypatch: Any) -> None:
    """After NPC reveals Verevin/crossroads-style info, structured state + journal/event; follow-up turn keeps clue id."""
    _setup_frontier_social_verevin_topic(tmp_path, monkeypatch)

    idx = {"n": 0}
    filler = _gm_ok("The world", "Rain drums the cobbles; the gate crowd shifts.")

    def call_gpt(_messages: list[dict[str, str]]) -> dict[str, Any]:
        i = idx["n"]
        idx["n"] += 1
        if i == 0:
            return _gm_opening()
        return filler

    _patch_call_gpt(monkeypatch, call_gpt)

    apply_new_campaign_hard_reset()
    _seed_world_runner_verevin_topic()
    storage.activate_scene("frontier_gate")

    turns = [
        "Begin.",
        "Ask the tavern runner about House Verevin.",
        "Where can I find their stronghold?",
    ]
    payloads: list[dict[str, Any]] = []

    for t in turns:
        payloads.append(chat(ChatRequest(text=t)))

    sess1 = payloads[1].get("session") if isinstance(payloads[1].get("session"), dict) else {}
    markers = _collect_clue_markers(sess1)
    j1 = payloads[1].get("journal") if isinstance(payloads[1].get("journal"), dict) else {}
    world1 = payloads[1].get("world") if isinstance(payloads[1].get("world"), dict) else {}
    ev1 = world1.get("event_log") if isinstance(world1.get("event_log"), list) else []

    structured_ok = (
        SOCIAL_VEREVIN_CLUE_ID in markers["clue_knowledge_ids"]
        or SOCIAL_VEREVIN_CLUE_ID in markers["runtime_discovered_clue_ids"]
    )
    journal_ok = SOCIAL_VEREVIN_MARKER in _journal_blob(j1)
    event_ok = any(
        isinstance(e, dict)
        and e.get("type") == "social_lead_revealed"
        and e.get("clue_id") == SOCIAL_VEREVIN_CLUE_ID
        for e in ev1
    )
    rt1 = sess1.get("scene_runtime") if isinstance(sess1.get("scene_runtime"), dict) else {}
    fg_rt = rt1.get("frontier_gate") if isinstance(rt1.get("frontier_gate"), dict) else {}
    pending = fg_rt.get("pending_leads") if isinstance(fg_rt.get("pending_leads"), list) else []
    pending_ok = any(
        isinstance(p, dict) and p.get("clue_id") == SOCIAL_VEREVIN_CLUE_ID and p.get("leads_to_scene") == "old_milestone"
        for p in pending
    )

    assert structured_ok and journal_ok and event_ok and pending_ok, (
        f"markers={markers!r} journal_blob_has_marker={journal_ok} event_ok={event_ok} pending_ok={pending_ok}"
    )

    social_events = [
        e
        for e in (world1.get("event_log") or [])
        if isinstance(e, dict)
        and e.get("type") == "social_lead_revealed"
        and e.get("clue_id") == SOCIAL_VEREVIN_CLUE_ID
    ]
    assert len(social_events) == 1

    # Follow-up: clue remains in saved session (no reliance on prose-only memory).
    sess2 = payloads[2].get("session") if isinstance(payloads[2].get("session"), dict) else {}
    markers2 = _collect_clue_markers(sess2)
    assert SOCIAL_VEREVIN_CLUE_ID in markers2["clue_knowledge_ids"] or SOCIAL_VEREVIN_CLUE_ID in markers2["runtime_discovered_clue_ids"]

    stored = storage.load_session()
    markers_disk = _collect_clue_markers(stored)
    assert SOCIAL_VEREVIN_CLUE_ID in markers_disk["clue_knowledge_ids"] or SOCIAL_VEREVIN_CLUE_ID in markers_disk["runtime_discovered_clue_ids"]
