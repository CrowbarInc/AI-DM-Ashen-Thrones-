# Campaign

Campaign: ATGB-03B Provider Accounting Integrity
Identifier: `atgb_03b_provider_accounting_integrity`
Date: 2026-10-18
Generated: 2026-10-18T21:41:50.805094+00:00
Purpose: Repair provider-request accounting across production dispatch owners and validate safe ATGB request bounds without live execution.

# Executive Summary

The existing budget owner now reserves allowance atomically and writes durable attempt identity before dispatch. Seven production owners, including startup preflight, share the lifecycle. Current source/readiness verification passes. Latest 59 lifecycle/owner/readiness checks pass; relevant regression run 225/227 with both failures reproduced before repair. One isolated Windows reset-write error passed targeted retry. No new provider requests, gameplay change, baseline run or score; original evidence preserved.

Objective status: `IMPLEMENTED; CURRENT-SOURCE ACCOUNTING READINESS VERIFIED; REVIEW PENDING; NO LIVE EXECUTION`.

# Changes Made

## Production changes

- Provider budget admission/reservation, durable lifecycle, stable identity and idempotent completion; integrations at all seven known owners.
- S04.2 early-return path exposes existing performance fields and separately scoped accounting metadata; reply/decisions unchanged.

## Validation changes

- Deterministic successful/failed/interrupted/refused dispatch tests for every owner; concurrency, incomplete telemetry, ledger failure, readiness mutation and ATGB isolation/budget tests.

## Tooling changes

- ATGB readiness verifies guarded SDK sites and reviewed source hashes. Worker reconciles admissions, preserves host telemetry, receives remaining campaign budgets and deadline.

## Documentation changes

- Complete dispatch inventory, root-cause/correction report, session orientation and scope/comparability review.

## Generated artifacts

- All test attempts, original-source comparison diff, payload AST checks, readiness/preservation records and standard handoff.

# What Was Tested

- **Focused tests:** Latest current lifecycle/dispatch-owner/readiness suite: 59 passed. ATGB accounting, infrastructure and readiness checks observed passing; see per-attempt JUnit records.
- **Broader relevant tests:** 227 relevant provider/gameplay/ATGB tests: 225 passed, 2 pre-existing failures reproduced using original budget/call_gpt in memory.
- **Full suite:** Not run.
- **Runtime validation:** Provider-disabled real chat/reset isolation and controlled provider stubs only; no live benchmark or real API request.
- **Model/runtime boundary:** Original SDK call arguments/model routing unchanged at all seven dispatch owners; real-provider behavior unmeasured.
- **New regressions:** None established in the exercised scope. One Windows reset file-replacement error passed targeted retry; original failure retained.
- **Pre-existing failures:** Exact routing metadata expectation and expression answer_sufficiency expectation both reproduce with pre-repair code.
- **Self-contained bundle review:** ZIP includes all seven changed owners and budget source, reviewed-source manifest, before-source diff, tests and every JUnit attempt, complete dispatch inventory, preservation/AST checks, readiness, and original accounting reports. Manifest payload hashes verified after packaging.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Review infrastructure correction, dispatch coverage, telemetry compatibility and known limitations before any separately authorized ATGB continuation.
- Do not infer gameplay improvement or assign original conversational scores from accounting tests. All human judgments remain pending.

# Known Problems / Unresolved Findings

## Campaign-specific

- Accounting is process-local and opt-in; active accounting requires fresh durable ledger. No automatic resume of prior ledger.
- JSONL consumers must recognize lifecycle events; historical completion-only records cannot be retroactively certified.
- Changed application sources/unknown dispatch sites require renewed readiness review.

## Pre-existing baseline

- Two reproduced regression failures remain unchanged.
- Windows isolated reset os.replace can fail transiently; targeted retry passed.
- Original ATGB baseline remains 15/37 captured, unscored, with S07/S09 opening delivery unmeasured.

# Missing Concepts / Future Capabilities

- No account-wide/distributed request quota or automatic crash-resume accounting is implemented.
- Complete live baseline and authorized human scoring remain outside this pass.

# What This Campaign Does NOT Prove

- Live-provider benchmark completion, conversational improvement, a gameplay score, new cost/latency measurements, or SDK transport-request counts.
- Completeness of historical ATGB-03 ledgers or same-trial S04 resume continuity.
- Budget safety of independently launched experimental utilities or arbitrary future provider code.

# Recommended Next Step

Await review. Do not run live ATGB, modify gameplay, or start Product Realization work. A later authorized continuation must use proven allowances, explicit deadlines and distinct S04 trial provenance.

# Review Bundle Contents

Bundle file count: `63`
Bundle ZIP size: `000000906393` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/reports/atgb_03b_provider_accounting_integrity.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/reports/atgb_03b_provider_accounting_integrity.md`.
- `support/artifacts/atgb/atgb_03/S03/provider_usage.jsonl`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03/S03/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03/S04/provider_usage.jsonl`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03/S04/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03/S04/transcript.md`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03/S04/transcript.md`.
- `support/artifacts/atgb/atgb_03a/accounting_readiness.json`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03a/accounting_readiness.json`.
- `support/artifacts/atgb/atgb_03a/original_accounting_analysis.json`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03a/original_accounting_analysis.json`.
- `support/artifacts/atgb/atgb_03b/accounting.xml`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03b/accounting.xml`.
- `support/artifacts/atgb/atgb_03b/accounting_final.xml`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03b/accounting_final.xml`.
- `support/artifacts/atgb/atgb_03b/accounting_fixed.xml`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03b/accounting_fixed.xml`.
- `support/artifacts/atgb/atgb_03b/accounting_readiness.json`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03b/accounting_readiness.json`.
- `support/artifacts/atgb/atgb_03b/accounting_scope.diff`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03b/accounting_scope.diff`.
- `support/artifacts/atgb/atgb_03b/accounting_verified.xml`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03b/accounting_verified.xml`.
- `support/artifacts/atgb/atgb_03b/audit_scope.py`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03b/audit_scope.py`.
- `support/artifacts/atgb/atgb_03b/dispatch_inventory.json`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03b/dispatch_inventory.json`.
- `support/artifacts/atgb/atgb_03b/environmental_worker_failure.json`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03b/environmental_worker_failure.json`.
- `support/artifacts/atgb/atgb_03b/package_review.py`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03b/package_review.py`.
- `support/artifacts/atgb/atgb_03b/preflight_retry.xml`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03b/preflight_retry.xml`.
- `support/artifacts/atgb/atgb_03b/preservation_before.json`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03b/preservation_before.json`.
- `support/artifacts/atgb/atgb_03b/preservation_checks.json`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03b/preservation_checks.json`.
- `support/artifacts/atgb/atgb_03b/prior_failures.xml`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03b/prior_failures.xml`.
- `support/artifacts/atgb/atgb_03b/regression.xml`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03b/regression.xml`.
- `support/artifacts/atgb/atgb_03b/reproduce_prior_failures.py`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03b/reproduce_prior_failures.py`.
- `support/artifacts/atgb/atgb_03b/scope_review.json`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03b/scope_review.json`.
- `support/artifacts/atgb/atgb_03b/source_before/game/api.py`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03b/source_before/game/api.py`.
- `support/artifacts/atgb/atgb_03b/source_before/game/api_upstream_preflight.py`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03b/source_before/game/api_upstream_preflight.py`.
- `support/artifacts/atgb/atgb_03b/source_before/game/expressive_dialogue.py`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03b/source_before/game/expressive_dialogue.py`.
- `support/artifacts/atgb/atgb_03b/source_before/game/gm.py`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03b/source_before/game/gm.py`.
- `support/artifacts/atgb/atgb_03b/source_before/game/host_constrained_candidates.py`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03b/source_before/game/host_constrained_candidates.py`.
- `support/artifacts/atgb/atgb_03b/source_before/game/live_chat_interpretation.py`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03b/source_before/game/live_chat_interpretation.py`.
- `support/artifacts/atgb/atgb_03b/source_before/game/provider_budget.py`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03b/source_before/game/provider_budget.py`.
- `support/artifacts/atgb/atgb_03b/source_before/game/semantic_interpreter.py`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03b/source_before/game/semantic_interpreter.py`.
- `support/artifacts/atgb/atgb_03b/source_before/game/unified_semantic_planning.py`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03b/source_before/game/unified_semantic_planning.py`.
- `support/artifacts/atgb/atgb_03b/source_before/tests/test_atgb_accounting.py`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03b/source_before/tests/test_atgb_accounting.py`.
- `support/artifacts/atgb/atgb_03b/source_before/tools/atgb/accounting.py`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03b/source_before/tools/atgb/accounting.py`.
- `support/artifacts/atgb/atgb_03b/source_before/tools/atgb/chat_worker.py`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03b/source_before/tools/atgb/chat_worker.py`.
- `support/artifacts/atgb/atgb_03b/source_before/tools/atgb/driver.py`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03b/source_before/tools/atgb/driver.py`.
- `support/artifacts/atgb/atgb_03b/surface_final.xml`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03b/surface_final.xml`.
- `support/artifacts/atgb/atgb_03b/validation_results.json`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `artifacts/atgb/atgb_03b/validation_results.json`.
- `support/data/validation/review_handoffs/atgb_03b_provider_accounting_integrity.json`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `data/validation/review_handoffs/atgb_03b_provider_accounting_integrity.json`.
- `support/development/reports/atgb_03_initial_live_baseline.md`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `development/reports/atgb_03_initial_live_baseline.md`.
- `support/development/reports/atgb_03a_provider_accounting.md`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `development/reports/atgb_03a_provider_accounting.md`.
- `support/docs/NEXT_SESSION.md`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `docs/NEXT_SESSION.md`.
- `support/game/api.py`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `game/api.py`.
- `support/game/api_upstream_preflight.py`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `game/api_upstream_preflight.py`.
- `support/game/expressive_dialogue.py`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `game/expressive_dialogue.py`.
- `support/game/gm.py`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `game/gm.py`.
- `support/game/host_constrained_candidates.py`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `game/host_constrained_candidates.py`.
- `support/game/live_chat_interpretation.py`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `game/live_chat_interpretation.py`.
- `support/game/provider_budget.py`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `game/provider_budget.py`.
- `support/game/semantic_interpreter.py`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `game/semantic_interpreter.py`.
- `support/game/unified_semantic_planning.py`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `game/unified_semantic_planning.py`.
- `support/tests/test_atgb_accounting.py`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `tests/test_atgb_accounting.py`.
- `support/tests/test_atgb_infrastructure.py`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `tests/test_atgb_infrastructure.py`.
- `support/tests/test_atgb_readiness.py`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `tests/test_atgb_readiness.py`.
- `support/tests/test_model_routing_runtime.py`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `tests/test_model_routing_runtime.py`.
- `support/tests/test_pr_eg_r3_r1_expression_semantics.py`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `tests/test_pr_eg_r3_r1_expression_semantics.py`.
- `support/tests/test_provider_accounting_integrity.py`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `tests/test_provider_accounting_integrity.py`.
- `support/tools/atgb/accounting.py`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `tools/atgb/accounting.py`.
- `support/tools/atgb/chat_worker.py`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `tools/atgb/chat_worker.py`.
- `support/tools/atgb/driver.py`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `tools/atgb/driver.py`.
- `support/tools/atgb/provider_accounting_integrity.json`: Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims. Canonical source: `tools/atgb/provider_accounting_integrity.json`.

## Explicit omissions

No explicitly requested file was omitted.

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
