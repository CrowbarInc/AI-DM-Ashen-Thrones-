# ATGB-03C — Initial live conversational baseline continuation

Date: 2026-10-18. Evaluation only. Human review pending.

Captured 24/24 continuation turns. Combined with the 13 original S01–S03 turns, the baseline set contains 37/37 unique turns. Original S04 trial 1 remains a separate two-turn historical trial; total observations including it: 39. No conversational score, evaluated successes/failures, or improvement claim is established.

| Scenario | Trial | Captured/planned | Infrastructure | Review qualification |
| --- | ---: | ---: | --- | --- |
| S04 | 2 | 4/4 | completed | pending review |
| S05 | 1 | 4/4 | completed | pending review |
| S06 | 1 | 4/4 | completed | pending review |
| S07 | 1 | 4/4 | completed | opening delivery limited |
| S08 | 1 | 4/4 | completed | pending review |
| S09 | 1 | 2/2 | completed | opening delivery limited |
| S10 | 1 | 2/2 | completed | pending review |

## Readiness and preservation

Read the current Constitution, validation/handoff authorities, ATGB-01 design and rubric, adopted ATGB-02 specification/implementation/execution instructions, frozen ATGB-02A readiness, and ATGB-03/03A/03B reports. Current readiness passes all seven reviewed guarded dispatch owners and the pinned application source surface. Thirteen selected source files match the preserved ATGB-03B review ZIP. Corpus/baseline match original ATGB-03 hashes. All 552 protected snapshot files remain byte-identical, including original results, provider ledgers, reports, partial S04, production/harness sources and canonical campaign data. HEAD: `b012c3d7e5887fdfb09d10bb9cc0f0220de09df9`; extensive pre-existing dirty/untracked worktree retained. No commit made. Hashes and full initial status identify actual running bytes.

Frozen baseline: frontier-gate-v1, manifest 4197114379ba9c406d9b2135085eb605d8235fd9a34dcebe852b95451ef41ae9. Ten final provider-disabled preflights pass. Each attempted live scenario has its own fresh frozen-baseline store and live preflight, empty initial history and frontier_gate starting scene. See scenario_readiness.json and retained worker/job/state files. No canonical campaign store or previous conversation was reused.

## Execution and provider evidence

The unchanged production `POST /api/chat` TestClient path received approved fixture lines. This establishes API conversation evidence; browser-rendered UI was not tested. All configured roles remain gpt-4.1-mini with routing enabled and uncontrolled sampling. Credentials were verified available without exposing values. Returned model ids: ['gpt-4.1-mini-2025-04-14'].

Fresh limits: 48 application admissions, 900 elapsed seconds overall, at most 180 seconds per scenario worker, 120,000 total tokens (100,000 input / 20,000 output). Workers receive remaining campaign allowances and deadlines. Actual elapsed: 157.518 seconds. No live scenario retries or accounting safeguards bypassed. SDK transport retries remain unchanged and are not separately counted or absolutely bounded by application admissions. Input reservation uses the reviewed estimates; output caps and post-response usage checks remain active. Expenditure is unavailable without a verified pinned price; no dollar limit was fabricated.

Continuation accounting ATGB-03B-1: 23 admitted, 23 dispatched, 23 completed, 0 failed/interrupted completions, 0 pending, 0 unknown usage. Available tokens: 37222 input / 4137 output. Per-scenario raw lifecycle ledgers, response ids, returned model, provider latency, final process snapshots and reconciliation are preserved. Host metadata is independent in result.json and provider_accounting.json; do not replace it with ledger totals. Host latency available on 22/24 captured turns, range 15–4565 ms. See turn_latency.json for retries and individual values.

| Scenario | Admitted | Dispatched | Completed | Host count subtotal | Missing host-count turns | Input / output tokens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| S04 | 3 | 3 | 3 | 1 | 0 | 3154 / 345 |
| S05 | 5 | 5 | 5 | 3 | 0 | 7079 / 754 |
| S06 | 3 | 3 | 3 | 2 | 2 | 4057 / 407 |
| S07 | 4 | 4 | 4 | 4 | 0 | 7682 / 870 |
| S08 | 4 | 4 | 4 | 4 | 0 | 7926 / 834 |
| S09 | 2 | 2 | 2 | 2 | 0 | 3660 / 464 |
| S10 | 2 | 2 | 2 | 2 | 0 | 3664 / 463 |

S04/S05 each include one contract-interpretation and one expression request beyond the host subtotal; S06 includes one expression request beyond its known host subtotal. S06 has two unavailable host-performance records. S04.2 early-return performance is now present, but original S04.2 remains untouched and unavailable. Ledger completeness does not fill missing host latency or change its scope.

The original ATGB-03 ledger is completion-only: 12 observed requests, 21,531 input / 2,190 output tokens. It is an observed historical subtotal, not a certified admission upper bound. Those metrics are not merged with the new admission counts. The accounting version boundary is explicit even though both passes share HEAD. Accounting changes support observability; they do not establish conversational improvement.

## Infrastructure and setup limitations

Provider-disabled preparation retained a sandbox S01 session-save WinError 5, an unsandboxed S07 combat-save WinError 5, and one failing reset reproducibility check (103/104 focused checks passed). The isolated reset check passed with the bundled runtime; a final ten-scenario preparation passed. These are setup/environment failures, never assigned gameplay failures. The interrupted sandbox test attempt is also retained. No source repair or weakened expectation was used. Initial live dispatch was rejected before process creation by automatic approval review; the user explicitly approved the stated payload/destination/limits, recorded in export_authorization.json, and the authorized command then ran.

S07/S09 opening delivery is a setup/delivery limitation. Authored rain, banners, hawking and posture cues exist in the validated world/scene seeds. The fixture assumes availability. The approved worker silently resets and submits only the scenario lines, without delivering an opening to the player before the first turn. Thus world-state presence is verified; conversational opening delivery is absent in this API sequence; browser/journal visibility is unverified. No extra context was injected. S07's opening-dependent naturalness/banner criteria cannot support a fully valid scenario measurement under the assumed setup. S09's explicitly named ambiguity can be reviewed, but posture delivery cannot be presumed. Human reviewers must mark unsupported criteria uncertain/not evaluated instead of scoring missing setup as failed gameplay. See opening_context.json and exact transcripts.

## Human review and coverage

The approved generator produced continuation_worksheet.md/.json for 24 new observations and combined_baseline_worksheet.md/.json for 37 unique baseline turns. Original partial S04 has its own untouched worksheet/result and remains reviewable separately. Every judgment is pending: interpretation, response adequacy, authority, severity, clarification, continuity and conversation-level naturalness. 24 continuation observations are available for human inspection; six S07/S09 observations carry opening-context caveats, so evidence availability is not unconditional criterion eligibility. No raw technical-completion count is a gameplay success. Diagnostic zeros in raw harness reports are unreviewed placeholders, not measured absence of failures. The standard behavioral evidence packet at artifacts/atgb/atgb_03c/behavioral_evidence contains every exact continuation exchange, labeled runtime evidence with all judgments unreviewed; outcome-category selections are unmeasured rather than invented successes/failures.

Benchmarks/versions remain ATGB-02 / ATGB-01 / atgb-rubric-01 / ATGB-02-s07-held-out. Related and previously exposed held-out partitions stay separate. Independent generalization is not demonstrated; single trial, single environment, uncontrolled sampling, opening delivery and API-only observation limit comparability. No gameplay behavior, fixture expectation, rubric, architecture, provider payload, model configuration or production source was changed. Focused infrastructure/dispatch checks and real live API exchanges were run; no full-suite or broad regression claim is made.

## Stop and review

Execution is stopped after this capture/package pass. Review transcripts and setup limitations, then enter authorized human judgments using uncertain/not evaluated where needed. The live evidence capture does not make this a completed gameplay-performance measurement. No conversational repair or Product Realization campaign is initiated. Standard review: handoff/CURRENT_REVIEW.md and handoff/CURRENT_REVIEW.zip.
