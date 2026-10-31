# ATGB-03 — Initial live conversational baseline execution report

Date: 2026-10-18. Status: PARTIAL LIVE EXECUTION; STOPPED BY INFRASTRUCTURE ACCOUNTING; HUMAN REVIEW PENDING.

## Outcome

S01 passed its live infrastructure gate. S02 and S03 completed. S04 captured two turns, then the approved harness stopped with `provider_call_ceiling_not_observable` before S04.3. The campaign stopped there; S05–S10 were not attempted. Fifteen of 37 turns were captured. There is no aggregate gameplay score and no claim that gameplay improved. All three human judgments remain pending for every captured turn; the other 22 turns are not evaluated.

| Scenario | Captured/planned turns | Execution status |
| --- | --- | --- |
| S01 | 4/4 | completed |
| S02 | 4/4 | completed |
| S03 | 5/5 | completed |
| S04 | 2/4 | infrastructure_stop |
| S05 | 0/4 | not_attempted_after_infrastructure_stop |
| S06 | 0/4 | not_attempted_after_infrastructure_stop |
| S07 | 0/4 | not_attempted_after_infrastructure_stop |
| S08 | 0/4 | not_attempted_after_infrastructure_stop |
| S09 | 0/2 | not_attempted_after_infrastructure_stop |
| S10 | 0/2 | not_attempted_after_infrastructure_stop |

## Versions, authority and provenance

Benchmark ATGB-02; scenario ATGB-01; rubric atgb-rubric-01; partition ATGB-02-s07-held-out (25 visible / 4 related / 8 held-out). Frozen baseline frontier-gate-v1, pinned manifest SHA-256 4197114379ba9c406d9b2135085eb605d8235fd9a34dcebe852b95451ef41ae9. Repository HEAD b012c3d7e5887fdfb09d10bb9cc0f0220de09df9, with extensive pre-existing dirty/untracked work. `initial_git_status.txt` and `configuration_and_provenance.json` record that state and 240 execution/input hashes. The Development Constitution, Validation Evidence Standard, ATGB specification, design/rubric/catalog, execution instructions, readiness report and review-handoff standard governed this evaluation.

Preparation checked 31 approved harness/corpus files against readiness evidence and its preserved review ZIP. All ten provider-disabled preflights reproduced ATGB-02A's normalized state hash c12cb0dfe6a31980b4ecc00a59cc359a143a76452e517a36ad76753a6145561a. Existing focused checks: 24 passed outside the sandbox; separate existing provider-disabled chat check also passed. First setup-directory errors and the terminated sandbox retry are retained as environmental attempts. No broad/full-suite claim is made.

The first live command was rejected before process creation by automatic approval review. The user then explicitly approved resumption and the OpenAI data export. `resume_checks.json` records that approval and a fresh unchanged-source/configuration check. Historical blocked records remain under `pre_execution_blocked/`; they describe the earlier state, not the final outcome.

## Execution configuration and limits

Provider: OpenAI, https://api.openai.com/v1. All configured model roles remained gpt-4.1-mini; all recorded returned model ids are gpt-4.1-mini-2025-04-14. Existing model routing stayed enabled. No model, provider credential, production prompt or sampling setting was changed. Credentials were checked for availability without recording values. The production chat route POST /api/chat was invoked with the existing player-mode request through the approved TestClient worker. This is API conversation evidence, not browser-rendered UI validation.

Ceilings were 80 application provider requests and 1800 seconds overall, with S01 limited to 12 and 300. Scenario workers also had at most 300 seconds each within the remaining overall deadline. Existing provider accounting enforced its request guard and wrote raw usage records. No live attempt was retried by this campaign. Recorded scenario wall time: 35.632 seconds. No ceiling was exhausted; execution stopped because a count became unavailable. SDK-internal transport retries are not independently observable; application requests and elapsed limits are the stated bounds.

Every attempted scenario used a distinct frozen-baseline store, fresh reset and empty transcript. Live preflights passed for S01–S04. S01 reset evidence shows no selected interlocutor, discoveries, flags or prior transcript; all four expected responses were captured without an infrastructure error. Its four real OpenAI interpretation requests establish intended provider use, and isolation checks and canonical-file hashes establish that the player campaign was not used as a write store. Stage A acceptance is infrastructure acceptance only. Conversational mistakes did not trigger repair or block Stage B.

## Usage and latency

The raw provider ledger records 12 sent application requests: {"interpretation": 11, "expression": 1}. Every recorded request has consistent provider-reported token fields. Ledger token subtotal: 21531 input and 2190 output. These are observed usage for recorded requests only. Provider returned ids, latency and usage are preserved in provider_usage.jsonl and consolidated provider_telemetry.json.

The host turn summaries contain a known provider-call subtotal of 11, plus one unavailable turn count. They omit S03.2's expression request even though that request appears in the raw provider ledger (156 input / 9 output tokens). The two telemetry sources therefore do not agree in scope and must not be substituted silently. S04.2 has no performance object: call count, tokens, retries and response latency are unavailable, while its detail counters say zero interpretation/narration/retries. Missing performance data was not converted to zero or inferred from those detail counters.

Host response latencies were captured for 14 of 15 turns: range 89–4155 ms. S04.2 latency is unavailable. Per-turn host telemetry is preserved unchanged in turn_telemetry.json and the raw results. Recorded host retry counters are zero where present; the missing counter remains unavailable. Dollar cost is unavailable because no verified complete pricing/cost telemetry was supplied. Conservative call/time ceilings were used; no token estimate is represented as measured usage and no expenditure is invented.

## Infrastructure failure and setup limitations

S04.2 returned HTTP success and a captured response, but lacked resolution.metadata.performance. Before S04.3, the approved benchmark could no longer observe its configured call ceiling, so it refused further turns. This is an evaluation/infrastructure accounting limitation, not an assigned conversational failure. The earliest established instrumentation problem is the missing performance object on the captured turn; no gameplay cause is inferred or repaired. Actual text and log metadata remain available for independent review.

S07/S09 were not executed. Required opening-context delivery is NOT EVALUATED (delivered=null), not confirmed absent or successful. Preparation verifies authored opening seeds only. No extra narrative was inserted to satisfy either scenario. No missing starting condition received a conversational failure score. S04.3–S04.4 and every S05–S10 turn have no captured response and no conversational score.

## Unscored conversational observations

These are factual quotations and provenance notes, not rubric judgments. S01.2 answered “That has not been established in the information available to you.” S01.3 answered “I cannot tell who that is addressed to. Nothing has been attempted.” S03.3 asked “Which person do you mean: Gate Guard or Gate Serjeant or Tavern Runner? Nothing has been attempted.” S04.1 delivered the serjeant route-change sentence. S04.2 replied “I can't interpret that from the current scene without using information you have not been shown.” Whether each interpretation, response and authority choice satisfies the approved criteria is pending human review.

There were no narration-purpose requests in the recorded ledger. Most player-facing text was host-owned; one expression request was made. Live-provider mode does not imply every reply was model-generated. The report measures the existing combined production path and makes no claim of unconstrained generative narration quality.

## Human review package and reporting discipline

Raw per-scenario result.json, report.md, worksheet.md/.json, provider usage, worker/job JSON, complete isolated final state and session logs are preserved. S01/transcript.md is the smoke transcript; S02–S04/transcript.md preserve subsequent complete/partial conversations. Combined worksheet.md/.json uses the existing worksheet generator for the 15 captured turns and retains separate interpretation, response adequacy, authority, minor/major/critical severity, clarification, continuity and conversation-quality fields. No human judgments have been entered.

The campaign reporting mechanism writes evaluation_status.json and per-scenario review_status.md to distinguish pending judgments, uncaptured/not evaluated turns and the infrastructure stop. Evaluated-success, evaluated-failure and uncertain counts are null until supplied by an authorized human. The original report's diagnostic zeros for unreviewed failure categories are retained as raw evidence but must not be read as measured zero failures. This presentation correction changes only campaign reporting, not execution, scoring rules, expectations or production behavior. No exact prose matching was used.

## Preservation and comparability

All recorded execution/input sources and canonical campaign data remain byte-identical to the initial snapshot. No interpreter, routing, fallback, NPC knowledge, scenario expectation, scoring rubric, production behavior or model configuration was modified. There was no Product Realization repair campaign. Held-out content was previously exposed in ATGB-01, and no held-out scenario ran here; independent generalization is not measured. The partial single-trial, single-environment result does not establish the full live baseline. Existing PR-BL versus later PR-EG orientation history remains out of scope.

## Recommended next action

Review this partial evidence and the benchmark accounting limitation. A separately reviewed infrastructure correction/readiness check is needed before another baseline attempt; do not weaken the stop guard or modify gameplay to improve outcomes. An authorized human may score only captured, sufficiently supported turns, using uncertain or not evaluated when appropriate. The first baseline is not fully executed or fully scored. Stop this observation pass after preparing the standard review ZIP.
