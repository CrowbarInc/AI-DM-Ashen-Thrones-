# PR-DF Recommendation

No architecture is the winner. The recommendation is an experiment order and the conditions that would keep, supplement, or replace the current pipeline.

## 1. Evidence-based findings

- The current free-text turn already has a single contract, a selector, domain resolvers, and a mutator that runs before narration. That is Candidate A. The stage list is `AUTHORITATIVE_TURN_STAGE_ORDER` in `game/api_turn_support.py`.
- After PR-DE, a harmless preference still builds an 87,583-byte narration request (S1). A consequential social turn builds 97,373 bytes (C1). Estimates `ceil(bytes/4)` are 21,896 and 24,344 input units. They are not invoices.
- The largest remaining S1 pieces are policy, instructions, the resolution decision, and the answer recipe. Deduplicating seven mirrored contracts did not change that shape.
- A model interpretation proposal already exists and is defined as non-authoritative (`game/semantic_interpreter.py`). It runs only on fast-path abstention when live interpretation is enabled. Candidate B is a generalization of that seam to an ordered plan plus an executor. The production interpreter is not that executor.
- Tool use does not exist. The eight tools in `PR-DF_candidate_C.md` are a contract for a later harness.
- `state_authority` already refuses model-named mutation owners. The post-narration gateway in `chat` is still observe-only. The experiment compares architectures with that gateway left out of the harness so it does not silently score as a feature of A.
- Combat HP, clocks, visibility, improvisation rejects, and the PR-DE fixture builders are reusable by all three candidates.
- Downtime is classified and unwired. Inventory spend is not a general API. Multi-step undo is not an engine feature. The harness snapshot is the specified substitute.
- Required-suite failures (27) and shared-pipeline failures (24) are inherited. They are not new evidence about B or C, and they are not repaired here.
- Live calls in this cycle: 0.

## 2. Unresolved questions

These are questions for the experiment, not holes in the specification.

- On scenario 10, does A stop without removing the board, and can a gold plan for B do the same through the current resolvers?
- Does scenario 12's hypothetical mobile NPC actually move under `advance_world_tick`, or is that a shared gap?
- What is `R`, the narration retry count, on S1 and C1 with the pinned model? PR-DE did not measure acceptance.
- How large is `input_plan` and `input_round(r)` once the harness exists?
- Does the narration payload given to the model contain hidden strings even when the player-facing reply does not?
- Can a read-only adjudication preview be wrapped without calling `resolve_attack`? If not, the tool returns `unsupported`.

## 3. Candidate-specific risks

**A.** Ordinary turns pay a large narration context. Unusual compounds collapse to one parse or to `generation`, which can still talk as if the compound succeeded. The production gateway can adopt post-narration structure. Inherited resolver misses (unbound M1, shared-pipeline failures) will show up in the preflight and must be labeled as engine results.

**B.** Plan tokens sit on top of the same narration payload in the first experiment, so B can cost more on turns A already handles. The planner can sound decisive about a step the executor refuses, and the shared narration call can repeat that error. A harness that applies plan fields directly would violate authority. That failure mode is a build error, not a property of the architecture, and the preflight is there to catch it.

**C.** Several cheap tool calls can exceed one large narration call. The model can treat earlier tool chatter as memory. Preview-versus-roll is the easiest way to corrupt combat while looking read-only. The round cap can end a turn with no useful reply.

## 4. Minimum viable experiment

Deterministic preflight, no provider:

- Scenarios 1–14 on in-memory copies.
- Candidate A through current resolvers, interpretation off.
- Candidates B and C through gold transcripts and illegal transcripts.
- Shared tick, shared dice, shared narration payload bytes, no production saves, no post-GM gateway.

Optional live arm only after that preflight passes, on S1, C1, B1, and scenarios 10, 11, and 13.

## 5. Estimated implementation scope

Authority preflight, including the validator, step runner, dispatcher, and scripted transcripts: on the order of one to two weeks for someone who already knows this tree. See `PR-DF_engine_reuse.md`. That range is a planning estimate.

Out of scope: rewriting `chat`, changing resolvers, shrinking the narration payload, repairing the 24 shared-pipeline failures, wiring downtime, adding an inventory ledger.

If the runner cannot call the resolvers without those rewrites, stop. The decision for that later cycle would be C — current architecture constraint. This cycle does not reach that decision, because the resolvers are already callable from the PR-DE harness without `chat`.

## 6. Order of experiments

1. **A oracle.** State tuples for the existing fixtures. Confirms the sheet and the save-path guard.
2. **Scripted B.** Gold plans and illegal plans. No model.
3. **Scripted C.** Gold tools and illegal tools, including a preview that must not change HP.
4. **Live subset.** Same model configuration. Publish sums, not per-call anecdotes.
5. **Framework.** Apply `PR-DF_decision_framework.md` only with those tables in hand.

## 7. When A stays the preferred player path

Keep A as the only player path when any of these is true:

- The preflight cannot show a clean authority pass for B and C on scenarios 4, 8, 13, and 14.
- On the live subset, B and C do not raise the unusual-action passes (scenarios 10 and 11) above A.
- Their median completed-turn input estimate on successful S1 and C1 runs is higher than A's, and usefulness is not better.
- The weighted score gap against A is under 8 after disqualifiers.
- The prototype starts to need a second writer.

A remaining expensive is not, by itself, a reason to leave A. It is a reason to keep measuring A and to try a supplement only under the next section.

## 8. When B or C should supplement or replace

**Supplement**, at the existing abstention seam, when all of these hold:

- A resolves the case as `generation` or `unsupported` for a reason the transcript shows is interpretive (no matching contract subject), not because the action is illegal.
- B or C completes the scenario sheet, including the refusals on 10, 13, and 14.
- The extra calls stay inside the budgets.
- The supplement is a fallback in front of the same resolvers, not a second world.
- The narration payload stays the shared one until a separate experiment.

The nearest insertion point is the branch in `establish_ordinary_gameplay_contract` that already retries interpretation after abstention. A supplement would replace that single proposal with a plan or a tool round only on that branch. Ordinary S1 turns would stay on A.

**Replace** A only when the live subset and the full scenario sheet have been scored, no disqualifier fired, the weighted gap is at least 8 in favor of one candidate, and completed-turn cost on successful S1 and C1 is lower or equal. This document does not claim those results.

Replacement still means the winner calls the current resolvers. It does not mean a new simulation.
