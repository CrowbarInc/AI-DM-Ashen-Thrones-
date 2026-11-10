# PR-PLAY-30 investigation pipeline
Actual trace: POST /api/chat → deterministic conversation/movement routing → destination_not_established → conversational_decline → player publication. No interpreter or exploration resolver executed.

The router's _destination_phrase takes the last matching destination preposition and does not split an infinitive purpose clause. For this text it extracts “investigate the muddy footprints” after “to”. _INSPECT_CUE_RE includes inspect/examine/look at/check/study/read, but not investigate. Movement recognition therefore treats the purpose as a destination and the exit matcher finds no match. Source evidence: conversational_orchestration.py:1060,1162-1174,1298-1330,1487-1502.

| Boundary | Observed |
|---|---|
| Interpretation | Provider skipped; live_chat_interpretation=null. |
| Decomposition/referent | Not performed; configured two-component mock unused. |
| Spatial grounding | Decline: destination_not_established. No crate area or local footprint target. |
| Target selection | None. |
| Eligibility/resolver | resolver_invoked=false, gameplay_parser_invoked=false. |
| Skill/check | None; remote print interactable has no configured check. |
| Deterministic outcome | No attempted exploration; kind=conversational_decline, success=false. |
| State/time | turn_counter 3→3; time_pressure 3→3; world unchanged; clue retained. |
| Narration | Deterministic decline: “You want to reach investigate the muddy footprints, but that is not an established destination from here. You stay where you are.” |
| Integrity/confidentiality | Pass for observed limited effects. |
| Semantic | action_or_compound_rejection; gameplay_completed=false; stop=true. |

First failed execution boundary: spatial grounding in deterministic movement routing, before provider interpretation. Two causes must remain separate: (1) existing routing defect captures purpose as destination; (2) absent authored exact-clue-to-current-target/local-area mapping. Fixing the regex alone does not authorize travel or evidence identity.

Existing legitimate downstream trace (source inspection only): INSPECT current target → bridge investigate action → classify_referenced_surface → match authored interactable → check eligibility/already searched → should_trigger_check (no config, no roll) → discover_clue milestone_mud_prints → existing overlay/clue/search persistence → normal turn tick → grounded narration. Not executed or claimed as validated here.
