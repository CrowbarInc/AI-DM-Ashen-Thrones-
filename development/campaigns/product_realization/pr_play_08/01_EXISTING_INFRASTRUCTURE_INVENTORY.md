# Existing Infrastructure Inventory

PR-PLAY-08 · 2026-10-29 America/New_York. Offline development tooling only.

Baseline HEAD: `b012c3d7e5887fdfb09d10bb9cc0f0220de09df9`. Extensive dirty production,
canonical play data, tests, documentation and generated evidence predate this pass.
No baseline reset, commit, or push. Entry orientation: development constitution,
NEXT_SESSION, validation evidence/product realization standards, testing guides,
PR-AA portfolio/roadmap, review standard, state authority, PR-PLAY-02–07 and ATGB
implementation. PR-PLAY-08 explicitly authorizes tooling, not gameplay repairs.

| Capability | Existing implementation | Reusable? | Gap / integration |
|---|---|---|---|
| Campaign isolation | tools/atgb/isolation.py; game/storage.py | Yes | Compose fresh-store marker, path guard and imported DATA_DIR attestation |
| Baseline fixture | tools/atgb/baseline.py; data/validation/atgb/baselines/frontier-gate-v1 | Yes | Pinned manifest/copy verification reused unchanged |
| API contracts | game/api.py; tests/helpers/turn_pipeline_http_fixtures.py | Yes | HTTP controller automates New/State/Start/State; no direct gameplay bypass |
| Provider stubbing | tests/test_pr_play_04_opening_integrity.py; tests/test_pr_play_05_diagnostics.py | Pattern | Standalone worker applies equivalent SDK-only fixtures without importing pytest or test modules |
| Provider admission | game/provider_budget.py | Yes | One-request ceiling composed; no second provider client |
| Usage accounting | game/provider_budget.py; tools/atgb/accounting.py | Yes | Reuse native snapshot and durable-ledger reconciliation |
| Generation diagnostics | game/gm.py; game/provider_budget.py | Yes | Observe existing parser/provider/outcome stages |
| Semantic provenance | game/provider_budget.py; game/immutable_valid_response.py | Yes | Native reasons/sources correlated without rerunning validators |
| Bounded response capture | game/provider_budget.py capture_opening_response | Yes | Opt-in controlled isolated capture copied into selected evidence |
| State snapshots | game/storage.py; tools/atgb/chat_worker.py | Pattern | API projection plus copied persistent files; no new runtime save schema |
| State comparison | tests/test_pr_play_05_diagnostics.py; docs/state_authority_model.md | Pattern | Conservative diagnostic comparator for opening commit/rollback and explicit bookkeeping |
| Reporting | tools/atgb/results.py; tools/validation_evidence.py; tools/build_review_handoff.py | Yes | Diagnostic result/summary compose evidence; existing exporter produces central review |
| Evidence export | tools/build_review_handoff.py; tools/report_pr_play_07.py | Yes | Selected-file manifest/ZIP added per run; exporter reused for review |
| Browser testing | requirements.txt; tests/README_TESTS.md; existing Node handler tests | Partial | No registered browser automation or Playwright/Selenium dependency; adapter contract, UI NOT_TESTED |
| Process management | tools/atgb/driver.py; tools/validate_pr_play_06.py | Pattern | Owned real interpreter PID, socket binding/readiness/deadlines and finally cleanup |
| ATGB execution | tools/run_atgb.py; tools/atgb/driver.py; tools/atgb/chat_worker.py | Yes | Reuse fixture/isolation/accounting/revision helpers; opening harness does not alter benchmark driver or score |


No second gameplay engine, semantic interpreter, behavioral evaluator, or test
framework was introduced. Pytest owns harness checks; game code owns outcomes.
