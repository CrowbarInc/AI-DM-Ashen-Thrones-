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
from game.clues import _social_resolution_carries_information
from game.defaults import default_scene
from game.journal import build_player_journal
from game.models import ChatRequest
from game.storage import get_npc_runtime, get_scene_runtime, get_world_flag
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


def _bootstrap_scene_if_missing(scene_id: str) -> None:
    path = storage.scene_path(scene_id)
    if not path.exists():
        storage._save_json(path, default_scene(scene_id))


def _pending_leads_snapshot(session: dict[str, Any], scene_id: str) -> list[dict[str, Any]]:
    rt = get_scene_runtime(session, scene_id)
    raw = rt.get("pending_leads") or []
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for p in raw:
        if isinstance(p, dict):
            out.append(
                {
                    "clue_id": p.get("clue_id"),
                    "leads_to_scene": p.get("leads_to_scene"),
                    "leads_to_npc": p.get("leads_to_npc"),
                }
            )
    return out


def _lead_ids_from_clue_knowledge(session: dict[str, Any]) -> list[str]:
    ck = session.get("clue_knowledge") if isinstance(session.get("clue_knowledge"), dict) else {}
    return sorted(str(k) for k in ck.keys() if isinstance(k, str) and k.strip())


def _event_log_len(world: dict[str, Any] | None) -> int:
    if not isinstance(world, dict):
        return 0
    ev = world.get("event_log")
    return len(ev) if isinstance(ev, list) else 0


def _ltc_compact_failure(msg: str, turns: list[str], payloads: list[dict[str, Any]]) -> str:
    """Compact transcript-debug block (structural fields only)."""
    lines = [msg, "", "player_lines:", json.dumps(turns, indent=2), ""]
    prev_ev = 0
    prev_scene: str | None = None
    for i, pl in enumerate(payloads):
        snap = snapshot_from_chat_payload(i, turns[i] if i < len(turns) else "", pl)
        sess = pl.get("session") if isinstance(pl.get("session"), dict) else {}
        world = pl.get("world") if isinstance(pl.get("world"), dict) else {}
        evn = _event_log_len(world)
        scene_after = snap.get("scene_id")
        lines.append(f"--- turn {i} ---")
        lines.append(f"  player_text: {turns[i]!r}" if i < len(turns) else f"  player_text: <missing>")
        lines.append(f"  scene_after: {scene_after!r}  (scene_before_turn: {prev_scene!r})")
        lines.append(
            f"  routed_target: id={latest_target_id(snap)!r} source={latest_target_source(snap)!r} "
            f"interlocutor={snap.get('current_interlocutor')!r}"
        )
        lines.append(f"  lead_ids (clue_knowledge): {_lead_ids_from_clue_knowledge(sess)}")
        lines.append(f"  pending_leads[frontier_gate]: {json.dumps(_pending_leads_snapshot(sess, 'frontier_gate'), default=str)}")
        lines.append(f"  event_log_delta: {evn - prev_ev} (total {evn})")
        if isinstance(world.get("event_log"), list):
            tail = world["event_log"][-3:]
            lines.append(f"  event_log_tail: {json.dumps(tail, default=str)}")
        res = pl.get("resolution") if isinstance(pl.get("resolution"), dict) else {}
        soc = res.get("social") if isinstance(res.get("social"), dict) else {}
        esc = soc.get("social_escalation") if isinstance(soc.get("social_escalation"), dict) else {}
        if esc:
            lines.append(f"  social_escalation: {json.dumps({k: esc.get(k) for k in ('escalation_level', 'force_actionable_lead', 'force_partial_answer', 'add_suspicion')}, default=str)}")
        nsc = ((res.get("metadata") or {}).get("narration_state_consistency") or {}) if isinstance(res.get("metadata"), dict) else {}
        if nsc:
            lines.append(f"  narration_state_consistency: {json.dumps(nsc, default=str)}")
        prev_ev = evn
        prev_scene = str(scene_after) if scene_after else prev_scene
    return "\n".join(lines)


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


def test_frontier_gate_social_lead_becomes_actionable_and_pursuable(tmp_path: Path, monkeypatch: Any) -> None:
    """E2E: social lead at frontier_gate → structured pending/clue/affordance → travel → scene changes."""
    _setup_frontier_social_verevin_topic(tmp_path, monkeypatch)
    _bootstrap_scene_if_missing("old_milestone")

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
        "I follow the missing patrol rumor.",
    ]
    payloads: list[dict[str, Any]] = []
    for t in turns:
        payloads.append(chat(ChatRequest(text=t)))

    try:
        sess_mid = payloads[1].get("session") if isinstance(payloads[1].get("session"), dict) else {}
        markers = _collect_clue_markers(sess_mid)
        fg_pending = _pending_leads_snapshot(sess_mid, "frontier_gate")
        world1 = payloads[1].get("world") if isinstance(payloads[1].get("world"), dict) else {}
        ui1 = payloads[1].get("ui") if isinstance(payloads[1].get("ui"), dict) else {}
        afford = ui1.get("affordances") if isinstance(ui1.get("affordances"), list) else []
        travel_ids = [
            str(a.get("targetSceneId") or a.get("target_scene_id") or "").strip()
            for a in afford
            if isinstance(a, dict) and str(a.get("type") or "").strip().lower() in ("scene_transition", "travel")
        ]

        lead_structured = (
            SOCIAL_VEREVIN_CLUE_ID in markers["clue_knowledge_ids"]
            or SOCIAL_VEREVIN_CLUE_ID in markers["runtime_discovered_clue_ids"]
        )
        pending_ok = any(
            isinstance(p, dict)
            and p.get("clue_id") == SOCIAL_VEREVIN_CLUE_ID
            and p.get("leads_to_scene") == "old_milestone"
            for p in fg_pending
        )
        ev1 = world1.get("event_log") if isinstance(world1.get("event_log"), list) else []
        event_ok = any(
            isinstance(e, dict)
            and e.get("type") == "social_lead_revealed"
            and e.get("clue_id") == SOCIAL_VEREVIN_CLUE_ID
            for e in ev1
        )
        afford_ok = "old_milestone" in travel_ids

        assert lead_structured and (pending_ok or afford_ok or event_ok), (
            f"expected social lead surface: lead_structured={lead_structured} pending={fg_pending!r} "
            f"travel_targets={travel_ids!r} event_ok={event_ok}"
        )

        final = payloads[-1]
        scene_inner = (final.get("scene") or {}).get("scene") if isinstance(final.get("scene"), dict) else {}
        assert scene_inner.get("id") == "old_milestone", _ltc_compact_failure(
            "expected travel to old_milestone after social lead", turns, payloads
        )
    except AssertionError as e:
        pytest.fail(_ltc_compact_failure(str(e), turns, payloads))


def test_transcript_frontier_gate_social_flavor_triggers_minimum_actionable_lead_debug(tmp_path: Path, monkeypatch: Any) -> None:
    """LtC: opening social success without narration travel hooks still yields pending + action-debug fields."""
    patch_transcript_storage(monkeypatch, tmp_path)
    write_default_bootstrap_scenes()
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")

    idx = {"n": 0}
    filler = _gm_ok("The runner", "The runner ladles thick stew and counts coins without meeting your eyes.")

    def call_gpt(_messages: list[dict[str, str]]) -> dict[str, Any]:
        i = idx["n"]
        idx["n"] += 1
        if i == 0:
            return _gm_opening()
        return filler

    _patch_call_gpt(monkeypatch, call_gpt)

    apply_new_campaign_hard_reset()
    storage.activate_scene("frontier_gate")

    chat(ChatRequest(text="Begin."))
    pl = chat(ChatRequest(text="Ask the tavern runner about the hot stew."))

    dbg = pl.get("debug") if isinstance(pl.get("debug"), dict) else {}
    sess = pl.get("session") if isinstance(pl.get("session"), dict) else {}
    rt = get_scene_runtime(sess, "frontier_gate")
    pending = rt.get("pending_leads") or []
    has_actionable = any(
        isinstance(p, dict)
        and (
            str(p.get("leads_to_scene") or "").strip()
            or str(p.get("leads_to_npc") or "").strip()
            or str(p.get("leads_to_rumor") or "").strip()
        )
        for p in pending
    )

    assert has_actionable, f"expected at least one actionable pending lead, got {pending!r}"
    assert "minimum_actionable_lead_enforced" in dbg, dbg
    if dbg.get("minimum_actionable_lead_enforced") is True:
        assert dbg.get("enforced_lead_id")
        assert dbg.get("enforced_lead_source") in ("discoverable_clue", "exit", "extracted_social")


def test_repeated_social_probe_does_not_stall_indefinitely(tmp_path: Path, monkeypatch: Any) -> None:
    """Repeated questions on an exhausted topic must surface escalation cost/redirect or partial progress flags."""
    patch_transcript_storage(monkeypatch, tmp_path)
    write_default_bootstrap_scenes()
    _bootstrap_scene_if_missing("old_milestone")
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")

    # Strict social-exchange validation needs a speaker-grounded first sentence plus answer-shaped dialogue.
    guard_line = (
        'The Guard Captain keeps his voice flat. "I have told you what I know about the missing patrol."'
    )
    idx = {"n": 0}

    def call_gpt(_messages: list[dict[str, str]]) -> dict[str, Any]:
        i = idx["n"]
        idx["n"] += 1
        if i == 0:
            return _gm_opening()
        return {
            "player_facing_text": guard_line,
            "tags": ["scene_momentum:new_information"],
            "scene_update": None,
            "activate_scene_id": None,
            "new_scene_draft": None,
            "world_updates": None,
            "suggested_action": None,
            "debug_notes": "",
        }

    _patch_call_gpt(monkeypatch, call_gpt)

    apply_new_campaign_hard_reset()
    storage.activate_scene("frontier_gate")

    turns = ["Begin.", "Guard Captain, what happened to the missing patrol?"] + [
        "What about the missing patrol?"
    ] * 5
    payloads: list[dict[str, Any]] = []
    for t in turns:
        payloads.append(chat(ChatRequest(text=t)))

    def _signals_ok(pl: dict[str, Any]) -> bool:
        res = pl.get("resolution") if isinstance(pl.get("resolution"), dict) else {}
        gm = pl.get("gm_output") if isinstance(pl.get("gm_output"), dict) else {}
        sess = pl.get("session") if isinstance(pl.get("session"), dict) else {}
        tags = [str(x).lower() for x in (gm.get("tags") or []) if isinstance(x, str)]
        soc = res.get("social") if isinstance(res.get("social"), dict) else {}
        esc = soc.get("social_escalation") if isinstance(soc.get("social_escalation"), dict) else {}
        if int(esc.get("escalation_level") or 0) >= 2 and (
            esc.get("force_actionable_lead")
            or esc.get("force_partial_answer")
            or esc.get("add_suspicion")
            or esc.get("convert_refusal_to_conditioned_offer")
        ):
            return True
        if any("topic_pressure" in t for t in tags):
            return True
        sus = int(get_npc_runtime(sess, "guard_captain").get("suspicion") or 0)
        if sus >= 1:
            return True
        if _social_resolution_carries_information(res):
            return True
        nsc = ((res.get("metadata") or {}).get("narration_state_consistency") or {}) if isinstance(res.get("metadata"), dict) else {}
        if nsc.get("narration_state_mismatch_detected") and nsc.get("mismatch_repair_applied") not in (None, "", "none"):
            return True
        return False

    try:
        assert any(_signals_ok(pl) for pl in payloads[2:]), (
            "expected escalation, suspicion, topic_pressure retry, state repair, or informational resolution"
        )
    except AssertionError as e:
        pytest.fail(_ltc_compact_failure(str(e), turns, payloads))


def test_social_output_with_new_hook_cannot_remain_no_new_information(tmp_path: Path, monkeypatch: Any) -> None:
    """Transcript: engine 'no new info' hint + narration with investigatory hooks → resolution repaired structurally."""
    patch_transcript_storage(monkeypatch, tmp_path)
    write_default_bootstrap_scenes()
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")

    reveal_line = (
        'The Guard Captain taps the notice board. "The missing patrol was last sent toward the old milestone."'
    )
    hook_line = (
        'The Guard Captain lowers his voice. "I cannot say more here—ask around the old trading crossroads."'
    )
    idx = {"n": 0}

    def call_gpt(_messages: list[dict[str, str]]) -> dict[str, Any]:
        i = idx["n"]
        idx["n"] += 1
        if i == 0:
            return _gm_opening()
        if i == 1:
            return {
                "player_facing_text": reveal_line,
                "tags": ["scene_momentum:new_information"],
                "scene_update": None,
                "activate_scene_id": None,
                "new_scene_draft": None,
                "world_updates": None,
                "suggested_action": None,
                "debug_notes": "",
            }
        return {
            "player_facing_text": hook_line,
            "tags": ["scene_momentum:new_information"],
            "scene_update": None,
            "activate_scene_id": None,
            "new_scene_draft": None,
            "world_updates": None,
            "suggested_action": None,
            "debug_notes": "",
        }

    _patch_call_gpt(monkeypatch, call_gpt)

    apply_new_campaign_hard_reset()
    storage.activate_scene("frontier_gate")

    turns = [
        "Begin.",
        "Guard Captain, what happened to the missing patrol?",
        "What about the missing patrol?",
    ]
    payloads: list[dict[str, Any]] = []
    for t in turns:
        payloads.append(chat(ChatRequest(text=t)))

    res = payloads[-1].get("resolution") if isinstance(payloads[-1].get("resolution"), dict) else {}
    try:
        low_hint = str(res.get("hint") or "").lower()
        assert "no new information was revealed" not in low_hint
        assert _social_resolution_carries_information(res)
        nsc = ((res.get("metadata") or {}).get("narration_state_consistency") or {}) if isinstance(res.get("metadata"), dict) else {}
        assert nsc.get("narration_state_mismatch_detected") is True
        assert nsc.get("mismatch_repair_applied") not in (None, "", "none")
    except AssertionError as e:
        pytest.fail(_ltc_compact_failure(str(e), turns, payloads))


def test_transcript_hail_runner_then_declared_switch_to_refugee(tmp_path: Path, monkeypatch: Any) -> None:
    """Hail tavern_runner, establish social continuity, then declared-action switch must bind refugee."""
    patch_transcript_storage(monkeypatch, tmp_path)
    write_default_bootstrap_scenes()
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")

    opening = {
        "player_facing_text": 'Rain hammers the gate stones. "Keep the line moving."',
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }

    idx = {"n": 0}

    def call_gpt(_messages: list[dict[str, str]]) -> dict[str, Any]:
        i = idx["n"]
        idx["n"] += 1
        if i == 0:
            return opening
        return {
            "player_facing_text": f'Someone meets your eyes. "Reply {i}."',
            "tags": [],
            "scene_update": None,
            "activate_scene_id": None,
            "new_scene_draft": None,
            "world_updates": None,
            "suggested_action": None,
            "debug_notes": "",
        }

    monkeypatch.setattr("game.api.call_gpt", call_gpt)
    monkeypatch.setattr("game.api.parse_social_intent", lambda *_a, **_k: None)
    monkeypatch.setattr("game.api.parse_exploration_intent", lambda *_a, **_k: None)
    monkeypatch.setattr("game.api.parse_intent", lambda *_a, **_k: None)

    apply_new_campaign_hard_reset()
    storage.activate_scene("frontier_gate")

    turns = [
        "Begin.",
        "Hey there, tavern runner — what's the latest rumor?",
        'Galinor turns to speak with a nearby refugee. "Do you know anything about the old milestone?"',
    ]
    payloads = [chat(ChatRequest(text=t)) for t in turns]

    res = payloads[-1].get("resolution") if isinstance(payloads[-1], dict) else {}
    soc = res.get("social") if isinstance(res.get("social"), dict) else {}
    # Dialogue-first may stamp explicit_target on the normalized action while declared switch still
    # chose refugee over tavern_runner continuity — the regression is wrong npc_id, not label on source.
    assert soc.get("npc_id") == "refugee", soc
    assert soc.get("npc_id") != "tavern_runner"
    assert soc.get("declared_switch_detected") is True
    assert soc.get("declared_switch_target_actor_id") == "refugee"
    assert soc.get("continuity_overridden_by_declared_switch") is True

    snap = snapshot_from_chat_payload(2, turns[-1], payloads[-1])
    assert latest_target_id(snap) == "refugee"


def test_transcript_hail_runner_switch_refugee_then_alright_runner_rebinds_tavern_runner(
    tmp_path: Path, monkeypatch: Any
) -> None:
    """After declared switch to refugee, a softened 'Runner' vocative must override continuity."""
    patch_transcript_storage(monkeypatch, tmp_path)
    write_default_bootstrap_scenes()
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")

    opening = {
        "player_facing_text": 'Rain hammers the gate stones. "Keep the line moving."',
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    idx = {"n": 0}

    def call_gpt(_messages: list[dict[str, str]]) -> dict[str, Any]:
        i = idx["n"]
        idx["n"] += 1
        if i == 0:
            return opening
        return {
            "player_facing_text": f'Someone meets your eyes. "Reply {i}."',
            "tags": [],
            "scene_update": None,
            "activate_scene_id": None,
            "new_scene_draft": None,
            "world_updates": None,
            "suggested_action": None,
            "debug_notes": "",
        }

    monkeypatch.setattr("game.api.call_gpt", call_gpt)
    monkeypatch.setattr("game.api.parse_social_intent", lambda *_a, **_k: None)
    monkeypatch.setattr("game.api.parse_exploration_intent", lambda *_a, **_k: None)
    monkeypatch.setattr("game.api.parse_intent", lambda *_a, **_k: None)

    apply_new_campaign_hard_reset()
    storage.activate_scene("frontier_gate")

    turns = [
        "Begin.",
        "Hey there, tavern runner — what's the latest rumor?",
        'Galinor turns to speak with a nearby refugee. "Do you know anything about the old milestone?"',
        "Alright Runner, you've piqued my interest—tell me about the patrol rumor.",
    ]
    payloads = [chat(ChatRequest(text=t)) for t in turns]

    res = payloads[-1].get("resolution") if isinstance(payloads[-1], dict) else {}
    soc = res.get("social") if isinstance(res.get("social"), dict) else {}
    assert soc.get("npc_id") == "tavern_runner", soc
    assert soc.get("npc_id") != "refugee"
    assert soc.get("continuity_overridden_by_spoken_vocative") is True

    snap = snapshot_from_chat_payload(3, turns[-1], payloads[-1])
    assert latest_target_id(snap) == "tavern_runner"
