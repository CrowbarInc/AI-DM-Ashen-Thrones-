# 07 — Final-Emission and Fallback Analysis

Response ownership for the original six turns:

| Stage | Responsibility / observed effect |
|---|---|
| Browser | Sends input without a communication override, renders returned gm_output.player_facing_text |
| Interpreter provider | Supplies structured descriptions, modes, components, sometimes clarification_question; not player-facing narration |
| PR-DO adapter/eligibility | Structure, allowed ids/enums and eligible/unsupported/OOC/abstain classification |
| Live wrapper | Creates blocked/accepted outcomes and candidate fallback/question text |
| API + orchestration | For blocked outcomes WITH a record, builds a new decision; can replace wrapper text. For accepted output, decides whether bridge is needed. |
| Bridge | On turn five only, rejects ASK without an NPC target. Correctly prevents invalid execution. |
| Early response function | Emits deterministic decision text, appends transcript, optionally saves context. Owns all six final replies. |
| Domain resolver / gm narration / final emission / retry | Not reached on any of these six; invocation flags zero, original logs contain no narration response. |

Exact fallback owners: generic “What are you trying to accomplish?” is `_focused_bridge_clarification`'s default at game/conversational_orchestration.py:472; “Who are you asking?” is its missing_target/ASK branch at :457; proposal template :1172; unsupported confirmation :1376–1377. These are early deterministic fallbacks, not final-emission fallbacks.

Turn one's provider understood session readiness, and turn two understood campaign start. The failure then arises when no operation is equated with insufficient intention. Turn three adds an interpreter error (INVENTORY_GRANT); orchestration further transforms an unsupported classification into an offer. Turn six has a provider-written clarification question, but status INTERPRETED means the record decision's not-interpreted branch does not select it. The wrapper's SAFE_ABSTENTION question is also superseded by record-to-compound processing. The existence of that question does not prove it would fully solve the conversation, but it proves a response-owner override occurs upstream of final emission.

No useful provider-generated narrative answer was rejected by validation in these turns: no such answer was requested. No retry loop repeated an invalid narrative premise: retries are zero. Unsupported handling dominates turns three/four/six, while turns one/two are empty-component fallbacks and turn five is a missing-target bridge fallback. It would be incorrect to blame every turn on the interpreter, or every fallback on final_emission_gate.

Current downstream finalization is wired from game/api_turn_support.py:734,747,1411,1426 through final_emission_runtime. The early function game/api.py:731–815 does not call it. Persistent social validation issues documented in PR-ED are separate evidence and were not reclassified as causes here.
