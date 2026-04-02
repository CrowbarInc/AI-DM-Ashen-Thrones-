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


def _titles_from_buckets(journal: dict) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for key in ("active_leads", "pursued_leads", "stale_leads", "resolved_leads", "obsolete_leads"):
        rows = journal.get(key) or []
        out[key] = [str(r.get("title") or "") for r in rows if isinstance(r, dict)]
    return out


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


def test_journal_unresolved_lists_nonterminal_lead_titles_excludes_terminal_registry_rows():
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
    # ``unresolved_leads`` is a compatibility alias: sorted titles from active/pursued/stale registry rows.
    assert "A" in journal["unresolved_leads"]
    assert "B" not in journal["unresolved_leads"]
    assert "C" not in journal["unresolved_leads"]
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


def test_journal_nonterminal_buckets_by_status_unresolved_and_counts():
    """A: active / pursued / stale placement, unresolved_leads titles, lead_counts."""
    session: dict = {"scene_runtime": {}, "clue_knowledge": {}}
    upsert_lead(
        session,
        create_lead(
            title="Only active",
            summary="",
            id="la",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
        ),
    )
    upsert_lead(
        session,
        create_lead(
            title="Only pursued",
            summary="",
            id="lb",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.PURSUED,
        ),
    )
    upsert_lead(
        session,
        create_lead(
            title="Only stale",
            summary="",
            id="lc",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.STALE,
        ),
    )
    journal = build_player_journal(session, {}, _minimal_scene_env("lab_scene"))
    bt = _titles_from_buckets(journal)
    assert bt["active_leads"] == ["Only active"]
    assert bt["pursued_leads"] == ["Only pursued"]
    assert bt["stale_leads"] == ["Only stale"]
    assert bt["resolved_leads"] == []
    assert bt["obsolete_leads"] == []
    assert journal["unresolved_leads"] == ["Only active", "Only pursued", "Only stale"]
    assert journal["lead_counts"] == {
        "active": 1,
        "pursued": 1,
        "stale": 1,
        "resolved": 0,
        "obsolete": 0,
        "nonterminal": 3,
        "total": 3,
    }


def test_journal_terminal_excluded_from_actionable_and_terminal_fields():
    """B: terminal rows not in active/pursued/stale; resolved/obsolete journal shape."""
    session: dict = {"scene_runtime": {}, "clue_knowledge": {}}
    upsert_lead(
        session,
        create_lead(title="Done lead", summary="", id="lr", lifecycle=LeadLifecycle.DISCOVERED, status=LeadStatus.ACTIVE),
    )
    resolve_session_lead(
        session,
        "lr",
        resolution_type="confirmed",
        resolution_summary="wrapped up",
        turn=7,
    )
    upsert_lead(
        session,
        create_lead(title="Gone lead", summary="", id="lo", lifecycle=LeadLifecycle.DISCOVERED, status=LeadStatus.ACTIVE),
    )
    obsolete_session_lead(session, "lo", obsolete_reason="withdrawn", turn=3, consequence_ids=["fx_1", "fx_2"])

    journal = build_player_journal(session, {}, _minimal_scene_env("lab_scene"))
    bt = _titles_from_buckets(journal)
    assert bt["active_leads"] == []
    assert bt["pursued_leads"] == []
    assert bt["stale_leads"] == []
    assert set(bt["resolved_leads"]) == {"Done lead"}
    assert set(bt["obsolete_leads"]) == {"Gone lead"}

    res_row = next(r for r in journal["resolved_leads"] if r.get("id") == "lr")
    assert res_row.get("resolved_at_turn") == 7
    assert res_row.get("resolution_type") == "confirmed"
    assert res_row.get("resolution_summary") == "wrapped up"

    obs_row = next(r for r in journal["obsolete_leads"] if r.get("id") == "lo")
    assert obs_row.get("obsolete_reason") == "withdrawn"
    assert obs_row.get("consequence_ids") == ["fx_1", "fx_2"]


def test_journal_discovered_clues_independent_terminal_titles_absent_from_actionable():
    """C: clue strings remain in discovered_clues; terminal titles not in actionable buckets."""
    session: dict = {"scene_runtime": {}, "clue_knowledge": {}}
    upsert_lead(
        session,
        create_lead(title="Open thread", summary="", id="k_act", lifecycle=LeadLifecycle.DISCOVERED, status=LeadStatus.ACTIVE),
    )
    upsert_lead(
        session,
        create_lead(title="Closed thread", summary="", id="k_res", lifecycle=LeadLifecycle.DISCOVERED, status=LeadStatus.ACTIVE),
    )
    upsert_lead(
        session,
        create_lead(title="Dead thread", summary="", id="k_obs", lifecycle=LeadLifecycle.DISCOVERED, status=LeadStatus.ACTIVE),
    )
    resolve_session_lead(session, "k_res", resolution_type="dismissed", resolution_summary="n/a", turn=1)
    obsolete_session_lead(session, "k_obs", obsolete_reason="irrelevant", turn=1)

    session["clue_knowledge"]["k_act"] = {"state": "discovered", "text": "Still matters.", "presentation": "explicit"}
    session["clue_knowledge"]["k_res"] = {"state": "discovered", "text": "Resolved clue line.", "presentation": "explicit"}
    session["clue_knowledge"]["k_obs"] = {"state": "discovered", "text": "Obsolete clue line.", "presentation": "explicit"}

    journal = build_player_journal(session, {}, _minimal_scene_env("lab_scene"))
    clues = journal["discovered_clues"]
    assert "Still matters." in clues
    assert "Resolved clue line." in clues
    assert "Obsolete clue line." in clues

    actionable_titles = (
        _titles_from_buckets(journal)["active_leads"]
        + _titles_from_buckets(journal)["pursued_leads"]
        + _titles_from_buckets(journal)["stale_leads"]
    )
    assert actionable_titles == ["Open thread"]
    assert "Closed thread" not in journal["unresolved_leads"]
    assert "Dead thread" not in journal["unresolved_leads"]


def test_journal_lead_without_clue_knowledge_still_bucketed_by_registry():
    """D: registry row with no clue_knowledge still lands in the status bucket."""
    session: dict = {"scene_runtime": {}, "clue_knowledge": {}}
    upsert_lead(
        session,
        create_lead(
            title="Registry only",
            summary="syn",
            id="reg_only",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.PURSUED,
            priority=3,
        ),
    )
    journal = build_player_journal(session, {}, _minimal_scene_env("lab_scene"))
    assert journal["pursued_leads"] == [
        {
            "id": "reg_only",
            "title": "Registry only",
            "summary": "syn",
            "type": "rumor",
            "status": "pursued",
            "confidence": "rumor",
            "priority": 3,
            "next_step": "",
            "related_npc_ids": [],
            "related_location_ids": [],
            "parent_lead_id": None,
            "superseded_by": None,
        }
    ]
    assert journal["unresolved_leads"] == ["Registry only"]
    assert journal["active_leads"] == []
    assert journal["stale_leads"] == []


def test_journal_sort_order_within_bucket_priority_recency_title_id():
    """E: same-bucket sort: higher priority, then more recent turn, then title, then id."""
    session: dict = {"scene_runtime": {}, "clue_knowledge": {}}
    upsert_lead(
        session,
        create_lead(
            title="Zebra",
            summary="",
            id="id_z",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
            priority=1,
            last_updated_turn=1,
        ),
    )
    upsert_lead(
        session,
        create_lead(
            title="Alpha",
            summary="",
            id="id_a",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
            priority=1,
            last_updated_turn=10,
        ),
    )
    upsert_lead(
        session,
        create_lead(
            title="Beta",
            summary="",
            id="id_hi",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
            priority=2,
            last_updated_turn=1,
        ),
    )
    upsert_lead(
        session,
        create_lead(
            title="Alpha",
            summary="",
            id="id_b",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
            priority=1,
            last_updated_turn=10,
        ),
    )

    journal = build_player_journal(session, {}, _minimal_scene_env("lab_scene"))
    ids = [r["id"] for r in journal["active_leads"]]
    assert ids == ["id_hi", "id_a", "id_b", "id_z"]


def test_journal_unresolved_leads_dedupes_duplicate_titles_across_registry_rows():
    """F: compatibility alias is title-based, sorted, deduped when two rows share a title."""
    session: dict = {"scene_runtime": {}, "clue_knowledge": {}}
    upsert_lead(
        session,
        create_lead(title="Shared title", summary="", id="row_a", lifecycle=LeadLifecycle.DISCOVERED, status=LeadStatus.ACTIVE),
    )
    upsert_lead(
        session,
        create_lead(title="Shared title", summary="", id="row_b", lifecycle=LeadLifecycle.DISCOVERED, status=LeadStatus.ACTIVE),
    )
    journal = build_player_journal(session, {}, _minimal_scene_env("lab_scene"))
    assert journal["unresolved_leads"] == ["Shared title"]
    assert len(journal["active_leads"]) == 2
