# PR-DF Failure Modes

Each row is a risk on a completed turn. Prevention is the control that stops the bad write or the bad call. Detection is how the harness notices. Recovery is what the player or the copy gets afterward. Residual risk remains after those controls.

Scores are not assigned. B and C have no runs.

## A. Wrong resolver

| | A | B | C |
|---|---|---|---|
| Likely cause | Fast-path contract subject or a gated parser returns a different family than the utterance. M1-style miss is a current example of a non-bind, which may be a lexicon gap rather than this failure. | Planner `proposed_resolver` disagrees with `select_ordinary_resolver`. | Model calls execution with a mismatched step. |
| Prevention | Contract selector remains the owner. Experiment pins interpretation off so a second model cannot "fix" the selector during A's run. | Contract selector wins. Disagreement is logged. | `propose_action` dry-run must match the selector or execution returns `conflict`. |
| Detection | Scenario expected-kind check. Log `selected_resolver`. | Same, plus disagreement flag. | Tool code `conflict`. |
| Recovery | `generation`, unsupported, or clarification. State unchanged beyond the shared tick. | Same. The plan is not retried into a different family inside the step. | Same. |
| Residual | A real lexicon gap stays until patterns change. That change is outside this experiment. | A legal selector can still be the wrong play if the contract builder misreads the step text the executor synthesized. | Same residual as B. |

## B. Incorrect entity reference

| | A | B | C |
|---|---|---|---|
| Likely cause | Alias collision. Scenario 11 is built for this. | Planner id not in the catalog, or a cleared id refilled from habit in narration. | `query_known_entities` used as a search, then an arbitrary row executed. |
| Prevention | Catalog plus ambiguous contract. | Ids outside the catalog are cleared. Multiple matches stop the plan. | Empty-query dump is `permission`. Multiple matches return `ambiguous` and do not choose. |
| Detection | Interlocutor id and target id versus the scenario. | Same. | Tool trace shows a chosen id without a unique match. |
| Recovery | Clarification fallback. | Stop before mutation. | Execution refused. |
| Residual | Discourse focus from a previous scenario on the same copy can legally bind "him." Fresh-state runs must not inherit focus. | Narration can name the wrong person after a clean refusal. Text checklist catches that only on the live arm. | Same text residual. |

## C. Unsupported action plan

| | A | B | C |
|---|---|---|---|
| Likely cause | No pattern for pry, downtime, or a compound. | Plan of four steps includes an unsupported one. | Model keeps calling execution after `unsupported`. |
| Prevention | Noncombat `route="none"` and downtime code. | Executor rejects the step before mutation. Later dependents do not run. | Four-round cap. Repeat of the same refusal counts toward the cap. |
| Detection | Resolution kind unsupported / blocked, or `generation` with unchanged entity set. | Step status list. | Tool code `unsupported`. |
| Recovery | Engine fallback or narration that must not claim success. | Player-facing line that the step did not happen. | Same. |
| Residual | `generation` can still describe success. Live-arm checklist. | Same, because narration is shared. | Cap exhausts the turn without a useful reply. |

## D. Invalid tool selection

| | A | B | C |
|---|---|---|---|
| Likely cause | Not a tool architecture. The analogue is the parser cascade calling a stage the contract did not permit. | Planner operation outside the enum. | Unknown tool name or `request_action_execution` without a clean proposal. |
| Prevention | `stage_permitted` and `reject_contradicting_action`. | Schema reject. | Dispatcher allow-list. Execution re-validates. |
| Detection | Trace `resolver_contradiction_rejected`. | Plan status `failed`. | `permission` or `conflict`. |
| Recovery | Drop the candidate parse. | No mutation from that plan. | No mutation from that call. |
| Residual | A permitted stage can still be the wrong one (mode A). | None beyond a bad narration. | Model spends rounds on invalid calls and hits the cap. |

## E. Unauthorized state mutation

| | A | B | C |
|---|---|---|---|
| Likely cause | Observe-only post-GM gateway on production `chat`. Resolver bug. Narration treated as canon by a later reader. | Executor applies a plan field that is not a resolver argument. | Tool handler writes a free-form patch. Preview tool calls `resolve_attack`. |
| Prevention | Harness does not call `_apply_post_gm_updates`. Model owner strings stay non-authoritative. | Dropped fields: rolls, flags, hidden facts, prose canon. | No world-patch tool. Preview must not roll. |
| Detection | State tuple diff against the scenario's authorized set. | Same. | HP or flag diff after a preview call. |
| Recovery | Discard the harness copy for that step. Production files are not in the path. | Same. | Restore pre-call snapshot. |
| Residual | A resolver can legally write something the scenario did not expect. That fails the scenario and is an engine fact, shared by all three if they call that resolver. | Harness bug that calls the mutator with model JSON. Review the diff in the preflight before any live arm. | Same. |

## F. Hallucinated world fact

| | A | B | C |
|---|---|---|---|
| Likely cause | Narration states a clue, exit, or event the resolution does not contain. | Planner `intent_summary` leaked into the reply, or narration describes a refused step. | Model prose between tools. |
| Prevention | Existing narration validators and monotonic contract check. | Summary stripped. Validators unchanged. | Tool results are the only facts the narration stage is given beyond A's payload. |
| Detection | Live-arm checklist against resolver fields and visible facts. Deterministic preflight checks engine-authored lines only. | Same. | Hidden and prohibited strings in the transcript. |
| Recovery | Retry up to 2, then fallback line. | Same narration budget. | Same. |
| Residual | Validators can miss a fluent invention. PR-DE did not measure first-attempt acceptance. | Same residual as A on the narration call. | Tool transcript can repeat an earlier hallucination into the next round. |

## G. Hidden-information disclosure

| | A | B | C |
|---|---|---|---|
| Likely cause | Payload or reply contains a GM-only string. H1 and scenario 14. | Query helper returns the wrong projection. | `inspect_resulting_state` field list extended. |
| Prevention | Visibility contract. Improvisation hidden-term reject. H1 off the reduced projector. | Queries use the visibility builder. | Field allow-list. `hidden_facts` is not a field. |
| Detection | String search of player-visible text and of B/C query JSON against the fixture hidden list. | Same. | Same, including every tool result. |
| Recovery | Retry / fallback. Ledger row rejected. | Failed query returns `not_visible` and empty result. | Same. |
| Residual | A's narration payload may still contain hidden material for the model even when the reply is clean. The experiment records whether hidden strings appear in the provider input. That is a disclosure-to-model finding, reported separately from disclosure-to-player. | If B's narration call uses A's payload, the model-side exposure matches A. | Query path should be cleaner. Narration path matches A. |

## H. Conversation continuity failure

| | A | B | C |
|---|---|---|---|
| Likely cause | Scene change clears context. Wrong interlocutor. Follow-up classified as a new topic. Inherited dialogue-lock failures exist on the shared suite. | Step targets a different npc id. | Execution uses a newly queried id. |
| Prevention | Discourse focus and directed entry, shared. | Scenario 2 expects a stable id. | NPC context tool does not change focus. Only execution does, through the social resolver. |
| Detection | Interlocutor id before and after S2. | Same. | Same. |
| Recovery | Existing continuity break rules when the action is non-social. | Do not run a second social step that switches speaker unless the utterance named one. | Same. |
| Residual | Inherited dialogue-lock defects can fail S2 for every candidate that uses the same social resolver. That is a shared engine result. | A replan could legally switch if the contract says so. Log it. | Same. |

## I. Retry loop

| | A | B | C |
|---|---|---|---|
| Likely cause | Validator rejects narration. Scene-stall path. PR-CK notes two provider calls when momentum is due. | Replan plus narration retries. | Tool rounds plus narration retries. |
| Prevention | `MAX_TARGETED_RETRY_ATTEMPTS = 2`. Interpretation is not retried. | One replan. Narration budget unchanged. | Four tool rounds. Narration budget unchanged. |
| Detection | Call counter versus the formulas in the cost model. | Same. | Same. |
| Recovery | Fallback line. Turn ends. | Turn ends as failed plan or fallback text. | `budget` code. |
| Residual | Two retries can triple narration input. Acceptance rate is unmeasured, so the expected value is unknown. | A replan that repeats the same plan still consumes `Q`. | The model can oscillate between two tools until the cap. |

## J. Partial execution failure

| | A | B | C |
|---|---|---|---|
| Likely cause | Single action, so partial plans are rare. A compound utterance collapses to one parse or to generation. | Step 1 commits, step 2 throws or is rejected. | First execution commits, second is `unsupported`. |
| Prevention | One action. | Snapshot per step. Dependents of a failed step do not run. | Same snapshot. |
| Detection | Scenario 10: scene unchanged and board still present. | Step status: committed, refused. | Tool `mutation` field. |
| Recovery | N/A for a single action that never started. | Copy stays at the last success. Player text must not claim the refused step. | Same. |
| Residual | A may narrate both halves as one blur. That can fail the text checklist without a state failure. | No undo of step 1. Scenario 10's first step is specified to be non-mutating under the M1 rule, so the residual is small there. A future compound whose first step mutates will keep that mutation. | Same. |

## K. Transaction rollback failure

| | A | B | C |
|---|---|---|---|
| Likely cause | There is no engine undo. A bug in the harness snapshot (shallow copy of nested combat HP or world NPCs). | Same. | Preview path mutates, then the "restore" restores the already-mutated object. |
| Prevention | Deep copy before each step. Production stores are not the copy. | Same. | Adjudication preview is specified not to call rolling functions. |
| Detection | Compare HP and flags to a second control copy that never ran the failed call. | Same. | HP unchanged assertion on preview. |
| Recovery | Discard the whole turn copy if the control diverges. | Same. | Same. |
| Residual | Nested mutability bugs in a hand-rolled copy. The preflight must include scenario 14 and B1 as copy tests before any live call. | Same. | Same. |

## L. Excessive latency or token consumption

| | A | B | C |
|---|---|---|---|
| Likely cause | 87 KB-class narration payload, times retries. | Plan tokens added on top of that payload. | Growing tool transcripts times up to four rounds, plus the payload. |
| Prevention | Record bytes with the PR-DE method. Do not shrink the payload in this experiment. | Caps on `Q` and steps. | Round cap. Do not persist tool chatter into the next turn's narration payload. |
| Detection | `input_*` formulas. Latency keys. | Same. | Sum of round sizes. |
| Recovery | End the turn at the budget. Score the turn unsuccessful if the budget is hit before a scenario success. | Same. | Same. |
| Residual | Without measured `R` and without measured plan or tool sizes, cost claims stay empty. That is required. | A successful unusual turn can still cost more than A's failed cheap refusal. The metric is cost per **successful** turn, defined by the scenario sheet, not cost per call. | Same. |

## M. Unnatural or evasive narration

| | A | B | C |
|---|---|---|---|
| Likely cause | Fallback lines and validator rewrites. Large policy payload producing generic caution. | Clarification questions that are engine lines. | Tool errors spoken aloud as system text. |
| Prevention | Existing player-facing sanitizer and diegetic-voice checks. | Clarification must use the engine line or a question that passes the hidden-term check. | Tool codes stay in the trace. The player hears the narration or the engine line. |
| Detection | Live-arm rubric: the reply answers the permitted interpretation or clearly refuses. It does not add a point for length or drama. | Same. | Same. |
| Recovery | Fallback is a legal recovery. It scores as useful only if the scenario accepts an engine line (checks, ambiguity, adversarial refusals). | Same. | Same. |
| Residual | Deterministic preflight does not judge prose style. A candidate can look good on state and fail the live rubric. | Same. | Evasive tool-chatter can burn the round cap and leave only a fallback. |

## N. World-clock inconsistency

| | A | B | C |
|---|---|---|---|
| Likely cause | `chat` ticks every turn, including talk. A second tick from a tool. Scenario 12's courier moves to the wrong place if the fixture is wrong. | Plan `advance_time` calls the clock again. | `advance_authorized_time` called twice, or called in addition to the harness tick. |
| Prevention | Harness performs the one tick for every candidate. | `advance_time` is an acknowledgement, not a second call. | Second call returns `already_applied`. |
| Detection | `time_pressure` delta is 1. Tick event list length matches a single `advance_world_tick` on the control copy. | Same. | Same. |
| Recovery | If a second tick is detected, discard the turn copy and fail the candidate for that scenario. | Same. | Same. |
| Residual | The shared policy ticks talk turns. That can look like "too much time" and still be consistent. Downtime remains unwired, so a rest request cannot advance a different clock legally. | Same. | Same. |
