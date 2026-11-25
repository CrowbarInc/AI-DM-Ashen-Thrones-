"""Provider-disabled acceptance for incidental examination posture."""

import json
import os

import pytest

from game import conversational_orchestration as co, storage
from tests.test_inspection_communication_admission import (
    EXTENDED, assert_discovery, assert_quiet, captured, load, play_capture, reason, replay, trace,
)
from tests.test_repeat_statement_routing_ownership import historical_snapshot


def test_exact_t04_on_original_timeline(replay, monkeypatch):
    # Recreate the recorded T01 refusal only while restoring the original prefix.
    reconcile = co._inspection_communication_consistency
    with monkeypatch.context() as historical:
        historical.setattr(
            co, "_inspection_communication_consistency",
            lambda record, text, **kwargs: reconcile(record, text + " now", **kwargs),
        )
        play_capture(replay, EXTENDED / "T01.json", "historical-prefix-t01")
    for turn in ("02", "03"):
        play_capture(replay, EXTENDED / f"T{turn}.json", f"historical-prefix-t{turn}")
    source = EXTENDED / "T04.json"
    historical = load(source)
    assert historical_snapshot() == historical["before"]
    row = play_capture(replay, source, "exact-t04", duplicate=True)
    outcome, = row["host"]["interpret_production_turn"]
    assert outcome["raw_interpretation"] == captured(source)[1]
    assert outcome["record"]["action_components"] == historical["interpreter_outcomes"][0]["result"]["record"]["action_components"]
    if os.environ.get("ASHEN_POSTURE_BASELINE") == "1":
        assert reason(row) == "communication_before_execution"
        assert row["response"] == historical["response"]
        assert historical_snapshot() == historical["after"]
        assert_quiet(row)
        return
    assert_discovery(row, "prints", "milestone_mud_prints")
    decision = row["host"]["decision_from_interpretation_record"][-1]
    assert decision["proposed_operation"] == "INSPECT"
    assert decision["proposed_target"] == "prints"
    audit = row["persisted_log_resolution"]["metadata"]["live_chat_interpretation"]
    assert audit["record"] == outcome["record"]
    assert audit["normalized_record"]["contract_consistency"]["suppressed_component"] == outcome["record"]["action_components"][0]
    assert row["after"]["session"]["turn_counter"] == 6
    assert row["after"]["session"]["clocks"]["time_pressure"] == 2
    assert set(storage.load_session()["clue_knowledge"]) == {"milestone_mud_prints"}


def interpretation(*components, recipient="GM", purpose="ACTION", permitted=(), unresolved=(),
                   mode="IN_WORLD_ACTION", status="INTERPRETED", question="", evidence=()):
    return {
        "communication": {"recipient": recipient, "purpose": purpose, "subject": "", "evidence_refs": list(evidence)},
        "communication_mode": mode,
        "interpretation_status": status,
        "player_intent": {"summary": "Offline action-decomposition fixture"},
        "asserted_premises": [],
        "requested_outcomes": [],
        "action_components": [
            {"order": order, "operation_class": op, "target_ref": target, "description": description}
            for order, (op, target, description) in enumerate(components, 1)
        ],
        "references": {"permitted_entity_ids": list(permitted), "unresolved_references": list(unresolved)},
        "clarification_question": question,
        "correction": {"subject": "NONE", "note": ""},
    }


def inspection_fixture(posture="Crouch", *, target="prints", **kwargs):
    return interpretation(
        ("MOVE", None, posture), ("INSPECT", target, "Examine the named surface"),
        permitted=[target] if target else [], **kwargs,
    )


@pytest.fixture
def milestone(replay):
    row = play_capture(replay, EXTENDED / "T03.json", "fixture-travel-to-milestone")
    assert row["after"]["session"]["active_scene_id"] == "old_milestone"
    assert len(row["host"]["advance_world_tick"]) == 1
    return replay


def submit(replay, name, text, record, *, duplicate=True):
    row = replay(name, {"text": text}, json.dumps(record), duplicate=duplicate)
    resolution = row["persisted_log_resolution"] or {}
    metadata = resolution.get("metadata") or {}
    normalized = (metadata.get("live_chat_interpretation") or {}).get("normalized_record") or {}
    consistency = normalized.get("contract_consistency") or {}
    bridge = row["host"].get("normalized_action_from_interpretation") or []
    outcomes = row["host"].get("interpret_production_turn") or []
    for outcome in outcomes:
        if outcome.get("raw_interpretation"):
            assert json.loads(outcome["raw_interpretation"]) == record
    row["decomposition_audit"] = {
        "input_kind": "offline_fixture",
        "proposed_components": record["action_components"],
        "incidental_evidence": consistency if consistency.get("suppressed_component") else None,
        "retained_components": normalized.get("action_components", record["action_components"]),
        "component_classification": [
            {
                "component": component,
                "classification": (
                    "incidental_posture" if component == consistency.get("suppressed_component")
                    else "primary_inspection" if component.get("operation_class") == "INSPECT"
                    else "independent_or_unresolved"
                ),
            }
            for component in record["action_components"]
        ],
        "grounding_and_bridge": bridge,
        "interpretation_disposition": outcomes[-1].get("reason") if outcomes else None,
        "adapted_components": ((outcomes[-1].get("record") or {}).get("action_components")
                               if outcomes else None),
        "admission": metadata.get("conversational_decision"),
        "state_delta": {
            key: {"before": row["before"][key], "after": value}
            for key, value in row["after"].items() if value != row["before"][key]
        },
    }
    trace(name, row)
    return row


def assert_retained(row):
    assert_quiet(row)
    assert row["decomposition_audit"]["incidental_evidence"] is None
    assert row["decomposition_audit"]["retained_components"] == row["decomposition_audit"]["proposed_components"]
    assert row["response"]["gm_output"]["player_facing_text"]


@pytest.mark.parametrize(("name", "text", "posture", "target", "clue"), [
    ("crouch-examine", "I crouch and examine the footprints.", "Crouch", "prints", "milestone_mud_prints"),
    ("kneel-purpose-plural", "I kneel to inspect the tracks.", "Kneel", "prints", "milestone_mud_prints"),
    ("bend-study", "I bend down and study the prints.", "Bend down", "prints", "milestone_mud_prints"),
    ("lean-notice", "I lean closer to inspect the notice.", "Lean closer", "notice_board", "notice_patrol_route"),
    ("same-surface-squat", "I squat beside the tracks and look closely.", "Squat beside the tracks", "prints", "milestone_mud_prints"),
    ("crouch-purpose-alias", "I crouch for a better look at the mud.", "Crouch", "prints", "milestone_mud_prints"),
    ("lower-stone", "I lower myself to examine the weathered stone.", "Lower myself", "milestone", "milestone_mud_prints"),
    ("tilt-marker", "I tilt my head to examine the marker.", "Tilt my head", "milestone", "milestone_mud_prints"),
    ("lean-read", "I lean closer to read the curfew notice.", "Lean closer", "notice_board", "notice_patrol_route"),
    ("stoop-current-ground", "I stoop and inspect the mud track.", "Stoop", "prints", "milestone_mud_prints"),
], ids=lambda value: value if isinstance(value, str) and " " not in value else None)
def test_grounded_posture(request, replay, name, text, posture, target, clue):
    if target != "notice_board":
        request.getfixturevalue("milestone")
    row = submit(replay, name, text, inspection_fixture(posture, target=target))
    assert_discovery(row, target, clue)
    receipt, = row["host"]["resolve_exploration_action"]
    assert receipt["clue_text"] in row["response"]["gm_output"]["player_facing_text"]
    audit = row["decomposition_audit"]
    assert audit["incidental_evidence"]["target_id"] == target
    assert [part["classification"] for part in audit["component_classification"]] == [
        "incidental_posture", "primary_inspection",
    ]
    assert len(audit["retained_components"]) == 1


@pytest.mark.parametrize(("name", "text", "components"), [
    ("cross-courtyard", "I cross the courtyard and examine the notice.",
     [("MOVE", None, "Cross the courtyard"), ("INSPECT", "notice_board", "Examine the notice")]),
    ("walk-gate", "I walk to the gate and inspect the guard's equipment.",
     [("MOVE", None, "Walk to the gate"), ("INSPECT", None, "Inspect the guard's equipment")]),
    ("climb-roof", "I climb the ladder and examine the roof.",
     [("MOVE", None, "Climb the ladder"), ("INSPECT", None, "Examine the roof")]),
    ("enter-cellar", "I enter the cellar and inspect the crates.",
     [("MOVE", None, "Enter the cellar"), ("INSPECT", None, "Inspect the crates")]),
    ("behind-wall", "I move behind the wall and examine the tracks.",
     [("MOVE", None, "Move behind the wall"), ("INSPECT", "prints", "Examine the tracks")]),
    ("leave-milestone", "I leave the milestone and inspect the gate.",
     [("MOVE", "leave_for_return_to_cinderwatch_gate", "Leave the milestone"), ("INSPECT", None, "Inspect the gate")]),
    ("three-steps", "I take three steps toward the tracks and kneel.",
     [("MOVE", None, "Take three steps toward the tracks"), ("UNSUPPORTED_MECHANIC", None, "Kneel")]),
    ("run-road", "I run across the road and examine the wagon.",
     [("MOVE", None, "Run across the road"), ("INSPECT", None, "Examine the wagon")]),
    ("hide-wall", "I crouch behind the wall to hide.",
     [("MOVE", None, "Crouch behind the wall"), ("STEALTH_MODE_TOGGLE", None, "Hide")]),
    ("duck-window", "I duck beneath the window and listen.",
     [("MOVE", None, "Duck beneath the window"), ("PERCEIVE", None, "Listen")]),
    ("drop-prone", "I drop prone to avoid the arrows.",
     [("MOVE", None, "Drop prone"), ("UNSUPPORTED_MECHANIC", None, "Avoid the arrows")]),
    ("kneel-cover", "I kneel behind cover and watch the road.",
     [("MOVE", None, "Kneel behind cover"), ("PERCEIVE", None, "Watch the road")]),
    ("stay-unseen", "I lower myself to stay out of sight.",
     [("MOVE", None, "Lower myself"), ("STEALTH_MODE_TOGGLE", None, "Stay out of sight")]),
    ("spring-forward", "I crouch and prepare to spring forward.",
     [("MOVE", None, "Crouch"), ("UNSUPPORTED_MECHANIC", None, "Prepare to spring forward")]),
    ("brace-door", "I brace myself and inspect the door.",
     [("MOVE", None, "Brace myself"), ("INSPECT", None, "Inspect the door")]),
    ("draw-sword", "I draw my sword and inspect the tracks.",
     [("USE_VISIBLE_OBJECT", None, "Draw my sword"), ("INSPECT", "prints", "Inspect the tracks")]),
    ("light-torch", "I light a torch and examine the wall.",
     [("USE_VISIBLE_OBJECT", None, "Light a torch"), ("INSPECT", None, "Examine the wall")]),
    ("open-chest", "I open the chest and inspect its contents.",
     [("USE_VISIBLE_OBJECT", None, "Open the chest"), ("INSPECT", None, "Inspect its contents")]),
    ("take-map", "I take out my map and read the notice.",
     [("USE_VISIBLE_OBJECT", None, "Take out my map"), ("INSPECT", "notice_board", "Read the notice")]),
    ("pick-up-letter", "I pick up the letter and examine it.",
     [("USE_VISIBLE_OBJECT", None, "Pick up the letter"), ("INSPECT", None, "Examine it")]),
    ("put-away-weapon", "I put away my weapon and question the captain.",
     [("USE_VISIBLE_OBJECT", None, "Put away my weapon"), ("ASK", "guard_captain", "Question the captain")]),
    ("inspect-then-leave", "I inspect the footprints, then leave.",
     [("INSPECT", "prints", "Inspect the footprints"), ("MOVE", None, "Leave")]),
    ("afterward-return", "I examine the notice and afterward return to the gate.",
     [("INSPECT", "notice_board", "Examine the notice"), ("MOVE", None, "Return to the gate")]),
    ("walk-before-check", "I walk to the milestone before checking the mud.",
     [("MOVE", None, "Walk to the milestone"), ("INSPECT", "prints", "Check the mud")]),
    ("read-then-ask", "I read the inscription and then ask the captain about it.",
     [("INSPECT", None, "Read the inscription"), ("ASK", "guard_captain", "Ask the captain about it")]),
    ("three-ordered-actions", "I open the door, step inside, and inspect the room.",
     [("USE_VISIBLE_OBJECT", None, "Open the door"), ("MOVE", None, "Step inside"), ("INSPECT", None, "Inspect the room")]),
    ("step-closer", "I step closer and inspect the marks.",
     [("MOVE", None, "Step closer"), ("INSPECT", None, "Inspect the marks")]),
    ("circle-table", "I move around the table to read the inscription.",
     [("MOVE", None, "Move around the table"), ("INSPECT", None, "Read the inscription")]),
    ("beside-guard", "I crouch beside the guard and examine his boots.",
     [("MOVE", None, "Crouch beside the guard"), ("INSPECT", None, "Examine his boots")]),
    ("lean-doorway", "I lean into the doorway and look around.",
     [("MOVE", None, "Lean into the doorway"), ("PERCEIVE", None, "Look around")]),
    ("approach-wagon", "I approach the wagon and check its wheels.",
     [("MOVE", None, "Approach the wagon"), ("INSPECT", None, "Check its wheels")]),
], ids=lambda value: value if isinstance(value, str) else None)
def test_independent_requests(request, replay, name, text, components):
    ids = [target for _, target, _ in components if target]
    if "prints" in ids or name == "leave-milestone":
        request.getfixturevalue("milestone")
    row = submit(replay, name, text, interpretation(*components, permitted=ids))
    assert_retained(row)


@pytest.mark.parametrize(("name", "text"), [
    ("missing-markings", "I lower myself to examine the markings."),
    ("missing-inscription", "I tilt my head to examine the inscription."),
    ("missing-ground", "I stoop and inspect the ground."),
    ("missing-letter-table", "I lean over the table to read the letter."),
    ("other-scene-notice", "I lean closer to inspect the notice."),
    ("unbound-pronoun", "I crouch and examine it."),
    ("unknown-preposition-scope", "I crouch and examine the prints under the wagon."),
    ("two-named-surfaces", "I crouch and examine the prints and the milestone."),
])
def test_unestablished_targets(milestone, name, text):
    # This intentionally overclaims the model target. The fixture world is
    # authoritative and contains none of the missing objects or locations.
    posture = {
        "missing-markings": "Lower myself", "missing-inscription": "Tilt my head",
        "missing-ground": "Stoop", "missing-letter-table": "Lean over the table",
        "other-scene-notice": "Lean closer",
    }.get(name, "Crouch")
    row = submit(milestone, name, text, inspection_fixture(posture))
    assert_retained(row)


@pytest.mark.parametrize(("name", "patch"), [
    ("hidden", {"hidden": True}),
    ("invisible", {"visible": False}),
    ("inaccessible", {"accessible": False}),
    ("unreachable", {"reachable": False}),
    ("unavailable", {"availability": "blocked"}),
    ("gm-only", {"gm_only": True}),
    ("nonpublic", {"public": False}),
    ("access-check", {"skill_check": {"skill_id": "climb"}}),
    ("access-caveat", {"notes": "The prints are inaccessible."}),
    ("duplicate-alias", None),
    ("absent-row", None),
    ("scene-in-combat", None),
    ("combat-active", None),
])
def test_current_surface_authority(milestone, name, patch):
    scene = storage.load_active_scene()
    inner = scene["scene"]
    prints = next(row for row in inner["interactables"] if row["id"] == "prints")
    if patch:
        prints.update(patch)
    elif name == "duplicate-alias":
        stone = next(row for row in inner["interactables"] if row["id"] == "milestone")
        stone["aliases"].append("footprints")
    elif name == "absent-row":
        inner["interactables"].remove(prints)
    elif name == "scene-in-combat":
        inner["mode"] = "combat"
    elif name == "combat-active":
        storage.save_combat({**storage.load_combat(), "in_combat": True})
    storage.save_scene(scene)
    row = submit(milestone, name, "I crouch and examine the footprints.", inspection_fixture())
    assert_retained(row)


@pytest.mark.parametrize("name", [
    "movement-description", "concealment-description", "posture-with-distinct-target", "wrong-inspection-target",
    "missing-inspection-target", "reversed-order", "third-component", "unresolved-reference",
    "target-not-permitted", "requires-clarification", "unsupported-status", "invalid-evidence",
    "question-label", "description-label", "npc-label", "rules-mode",
])
def test_record_authority(milestone, name):
    record = inspection_fixture()
    move, inspect = record["action_components"]
    text = "I crouch and examine the footprints."
    if name == "movement-description":
        move["description"] = "Step toward the footprints"
    elif name == "concealment-description":
        move["description"] = "Crouch to stay out of sight"
    elif name == "posture-with-distinct-target":
        move["target_ref"] = "milestone"
        record["references"]["permitted_entity_ids"].append("milestone")
    elif name == "wrong-inspection-target":
        inspect["target_ref"] = "milestone"
        record["references"]["permitted_entity_ids"] = ["milestone"]
    elif name == "missing-inspection-target":
        inspect["target_ref"] = None
    elif name == "reversed-order":
        record["action_components"] = [{**inspect, "order": 1}, {**move, "order": 2}]
    elif name == "third-component":
        record["action_components"].append({
            "order": 3, "operation_class": "USE_VISIBLE_OBJECT", "description": "Draw a weapon", "target_ref": None,
        })
    elif name == "unresolved-reference":
        record["references"]["unresolved_references"] = ["destination"]
    elif name == "target-not-permitted":
        record["references"]["permitted_entity_ids"] = ["milestone"]
    elif name == "requires-clarification":
        record["clarification_question"] = "Where do you want to move?"
    elif name == "unsupported-status":
        record["interpretation_status"] = "UNSUPPORTED_REQUEST"
    elif name == "invalid-evidence":
        record["communication"]["evidence_refs"] = ["inaccessible:1"]
    elif name in {"question-label", "description-label"}:
        record["communication"]["purpose"] = name.split("-")[0].upper()
    elif name == "npc-label":
        record["communication"]["recipient"] = "NPC"
    elif name == "rules-mode":
        record["communication_mode"] = "RULES_QUESTION"
        record["communication"].update(recipient="SESSION", purpose="RULES")
    row = submit(milestone, name, text, record)
    assert_retained(row)


@pytest.mark.parametrize(("name", "text"), [
    ("hypothetical", "What if I crouch and examine the footprints?"),
    ("question", "Can I crouch and examine the footprints?"),
    ("negation", "I do not crouch and examine the footprints."),
    ("conditional", "I crouch and examine the footprints if the road is clear."),
    ("alternate", "I crouch and examine the footprints or go back to the gate."),
    ("third-request", "I crouch and examine the footprints, then pocket the letter."),
])
def test_complete_literal_request_required(milestone, name, text):
    row = submit(milestone, name, text, inspection_fixture())
    assert_retained(row)
