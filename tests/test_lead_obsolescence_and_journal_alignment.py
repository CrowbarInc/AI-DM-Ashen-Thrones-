"""Block 4C — runtime supersession obsolescence and journal/unresolved alignment with lead lifecycle."""
from __future__ import annotations

from game.affordances import generate_scene_affordances
from game.exploration import process_investigation_discovery
from game.journal import build_player_journal
from game.leads import (
    LeadLifecycle,
    LeadStatus,
    create_lead,
    debug_dump_leads,
    get_lead,
    obsolete_session_lead,
    resolve_session_lead,
    upsert_lead,
)
from game.storage import get_scene_runtime


def _minimal_scene_env(scene_id: str) -> dict:
    return {"scene": {"id": scene_id, "visible_facts": [], "exits": [], "mode": "exploration"}}


def test_investigation_discovery_supersedes_obsoletes_old_lead_and_stamps_reason():
    session: dict = {"scene_runtime": {}, "clue_knowledge": {}, "turn_counter": 4}
    upsert_lead(
        session,
        create_lead(
            title="Prior rumor",
            summary="",
            id="lead_old",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
        ),
    )
    world: dict = {"inference_rules": [], "clues": {}}
    scene_envelope = {
        "scene": {
            "id": "lab_scene",
            "discoverable_clues": [
                {
                    "id": "clue_new",
                    "text": "Captain confirms the eastern route.",
                    "leads_to_scene": "old_milestone",
                    "supersedes_lead_id": "lead_old",
                },
            ],
        }
    }
    revealed = process_investigation_discovery(scene_envelope, session, world=world)
    assert len(revealed) == 1
    old = get_lead(session, "lead_old")
    assert old is not None
    assert old.get("lifecycle") == "obsolete"
    assert old.get("obsolete_reason") == "superseded"
    assert old.get("superseded_by") == "clue_new"
    assert get_lead(session, "clue_new") is not None
    dump = debug_dump_leads(session)
    assert any(r.get("id") == "lead_old" for r in dump)


def test_obsolete_lead_dropped_from_follow_affordances():
    session: dict = {"scene_runtime": {}, "clue_knowledge": {}, "turn_counter": 1}
    upsert_lead(
        session,
        create_lead(title="Cold", summary="", id="lead_old", lifecycle=LeadLifecycle.DISCOVERED),
    )
    obsolete_session_lead(session, "lead_old", obsolete_reason="stale", turn=1)
    rt = get_scene_runtime(session, "lab_scene")
    rt["pending_leads"] = [
        {
            "clue_id": "x",
            "authoritative_lead_id": "lead_old",
            "text": "Follow this thread",
            "leads_to_scene": "old_milestone",
        }
    ]
    scene = _minimal_scene_env("lab_scene")
    affs = generate_scene_affordances(scene, "exploration", session, list_scene_ids_fn=lambda: ["lab_scene", "old_milestone"])
    assert not any(isinstance(a.get("label"), str) and str(a["label"]).startswith("Follow lead:") for a in affs)


def test_journal_unresolved_excludes_resolved_and_obsolete_mapped_clues():
    session: dict = {"scene_runtime": {}, "clue_knowledge": {}}
    upsert_lead(
        session,
        create_lead(title="A", summary="", id="c_act", lifecycle=LeadLifecycle.DISCOVERED, status=LeadStatus.ACTIVE),
    )
    upsert_lead(
        session,
        create_lead(title="B", summary="", id="c_res", lifecycle=LeadLifecycle.DISCOVERED, status=LeadStatus.ACTIVE),
    )
    resolve_session_lead(
        session,
        "c_res",
        resolution_type="confirmed",
        resolution_summary="done",
        turn=1,
    )
    upsert_lead(
        session,
        create_lead(title="C", summary="", id="c_obs", lifecycle=LeadLifecycle.DISCOVERED, status=LeadStatus.ACTIVE),
    )
    obsolete_session_lead(session, "c_obs", obsolete_reason="gone", turn=1)

    session["clue_knowledge"]["c_act"] = {
        "state": "discovered",
        "text": "Active thread text.",
        "presentation": "explicit",
    }
    session["clue_knowledge"]["c_res"] = {
        "state": "discovered",
        "text": "Resolved thread text.",
        "presentation": "explicit",
    }
    session["clue_knowledge"]["c_obs"] = {
        "state": "discovered",
        "text": "Obsolete thread text.",
        "presentation": "explicit",
    }

    journal = build_player_journal(session, {}, _minimal_scene_env("lab_scene"))
    assert "Active thread text." in journal["unresolved_leads"]
    assert "Resolved thread text." not in journal["unresolved_leads"]
    assert "Obsolete thread text." not in journal["unresolved_leads"]
    assert "Active thread text." in journal["discovered_clues"]
    assert "Resolved thread text." in journal["discovered_clues"]


def test_supersession_noop_when_superseded_lead_id_missing():
    session: dict = {"scene_runtime": {}, "clue_knowledge": {}, "turn_counter": 1}
    world: dict = {"inference_rules": [], "clues": {}}
    scene_envelope = {
        "scene": {
            "id": "lab_scene",
            "discoverable_clues": [
                {
                    "id": "clue_only",
                    "text": "Standalone discovery.",
                    "leads_to_scene": "old_milestone",
                    "supersedes_lead_id": "there_is_no_such_lead",
                },
            ],
        }
    }
    process_investigation_discovery(scene_envelope, session, world=world)
    assert get_lead(session, "clue_only") is not None
    assert get_lead(session, "there_is_no_such_lead") is None


def test_supersession_does_not_obsolete_unrelated_lead():
    session: dict = {"scene_runtime": {}, "clue_knowledge": {}, "turn_counter": 2}
    upsert_lead(
        session,
        create_lead(title="Target", summary="", id="lead_target", lifecycle=LeadLifecycle.DISCOVERED),
    )
    upsert_lead(
        session,
        create_lead(title="Other", summary="", id="lead_other", lifecycle=LeadLifecycle.DISCOVERED),
    )
    world: dict = {"inference_rules": [], "clues": {}}
    scene_envelope = {
        "scene": {
            "id": "lab_scene",
            "discoverable_clues": [
                {
                    "id": "clue_new",
                    "text": "Replacement intel.",
                    "leads_to_scene": "old_milestone",
                    "supersedes_lead_id": "lead_target",
                },
            ],
        }
    }
    process_investigation_discovery(scene_envelope, session, world=world)
    assert get_lead(session, "lead_target").get("lifecycle") == "obsolete"
    assert get_lead(session, "lead_other").get("lifecycle") == LeadLifecycle.DISCOVERED.value
