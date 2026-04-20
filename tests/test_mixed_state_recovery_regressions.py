"""Recovery regressions: mixed old/new routing paths (transcript + authority collisions).

Failure blocks intentionally echo the fields needed when manual runs disagree with CI.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import pytest

from game import storage
from game.api import chat
from game.campaign_reset import apply_new_campaign_hard_reset
from game.clues import _social_resolution_carries_information
from game.defaults import default_session
from game.gm import _is_placeholder_only_player_facing_text
from game.interaction_context import (
    apply_conservative_emergent_enrollment_from_gm_output,
    canonical_scene_addressable_roster,
    rebuild_active_scene_entities,
    resolve_authoritative_social_target,
)
from game.models import ChatRequest
from game.storage import get_npc_runtime, get_scene_runtime
from tests.debug_trace_utils import latest_compact_debug_trace_entry
from tests.helpers.transcript_runner import (
    latest_target_id,
    latest_target_source,
    patch_transcript_storage,
    snapshot_from_chat_payload,
    write_default_bootstrap_scenes,
)

pytestmark = [
    pytest.mark.integration,
    pytest.mark.regression,
    pytest.mark.transcript,
    pytest.mark.slow,
]

_GM_OK_MARKER = "MIXED_STATE_GM_OK"


def _gm_ok(speaker: str, line: str) -> dict[str, Any]:
    return {
        "player_facing_text": f'{speaker} says, "{line}"',
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }


def _gm_opening_gate() -> dict[str, Any]:
    return _gm_ok(
        "The gate",
        "Rain hammers the cobbles; torches hiss; the queue shuffles forward under bored watch.",
    )


def _patch_call_gpt(monkeypatch: Any, fn: Callable[..., dict[str, Any]]) -> None:
    monkeypatch.setattr("game.api.call_gpt", fn)


def _lead_ids_from_clue_knowledge(session: dict[str, Any]) -> list[str]:
    ck = session.get("clue_knowledge") if isinstance(session.get("clue_knowledge"), dict) else {}
    return sorted(str(k) for k in ck.keys() if isinstance(k, str) and k.strip())


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
                    "leads_to_rumor": p.get("leads_to_rumor"),
                }
            )
    return out


def _last_debug_trace(session: dict[str, Any]) -> dict[str, Any]:
    dt = session.get("debug_traces") if isinstance(session.get("debug_traces"), list) else []
    return latest_compact_debug_trace_entry(dt)


def _mixed_state_failure_block(
    msg: str,
    *,
    failing_turn: int,
    turns: list[str],
    payloads: list[dict[str, Any]],
    scene_id_for_pending: str = "frontier_gate",
) -> str:
    lines = [msg, ""]
    if failing_turn < 0 or failing_turn >= len(payloads):
        lines.append(f"(invalid failing_turn={failing_turn}; payloads={len(payloads)})")
        lines.append(f"player_lines: {json.dumps(turns, indent=2)}")
        return "\n".join(lines)

    pl = payloads[failing_turn]
    player_line = turns[failing_turn] if failing_turn < len(turns) else ""
    sess = pl.get("session") if isinstance(pl.get("session"), dict) else {}
    trace = _last_debug_trace(sess)
    res = pl.get("resolution") if isinstance(pl.get("resolution"), dict) else {}
    meta = res.get("metadata") if isinstance(res.get("metadata"), dict) else {}
    nsc = meta.get("narration_state_consistency") if isinstance(meta.get("narration_state_consistency"), dict) else {}
    snap = snapshot_from_chat_payload(failing_turn, player_line, pl)
    dbg = pl.get("debug") if isinstance(pl.get("debug"), dict) else {}
    soc = res.get("social") if isinstance(res.get("social"), dict) else {}

    lines.append(f"failing_turn_index: {failing_turn}")
    lines.append(f"player_line: {player_line!r}")
    lines.append(f"canonical_entry_path: {trace.get('canonical_entry_path')!r}")
    lines.append(f"canonical_entry_reason: {trace.get('canonical_entry_reason')!r}")
    lines.append(f"canonical_entry_target_actor_id: {trace.get('canonical_entry_target_actor_id')!r}")
    lines.append(f"target_actor (snapshot latest_target_id): {latest_target_id(snap)!r}")
    lines.append(f"target_actor_source: {latest_target_source(snap)!r}")
    lines.append(f"resolution.kind: {res.get('kind')!r}")
    lines.append(f"resolution.social.npc_id: {soc.get('npc_id')!r}")
    lines.append("reconciled_mismatch_flags:")
    lines.append(f"  narration_state_mismatch_detected: {nsc.get('narration_state_mismatch_detected')!r}")
    lines.append(f"  mismatch_repair_applied: {nsc.get('mismatch_repair_applied')!r}")
    lines.append(f"  mismatch_repairs_applied: {json.dumps(nsc.get('mismatch_repairs_applied'), default=str)}")
    lines.append(f"debug.narration_state_mismatch_detected: {dbg.get('narration_state_mismatch_detected')!r}")
    lines.append(f"debug.mismatch_repair_applied: {dbg.get('mismatch_repair_applied')!r}")
    lines.append(f"scene_before: {trace.get('scene_before')!r}")
    lines.append(f"scene_after: {trace.get('scene_after')!r}")
    lines.append(f"lead_ids (clue_knowledge): {_lead_ids_from_clue_knowledge(sess)}")
    lines.append(
        f"pending_leads[{scene_id_for_pending!r}]: "
        f"{json.dumps(_pending_leads_snapshot(sess, scene_id_for_pending), default=str)}"
    )
    lines.append("")
    lines.append("transcript_turns:")
    lines.append(json.dumps(turns, indent=2))
    return "\n".join(lines)


def _fail_mixed(
    msg: str,
    *,
    failing_turn: int,
    turns: list[str],
    payloads: list[dict[str, Any]],
) -> None:
    pytest.fail(_mixed_state_failure_block(msg, failing_turn=failing_turn, turns=turns, payloads=payloads))


def _setup_transcript_frontier(tmp_path: Path, monkeypatch: Any) -> None:
    patch_transcript_storage(monkeypatch, tmp_path)
    write_default_bootstrap_scenes()
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def _frontier_gate_context() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    session["scene_state"]["active_scene_id"] = "frontier_gate"
    world: dict[str, Any] = {"npcs": []}
    scene = storage.load_scene("frontier_gate")
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene)
    return session, world, scene


def test_approach_visible_figure_then_question_routes_social(tmp_path: Path, monkeypatch: Any) -> None:
    """Approach + ask in one turn must enter social for enrolled well-dressed watcher, not adjudication_query."""
    _setup_transcript_frontier(tmp_path, monkeypatch)

    opening = _gm_opening_gate()
    opening["player_facing_text"] = (
        "Rain hammers the cobbles. You notice a well-dressed watcher by the gate "
        "studying each newcomer's papers more than the ink."
    )
    idx = {"n": 0}

    def call_gpt(_messages: list[dict[str, str]]) -> dict[str, Any]:
        i = idx["n"]
        idx["n"] += 1
        if i == 0:
            return opening
        return _gm_ok("The watcher", _GM_OK_MARKER)

    _patch_call_gpt(monkeypatch, call_gpt)
    apply_new_campaign_hard_reset()
    storage.activate_scene("frontier_gate")

    turns = [
        "Begin.",
        (
            "I approach the well-dressed watcher and ask which noble house he is "
            "watching the gate for, and whether the missing patrol matters to his masters."
        ),
    ]
    payloads: list[dict[str, Any]] = []
    for t in turns:
        payloads.append(chat(ChatRequest(text=t)))

    pl = payloads[1]
    res = pl.get("resolution") if isinstance(pl.get("resolution"), dict) else {}
    try:
        assert res.get("kind") != "adjudication_query"
        assert res.get("kind") == "question"
        soc = res.get("social") if isinstance(res.get("social"), dict) else {}
        assert soc.get("social_intent_class") == "social_exchange"
        assert str(soc.get("npc_id") or "") == "emergent_well_dressed_watcher"
        sess = pl.get("session") if isinstance(pl.get("session"), dict) else {}
        trace = _last_debug_trace(sess)
        assert trace.get("canonical_entry_path") == "social"
    except AssertionError as e:
        _fail_mixed(str(e), failing_turn=1, turns=turns, payloads=payloads)


def test_emergent_addressable_persists_across_rebuild_cycle(monkeypatch: Any) -> None:
    """Narrated emergent actors must survive the active-scene rebuild path into the next roster."""
    session, world, scene = _frontier_gate_context()
    monkeypatch.setattr("game.storage.load_world", lambda: world)

    debug = apply_conservative_emergent_enrollment_from_gm_output(
        session=session,
        scene=scene,
        narration_text="Lord Ashvale studies you from the rain-slick steps, umbrella tilted like a crown.",
    )
    assert debug["emergent_actor_enrolled"] is True
    assert debug["emergent_actor_id"] == "emergent_lord_ashvale"

    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene)

    roster = canonical_scene_addressable_roster(
        world,
        "frontier_gate",
        scene_envelope=scene,
        session=session,
    )
    ids = {str(row.get("id") or "") for row in roster if isinstance(row, dict)}
    assert "emergent_lord_ashvale" in ids
    assert "emergent_lord_ashvale" in {
        str(raw) for raw in session["scene_state"].get("active_entities") or [] if isinstance(raw, str)
    }


def test_direct_vocative_resolves_to_seeded_emergent_addressable(monkeypatch: Any) -> None:
    """Authoritative social targeting must bind direct vocatives to in-scene emergent addressables."""
    session, world, scene = _frontier_gate_context()
    monkeypatch.setattr("game.storage.load_world", lambda: world)

    apply_conservative_emergent_enrollment_from_gm_output(
        session=session,
        scene=scene,
        narration_text="Lord Ashvale studies you from the rain-slick steps, umbrella tilted like a crown.",
    )
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene)

    auth = resolve_authoritative_social_target(
        session,
        world,
        "frontier_gate",
        player_text="Ashvale, answer plainly.",
        scene_envelope=scene,
        allow_first_roster_fallback=False,
    )

    assert auth.get("source") in ("vocative", "spoken_vocative"), auth
    assert auth.get("npc_id") == "emergent_lord_ashvale", auth
    assert auth.get("reason") not in ("no_addressable_target", "no addressable target resolved"), auth


def test_narration_only_emergent_continuity_survives_degraded_followup(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    """A narration-only introduction must stay socially targetable even when the follow-up GM turn degrades."""
    _setup_transcript_frontier(tmp_path, monkeypatch)

    idx = {"n": 0}

    def call_gpt(_messages: list[dict[str, str]]) -> dict[str, Any]:
        i = idx["n"]
        idx["n"] += 1
        if i == 0:
            return _gm_opening_gate()
        if i == 1:
            return {
                "player_facing_text": (
                    "Lord Ashvale studies you from the rain-slick steps, umbrella tilted like a crown."
                ),
                "tags": [],
                "scene_update": None,
                "activate_scene_id": None,
                "new_scene_draft": None,
                "world_updates": None,
                "suggested_action": None,
                "debug_notes": "",
            }
        return {
            "player_facing_text": (
                "I can't answer that. Based on what's established, we can determine very little here."
            ),
            "tags": [],
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
        "I take in the gate crowd and the banners.",
        "Lord Ashvale, answer plainly.",
    ]
    payloads: list[dict[str, Any]] = []
    payloads.append(chat(ChatRequest(text=turns[0])))
    with monkeypatch.context() as m:
        m.setattr("game.api.detect_retry_failures", lambda **kwargs: [])
        payloads.append(chat(ChatRequest(text=turns[1])))
    with monkeypatch.context() as m:
        m.setattr("game.gm.apply_social_exchange_retry_fallback_gm", lambda *a, **k: {})
        m.setattr("game.gm.minimal_social_emergency_fallback_line", lambda *_a, **_k: "")
        payloads.append(chat(ChatRequest(text=turns[2])))

    pl = payloads[2]
    res = pl.get("resolution") if isinstance(pl.get("resolution"), dict) else {}
    try:
        assert res.get("kind") != "adjudication_query"
        soc = res.get("social") if isinstance(res.get("social"), dict) else {}
        assert soc.get("social_intent_class") == "social_exchange"
        assert soc.get("npc_id") == "emergent_lord_ashvale"
        sess = pl.get("session") if isinstance(pl.get("session"), dict) else {}
        trace = _last_debug_trace(sess)
        assert trace.get("canonical_entry_path") == "social"
        assert trace.get("canonical_entry_reason") != "no_addressable_target"
    except AssertionError as e:
        _fail_mixed(str(e), failing_turn=2, turns=turns, payloads=payloads)


def test_emergent_vocative_repair_keeps_owner_under_dialogue_contract(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    """A degraded follow-up to an emergent actor must repair into owned dialogue, not generic filler."""
    _setup_transcript_frontier(tmp_path, monkeypatch)

    idx = {"n": 0}

    def call_gpt(_messages: list[dict[str, str]]) -> dict[str, Any]:
        i = idx["n"]
        idx["n"] += 1
        if i == 0:
            return _gm_opening_gate()
        if i == 1:
            return {
                "player_facing_text": (
                    "Lord Ashvale studies you from the rain-slick steps, umbrella tilted like a crown."
                ),
                "tags": [],
                "scene_update": None,
                "activate_scene_id": None,
                "new_scene_draft": None,
                "world_updates": None,
                "suggested_action": None,
                "debug_notes": "",
            }
        return {
            "player_facing_text": "For a breath, the scene holds while voices shift around you.",
            "tags": [],
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
        "I take in the gate crowd and the banners.",
        "Lord Ashvale, answer plainly.",
    ]
    payloads: list[dict[str, Any]] = []
    payloads.append(chat(ChatRequest(text=turns[0])))
    with monkeypatch.context() as m:
        m.setattr("game.api.detect_retry_failures", lambda **kwargs: [])
        payloads.append(chat(ChatRequest(text=turns[1])))
    payloads.append(chat(ChatRequest(text=turns[2])))

    pl = payloads[2]
    res = pl.get("resolution") if isinstance(pl.get("resolution"), dict) else {}
    gm = pl.get("gm_output") if isinstance(pl.get("gm_output"), dict) else {}
    meta = gm.get("_final_emission_meta") if isinstance(gm.get("_final_emission_meta"), dict) else {}
    try:
        assert res.get("kind") in {"question", "social_probe"}
        soc = res.get("social") if isinstance(res.get("social"), dict) else {}
        assert soc.get("social_intent_class") == "social_exchange"
        assert soc.get("npc_id") == "emergent_lord_ashvale"
        sess = pl.get("session") if isinstance(pl.get("session"), dict) else {}
        trace = _last_debug_trace(sess)
        assert trace.get("canonical_entry_path") == "social"
        text = str(gm.get("player_facing_text") or "")
        low = text.lower()
        assert "for a breath" not in low
        assert "scene holds" not in low
        assert "stands nearby" not in low
        assert "lord ashvale" in low
        assert not _is_placeholder_only_player_facing_text(text)
        assert meta.get("response_type_required") == "dialogue"
        assert meta.get("response_type_candidate_ok") is True
        assert meta.get("final_emitted_source") != "global_scene_fallback"
    except AssertionError as e:
        _fail_mixed(str(e), failing_turn=2, turns=turns, payloads=payloads)


def test_narrated_new_figure_can_be_addressed_next_turn(tmp_path: Path, monkeypatch: Any) -> None:
    """Narration introduces a titled figure; the following turn binds socially to that emergent id.

    When turn-3 narration hits the targeted-retry escape hatch with empty strict-social repair,
    continuity must still allow a vocative follow-up on turn 4 to bind to the same emergent id.
    """
    _setup_transcript_frontier(tmp_path, monkeypatch)

    idx = {"n": 0}

    def call_gpt(_messages: list[dict[str, str]]) -> dict[str, Any]:
        i = idx["n"]
        idx["n"] += 1
        if i == 0:
            return _gm_opening_gate()
        if i == 1:
            # Plain narration so emergent noble hint extraction can enroll Lord Ashvale (see test_emergent_scene_actors).
            return {
                "player_facing_text": (
                    "Lord Ashvale studies you from the rain-slick steps, umbrella tilted like a crown."
                ),
                "tags": [],
                "scene_update": None,
                "activate_scene_id": None,
                "new_scene_draft": None,
                "world_updates": None,
                "suggested_action": None,
                "debug_notes": "",
            }
        if 2 <= i <= 4:
            return {
                "player_facing_text": (
                    "I can't answer that. Based on what's established, we can determine very little here."
                ),
                "tags": [],
                "scene_update": None,
                "activate_scene_id": None,
                "new_scene_draft": None,
                "world_updates": None,
                "suggested_action": None,
                "debug_notes": "",
            }
        return _gm_ok("Lord Ashvale", _GM_OK_MARKER)

    _patch_call_gpt(monkeypatch, call_gpt)

    apply_new_campaign_hard_reset()
    storage.activate_scene("frontier_gate")

    turns = [
        "Begin.",
        "I take in the gate crowd and the banners.",
        "Lord Ashvale, are you here for the missing patrol or for me?",
        "Ashvale—one word: are the gates locked tonight?",
    ]
    payloads: list[dict[str, Any]] = []
    payloads.append(chat(ChatRequest(text=turns[0])))
    # Narration-only turn: disable targeted retries so scene_stall cannot replace GM text before emergent enrollment.
    with monkeypatch.context() as m:
        m.setattr("game.api.detect_retry_failures", lambda **kwargs: [])
        payloads.append(chat(ChatRequest(text=turns[1])))
    with monkeypatch.context() as m:
        m.setattr("game.gm.apply_social_exchange_retry_fallback_gm", lambda *a, **k: {})
        m.setattr("game.gm.minimal_social_emergency_fallback_line", lambda *_a, **_k: "")
        payloads.append(chat(ChatRequest(text=turns[2])))
    payloads.append(chat(ChatRequest(text=turns[3])))

    pl3 = payloads[2]
    res3 = pl3.get("resolution") if isinstance(pl3.get("resolution"), dict) else {}
    gm3 = pl3.get("gm_output") if isinstance(pl3.get("gm_output"), dict) else {}
    snap3 = snapshot_from_chat_payload(2, turns[2], pl3)
    try:
        if res3:
            assert res3.get("kind") == "question"
            assert res3.get("kind") != "adjudication_query"
            soc3 = res3.get("social") if isinstance(res3.get("social"), dict) else {}
            assert soc3.get("social_intent_class") == "social_exchange"
            nid3 = str(soc3.get("npc_id") or "")
        else:
            nid3 = str(latest_target_id(snap3) or "")
        assert nid3 == "emergent_lord_ashvale", f"unexpected npc_id={nid3!r}"
        sess3 = pl3.get("session") if isinstance(pl3.get("session"), dict) else {}
        trace3 = _last_debug_trace(sess3)
        assert trace3.get("canonical_entry_path") == "social"
        pft3 = str(gm3.get("player_facing_text") or "")
        assert pft3.strip()
        assert not _is_placeholder_only_player_facing_text(pft3)
    except AssertionError as e:
        _fail_mixed(str(e), failing_turn=2, turns=turns, payloads=payloads)

    pl4 = payloads[3]
    res4 = pl4.get("resolution") if isinstance(pl4.get("resolution"), dict) else {}
    snap4 = snapshot_from_chat_payload(3, turns[3], pl4)
    try:
        if res4:
            assert res4.get("kind") == "question"
            assert res4.get("kind") != "adjudication_query"
            soc4 = res4.get("social") if isinstance(res4.get("social"), dict) else {}
            assert soc4.get("social_intent_class") == "social_exchange"
            nid4 = str(soc4.get("npc_id") or "")
        else:
            nid4 = str(latest_target_id(snap4) or "")
        assert nid4 == "emergent_lord_ashvale", f"unexpected npc_id turn4={nid4!r}"
        sess4 = pl4.get("session") if isinstance(pl4.get("session"), dict) else {}
        trace4 = _last_debug_trace(sess4)
        assert trace4.get("canonical_entry_path") == "social"
    except AssertionError as e:
        _fail_mixed(str(e), failing_turn=3, turns=turns, payloads=payloads)


def test_social_text_with_hook_cannot_end_with_no_new_information_state(tmp_path: Path, monkeypatch: Any) -> None:
    """GM line contains an investigatory hook; structured hint/state must not stay 'no new information'."""
    _setup_transcript_frontier(tmp_path, monkeypatch)

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
            return _gm_opening_gate()
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

    pl = payloads[-1]
    res = pl.get("resolution") if isinstance(pl.get("resolution"), dict) else {}
    try:
        low_hint = str(res.get("hint") or "").lower()
        assert "no new information was revealed" not in low_hint
        assert _social_resolution_carries_information(res)
        meta = res.get("metadata") if isinstance(res.get("metadata"), dict) else {}
        nsc = meta.get("narration_state_consistency") if isinstance(meta.get("narration_state_consistency"), dict) else {}
        assert nsc.get("narration_state_mismatch_detected") is True
        assert nsc.get("mismatch_repair_applied") not in (None, "", "none")
    except AssertionError as e:
        _fail_mixed(str(e), failing_turn=len(payloads) - 1, turns=turns, payloads=payloads)


def _actionable_pending_or_lead(sess: dict[str, Any], scene_id: str) -> bool:
    for p in _pending_leads_snapshot(sess, scene_id):
        if any(
            str(p.get(k) or "").strip()
            for k in ("leads_to_scene", "leads_to_npc", "leads_to_rumor")
        ):
            return True
    return bool(_lead_ids_from_clue_knowledge(sess))


def test_frontier_gate_opening_social_success_produces_actionable_path(tmp_path: Path, monkeypatch: Any) -> None:
    """First substantive social question at the gate must leave an actionable pending lead or structured clue id."""
    _setup_transcript_frontier(tmp_path, monkeypatch)
    idx = {"n": 0}

    def call_gpt(_messages: list[dict[str, str]]) -> dict[str, Any]:
        i = idx["n"]
        idx["n"] += 1
        if i == 0:
            return _gm_opening_gate()
        return _gm_ok(
            "The captain",
            "The captain keeps his voice low. The east road and the old milestone are where the watch last sent them.",
        )

    _patch_call_gpt(monkeypatch, call_gpt)
    apply_new_campaign_hard_reset()
    storage.activate_scene("frontier_gate")

    turns = [
        "Begin.",
        "Guard Captain, where was the missing patrol last sent?",
    ]
    payloads: list[dict[str, Any]] = []
    for t in turns:
        payloads.append(chat(ChatRequest(text=t)))

    pl = payloads[1]
    sess = pl.get("session") if isinstance(pl.get("session"), dict) else {}
    ui = pl.get("ui") if isinstance(pl.get("ui"), dict) else {}
    afford = ui.get("affordances") if isinstance(ui.get("affordances"), list) else []
    travel_targets = [
        str(a.get("targetSceneId") or a.get("target_scene_id") or "").strip()
        for a in afford
        if isinstance(a, dict)
        and str(a.get("type") or "").strip().lower() in ("scene_transition", "travel")
    ]
    res = pl.get("resolution") if isinstance(pl.get("resolution"), dict) else {}
    try:
        assert res.get("kind") == "question"
        assert res.get("kind") != "adjudication_query"
        ok = _actionable_pending_or_lead(sess, "frontier_gate") or ("old_milestone" in travel_targets)
        assert ok, (
            f"expected pending actionable lead, clue_knowledge, or travel affordance to old_milestone; "
            f"travel_targets={travel_targets!r}"
        )
    except AssertionError as e:
        _fail_mixed(str(e), failing_turn=1, turns=turns, payloads=payloads)


def test_repeated_social_probe_progresses_or_costs(tmp_path: Path, monkeypatch: Any) -> None:
    """Same-topic probing must show escalation, suspicion, repair, or info within a bounded repeat window."""
    _setup_transcript_frontier(tmp_path, monkeypatch)
    guard_line = (
        'The Guard Captain keeps his voice flat. "I have told you what I know about the missing patrol."'
    )
    idx = {"n": 0}

    def call_gpt(_messages: list[dict[str, str]]) -> dict[str, Any]:
        i = idx["n"]
        idx["n"] += 1
        if i == 0:
            return _gm_opening_gate()
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

    max_repeats = 5
    turns = ["Begin.", "Guard Captain, what happened to the missing patrol?"] + [
        "What about the missing patrol?"
    ] * max_repeats
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
        nsc = (
            (res.get("metadata") or {}).get("narration_state_consistency") or {}
        ) if isinstance(res.get("metadata"), dict) else {}
        if nsc.get("narration_state_mismatch_detected") and nsc.get("mismatch_repair_applied") not in (
            None,
            "",
            "none",
        ):
            return True
        return False

    probe_payloads = payloads[2 : 2 + max_repeats]
    try:
        assert any(_signals_ok(pl) for pl in probe_payloads), (
            f"no progress/cost within {max_repeats} identical probes after initial question"
        )
    except AssertionError as e:
        _fail_mixed(str(e), failing_turn=len(payloads) - 1, turns=turns, payloads=payloads)


def test_generic_role_switch_to_active_guard_stays_social(tmp_path: Path, monkeypatch: Any) -> None:
    """With runner as active interlocutor, a new generic guard address must rebind to captain (not adjudication)."""
    _setup_transcript_frontier(tmp_path, monkeypatch)
    idx = {"n": 0}

    def call_gpt(_messages: list[dict[str, str]]) -> dict[str, Any]:
        i = idx["n"]
        idx["n"] += 1
        if i == 0:
            return _gm_opening_gate()
        if i == 1:
            return _gm_ok("The runner", "Stew's hot; coin buys a bowl and a whisper.")
        return _gm_ok("The captain", _GM_OK_MARKER)

    _patch_call_gpt(monkeypatch, call_gpt)
    apply_new_campaign_hard_reset()
    storage.activate_scene("frontier_gate")

    turns = [
        "Begin.",
        "Ask the tavern runner about the hot stew.",
        "Guard, what happened to the missing patrol?",
    ]
    payloads: list[dict[str, Any]] = []
    for t in turns:
        payloads.append(chat(ChatRequest(text=t)))

    pl = payloads[2]
    res = pl.get("resolution") if isinstance(pl.get("resolution"), dict) else {}
    try:
        assert res.get("kind") != "adjudication_query"
        assert res.get("kind") == "question"
        soc = res.get("social") if isinstance(res.get("social"), dict) else {}
        assert soc.get("social_intent_class") == "social_exchange"
        assert str(soc.get("npc_id") or "") == "guard_captain"
        sess = pl.get("session") if isinstance(pl.get("session"), dict) else {}
        trace = _last_debug_trace(sess)
        assert trace.get("canonical_entry_path") == "social"
    except AssertionError as e:
        _fail_mixed(str(e), failing_turn=2, turns=turns, payloads=payloads)


def test_retry_urgency_does_not_justify_forced_pathing() -> None:
    from game.gm import build_retry_prompt_for_failure

    p = build_retry_prompt_for_failure(
        {
            "failure_class": "topic_pressure_escalation",
            "topic_context": {"topic_key": "patrol", "previous_answer_snippet": "Unknown.", "repeat_count": 4},
        },
        response_policy=None,
        gm_output=None,
    ).lower()
    assert "forced pathing" in p
    assert "urgency sharpens salience" in p


def test_retry_salient_lead_optional_unless_exclusivity_contract() -> None:
    from game.anti_railroading import build_anti_railroading_contract
    from game.gm import build_retry_prompt_for_failure

    arc = build_anti_railroading_contract(resolution=None, player_text="Where next?")
    gm = {"anti_railroading_contract": arc}
    p = build_retry_prompt_for_failure(
        {"failure_class": "scene_stall"},
        response_policy=None,
        gm_output=gm,
    ).lower()
    assert "salient lead" in p or "mandatory path" in p


def test_retry_hard_constraint_can_remove_one_avenue_other_paths_remain() -> None:
    from game.gm import build_retry_prompt_for_failure

    p = build_retry_prompt_for_failure({"failure_class": "scene_stall"}, response_policy=None, gm_output=None).lower()
    assert "constraint" in p
    assert "others open" in p or "leaves others open" in p


def test_retry_guidance_compatible_with_explicit_commitment_exception() -> None:
    from game.gm import build_retry_prompt_for_failure

    arc = {
        "enabled": True,
        "forbid_player_decision_override": True,
        "forbid_forced_direction": True,
        "forbid_exclusive_path_claims_without_basis": True,
        "forbid_lead_to_plot_gravity_upgrade": True,
        "allow_directional_language_from_resolved_transition": False,
        "allow_exclusivity_from_authoritative_resolution": False,
        "allow_commitment_language_when_player_explicitly_committed": True,
        "surfaced_lead_ids": [],
        "surfaced_lead_labels": [],
    }
    p = build_retry_prompt_for_failure(
        {"failure_class": "followup_soft_repetition", "followup_context": {}},
        response_policy=None,
        gm_output={"anti_railroading_contract": arc},
    ).lower()
    assert "explicit player-stated commitment" in p or "echo explicit" in p


def test_retry_urgency_does_not_justify_forced_pathing() -> None:
    from game.gm import build_retry_prompt_for_failure

    p = build_retry_prompt_for_failure(
        {
            "failure_class": "topic_pressure_escalation",
            "topic_context": {"topic_key": "patrol", "previous_answer_snippet": "Unknown.", "repeat_count": 4},
        },
        response_policy=None,
        gm_output=None,
    ).lower()
    assert "forced pathing" in p
    assert "urgency sharpens salience" in p


def test_retry_salient_lead_optional_unless_exclusivity_contract() -> None:
    from game.anti_railroading import build_anti_railroading_contract
    from game.gm import build_retry_prompt_for_failure

    arc = build_anti_railroading_contract(resolution=None, player_text="Where next?")
    gm = {"anti_railroading_contract": arc}
    p = build_retry_prompt_for_failure(
        {"failure_class": "scene_stall"},
        response_policy=None,
        gm_output=gm,
    ).lower()
    assert "salient lead" in p or "mandatory path" in p


def test_retry_hard_constraint_can_remove_one_avenue_other_paths_remain() -> None:
    from game.gm import build_retry_prompt_for_failure

    p = build_retry_prompt_for_failure({"failure_class": "scene_stall"}, response_policy=None, gm_output=None).lower()
    assert "constraint" in p
    assert "others open" in p or "leaves others open" in p


def test_retry_guidance_compatible_with_explicit_commitment_exception() -> None:
    from game.gm import build_retry_prompt_for_failure

    arc = {
        "enabled": True,
        "forbid_player_decision_override": True,
        "forbid_forced_direction": True,
        "forbid_exclusive_path_claims_without_basis": True,
        "forbid_lead_to_plot_gravity_upgrade": True,
        "allow_directional_language_from_resolved_transition": False,
        "allow_exclusivity_from_authoritative_resolution": False,
        "allow_commitment_language_when_player_explicitly_committed": True,
        "surfaced_lead_ids": [],
        "surfaced_lead_labels": [],
    }
    p = build_retry_prompt_for_failure(
        {"failure_class": "followup_soft_repetition", "followup_context": {}},
        response_policy=None,
        gm_output={"anti_railroading_contract": arc},
    ).lower()
    assert "explicit player-stated commitment" in p or "echo explicit" in p
