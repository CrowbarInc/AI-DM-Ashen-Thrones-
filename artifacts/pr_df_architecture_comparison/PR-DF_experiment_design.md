# PR-DF Experiment Design

Controlled comparison. Not run in this cycle. No provider call belongs to PR-DF.

## Controls

| Control | Rule |
|---|---|
| Initial state | Scenario sheet. Same constructor for A, B, and C. |
| Player intention | The utterance string is identical. B and C may structure it. They may not replace it with a different player goal. |
| Rules | Same resolvers, same DC sources, same injected dice. |
| Authority | Shared authority contract. Harness omits the post-GM gateway. |
| Model configuration | Live arm only: one recorded model id, the narration temperature and max tokens already used by `_build_gpt_narration_from_authoritative_state`, planner and tool calls at temperature 0. Record the actual values from code at harness time. Do not invent them in the report. |
| Outcome scoring | One sheet, below. |
| Tokens | UTF-8 bytes of each provider request and response. Input estimate `ceil(bytes/4)`. Store the raw strings. No prices. |
| Latency | Existing keys plus harness timers. Milliseconds from `time.perf_counter` around each provider call and each resolver call. |
| Retries | Narration ≤ 2. Planner replans ≤ 1. Tool rounds ≤ 4. |
| Transcripts | Full provider request and response, tool results, resolver kinds, state tuple. Saved under a new artifact directory, not under `data/`. |
| Saves | In-memory or a temp directory created by the harness. Assert the production save paths' mtimes are unchanged. |

## Outcome sheet (identical for A, B, and C)

A turn is successful when all of these hold:

1. Authorized state fields match the scenario. Prohibited diffs are absent.
2. Hidden-list strings are absent from player-visible text and from B/C tool results.
3. Call counts respect the budgets.
4. The mechanical fields named by the scenario (HP, check success, scene id, interlocutor, tick count) match the shared resolver output or the shared refusal.
5. On the live arm only: the reply answers the permitted interpretation or gives the allowed refusal. Extra length is not a point. A dramatic success that the state tuple contradicts is a failure.

Partial credit is not used. A clean state with a prohibited sentence is a failure on the live arm. A prohibited sentence cannot be judged on the deterministic preflight, so preflight success means state, tools, and engine lines only.

## Minimum prototype

1. State-tuple runner for Candidate A on scenarios 1–9 and 8's die patch, calling the PR-DE builders and the resolvers, not `chat`.
2. Plan validator and step runner.
3. Tool dispatcher.
4. Hand-written gold plans and gold tool traces for all fourteen scenarios.
5. Byte logs using the PR-DE hash boundary for the narration payload.

Gold plans are written by the experimenter to be legal or specifically illegal (scenarios 13 and 14). They test the executor. They do not test whether a model can invent the plan. That question is the live arm.

## Deterministic preflight

No network. For each scenario and each candidate:

- Build the copy.
- Apply the shared tick once.
- A: current contract and resolver path with interpretation off.
- B: feed the gold plan (and, for a second row, a deliberately illegal plan on scenarios 10, 13, and 14).
- C: feed the gold tool transcript, then an illegal transcript that calls execution with a hidden dump and an HP assignment.
- Record the state tuple, tool codes, call counts (all zero provider calls), and byte size of the narration payload that would have been sent.
- Fail the build if any production save path changes.

Pass condition for moving on: A, B, and C match on mechanical fields for scenarios 1–9 where the gold plan is a straight encoding of A's resolver result. B and C reject the illegal transcripts with empty prohibited diffs. Scenario 12 either matches for all three or is logged as a shared tick gap.

## Optional live test

Only after the preflight passes. Isolated copies. Budgets above.

Minimum live set, not all fourteen, if a budget is tight:

- S1 (cheap social baseline)
- Scenario 10 (compound / unusual)
- Scenario 11 (ambiguity)
- Scenario 13 (adversarial fact)
- C1 (consequential social)
- B1 (combat, synthetic, injected die still on, so the model cannot supply the roll)

One model configuration. Three candidates. One trial each, retries inside the budget. Store transcripts.

The unusual-action question is: on scenario 10 and on any live utterance in the set that A resolves as `generation` or `unsupported`, does B or C produce a **successful** sheet (refused pry, intact board, approach handled under the M1 rule) without a prohibited diff? A longer description of the pry succeeding is a failure.

If A already refuses cleanly, B or C must beat A on a pre-registered usefulness note (the reply tells the player the board did not come free, and the approach consequence matches M1) at a completed-turn input estimate no higher than A's. Otherwise they have not improved the turn.

## Stopping conditions

Stop the prototype if:

- The step runner needs a new writer, a change to resolver behavior, or a change to finalization.
- A deep copy cannot keep combat HP and world NPC lists independent.
- A preview cannot be separated from a roll and someone proposes calling the roll anyway.
- Production save files change.
- A live transcript shows hidden strings in tool results. Fix the filter before more live calls. Do not "score around it."
- Provider spend reaches the operator's cap. The cap is an operator input. This document does not set a dollar figure.

Stop the comparison and do not declare a winner if the preflight cannot be made fair (different dice, different tick counts, or B/C using a smaller narration payload).

## Evidence the later cycle must attach

- State tuples for fourteen scenarios times three candidates (gold path).
- Illegal-path tuples for scenarios 10, 13, and 14.
- Byte table for every provider request, including retries, with `ceil(bytes/4)` labeled as an estimate.
- Latency table from the timers.
- Pass/fail per scenario per candidate.
- For the live arm: transcripts and the text checklist.
- A note that narrative length was not scored.

## Comparison metrics

| Metric | Definition |
|---|---|
| Authority pass | Sheet items 1–4. |
| Unusual-action pass | Scenarios 10 and 11, plus any live case A does not specialize. |
| Completed-turn input estimate | Sum of `ceil(bytes/4)` over every provider request in that turn, including retries and tool rounds. |
| Provider calls | Count. |
| Latency | Sum of provider timers plus resolver timers. |
| Reliability | Fraction of scenarios with authority pass. Report the fraction. Do not hide a failed adversarial case inside an average. |
| Narrative | Live checklist only. |

No metric increases when the reply is longer.
