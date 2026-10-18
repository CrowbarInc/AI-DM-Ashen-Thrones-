# PR-EC — Movement, Partial Intent & Multi-Action Handling

## 01 — Executive Summary

PR-EC extends the PR-EA/PR-EB conversational decision layer. It does not add a second simulation engine.

What changed:
- Ordinary movement sentences are recognized without command syntax and, when the destination matches an authored exit or alias, are handed to the existing movement bridge and resolver.
- Questions, tentative remarks, hypotheticals, capability questions, and planning statements are kept non-mutating.
- Incomplete movement asks where the player is going, unless a focused destination or a previous visited scene makes the destination clear.
- Compound consequential requests are named and held for confirmation. Consequential steps are not dropped, and unexecuted steps are not narrated as done.
- Leaving a conversation and then moving clears the active interlocutor only when the move is actually handed off, and the move still goes through the existing resolver.
- Pending clarification is stored on the session and survives a save/load round trip.

What improved:
- Players can say "I go to the docks", "I make for the harbor", or "Let's head down to the waterfront" and reach the same authored exit when those words are aliases of that exit.
- "Can I reach the docks from here?" answers and does not move or advance clocks.
- "I examine the lock, then try to pick it" does not narrate the lock as picked.

What remains incomplete:
- Live-provider semantic competence was not measured. Deterministic routing of a holdout set passed; that is not general language understanding.
- Multiple consequential actions are confirmed one at a time. The engine does not run an unbounded action sequence.
- The broader social, final-emission, retry, and exploration-routing failures from the baseline are still present.
- Synonyms such as harbor/waterfront resolve only when the scene data lists them as aliases. The engine does not invent a place.

Production path: yes. `/api/chat` calls `deterministic_conversational_decision` before clocks, ticks, and resolver execution whenever no stored interpretation harness is injected. An `EXECUTE` decision is still validated by `normalized_action_from_interpretation` and the existing resolver. Non-execute decisions return without a resolver.

Decision: **B — PR-EC ACCEPTED WITH LIMITATIONS**.

## 02 — Preimplementation Baseline

Full write-up: `PR-EC_preimplementation_baseline.md`.

- Revision: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff` on `feature/product-realization`, dirty worktree (427 status lines).
- Python 3.12.0, pytest 9.1.1, Windows.
- Command: the suite listed in the baseline file.
- Result before edits: 244 collected, 214 passed, 30 failed, 18.51s.
- JUnit: `artifacts/pr_ec_movement_partial_intent/baseline_junit.xml`.
- The 30 failures are social/final-emission/retry mismatches and four exploration chat routing failures, plus one `WinError 5` file-replace error.
- The baseline is reproducible enough to classify later failures. It is not a clean passing suite, and it was not cleaned up.

## 03 — Architecture Comparison

PR-EB production flow:

`/api/chat` -> communication mode -> deterministic conversational decision with session/world context -> non-mutating answer/clarify, or one bridged `EXECUTE` record -> existing bridge -> existing resolver -> narration -> persistence.

PR-EC production flow:

`/api/chat` -> communication mode -> if a stored interpretation harness is present, keep that path -> otherwise deterministic decision with movement, partial-intent, and compound classification -> non-mutating answer/clarify/decline/plan, or one bridged operation -> existing bridge -> existing resolver.

New interpretation capabilities, still inside `game/conversational_orchestration.py`:
- Movement versus question versus tentative versus hypothetical versus capability versus planning versus incomplete.
- Destination grounding against authored exits, aliases, and visited scenes.
- Compound steps with support flags and a pending sequence.
- Incidental farewell or thanks separated from the consequential step.

Resolver ownership:
- Location changes, travel time, obstacles, and inspection results stay with the existing bridge and exploration/social resolvers.
- A recognized destination that is not an authored exit does not move the player.
- An exit with no authored destination is still submitted to the bridge, which rejects `exit_has_no_authored_destination`.

Persistence ownership:
- Pending clarification and an optional focused destination live on `session["conversational_context"]`.
- `save_session` / `load_session` already persist that document. PR-EC does not add a second store.
- Interlocutor clearing reuses the PR-EB interaction-context update.

Stored interpretation harnesses still take precedence over the new deterministic layer so replay tests keep their injected records. Production leaves that hook unset.

## 04 — Intent Contract

`ConversationalDecision` gained:
- `intent_modality`: `committed`, `incomplete`, `tentative`, `hypothetical`, `capability_question`, `informational`, `planning`.
- `secondary_intentions`: later steps that were recognized and not executed.
- `execution_policy`: `execute_primary`, `answer_only`, `clarify_before_execution`, `decline_unauthorized_route`, `defer_uncommitted`.

Movement:
- A committed trip with one grounded exit becomes `EXECUTE` / `MOVE` and the existing bridge.
- A question about reachability becomes `ANSWER`. A unique exit may be remembered as `focused_destination` for a later incomplete phrase such as "I start heading out."
- Tentative, hypothetical, capability, and planning lines do not execute.
- An incomplete trip asks "Where are you trying to go?" and stores `pending_clarification`.
- Ambiguous exits ask which one, with the choices stored.
- An unknown place is declined. It is not snapped to a nearby exit.
- "Go back" / "the place we came from" can use a single exit whose target is an earlier `visited_scene_ids` entry.

Compound policy:
- One consequential operation plus incidental thanks, nods, or leaving a person may execute that one operation.
- Two or more consequential operations are not executed together. The reply names them and asks whether to start with the first supported one.
- "Yes" runs only that step. Unsupported remainders stay pending and are not described as completed.
- Passive waits ("I wait", "I remain silent and observe") are not treated as travel refusals. They stay on the existing world-progress path.

Clarification:
- Short replies resume a pending destination, an ambiguous choice, or a confirmed compound step.
- A pending record expires when the scene id changes.
- A question does not get consumed as the clarification answer.

## 05 — Production Integration Evidence

`/api/chat` still enters `deterministic_conversational_decision` before turn advancement when no stored interpretation is injected.

Movement handoff:
- "I go to the docks." produced `resolution.action_id == exit_docks`, `target_scene_id == waystation_street`, metadata operation `MOVE`, and `active_scene_id` changed to the street. Interpretation provider call count stayed 0 because the provider hook raises if called.

Compound handling:
- "I put away my sword and open the door." returned `conversational_clarify`, named both steps, and left scene and turn counter unchanged.
- "I examine the lock, then try to pick it." asked to examine first and said the pick was not done. "yes" resolved only `iron_lock`. The narration was "You examine the iron lock. It is rusted." The pending remainder was the pick.

Dialogue transition:
- With Sergeant Mara active, "I thank the guard and head toward the docks." moved through the docks exit and cleared `active_interaction_target_id`.

Non-mutating question:
- "Can I reach the docks from here?" returned `conversational_answer`, provider interpretation requests 0, clocks unchanged, turn counter unchanged, scene unchanged. Visible text included "You have not moved."

Impossible route:
- "I walk through the sealed stone wall." matched an authored exit with no destination. The bridge rejected `exit_has_no_authored_destination`. Scene and turn counter stayed put. Visible text: "That way is closed. There is no established passage, and you stay where you are."

When a grounded move is recovered from a short reply ("the northern gate") or from context ("I start heading out"), processing text is rewritten to the grounded sentence ("Go to northern gate.") before the ordinary contract is built. The player's original line remains the logged input. This keeps the existing travel contract from rejecting the bridged move as a contradiction.

## 06 — Behavioral Acceptance Results

1. Direct movement — **PASS**. "I go to the docks." invoked the existing `MOVE` resolver and changed scene.
2. Movement paraphrase — **PASS**. "I make for the harbor." and "Let's head down to the waterfront." selected the same exit through authored aliases.
3. Movement question — **PASS**. Reachability answer, no movement, no clock change, no interpretation provider call.
4. Tentative movement — **PASS**. "I was thinking about visiting the docks." did not resolve or advance the turn.
5. Incomplete movement — **PASS**. "I head out." asked "Where are you trying to go?" With a focused docks destination, "I start heading out." then moved.
6. Impossible movement — **PASS**. Sealed wall stayed on the bridge rejection path. No location change.
7. Dialogue to movement — **PASS**. Thanks plus travel moved and ended the active social target.
8. Compound independent actions — **PASS**. Both steps were named. Neither was executed before confirmation.
9. Dependent sequence — **PASS**. Inspection ran only after confirmation. The pick was not narrated as done and remained pending.
10. Hypothetical action — **PASS**. "What would happen if I opened the door?" did not mutate clocks or scene. Text: "I can't say what would happen for certain, and nothing has been attempted."
11. Ambiguous destination — **PASS**. "I go to the gate." offered the northern gate, market gate, and courtyard gate.
12. Clarification continuation — **PASS**. "the northern gate" restored the move and invoked the resolver once.
13. Save/load pending intention — **PASS**. After "I leave.", the session file was rewritten and reloaded. "the docks" then moved once. Pending clarification was cleared. Turn counter became 1.
14. Existing action regression — **PASS**. "I examine the courtyard lantern." is not intercepted. A stored `INSPECT` record still reaches the lantern resolver.
15. Generalization holdout — **PARTIAL**. All 14 holdout lines classified correctly in deterministic tests. Live-provider wording was not run.

Player-facing samples from those tests:
- "Where are you trying to go?"
- "You have not moved."
- "You're considering docks. Nothing has been attempted yet."
- "You can examine the lock first. I have not done this yet: try to pick it. Should I do the first one now?"
- "You want to reach the moon tavern, but that is not an established destination from here. You stay where you are."

No tested reply used "Please specify one valid action."

## 07 — Semantic Generalization Results

Development examples: 6/6 passed.
- Execute: "I go to the docks.", "I make for the harbor.", "Let's head down to the waterfront.", "I leave the guard and walk toward the docks."
- Answer, no move: "Can I get to the docks from here?", "I was thinking about visiting the docks."

Holdout examples: 14/14 passed. The sentences are in `tests/fixtures/pr_ec_holdout_expressions.json` and do not appear as literals in `game/conversational_orchestration.py`.
- Execute: quay, pier, wharf, and landing paraphrases.
- Answer: harbor reachability, waterfront on one's mind, docks described as loud, remembered harbor plus staying here, a suppose-question, and a possibility question.
- Clarify: "I make for the gate." with several gates, sheath-then-check, watch-while-heading, and "I start off."

Misclassifications in that set: none.
False executions in that set: none.
Unrecognized intentions in that set: none.
Excessive clarification: the compound and ambiguous cases clarify on purpose. Single grounded moves do not.

Limitation: these results show deterministic structural routing against a fixture world whose exits carry aliases. They do not show that a live model would make the same distinctions. Semantic generalization is incompletely validated for open-ended provider interpretation.

## 08 — Authority and Persistence Audit

Permitted:
- One bridged `MOVE`, `INSPECT`, or `ASK` when the existing bridge accepts the target.
- Session updates for pending clarification, focused destination, and clearing a social interlocutor on an authorized departure.
- Existing scene transition when the bridge and resolver accept the exit.

Prevented:
- Movement from a question, tentative line, hypothetical, capability question, or plan.
- Inventing a destination that is not an authored exit.
- Choosing among several gates without a player reply.
- Executing a second consequential step in the same confirmation.
- Narrating an unsupported pick as completed.
- Advancing clocks on the non-mutating decision path.
- Treating "I wait." as a travel refusal, after that regression was found and removed.

Resolver authority:
- The orchestration layer proposes one record. `normalized_action_from_interpretation` still checks mode, status, visibility, kind, and authored destination.
- Obstacle handling for an exit with no destination remains the bridge rejection.

Pending persistence:
- `pending_clarification` is written by the existing session save on a non-mutating decision.
- Reload via `load_session` restored a missing-destination pending record.
- The continuation executed once and cleared the pending record.

Duplicate execution:
- The continuation test asserted turn counter 1 and a null pending record after the move.

## 09 — Performance Report

Measurement environment: local Windows, provider hooks stubbed or asserted unused, pytest 9.1.1.

Representative deterministic turns in `tests/test_pr_ec_movement_partial_intent.py`:
- Provider interpretation requests: 0
- Narration provider calls on question, tentative, hypothetical, clarify, and decline paths: 0
- Narration provider calls on authorized moves: the existing narration path, stubbed in tests
- Retries added by PR-EC: 0
- Input tokens: not available
- Output tokens: not available
- Focused PR-EC/PR-EA/PR-EB pytest: 44 passed in 2.81s before the wait-regression repair, then 41 targeted passes in 3.24s after it
- Full comparison suite after the repair: 19.66s

Live latency, live token counts, and live retry behavior were not measured. PR-EC does not add a mandatory provider call on every turn. Turns the deterministic layer answers or clarifies skip interpretation. Authorized moves still use the existing narration path only.

## 10 — Regression Comparison

Baseline: 214 passed, 30 failed.
Post-repair comparison, including the new PR-EC tests: 248 passed, 31 failed, 19.66s.

The extra passing tests are the PR-EC file. Comparing only tests that existed in the baseline:

Inherited (29): the original social, final-emission, retry, mixed-action, and exploration-routing failures, with the same signatures. Listed in the baseline file, excluding the two called out below.

Resolved: none of the 30 baseline failures were fixed. That was out of scope.

New regressions:
- An intermediate build treated "I wait." and "I remain silent and observe." as non-actions. That skipped world progress and narration for six previously passing tests. The stay pattern was narrowed to explicit "stay here" / "don't go" refusals. Those six tests pass again.
- No remaining new failure changes location, resolver ownership, or save/load behavior in a rerun that is free of the Windows file lock.

Changed failure (1):
- `test_chat_dialogue_lock_final_output_beats_generic_fillers_and_keeps_contract_meta[visible_intro_filler]`
- Baseline signature: `PermissionError: [WinError 5]` while replacing `session.json`.
- After signature: unexpected social filler phrase `stands nearby`.
- This is the pre-existing social filler family, previously masked by the file-lock error. PR-EC did not edit that emission stack.

Unclassified / environmental (1):
- `test_runtime_scene_overlay_persists_and_active_scene_merges_without_scene_file_write` failed once after implementation with the same `WinError 5` rename error. Isolated rerun: passed in 1.18s. Not treated as a product defect.

PR-EA incomplete-movement tests were updated so they still require unchanged clocks, turn counter, scene, and world, and they now also expect the pending-destination record that continuation needs.

## 11 — Remaining Issues

PR-EC defects:
- None that still break movement authority, pending persistence, or the repaired wait path.
- Compound confirmation is one step at a time. A player who wanted both steps must confirm. That is the intended conservative policy, and it is still less fluid than a human GM.

PR-ED candidates:
- Live provider token, latency, and retry measurements.
- Broader social and final-emission repair.
- Richer narration of a confirmed first step that also reminds the player of the pending remainder inside the resolver's own prose. Today the reminder is on the clarification turn, and the remainder is stored.

Conversational limitations:
- Destination synonyms require authored aliases.
- "I want to get out of here" clarifies instead of guessing an exit, even if only one exit exists.
- Topic stacks and earlier-narration quotation remain at the PR-EB depth.
- Deterministic patterns will miss some natural phrasing that a live interpreter might catch, and they will also refuse some phrasing a live interpreter might wrongly execute.

Unrelated technical debt:
- The 29 inherited social/final-emission/retry/exploration failures.
- Intermittent Windows `session.json` replace errors under pytest.

## 12 — Final Recommendation

**B — PR-EC ACCEPTED WITH LIMITATIONS**

The production chat path recognizes ordinary movement, keeps questions and tentative lines from moving the player, grounds destinations in authored exits, names compound intentions instead of discarding them, resumes clarification after save/load, and still lets the existing bridge and resolvers decide success. No mandatory extra provider call was added.

The limitations are bounded: live semantic competence is unmeasured, multi-action execution is confirm-then-one-step, alias coverage is data-dependent, and the baseline's social and exploration failures remain. Those do not undo the movement and partial-intent behavior validated here.

Do not start PR-ED until this review is accepted.

## 13 — Changed-File Inventory

- `game/conversational_orchestration.py` — movement, partial-intent, and compound decisions; pending resume; contract fields.
- `game/api.py` — persist `focused_destination`; let stored interpretations keep precedence; rewrite grounded move processing text so the existing travel contract accepts a recovered destination.
- `tests/test_pr_ea_conversational_orchestration.py` — incomplete movement may store pending destination without advancing clocks or world.
- `tests/test_pr_ec_movement_partial_intent.py` — acceptance scenarios, development family, holdout family.
- `tests/fixtures/pr_ec_holdout_expressions.json` — holdout wording, established before the handlers and not copied into production code.
- `PR-EC_preimplementation_baseline.md` — pre-edit test record.
- `artifacts/pr_ec_movement_partial_intent/baseline_junit.xml` — baseline JUnit.
- `artifacts/pr_ec_movement_partial_intent/after_junit.xml` — post-repair comparison JUnit.
- `artifacts/pr_ec_movement_partial_intent/REVIEW.md` — this review.
- `handoff/CURRENT_REVIEW.md`, `handoff/REVIEW_MANIFEST.json`, `handoff/CURRENT_REVIEW.zip` — review package.

Validation commands:

```text
.\.venv\Scripts\python.exe -m pytest tests\test_pr_ec_movement_partial_intent.py tests\test_pr_ea_conversational_orchestration.py tests\test_pr_eb_conversational_continuity.py --tb=line -q --basetemp=codex_pytest_tmp_pr_ec_focus2 --override-ini="addopts="
```

Result: 44 passed.

```text
.\.venv\Scripts\python.exe -m pytest tests\test_pr_ea_conversational_orchestration.py tests\test_pr_eb_conversational_continuity.py tests\test_turn_pipeline_shared.py tests\test_pr_du_player_pipeline.py tests\test_pr_dq_ic_ooc_messages.py tests\test_social.py tests\test_pr_br_qualifier_movement_mixed_intent.py tests\test_unparsed_movement_state_narration_integrity.py tests\test_exploration_resolution.py tests\test_exploration_skill_checks.py tests\test_save_load.py tests\test_runtime_persistence_regression_suite_obj14.py tests\test_final_emission_gate.py tests\test_final_emission_response_type.py tests\test_pr_ec_movement_partial_intent.py --tb=no -q --basetemp=codex_pytest_tmp_pr_ec_after2 --junitxml=artifacts/pr_ec_movement_partial_intent/after_junit.xml --override-ini="addopts="
```

Result: 248 passed, 31 failed, 19.66s. Classification is in section 10.
