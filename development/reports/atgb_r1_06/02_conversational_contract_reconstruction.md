# 02 — Conversational Contract Reconstruction

## Shared preceding exchange and active topic

All three isolated trials use the preserved S08.1 exchange, not a new reconstructed conversation:

Player: **What's in front of me right now?**

GM: **You are at Cinderwatch Gate District. Rain, choke traffic, a notice board, and gate watch pressure frame the missing patrol inquiry. Visible points of interest: Notice board. Known exits: Enter Cinderwatch, Follow the missing patrol rumor. The notice board lists taxes, curfew rules, and a warning about a missing patrol. A gate serjeant manages the crowd and keeps one eye on the roster board. A tavern runner trades hot stew and rumors near the rain barrel. Threadbare watchers and refugees cluster along the muddy gate line. Ash Compact census delays have tightened the eastern caravan choke point.**

Topic: the visible scene, narrowed by the player's correction to its people. Intended operation: accept the subject repair and describe the visible people. No new perception attempt, NPC question, hidden knowledge request, pending-action revision, or rollback is required. The preceding question was broad, not literally a weather question; L3's premise that it was about weather is an inaccurate model paraphrase, not a canonical fact.

## Exact trial results

| Trial/source | Exact player input | Exact final response |
|---|---|---|
| R1-05 L1 | I meant the people, not the weather. | Do you mean to clarify that your previous reference was to the people present rather than the weather conditions? |
| R1-05 L2 | I meant the people, not the weather. | Do you mean to clarify that your previous statement referred to the people present rather than the weather conditions? |
| R1-03 L3 | No, I was asking about the people, not the weather. | Do you want a description of the people present at the gate district instead of the weather? |

All three raw interpretations contain GM / CLARIFICATION, legacy mode CLARIFICATION, status INTERPRETED, `evidence_refs: []`, no action components, and no unresolved references. L1/L2 permitted-entity lists are empty; L3 lists gate_guard, gate_serjeant, notice_board and tavern_runner. Those entity lists are not answer-evidence selections. All three summaries explicitly recognize people versus weather. L1/L2 requested outcome is that the GM understands the changed reference; L3 likewise says the GM understands the player is asking about people. This substitutes confirmation of comprehension for fulfilling the corrected request.

The exact raw JSON, request messages, host decision, response metadata and emission receipts appear in `artifacts/atgb/atgb_r1_06/trace_reconstruction.json`, indexed back to original files and hashes. This is a derived inspection index, not a new execution.

## Available authorized evidence

The provider user messages for **each** trial contain:

- `visible:1`: A gate serjeant manages the crowd and keeps one eye on the roster board.
- `visible:2`: A tavern runner trades hot stew and rumors near the rain barrel.
- `visible:3`: Threadbare watchers and refugees cluster along the muddy gate line.

They also contain scene summary, visible:0 notice-board text, visible:4 census delays and full prior reply:0. The three people passages are scene `visible_facts` and were already delivered verbatim in S08.1. Thus they are relevant, player-accessible and authorized; they support a meaningful description. They do not establish people's motives, private allegiances, identities beyond public roles, or why they are present. Public presence of a gate_guard catalog identifier alone is not sufficient evidence for an additional descriptive fact about that guard.

## Host routing and selected plan

For all three, legacy eligibility becomes NEEDS_CLARIFICATION; `interpret_production_turn` returns blocked / clarification_required **with the record retained**. API `chat` passes that record to `decision_from_interpretation_record`. `_communication_decision` assesses grounding, reaches `_pending_revision_decision` (returns null), and selects CLARIFY because purpose CLARIFICATION has no selected public evidence. The decision has `execution_policy: answer_only`, no proposed operation, `missing_information: []`, `context_references: []`, no context update, and no authoritative execution requirement.

There is no separate populated semantic answer plan on this route: the ConversationalDecision is the selected response plan. R1-05's recorded `planning_decision` returns null. The response API uses decision text directly. The immutable accepted-response metadata reports host_operation / authorized_host_speech, zero generation attempts and accepted/emitted exact match. It accepts and preserves the redundant question; it does not create it during expression. No narration model repairs or worsens it.

## Four independent judgments

| Dimension | Verdict | Evidence |
|---|---|---|
| Subject recognition | Correct | Summaries distinguish people from weather |
| Conversational disposition | Incorrect | Asks the player to restate an explicit correction |
| Evidence selection | Incorrect for this answerable request | No passages selected although three relevant public descriptions are supplied |
| Response realization | Faithful to wrong plan; inadequate to player | Final question exactly equals model question and host decision |

Illustrative expected output, **not observed**: “Understood. A gate serjeant manages the crowd and keeps one eye on the roster board. A tavern runner trades hot stew and rumors near the rain barrel. Threadbare watchers and refugees cluster along the muddy gate line.” This uses only supplied passages. It makes no claim to reveal private information or to improve the historical trial.
