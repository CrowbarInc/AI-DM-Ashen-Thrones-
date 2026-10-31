# 04 — S08.2 Before/After Trace

Source: frozen ATGB-03C S08 trial 1, `artifacts/atgb/atgb_03c/S08/result.json` and transcript.md. The raw historical model record and selected evidence refs are unavailable. This pass replays the interpretation-to-orchestration seam; it is not a new live ATGB trial.

Player: “I meant the people, not the weather.”

Prior player: “What's in front of me right now?” The delivered description names rain/choke traffic as well as the gate serjeant, tavern runner, watchers and refugees. Relevant pre-turn context is reconstructed from that delivered exchange and captured state: frontier_gate, no pending_intention, pending_clarification or last_executed_intention, no active interlocutor. The final store is not claimed to be a pre-turn snapshot. Full exact prior response, reconstructed seam state, both complete decisions and provenance are in s08_2_trace.json.

| Stage | Before | After |
| --- | --- | --- |
| Controlled interpretation | GM/DESCRIPTION or GM/CORRECTION; empty components/evidence | Identical stub |
| Routing reason | no_pending_intention | communication_before_execution |
| Mechanical handling selected | Yes, both stubs | No, both stubs; gate consulted and abstains |
| Response plan | “I don't have an unexecuted intention to revise. What do you want to change?” | “That has not been established in the information available to you.” |
| Context update | None | None |
| State changes / action execution | None | None |
| Provider calls in this replay | 0 | 0 |

The before result is observed both in the historical capture and by executing the saved pre-repair source. The after result is observed from current code with controlled empty-evidence records. No historical provider purpose is inferred from the host-overwritten purpose.

**Routing correctness: PASS.** Neither label triggers mechanical revision from conversational correction alone.

**Conversational adequacy of the empty-evidence deterministic fixture: FAIL.** The fallback does not describe the people despite the preserved prior description. The next observed boundary is ordinary GM evidence answering: it has no selected evidence and does not itself recover the requested subject from the stored reply. No downstream repair was attempted.

**Conversational adequacy of a production/live S08.2 replay: NOT EVALUABLE.** A live model call is prohibited and historical evidence selection was not retained. The selected-public-evidence unit control demonstrates only that this existing path can emit supplied public evidence. It does not prove the production model will select the people or justify a successful response claim.

Behavioral packet: `artifacts/validation_evidence/atgb_r1_02/`. Two controlled response-plan runs, two turns; UNREVIEWED. No representative semantic success, evaluator disagreement or stress probe was observed. No gameplay benchmark performance result.
