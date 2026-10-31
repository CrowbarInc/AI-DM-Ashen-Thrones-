# ATGB-03 — Initial live conversational baseline execution report

Date: 2026-10-18. Status: BLOCKED BEFORE LIVE EXECUTION. This is an incomplete evaluation campaign, not an established baseline or a scored gameplay result.

## Outcome and blocker

The S01 live command was rejected by automatic approval review before process creation. The stated reason was that benchmark/gameplay payloads would be exported to OpenAI and explicit authorization for that data export and destination was required. No live provider requests were issued by this campaign. Do not bypass the rejection. Explicit approval for transmission to OpenAI is needed before the prepared command can run.

Stage A was not executed, so its acceptance criteria are not evaluated. Stage B was not started. There are no live transcripts, live responses, token measurements, retries, response latencies or gameplay scores. All ten scenarios and all 37 turns are NOT EVALUATED. Human judgments remain pending; no capability has an evaluated zero-failure result.

## Authority and configuration

Reviewed the Development Constitution, Validation Evidence Standard, ATGB design/rubric, scenario catalog, implementation specification, execution instructions, ATGB-02A readiness report and standard review handoff requirements. The explicit ATGB-03 request supersedes the prior orientation's instruction to await the request before live execution; the separate automatic approval rejection remains binding.

Benchmark ATGB-02; scenario ATGB-01; partition ATGB-02-s07-held-out; rubric atgb-rubric-01; frozen baseline frontier-gate-v1. Partition counts: 25 visible, 4 related, 8 held-out. Repository HEAD: b012c3d7e5887fdfb09d10bb9cc0f0220de09df9. The worktree was already extensively dirty and untracked. HEAD alone does not identify running bytes: configuration_and_provenance.json records 240 execution/input hashes, and initial_git_status.txt records the initial worktree. Do not commit or revert pre-existing work.

OpenAI is the configured provider (https://api.openai.com/v1); all default, high-precision and retry-escalation model roles are gpt-4.1-mini, with existing routing enabled. Production uses OpenAI SDK Responses and chat-completion paths. Required API-key availability was checked as a boolean; no key was recorded or modified. Provider-disable flags were unset in the live process environment. No sampling or model settings were changed. The harness reports sampling as uncontrolled; individual production owners may set their own parameters.

## Readiness and validation

All 31 checked approved harness/corpus files match ATGB-02A source hashes or its preserved review ZIP. The pinned manifest and all seven frozen input files validate. Ten provider-disabled preflights pass, with the same normalized starting-state hash as ATGB-02A: c12cb0dfe6a31980b4ecc00a59cc359a143a76452e517a36ad76753a6145561a. The existing production chat regression passed outside the sandbox with providers disabled. Full focused readiness/infrastructure checks: 24 tests, 0 failures, 0 errors, 0 skipped. No full repository suite or gameplay evaluation was run.

The first test attempt used a missing parent for the pytest basetemp directory: 5 tests passed and 19 failed at setup. The parent was created and the attempt preserved. The sandboxed retry stalled on the known host-chat environment boundary; the separately authorized provider-disabled checks outside the sandbox passed. These are execution-environment findings, not conversational failures.

Canonical campaign data and all 240 execution/input sources remain byte-identical to the recorded initial state. Scenario stores use the approved isolated data path and reset. The provider-disabled checks do not establish live isolation success; that remains a Stage A acceptance requirement.

## Prepared execution bounds

Prepared campaign wrapper execute.py calls the approved harness without changing its code. Planned total ceiling: 80 application-level provider requests and 1800 elapsed seconds, including the S01 smoke subset of 12 requests and 300 seconds. Each scenario has an independent isolated store. The existing provider accounting guards the per-process request ceiling and writes provider records. The parent passes the remaining campaign allowance between scenarios. Campaign evidence retains stores, raw worker/job JSON, state slices and provider accounting. No failed live attempt is retried automatically.

Cost is unavailable without reliable complete token accounting and a price table; no expenditure estimate is invented. Conservative request/time limits therefore apply. Existing provider accounting also checks token availability; configured high token guardrails prevent its small manual-run defaults from silently truncating this benchmark. Actual token counts would still come only from provider records. SDK-internal transport retries are not independently measured by application-level counters; the elapsed timeout bounds a stalled worker. Usage from an interrupted request may be unavailable. These limitations must remain visible in any resumed live report.

## Scenario status and opening context

scenario_status.json lists every scenario as not attempted due to the approval blocker, with its passing machine preflight separately recorded. S07 and S09 required opening-context delivery is NOT EVALUATED: no player-facing live conversation ran. The silent reset establishes authored seeds, not delivery. No narrative context was injected and no missing setup was scored as conversational failure.

## Human review and evidence

worksheet_template.md/.json use the existing worksheet generator for all 37 expected turns, explicitly labelled UNEXECUTED TEMPLATE. There are no responses to score. Interpretation, response adequacy and authority remain separate; severity, clarification and continuity remain unscored. Conversation-level qualitative fields remain blank. After execution, generate actual worksheets from each live result using the existing harness. Reviewers must distinguish pass, fail, uncertain, unchecked/not evaluated, and infrastructure/setup failure, and preserve minor/major/critical severity. Fluency and authorized content do not establish response adequacy.

Raw preflight result/report/worksheets are preserved as infrastructure evidence only. Their legacy diagnostic zero counts do not establish zero conversational failures. The campaign status and template explicitly say NOT EVALUATED; no live report requiring a reporting-code correction was produced. No success/failure examples, severity judgments, or unscored conversational observations can be supplied without live exchanges. There is no gameplay-performance or improvement claim.

## Comparability and unresolved issues

Held-out scenarios were previously exposed in ATGB-01 and cannot establish fully independent generalization. This is one environment, no repeated live trial, and no human scoring. Dirty-worktree hashes are needed alongside HEAD. S07/S09 delivery remains unresolved. Existing PR-BL versus later PR-EG session-orientation history remains outside scope. No semantic interpreter, routing, fallback, NPC knowledge, scenario expectations, model configuration or production gameplay was changed.

## Next action

Obtain explicit approval to send the frozen benchmark inputs, authored world/scenario context and isolated conversation history to OpenAI at https://api.openai.com/v1 under the stated limits. Then recheck readiness/source hashes and configuration, execute S01 once, inspect actual provider evidence and isolation, and proceed only if infrastructure acceptance succeeds. Do not repair gameplay. Stop after live execution and review-package preparation; scoring requires an authorized human reviewer.
