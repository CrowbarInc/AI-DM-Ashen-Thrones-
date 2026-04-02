"""Follow-lead affordance metadata → successful scene_transition → commit_session_lead_with_context."""
from __future__ import annotations

import pytest

from game.affordances import generate_scene_affordances
from game.exploration import (
    apply_follow_lead_commitment_after_resolved_scene_transition,
    finalize_followed_lead,
    parse_exploration_intent,
    resolve_exploration_action,
)
from game.intent_parser import parse_freeform_to_action
from game.leads import LeadLifecycle, LeadStatus, create_lead, get_lead, upsert_lead
from game.prompt_context import build_narration_context
from game.scene_actions import normalize_scene_action
from game.storage import get_scene_runtime


def _scene_gate():
    return {
        "scene": {
            "id": "gate",
            "visible_facts": [],
            "exits": [],
            "mode": "exploration",
        }
    }


def test_follow_lead_affordance_carries_commitment_metadata():
    scene = _scene_gate()
    session: dict = {}
    upsert_lead(
        session,
        create_lead(
            title="Milestone",
            summary="",
            id="to_milestone",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
        ),
    )
    rt = get_scene_runtime(session, "gate")
    rt["pending_leads"] = [
        {
            "clue_id": "to_milestone",
            "authoritative_lead_id": "to_milestone",
            "text": "They were seen toward the old milestone.",
            "leads_to_scene": "old_milestone",
        }
    ]
    affs = generate_scene_affordances(
        scene, "exploration", session, list_scene_ids_fn=lambda: ["gate", "old_milestone"]
    )
    fl = next(a for a in affs if isinstance(a.get("label"), str) and a["label"].startswith("Follow lead:"))
    norm = normalize_scene_action(fl)
    md = norm.get("metadata") or {}
    assert md.get("authoritative_lead_id") == "to_milestone"
    assert md.get("clue_id") == "to_milestone"
    assert md.get("commitment_source") == "follow_lead_affordance"
    assert md.get("commitment_strength") == 1
    assert md.get("target_scene_id") == "old_milestone"
    assert "milestone" in (md.get("lead_text") or "").lower()


def test_successful_transition_commits_lead_with_context():
    session: dict = {"turn_counter": 4}
    upsert_lead(
        session,
        create_lead(
            title="Milestone lead",
            summary="",
            id="to_milestone",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
        ),
    )
    norm = normalize_scene_action(
        {
            "id": "follow-x",
            "label": "Follow lead: rumor",
            "type": "scene_transition",
            "targetSceneId": "old_milestone",
            "prompt": "I follow.",
            "metadata": {
                "authoritative_lead_id": "to_milestone",
                "commitment_source": "follow_lead_affordance",
                "commitment_strength": 1,
            },
        }
    )
    resolution = resolve_exploration_action(
        _scene_gate(),
        session,
        {},
        norm,
        list_scene_ids=lambda: ["gate", "old_milestone"],
    )
    assert resolution["resolved_transition"] is True
    assert resolution["target_scene_id"] == "old_milestone"
    apply_follow_lead_commitment_after_resolved_scene_transition(
        session, resolution, norm, target_scene_id="old_milestone"
    )
    row = get_lead(session, "to_milestone")
    assert row is not None
    assert row["lifecycle"] == "committed"
    assert row["status"] == "pursued"
    assert row["committed_at_turn"] == 4
    assert row["commitment_source"] == "follow_lead_affordance"
    assert row["commitment_strength"] == 1
    rmeta = resolution.get("metadata") or {}
    assert rmeta.get("commitment_applied") is True
    assert rmeta.get("committed_lead_id") == "to_milestone"
    assert rmeta.get("commitment_source") == "follow_lead_affordance"


def test_repeat_follow_lead_preserves_committed_at_turn():
    session: dict = {"turn_counter": 2}
    upsert_lead(
        session,
        create_lead(
            title="R",
            summary="",
            id="Lrep",
            lifecycle=LeadLifecycle.DISCOVERED,
        ),
    )
    norm = normalize_scene_action(
        {
            "id": "fl",
            "label": "Follow lead: x",
            "type": "scene_transition",
            "targetSceneId": "dest",
            "prompt": "go",
            "metadata": {
                "authoritative_lead_id": "Lrep",
                "commitment_source": "follow_lead_affordance",
                "commitment_strength": 1,
            },
        }
    )
    resolution = {
        "kind": "scene_transition",
        "resolved_transition": True,
        "target_scene_id": "dest",
        "action_id": "fl",
        "label": "x",
        "prompt": "go",
        "success": True,
    }
    apply_follow_lead_commitment_after_resolved_scene_transition(session, resolution, norm, target_scene_id="dest")
    first_turn = get_lead(session, "Lrep")["committed_at_turn"]
    session["turn_counter"] = 9
    apply_follow_lead_commitment_after_resolved_scene_transition(session, resolution, norm, target_scene_id="dest")
    row = get_lead(session, "Lrep")
    assert row["committed_at_turn"] == first_turn


def test_obsolete_lead_terminal_no_commitment_mutation():
    session: dict = {"turn_counter": 3}
    upsert_lead(
        session,
        create_lead(
            title="Stale thread",
            summary="",
            id="Lobs",
            lifecycle=LeadLifecycle.OBSOLETE,
            status=LeadStatus.ACTIVE,
        ),
    )
    before = dict(get_lead(session, "Lobs") or {})
    norm = normalize_scene_action(
        {
            "id": "fl",
            "label": "Follow lead: obsolete",
            "type": "scene_transition",
            "targetSceneId": "y",
            "metadata": {
                "authoritative_lead_id": "Lobs",
                "commitment_source": "follow_lead_affordance",
                "commitment_strength": 1,
            },
        }
    )
    resolution = {"kind": "scene_transition", "resolved_transition": True, "target_scene_id": "y", "metadata": {}}
    apply_follow_lead_commitment_after_resolved_scene_transition(session, resolution, norm, target_scene_id="y")
    row = get_lead(session, "Lobs")
    assert row.get("commitment_source") == before.get("commitment_source")
    assert row["lifecycle"] == "obsolete"
    assert (resolution.get("metadata") or {}).get("commitment_applied") is False


def test_resolved_lead_terminal_no_commitment_mutation():
    session: dict = {"turn_counter": 5}
    upsert_lead(
        session,
        create_lead(
            title="Done",
            summary="",
            id="Ldone",
            lifecycle=LeadLifecycle.RESOLVED,
            status=LeadStatus.RESOLVED,
            resolved_at_turn=10,
        ),
    )
    before = dict(get_lead(session, "Ldone") or {})
    norm = normalize_scene_action(
        {
            "id": "fl",
            "label": "Follow lead: done",
            "type": "scene_transition",
            "targetSceneId": "x",
            "metadata": {
                "authoritative_lead_id": "Ldone",
                "commitment_source": "follow_lead_affordance",
                "commitment_strength": 1,
            },
        }
    )
    resolution = {
        "kind": "scene_transition",
        "resolved_transition": True,
        "target_scene_id": "x",
        "metadata": {},
    }
    apply_follow_lead_commitment_after_resolved_scene_transition(session, resolution, norm, target_scene_id="x")
    row = get_lead(session, "Ldone")
    assert row.get("commitment_source") == before.get("commitment_source")
    assert row.get("commitment_strength") == before.get("commitment_strength")
    assert row["lifecycle"] == "resolved"
    assert row["status"] == "resolved"
    assert (resolution.get("metadata") or {}).get("commitment_applied") is False


def test_failed_transition_does_not_commit():
    session: dict = {"turn_counter": 1}
    upsert_lead(
        session,
        create_lead(title="N", summary="", id="Ln", lifecycle=LeadLifecycle.DISCOVERED),
    )
    norm = normalize_scene_action(
        {
            "id": "fl",
            "label": "Follow lead",
            "type": "scene_transition",
            "targetSceneId": "blocked",
            "metadata": {"authoritative_lead_id": "Ln", "commitment_source": "follow_lead_affordance", "commitment_strength": 1},
        }
    )
    resolution = {
        "kind": "scene_transition",
        "resolved_transition": False,
        "target_scene_id": None,
    }
    apply_follow_lead_commitment_after_resolved_scene_transition(session, resolution, norm, target_scene_id="blocked")
    row = get_lead(session, "Ln")
    assert row["lifecycle"] == "discovered"
    assert "metadata" not in resolution or not (resolution.get("metadata") or {}).get("committed_lead_id")


def test_generic_scene_transition_without_authoritative_id_does_not_commit():
    session: dict = {"turn_counter": 1}
    upsert_lead(
        session,
        create_lead(title="Orphan", summary="", id="orphan", lifecycle=LeadLifecycle.DISCOVERED),
    )
    norm = normalize_scene_action(
        {
            "id": "go-north",
            "label": "Go north",
            "type": "scene_transition",
            "targetSceneId": "north_room",
            "prompt": "I go north.",
        }
    )
    resolution = {
        "kind": "scene_transition",
        "resolved_transition": True,
        "target_scene_id": "north_room",
    }
    apply_follow_lead_commitment_after_resolved_scene_transition(session, resolution, norm, target_scene_id="north_room")
    row = get_lead(session, "orphan")
    assert row["lifecycle"] == "discovered"


def test_legacy_follow_lead_label_without_metadata_does_not_commit():
    session: dict = {"turn_counter": 1}
    upsert_lead(
        session,
        create_lead(title="Old", summary="", id="old_lead", lifecycle=LeadLifecycle.DISCOVERED),
    )
    norm = normalize_scene_action(
        {
            "id": "legacy-fl",
            "label": "Follow lead: old rumor text",
            "type": "scene_transition",
            "targetSceneId": "somewhere",
            "prompt": "I follow.",
        }
    )
    resolution = {
        "kind": "scene_transition",
        "resolved_transition": True,
        "target_scene_id": "somewhere",
    }
    apply_follow_lead_commitment_after_resolved_scene_transition(session, resolution, norm, target_scene_id="somewhere")
    row = get_lead(session, "old_lead")
    assert row["lifecycle"] == "discovered"


def test_unknown_authoritative_lead_id_is_silent_noop():
    session: dict = {"turn_counter": 1}
    norm = normalize_scene_action(
        {
            "id": "fl",
            "label": "Follow lead",
            "type": "scene_transition",
            "targetSceneId": "x",
            "metadata": {"authoritative_lead_id": "missing_lead_xyz"},
        }
    )
    resolution = {"kind": "scene_transition", "resolved_transition": True, "target_scene_id": "x"}
    apply_follow_lead_commitment_after_resolved_scene_transition(session, resolution, norm, target_scene_id="x")
    assert "metadata" not in resolution or "committed_lead_id" not in (resolution.get("metadata") or {})


def _scene_milestone_gate():
    return {
        "scene": {
            "id": "gate",
            "visible_facts": [],
            "exits": [{"label": "Old milestone path", "target_scene_id": "old_milestone"}],
            "mode": "exploration",
        }
    }


def _seed_single_pending_milestone_lead(session: dict) -> None:
    upsert_lead(
        session,
        create_lead(
            title="Milestone",
            summary="",
            id="to_milestone",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
        ),
    )
    rt = get_scene_runtime(session, "gate")
    rt["pending_leads"] = [
        {
            "clue_id": "to_milestone",
            "authoritative_lead_id": "to_milestone",
            "text": "Rumor at the old milestone.",
            "leads_to_scene": "old_milestone",
        }
    ]


def test_explicit_pursuit_text_commits_after_resolved_transition():
    session: dict = {"turn_counter": 7}
    _seed_single_pending_milestone_lead(session)
    scene = _scene_milestone_gate()
    raw = parse_freeform_to_action("follow the lead", scene, session=session)
    assert raw is not None
    md = raw.get("metadata") or {}
    assert md.get("authoritative_lead_id") == "to_milestone"
    assert md.get("commitment_source") == "explicit_player_pursuit"
    assert md.get("commitment_strength") == 2
    norm = normalize_scene_action(raw)
    resolution = resolve_exploration_action(
        scene,
        session,
        {},
        norm,
        list_scene_ids=lambda: ["gate", "old_milestone"],
    )
    assert resolution["resolved_transition"] is True
    apply_follow_lead_commitment_after_resolved_scene_transition(
        session, resolution, norm, target_scene_id="old_milestone"
    )
    row = get_lead(session, "to_milestone")
    assert row["lifecycle"] == "committed"
    assert row["status"] == "pursued"
    assert row["committed_at_turn"] == 7
    assert row["commitment_source"] == "explicit_player_pursuit"
    assert row["commitment_strength"] == 2


def test_parse_exploration_intent_passes_session_for_explicit_pursuit():
    session: dict = {}
    _seed_single_pending_milestone_lead(session)
    scene = _scene_milestone_gate()
    raw = parse_exploration_intent("pursue the lead", scene, session=session)
    assert raw is not None
    assert raw.get("type") == "scene_transition"
    assert (raw.get("metadata") or {}).get("authoritative_lead_id") == "to_milestone"


def test_explicit_pursuit_no_registry_row_no_metadata():
    session: dict = {}
    rt = get_scene_runtime(session, "gate")
    rt["pending_leads"] = [
        {
            "clue_id": "orphan",
            "authoritative_lead_id": "missing_registry_row",
            "text": "Loose thread",
            "leads_to_scene": "old_milestone",
        }
    ]
    scene = _scene_milestone_gate()
    raw = parse_freeform_to_action("follow the lead", scene, session=session)
    assert raw is None or (raw.get("metadata") or {}).get("authoritative_lead_id") is None


def test_explicit_pursuit_ambiguous_two_leads_no_metadata():
    session: dict = {}
    upsert_lead(
        session,
        create_lead(title="A", summary="", id="La", lifecycle=LeadLifecycle.DISCOVERED),
    )
    upsert_lead(
        session,
        create_lead(title="B", summary="", id="Lb", lifecycle=LeadLifecycle.DISCOVERED),
    )
    rt = get_scene_runtime(session, "gate")
    rt["pending_leads"] = [
        {
            "clue_id": "a",
            "authoritative_lead_id": "La",
            "text": "Lead A",
            "leads_to_scene": "old_milestone",
        },
        {
            "clue_id": "b",
            "authoritative_lead_id": "Lb",
            "text": "Lead B",
            "leads_to_scene": "north_room",
        },
    ]
    scene = {
        "scene": {
            "id": "gate",
            "exits": [
                {"label": "Old milestone path", "target_scene_id": "old_milestone"},
                {"label": "North", "target_scene_id": "north_room"},
            ],
        }
    }
    raw = parse_freeform_to_action("follow the lead", scene, session=session)
    assert raw is None or (raw.get("metadata") or {}).get("authoritative_lead_id") is None


def test_explicit_pursuit_go_to_the_x_lead_resolves_via_exit():
    session: dict = {"turn_counter": 2}
    _seed_single_pending_milestone_lead(session)
    scene = _scene_milestone_gate()
    raw = parse_freeform_to_action("go to the old milestone lead", scene, session=session)
    assert raw is not None
    assert raw.get("target_scene_id") == "old_milestone"
    md = raw.get("metadata") or {}
    assert md.get("authoritative_lead_id") == "to_milestone"
    norm = normalize_scene_action(raw)
    resolution = resolve_exploration_action(
        scene, session, {}, norm, list_scene_ids=lambda: ["gate", "old_milestone"]
    )
    apply_follow_lead_commitment_after_resolved_scene_transition(
        session, resolution, norm, target_scene_id="old_milestone"
    )
    assert get_lead(session, "to_milestone")["lifecycle"] == "committed"


def test_explicit_pursuit_two_leads_same_destination_no_metadata():
    session: dict = {}
    upsert_lead(session, create_lead(title="A", summary="", id="La", lifecycle=LeadLifecycle.DISCOVERED))
    upsert_lead(session, create_lead(title="B", summary="", id="Lb", lifecycle=LeadLifecycle.DISCOVERED))
    rt = get_scene_runtime(session, "gate")
    rt["pending_leads"] = [
        {
            "clue_id": "a",
            "authoritative_lead_id": "La",
            "text": "One rumor",
            "leads_to_scene": "old_milestone",
        },
        {
            "clue_id": "b",
            "authoritative_lead_id": "Lb",
            "text": "Other rumor",
            "leads_to_scene": "old_milestone",
        },
    ]
    scene = _scene_milestone_gate()
    raw = parse_freeform_to_action("go to the old milestone lead", scene, session=session)
    assert raw is None or (raw.get("metadata") or {}).get("authoritative_lead_id") is None


def test_explicit_pursuit_resolved_lead_no_commitment_mutation():
    """Terminal authoritative lead is excluded from actionable pursuit; no live 'follow the lead' binding."""
    session: dict = {"turn_counter": 4}
    upsert_lead(
        session,
        create_lead(
            title="Done",
            summary="",
            id="Ldone",
            lifecycle=LeadLifecycle.RESOLVED,
            status=LeadStatus.RESOLVED,
            resolved_at_turn=1,
        ),
    )
    rt = get_scene_runtime(session, "gate")
    rt["pending_leads"] = [
        {
            "clue_id": "x",
            "authoritative_lead_id": "Ldone",
            "text": "Old",
            "leads_to_scene": "old_milestone",
        }
    ]
    scene = _scene_milestone_gate()
    raw = parse_freeform_to_action("follow the lead", scene, session=session)
    assert raw is None
    before = dict(get_lead(session, "Ldone") or {})
    norm = normalize_scene_action(
        {
            "id": "fl",
            "label": "Follow lead: done",
            "type": "scene_transition",
            "targetSceneId": "old_milestone",
            "metadata": {
                "authoritative_lead_id": "Ldone",
                "commitment_source": "follow_lead_affordance",
                "commitment_strength": 1,
            },
        }
    )
    resolution = resolve_exploration_action(
        scene, session, {}, norm, list_scene_ids=lambda: ["gate", "old_milestone"]
    )
    apply_follow_lead_commitment_after_resolved_scene_transition(
        session, resolution, norm, target_scene_id="old_milestone"
    )
    row = get_lead(session, "Ldone")
    assert row.get("commitment_source") == before.get("commitment_source")
    assert row["lifecycle"] == "resolved"
    assert (resolution.get("metadata") or {}).get("commitment_applied") is False


def test_convergence_affordance_then_explicit_pursuit_idempotent():
    session: dict = {"turn_counter": 3}
    _seed_single_pending_milestone_lead(session)
    scene = _scene_milestone_gate()
    norm_aff = normalize_scene_action(
        {
            "id": "fl-aff",
            "label": "Follow lead: rumor",
            "type": "scene_transition",
            "targetSceneId": "old_milestone",
            "metadata": {
                "authoritative_lead_id": "to_milestone",
                "commitment_source": "follow_lead_affordance",
                "commitment_strength": 1,
            },
        }
    )
    res1 = resolve_exploration_action(
        scene, session, {}, norm_aff, list_scene_ids=lambda: ["gate", "old_milestone"]
    )
    apply_follow_lead_commitment_after_resolved_scene_transition(
        session, res1, norm_aff, target_scene_id="old_milestone"
    )
    first_turn = get_lead(session, "to_milestone")["committed_at_turn"]
    session["turn_counter"] = 50
    raw = parse_freeform_to_action("follow the lead", scene, session=session)
    norm_txt = normalize_scene_action(raw)
    res2 = resolve_exploration_action(
        scene, session, {}, norm_txt, list_scene_ids=lambda: ["gate", "old_milestone"]
    )
    apply_follow_lead_commitment_after_resolved_scene_transition(
        session, res2, norm_txt, target_scene_id="old_milestone"
    )
    row = get_lead(session, "to_milestone")
    assert row["committed_at_turn"] == first_turn
    assert row["lifecycle"] == "committed"
    assert row["status"] == "pursued"
    assert row["commitment_source"] == "explicit_player_pursuit"
    assert row["commitment_strength"] == 2


def test_resolved_authoritative_lead_omitted_from_follow_lead_affordances():
    scene = _scene_gate()
    session: dict = {"turn_counter": 1}
    upsert_lead(
        session,
        create_lead(
            title="Closed",
            summary="",
            id="closed_lead",
            lifecycle=LeadLifecycle.RESOLVED,
            status=LeadStatus.RESOLVED,
            resolved_at_turn=1,
            resolution_type="confirmed",
        ),
    )
    rt = get_scene_runtime(session, "gate")
    rt["pending_leads"] = [
        {
            "clue_id": "c1",
            "authoritative_lead_id": "closed_lead",
            "text": "A thread you already closed.",
            "leads_to_scene": "old_milestone",
        }
    ]
    affs = generate_scene_affordances(
        scene, "exploration", session, list_scene_ids_fn=lambda: ["gate", "old_milestone"]
    )
    assert not any(
        isinstance(a.get("label"), str) and str(a["label"]).startswith("Follow lead:") for a in affs
    )


def test_obsolete_authoritative_lead_omitted_from_follow_lead_affordances():
    scene = _scene_gate()
    session: dict = {}
    upsert_lead(
        session,
        create_lead(
            title="Cold",
            summary="",
            id="cold_lead",
            lifecycle=LeadLifecycle.OBSOLETE,
            status=LeadStatus.ACTIVE,
            obsolete_reason="stale",
        ),
    )
    rt = get_scene_runtime(session, "gate")
    rt["pending_leads"] = [
        {
            "clue_id": "c2",
            "authoritative_lead_id": "cold_lead",
            "text": "Stale rumor",
            "leads_to_scene": "old_milestone",
        }
    ]
    affs = generate_scene_affordances(
        scene, "exploration", session, list_scene_ids_fn=lambda: ["gate", "old_milestone"]
    )
    assert not any(
        isinstance(a.get("label"), str) and str(a["label"]).startswith("Follow lead:") for a in affs
    )


def test_finalize_followed_lead_resolved_stamps_metadata():
    session: dict = {"turn_counter": 11}
    upsert_lead(
        session,
        create_lead(
            title="Payoff",
            summary="",
            id="pay_lead",
            lifecycle=LeadLifecycle.COMMITTED,
            status=LeadStatus.PURSUED,
        ),
    )
    finalize_followed_lead(
        session,
        "pay_lead",
        terminal_mode="resolved",
        turn=11,
        resolution_type="confirmed",
        resolution_summary="The signet matches the ledger.",
        consequence_ids=["cons_ledger"],
    )
    row = get_lead(session, "pay_lead")
    assert row is not None
    assert row["lifecycle"] == "resolved"
    assert row["status"] == "resolved"
    assert row["resolution_type"] == "confirmed"
    assert row["resolution_summary"] == "The signet matches the ledger."
    assert row["resolved_at_turn"] == 11
    assert row.get("consequence_ids") == ["cons_ledger"]


def test_finalize_followed_lead_obsolete_stamps_metadata():
    session: dict = {"turn_counter": 4}
    upsert_lead(
        session,
        create_lead(title="Dud", summary="", id="dud_lead", lifecycle=LeadLifecycle.DISCOVERED),
    )
    finalize_followed_lead(
        session,
        "dud_lead",
        terminal_mode="obsolete",
        turn=4,
        obsolete_reason="trail went cold",
        consequence_ids=["cons_x"],
    )
    row = get_lead(session, "dud_lead")
    assert row["lifecycle"] == "obsolete"
    assert row["obsolete_reason"] == "trail went cold"
    assert row.get("consequence_ids") == ["cons_x"]


def test_finalize_followed_lead_invalid_terminal_mode_raises():
    session: dict = {}
    upsert_lead(session, create_lead(title="Z", summary="", id="z_lead"))
    with pytest.raises(ValueError, match="terminal_mode"):
        finalize_followed_lead(session, "z_lead", terminal_mode="maybe", resolution_type="x")


def test_finalize_followed_lead_missing_registry_row_raises():
    session: dict = {}
    with pytest.raises(ValueError, match="does not exist"):
        finalize_followed_lead(
            session,
            "missing_lead_id",
            terminal_mode="resolved",
            resolution_type="done",
        )


def test_prompt_export_filters_terminal_pending_leads():
    session: dict = {}
    upsert_lead(
        session,
        create_lead(
            title="Done",
            summary="",
            id="done_pl",
            lifecycle=LeadLifecycle.RESOLVED,
            status=LeadStatus.RESOLVED,
            resolution_type="confirmed",
            resolved_at_turn=1,
        ),
    )
    pending = [
        {
            "clue_id": "c",
            "authoritative_lead_id": "done_pl",
            "text": "Should not surface as active",
            "leads_to_scene": "x",
        }
    ]
    payload = build_narration_context(
        campaign={},
        world={},
        session=session,
        character={},
        scene={},
        combat={},
        recent_log=[],
        user_text="",
        resolution=None,
        scene_runtime={"pending_leads": pending},
        public_scene={"id": "gate"},
        discoverable_clues=[],
        gm_only_hidden_facts=[],
        gm_only_discoverable_locked=[],
        discovered_clue_records=[],
        undiscovered_clue_records=[],
        pending_leads=pending,
        intent={},
        world_state_view={},
        mode_instruction="",
        recent_log_for_prompt=[],
    )
    scene_block = payload.get("scene") or {}
    assert scene_block.get("pending_leads") == []
    rt_block = scene_block.get("runtime") or {}
    assert rt_block.get("pending_leads") == []
