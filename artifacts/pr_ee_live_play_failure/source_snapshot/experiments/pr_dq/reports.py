"""Review markdown for PR-DQ. No provider calls."""

from __future__ import annotations

from typing import Any


def message_contract() -> str:
    return """# PR-DQ IC/OOC Message Contract

One conversation. Each player utterance is one envelope. IC and OOC are properties of that envelope, not separate histories.

The experimental boundary is `ingest_player_message`. It does not execute gameplay and it does not call a provider.

## Envelope

| Field | Role |
| --- | --- |
| message_id | Stable id supplied by the caller. History rejects a duplicate id. |
| text | Original player input, including any IC: or OOC: prefix. |
| mode | IC, OOC, MIXED, or UNRESOLVED. |
| mode_source | AUTO, USER_OVERRIDE, or SYSTEM_DEFAULT. |
| requested_override | AUTO, IC, or OOC. The caller's selection. AUTO is the default. |
| intent | ACTION, DIALOGUE, QUESTION, CORRECTION, RULES_QUERY, CLARIFICATION, or OTHER. |
| status | PENDING, CLASSIFIED, AWAITING_CLARIFICATION, PROCESSED, or REJECTED. |
| destination | Logical route. Empty only before routing. |
| correction_subject | NONE, REFERENT, INTENTION, or COMMITTED_ACTION. |
| classification_basis | Why the mode was chosen. |
| processing_result | What the boundary did. Includes executed, resolver_invoked, and the deterministic response. |
| committed | True only after an accepted IC resolver result is kept. |
| adjudication_required | True when a committed turn would have to change and this cycle will not change it. |

Ingest classifies and routes before it returns, so a returned message is not left PENDING. PENDING remains a legal status for a message that has been received and not yet classified. SYSTEM_DEFAULT remains a legal mode source. This cycle never assigns it, and it is not a silent IC default.

Intent is caller-supplied. When the caller omits it, the intent is OTHER. The boundary does not infer intent from keywords.

## Mode selection

1. An explicit IC or OOC override becomes the mode. Source is USER_OVERRIDE. Automatic markers do not replace it.
2. AUTO with both an IC marker and an OOC marker, or with a marker that is not at the start of the text, becomes MIXED.
3. AUTO with a leading `OOC:` or `Out of character:` becomes OOC.
4. AUTO with a leading `IC:` or `In character:` becomes IC.
5. AUTO with none of those markers becomes UNRESOLVED.

Unrecognized text is not treated as IC.

## What this contract does not decide

Communication mode does not decide mechanical legality, dice, NPC decisions, world facts, inventory, HP, or time. An unsupported in-world request stays IC. The gameplay adapter rejects operation classes in the PR-DO unsupported set, including `UNSUPPORTED_MECHANIC`, and leaves the mode IC.
"""


def routing() -> str:
    return """# PR-DQ IC/OOC Routing

Classification chooses a destination. The destination chooses which function may run. It does not grant a world change.

| Mode and intent | Destination | Execution |
| --- | --- | --- |
| IC + ACTION | IC_ACTION | May call the experimental gameplay adapter when a hand-authored action is attached. |
| IC + DIALOGUE or QUESTION | IC_DIALOGUE | Same adapter, social question path when the action is hand-authored. |
| IC + any other intent | CLARIFICATION_REQUIRED | Not executed. |
| OOC + QUESTION | OOC_QUESTION | Deterministic non-mutating deferral. |
| OOC + CORRECTION | OOC_CORRECTION | Noted, or held for adjudication when the subject is COMMITTED_ACTION. |
| OOC + RULES_QUERY | OOC_RULES_QUERY | Deterministic non-mutating deferral. |
| OOC + any other intent | CLARIFICATION_REQUIRED | Not executed. An OOC override on an action sentence does not become an IC action. |
| MIXED | MIXED_MESSAGE | Deferred. Not passed to an IC resolver. |
| UNRESOLVED | CLARIFICATION_REQUIRED | Not executed. |

The four gameplay turns carry explicit IC metadata and a hand-authored action spec. The spec names an existing operation class and an existing resolver type: observe, question, scene_transition, or investigate. The adapter checks entity kind against the disposable scene, then calls `game.exploration.resolve_exploration_action` or `game.social.resolve_social_action`. An accepted scene transition updates the in-memory session and calls `advance_clock` once. It does not call `storage.activate_scene`.

There is no mixed-message segmenter. A mixed envelope is one history entry and one deferral.

Reclassification before `committed` is true updates the mode and destination. Reclassification after commit records POST_EXECUTION_CORRECTION, sets adjudication_required, and leaves the original text, mode, destination, and session in place.
"""


def safety() -> str:
    return """# PR-DQ IC/OOC Safety

OOC messages must not execute authoritative gameplay actions.

`execution_permitted` is true only for an uncommitted IC message whose destination is IC_ACTION or IC_DIALOGUE and whose status is still CLASSIFIED. OOC, MIXED, UNRESOLVED, rejected, and clarification messages fail that gate. The resolver wrapper raises if a non-IC message reaches it.

A message that does not execute is compared to the authoritative snapshot taken before dispatch. The snapshot covers scene, visited scenes, clocks, turn counter, NPC runtime, scene state, resolved interactables, flags, inventory, HP, combat action use, and world flags. A difference raises `OOCSafetyError`.

An OOC path does not:

- advance world time
- consume a combat action
- move a character
- change inventory
- change HP
- call a social or exploration resolver
- establish a world fact
- roll gameplay dice
- rewrite an earlier message or its result

An OOC correction with subject COMMITTED_ACTION returns a non-mutating adjudication notice. It does not undo the committed turn.

An IC override does not authorize an unsupported mechanic. The adapter rejects that class before any resolver call and restores nothing because it did not call.

An accepted IC result may keep session changes made by the existing resolver, then apply only the slice's own scene, clock, clue, and turn-counter updates. Character, combat, and the world document are restored from the pre-call copies even on acceptance, so this slice does not take HP, inventory, or world-flag changes from the resolver. An unaccepted resolver result restores the session copy as well. That discard happens before commit. It is not a rollback of committed history, and this cycle does not implement one.

No provider is called. Production `data/session.json`, `data/world.json`, `data/combat.json`, and `data/session_log.jsonl` are not the slice's store.
"""


def tests_document(summary: str) -> str:
    return f"""# PR-DQ IC/OOC Tests

Deterministic fixtures. No live provider calls.

## Message cases

| # | Case | Test |
| --- | --- | --- |
| 1 | Explicit IC override | test_explicit_ic_override |
| 2 | Explicit OOC override | test_explicit_ooc_override_blocks_an_action_sentence |
| 3 | AUTO mode | test_auto_mode_classifies_prefixes_and_defers_unmarked_text |
| 4 | OOC: prefix | test_ooc_prefix |
| 5 | IC: prefix | test_ic_prefix |
| 6 | Ordinary IC action | test_ordinary_ic_action_routes_to_the_gameplay_adapter |
| 7 | Ordinary IC dialogue | test_ordinary_ic_dialogue |
| 8 | OOC rules question | test_ooc_rules_question_does_not_execute |
| 9 | OOC correction | test_ooc_correction_of_a_committed_action_requires_adjudication |
| 10 | Ambiguous statement | test_ambiguous_statement_stays_unresolved |
| 11 | Unsupported IC mechanic | test_unsupported_ic_mechanic_stays_in_character |
| 12 | Mixed IC/OOC message | test_mixed_message_is_deferred |
| 13 | Reclassification before execution | test_reclassification_before_execution_reroutes |
| 14 | Reclassification after execution | test_reclassification_after_execution_does_not_rewrite_state |
| 15 | OOC message cannot advance time | test_ooc_message_cannot_advance_time |
| 16 | OOC message cannot invoke a gameplay resolver | test_ooc_message_cannot_invoke_a_gameplay_resolver |
| 17 | OOC message cannot mutate state | test_ooc_message_cannot_mutate_state |
| 18 | Unified history preserves message order | test_unified_history_preserves_message_order |
| 19 | Explicit override takes precedence | test_explicit_override_takes_precedence_over_automatic_classification |
| 20 | Rejected or deferred messages do not change state | test_rejected_or_deferred_messages_do_not_change_state |

## Vertical slice

| Test | What it locks |
| --- | --- |
| test_four_turn_sequence_keeps_the_ooc_interruption_in_one_history | Lantern, OOC interruption, Mara, gate, notice board. |
| test_slice_report_matches_the_played_sequence | History order, clock, scene, and resolver list. |
| test_notice_board_is_blocked_while_the_courtyard_is_active | Turn 4 does not resolve from the courtyard. |

## Regression

Full suite output is in `PR-DQ_regression_results.md`.

{summary.strip()}
"""


def current_review(slice_report: dict[str, Any], regression: str) -> str:
    steps = slice_report.get("steps") or []
    ooc = next((step for step in steps if step.get("message_id") == "msg_002"), {})
    kinds = [str(step.get("resolution_kind")) for step in steps if step.get("message_id") != "msg_002"]
    slice_ok = (
        slice_report.get("final_scene") == "waystation_street"
        and slice_report.get("time_pressure") == 1
        and slice_report.get("notice_resolved") is True
        and slice_report.get("history_ids") == ["msg_001", "msg_002", "msg_003", "msg_004", "msg_005"]
        and ooc.get("mutated_state") is False
        and ooc.get("resolver_invoked") is False
        and kinds == ["observe", "question", "scene_transition", "discover_clue"]
    )
    slice_line = "executed" if slice_ok else "failed"
    return f"""# CURRENT REVIEW

PR-DQ

MODE:
DETERMINISTIC GAMEPLAY SLICE
AND IC/OOC MESSAGE BOUNDARY

Live provider calls:
0

Production UI changes:
none

Four-turn slice:
{slice_line}. History {slice_report.get("history_ids")}. Final scene {slice_report.get("final_scene")}. time_pressure {slice_report.get("time_pressure")}. Notice resolved: {slice_report.get("notice_resolved")}. Resolver calls: {slice_report.get("resolver_calls")}.

IC/OOC message envelope:
Player messages use one envelope with message_id, original text, mode (IC, OOC, MIXED, UNRESOLVED), mode_source (AUTO, USER_OVERRIDE, SYSTEM_DEFAULT), intent, and processing status. Routing updates that object. It is not copied into a second history.

Explicit override support:
The experimental boundary accepts AUTO, IC, or OOC. AUTO is the default. IC and OOC are stored as USER_OVERRIDE and are not replaced by prefix detection. No selector is drawn in the UI.

Automatic classification status:
Deterministic only. Leading OOC:, Out of character:, IC:, and In character: are recognized. A non-leading or paired marker is MIXED and deferred. Unmarked text stays UNRESOLVED. Intent is caller-supplied or OTHER. Automatic detection is not solved. No provider is called.

OOC execution isolation:
OOC, MIXED, and UNRESOLVED messages cannot pass execution_permitted. They do not call a gameplay resolver, advance time, change HP, inventory, scene, NPC runtime, or world flags. A committed-action correction requests adjudication and does not mutate state.

Unified chronological history:
The slice stores five messages in submission order: lantern, OOC interruption, Mara, gate, notice board. Modes on that history are IC, OOC, IC, IC, IC. There is no separate OOC log.

OOC vertical-slice interruption:
"Wait, which street did Mara mention?" is msg_002, mode OOC, destination OOC_QUESTION. Executed: {ooc.get("executed")}. Resolver invoked: {ooc.get("resolver_invoked")}. Mutated state: {ooc.get("mutated_state")}. The following IC question still reaches Sergeant Mara, and the gate transition still reaches the street.

Remaining implementation gaps:
No chat UI and no AUTO|IC|OOC control. No AI classifier. No mixed-message segmenter. No conversation rollback and no historical rewrite. SYSTEM_DEFAULT is defined and unused. An OOC question receives a fixed deferral, not a generated answer. Unmarked player text is not treated as IC.

Regression results:
{regression.strip()}
"""
