"""PR-DQ IC/OOC message tests. Deterministic. No provider calls."""

from __future__ import annotations

import pytest

from experiments.pr_dq.classify import ingest_player_message
from experiments.pr_dq.gameplay import DisposableHarness, dispatch_message
from experiments.pr_dq.reclassify import reclassify_message
from experiments.pr_dq.route import execution_permitted
from experiments.pr_dq.safety import authoritative_snapshot
from experiments.pr_dq.slice import TURN_1
from experiments.pr_dq.world import GATE_ID, LANTERN_TEXT, STREET_ID

pytestmark = pytest.mark.unit


def _submit(harness: DisposableHarness, text: str, message_id: str, **kwargs):
    return harness.submit(text, message_id=message_id, **kwargs)


def test_explicit_ic_override() -> None:
    message = ingest_player_message(
        "OOC: I meant the lantern.",
        message_id="msg_ic",
        mode_override="IC",
        intent="ACTION",
    )
    assert message.mode == "IC"
    assert message.mode_source == "USER_OVERRIDE"
    assert message.requested_override == "IC"
    assert message.classification_basis == "user_override"
    assert message.text == "OOC: I meant the lantern."
    assert message.destination == "IC_ACTION"


def test_explicit_ooc_override_blocks_an_action_sentence() -> None:
    message = ingest_player_message(
        "I go through the courtyard gate.",
        message_id="msg_ooc",
        mode_override="OOC",
        intent="ACTION",
    )
    assert message.mode == "OOC"
    assert message.mode_source == "USER_OVERRIDE"
    assert message.destination == "CLARIFICATION_REQUIRED"
    assert execution_permitted(message) is False


def test_auto_mode_classifies_prefixes_and_defers_unmarked_text() -> None:
    unmarked = ingest_player_message(
        "I look at the lantern by the gate.",
        message_id="msg_auto",
        mode_override="AUTO",
    )
    assert unmarked.requested_override == "AUTO"
    assert unmarked.mode == "UNRESOLVED"
    assert unmarked.mode_source == "AUTO"
    assert unmarked.intent == "OTHER"
    assert execution_permitted(unmarked) is False

    marked = ingest_player_message(
        "OOC: which street?",
        message_id="msg_auto_ooc",
        mode_override="AUTO",
        intent="QUESTION",
    )
    assert marked.mode == "OOC"
    assert marked.mode_source == "AUTO"
    assert marked.classification_basis == "explicit_ooc_prefix"


def test_ooc_prefix() -> None:
    message = ingest_player_message(
        "OOC: I meant the other guard.",
        message_id="msg_prefix_ooc",
        mode_override="AUTO",
        intent="CORRECTION",
    )
    assert message.mode == "OOC"
    assert message.destination == "OOC_CORRECTION"
    assert message.text.startswith("OOC:")

    spelled = ingest_player_message(
        "Out of character: what does AC mean?",
        message_id="msg_prefix_spelled",
        mode_override="AUTO",
        intent="RULES_QUERY",
    )
    assert spelled.mode == "OOC"
    assert spelled.destination == "OOC_RULES_QUERY"


def test_ic_prefix() -> None:
    message = ingest_player_message(
        "IC: I look at the lantern by the gate.",
        message_id="msg_prefix_ic",
        mode_override="AUTO",
        intent="ACTION",
    )
    assert message.mode == "IC"
    assert message.mode_source == "AUTO"
    assert message.classification_basis == "explicit_ic_prefix"
    assert message.destination == "IC_ACTION"

    spelled = ingest_player_message(
        "In character: I ask Sergeant Mara about the street.",
        message_id="msg_prefix_ic_spelled",
        mode_override="AUTO",
        intent="DIALOGUE",
    )
    assert spelled.mode == "IC"
    assert spelled.destination == "IC_DIALOGUE"


def test_ordinary_ic_action_routes_to_the_gameplay_adapter() -> None:
    harness = DisposableHarness()
    message = _submit(
        harness,
        TURN_1["text"],
        "msg_action",
        mode_override="IC",
        intent="ACTION",
        action=TURN_1["action"],
    )
    assert message.destination == "IC_ACTION"
    assert message.mode == "IC"
    assert message.status == "PROCESSED"
    assert message.committed is True
    assert message.processing_result["resolver_invoked"] is True
    assert message.processing_result["resolution_kind"] == "observe"
    assert message.processing_result["resolution_success"] is None
    assert message.processing_result["response"] == LANTERN_TEXT
    assert harness.session["active_scene_id"] == "waystation_courtyard"
    assert harness.session["clocks"]["time_pressure"] == 0


def test_ordinary_ic_dialogue() -> None:
    message = ingest_player_message(
        "I ask Sergeant Mara whether the street is beyond the gate.",
        message_id="msg_dialogue",
        mode_override="IC",
        intent="DIALOGUE",
    )
    assert message.mode == "IC"
    assert message.destination == "IC_DIALOGUE"
    assert message.intent == "DIALOGUE"
    assert execution_permitted(message) is True


def test_ooc_rules_question_does_not_execute() -> None:
    harness = DisposableHarness()
    before = authoritative_snapshot(harness)
    message = _submit(
        harness,
        "OOC: Does inspiration let me reroll?",
        "msg_rules",
        mode_override="AUTO",
        intent="RULES_QUERY",
        action={"operation_class": "UNSUPPORTED_MECHANIC", "engine_type": "observe", "target_id": "courtyard_lantern"},
    )
    assert message.mode == "OOC"
    assert message.destination == "OOC_RULES_QUERY"
    assert message.processing_result["executed"] is False
    assert message.processing_result["resolver_invoked"] is False
    assert harness.resolver_calls == []
    assert authoritative_snapshot(harness) == before


def test_ooc_correction_of_a_committed_action_requires_adjudication() -> None:
    harness = DisposableHarness()
    committed = _submit(
        harness,
        TURN_1["text"],
        "msg_committed",
        mode_override="IC",
        intent="ACTION",
        action=TURN_1["action"],
    )
    original = committed.text
    before = authoritative_snapshot(harness)
    correction = _submit(
        harness,
        "OOC: I meant the other guard.",
        "msg_correction",
        mode_override="AUTO",
        intent="CORRECTION",
        correction_subject="COMMITTED_ACTION",
    )
    assert correction.destination == "OOC_CORRECTION"
    assert correction.adjudication_required is True
    assert correction.status == "AWAITING_CLARIFICATION"
    assert correction.processing_result["executed"] is False
    assert "Explicit adjudication is required" in correction.processing_result["response"]
    assert committed.text == original
    assert committed.processing_result["resolution_kind"] == "observe"
    assert authoritative_snapshot(harness) == before
    assert harness.history.ids() == ["msg_committed", "msg_correction"]


def test_ambiguous_statement_stays_unresolved() -> None:
    message = ingest_player_message("The lantern.", message_id="msg_ambiguous", mode_override="AUTO")
    assert message.mode == "UNRESOLVED"
    assert message.mode_source == "AUTO"
    assert message.destination == "CLARIFICATION_REQUIRED"
    assert message.intent == "OTHER"
    assert execution_permitted(message) is False


def test_unsupported_ic_mechanic_stays_in_character() -> None:
    harness = DisposableHarness()
    before = authoritative_snapshot(harness)
    message = _submit(
        harness,
        "I spend inspiration to reroll.",
        "msg_inspiration",
        mode_override="IC",
        intent="ACTION",
        action={"operation_class": "UNSUPPORTED_MECHANIC", "engine_type": "observe", "target_id": "courtyard_lantern"},
    )
    assert message.mode == "IC"
    assert message.mode_source == "USER_OVERRIDE"
    assert message.status == "REJECTED"
    assert message.destination == "IC_ACTION"
    assert message.processing_result["reason"] == "unsupported_mechanic"
    assert message.processing_result["resolver_invoked"] is False
    assert harness.resolver_calls == []
    assert authoritative_snapshot(harness) == before


def test_mixed_message_is_deferred() -> None:
    harness = DisposableHarness()
    before = authoritative_snapshot(harness)
    message = _submit(
        harness,
        "I look at the lantern. OOC: which street is that?",
        "msg_mixed",
        mode_override="AUTO",
        intent="ACTION",
        action=TURN_1["action"],
    )
    assert message.mode == "MIXED"
    assert message.destination == "MIXED_MESSAGE"
    assert message.status == "AWAITING_CLARIFICATION"
    assert message.processing_result["resolver_invoked"] is False
    assert harness.resolver_calls == []
    assert authoritative_snapshot(harness) == before
    assert len(harness.history) == 1


def test_reclassification_before_execution_reroutes() -> None:
    harness = DisposableHarness()
    message = ingest_player_message(
        "I look at the well.",
        message_id="msg_reclass",
        mode_override="IC",
        intent="ACTION",
    )
    assert message.destination == "IC_ACTION"
    reclassify_message(message, mode="OOC", intent="CORRECTION", correction_subject="REFERENT")
    harness.history.append(message)
    before = authoritative_snapshot(harness)
    dispatch_message(message, harness, TURN_1["action"])
    assert message.mode == "OOC"
    assert message.destination == "OOC_CORRECTION"
    assert message.committed is False
    assert message.processing_result["reclassification"] == "PRE_EXECUTION"
    assert message.processing_result["resolver_invoked"] is False
    assert harness.resolver_calls == []
    assert authoritative_snapshot(harness) == before


def test_reclassification_after_execution_does_not_rewrite_state() -> None:
    harness = DisposableHarness()
    message = _submit(
        harness,
        TURN_1["text"],
        "msg_done",
        mode_override="IC",
        intent="ACTION",
        action=TURN_1["action"],
    )
    assert message.committed is True
    scene = harness.session["active_scene_id"]
    clock = harness.session["clocks"]["time_pressure"]
    kind = message.processing_result["resolution_kind"]
    reclassify_message(message, mode="OOC", intent="CORRECTION", correction_subject="COMMITTED_ACTION")
    assert message.mode == "IC"
    assert message.destination == "IC_ACTION"
    assert message.text == TURN_1["text"]
    assert message.processing_result["resolution_kind"] == kind
    assert message.processing_result["reclassification"] == "POST_EXECUTION_CORRECTION"
    assert message.processing_result["history_rewritten"] is False
    assert message.processing_result["state_reverted"] is False
    assert message.adjudication_required is True
    assert harness.session["active_scene_id"] == scene
    assert harness.session["clocks"]["time_pressure"] == clock
    assert len(harness.history) == 1


def test_ooc_message_cannot_advance_time() -> None:
    harness = DisposableHarness()
    harness.session["clocks"]["time_pressure"] = 2
    before = authoritative_snapshot(harness)
    message = _submit(
        harness,
        "OOC: Advance time to tomorrow.",
        "msg_time",
        mode_override="OOC",
        intent="OTHER",
    )
    assert message.processing_result["advances_time"] is False
    assert message.processing_result["executed"] is False
    assert harness.session["clocks"]["time_pressure"] == 2
    assert authoritative_snapshot(harness) == before


def test_ooc_message_cannot_invoke_a_gameplay_resolver() -> None:
    harness = DisposableHarness()
    message = ingest_player_message(
        "I go through the courtyard gate.",
        message_id="msg_no_resolver",
        mode_override="OOC",
        intent="QUESTION",
    )
    harness.history.append(message)
    dispatch_message(
        message,
        harness,
        {"operation_class": "MOVE", "engine_type": "scene_transition", "target_id": GATE_ID, "target_scene_id": STREET_ID},
    )
    assert message.destination == "OOC_QUESTION"
    assert message.processing_result["resolver_invoked"] is False
    assert harness.resolver_calls == []
    assert harness.session["active_scene_id"] == "waystation_courtyard"


def test_ooc_message_cannot_mutate_state() -> None:
    harness = DisposableHarness()
    before = authoritative_snapshot(harness)
    message = _submit(
        harness,
        "OOC: Give me the lantern and heal me.",
        "msg_mutate",
        mode_override="OOC",
        intent="CORRECTION",
        correction_subject="REFERENT",
    )
    assert message.processing_result["executed"] is False
    assert message.processing_result["mutated_state"] is False
    assert harness.character["hp"]["current"] == 8
    assert harness.session["inventory"] == []
    assert harness.combat["player_turn_used"] is False
    assert harness.session["npc_runtime"] == {}
    assert authoritative_snapshot(harness) == before


def test_unified_history_preserves_message_order() -> None:
    harness = DisposableHarness()
    first = _submit(harness, "IC: I look at the lantern.", "msg_a", mode_override="AUTO", intent="ACTION")
    second = _submit(harness, "OOC: which street?", "msg_b", mode_override="AUTO", intent="QUESTION")
    third = _submit(harness, "The lantern.", "msg_c", mode_override="AUTO")
    assert harness.history.ids() == ["msg_a", "msg_b", "msg_c"]
    assert [item.mode for item in harness.history] == ["IC", "OOC", "UNRESOLVED"]
    assert harness.history.messages()[0] is first
    assert harness.history.messages()[1] is second
    assert harness.history.messages()[2] is third
    assert len(harness.history.records()) == 3


def test_explicit_override_takes_precedence_over_automatic_classification() -> None:
    forced_ic = ingest_player_message(
        "OOC: I meant the lantern.",
        message_id="msg_force_ic",
        mode_override="IC",
        intent="ACTION",
    )
    forced_ooc = ingest_player_message(
        "IC: I look at the lantern.",
        message_id="msg_force_ooc",
        mode_override="OOC",
        intent="QUESTION",
    )
    assert forced_ic.mode == "IC"
    assert forced_ic.mode_source == "USER_OVERRIDE"
    assert forced_ooc.mode == "OOC"
    assert forced_ooc.mode_source == "USER_OVERRIDE"
    assert forced_ooc.destination == "OOC_QUESTION"
    assert execution_permitted(forced_ooc) is False


def test_rejected_or_deferred_messages_do_not_change_state() -> None:
    cases = [
        ("The lantern.", "AUTO", None, "NONE", None),
        (
            "I look at the lantern. OOC: which street?",
            "AUTO",
            "ACTION",
            "NONE",
            TURN_1["action"],
        ),
        (
            "I spend inspiration to reroll.",
            "IC",
            "ACTION",
            "NONE",
            {"operation_class": "UNSUPPORTED_MECHANIC", "engine_type": "observe", "target_id": "courtyard_lantern"},
        ),
    ]
    for index, (text, override, intent, subject, action) in enumerate(cases):
        harness = DisposableHarness()
        before = authoritative_snapshot(harness)
        message = _submit(
            harness,
            text,
            f"msg_defer_{index}",
            mode_override=override,
            intent=intent,
            correction_subject=subject,
            action=action,
        )
        assert message.processing_result["executed"] is False
        assert message.committed is False
        assert harness.resolver_calls == []
        assert authoritative_snapshot(harness) == before
