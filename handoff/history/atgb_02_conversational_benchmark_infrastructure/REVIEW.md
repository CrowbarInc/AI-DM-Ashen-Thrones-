# Campaign

Campaign: ATGB-02 Conversational Benchmark Infrastructure
Identifier: `atgb_02_conversational_benchmark_infrastructure`
Date: 2026-10-18
Generated: 2026-10-18T20:30:00+00:00
Purpose: Implement the Ashen Thrones Gameplay Benchmark infrastructure from the ATGB-01 design, with S07 moved to held-out. Validate it with providers disabled. Do not run a live benchmark and do not change production gameplay.

# Executive Summary

Implementation outcome: fixtures for 37 turns, an isolated chat driver, a provider-disabled simulated mode, a provider-disabled host path, a human worksheet, and a result format. Original reproduction: not applicable; this pass repairs no gameplay failure. Related generalization: not applicable. Independent generalization: not evaluated. The held-out partition is stored and labeled previously exposed because those scenarios were already in the ATGB-01 review. Regression: 49 passed across playability, review-handoff, and validation-evidence tests; the full suite was not run. ATGB: no performance result. Provider-disabled validation captured 37 simulated turns and 4 host turns of S06. Both packages set gameplay_performance_claim to false. Known limitations: simulated mode does not call chat; host mode is not conversational competence; held-out turns are not unseen; no historical adapter and no dollar default. Remaining uncertainty: the live trial count and any future price ceiling are unset, and the PR-BL session orientation is still unreconciled with later PR-EG history. No gameplay improvement is claimed.

Objective status: `INFRASTRUCTURE READY — NO GAMEPLAY RESULT`.

# Changes Made

## Production changes

- No production gameplay module changed. game/ does not import the benchmark. evaluate_playability is not called.

## Validation changes

- Added tests/test_atgb_infrastructure.py. Playability scenarios, semantic calibration, and protected replay were not edited.

## Tooling changes

- Added tools/run_atgb.py and tools/atgb/. The driver posts to the existing POST /api/chat boundary in a subprocess and refuses unsafe data directories before reset.

## Documentation changes

- Added the ATGB-02 specification, execution note, and implementation report.
- Pointed docs/validation_evidence_standard.md at the implemented corpus and forbade a performance claim from infrastructure, host-only, or unscored output.
- Left the ATGB-01 catalog body in place and recorded that its index still lists S07 as development-visible.
- Updated docs/NEXT_SESSION.md. Did not start another Product Realization campaign.

## Generated artifacts

- Provider-disabled simulated run of all 37 turns at artifacts/atgb/atgb_02_infrastructure/.
- Provider-disabled host run of S06 at artifacts/atgb/atgb_02_host_probe/. Neither artifact is a gameplay benchmark result.

# What Was Tested

- **Focused tests:** 9 passed in tests/test_atgb_infrastructure.py. Covers fixture counts, catalog lines, isolation rejection, order, simulated labels, unavailable telemetry, worksheets, reproducibility, budget refusal, and one provider-disabled host scenario.
- **Broader relevant tests:** 49 passed across tests/test_playability_eval.py, tests/test_review_handoff.py, and tests/test_validation_evidence_standard.py.
- **Full suite:** Not run.
- **Runtime validation:** No live-provider execution. Original reproduction, related generalization, and independent generalization were not evaluated because this pass repairs no gameplay failure. Host S06 is infrastructure evidence only.
- **Model/runtime boundary:** No model was called. Provider-disabled host mode set ASHEN_DISABLE_PROVIDER_CALLS, ASHEN_DISABLE_LIVE_INTERPRETATION, and ASHEN_DISABLE_EXPRESSION_GENERATION, and removed the API key from the worker environment.
- **New regressions:** None observed in the focused or adjacent tests that were run.
- **Pre-existing failures:** Not reassessed. The full suite was not run. docs/product_realization_validation.md already had an uncommitted generalization paragraph; this pass does not claim that diff.
- **Self-contained bundle review:** The ZIP packages the specification, fixtures, harness, and provider-disabled reports. It contains no live-provider transcript and claims no gameplay performance result.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Accept or reject the ATGB-02 corpus and harness before any live baseline.
- The live trial count is still the design default of one. This pass does not choose a dollar ceiling.
- Held-out turns remain previously exposed. A later unexposed environment would be required before a strong generalization claim.
- The NEXT_SESSION product orientation versus later PR-EG history remains a separate maintenance item. This package does not decide it.

# Known Problems / Unresolved Findings

## Campaign-specific

- Simulated replies are a test double. They do not exercise POST /api/chat.
- The host performance counter can report a provider call for the provider-disabled narration fallback. The harness preserves the count and does not treat it as a sent request when tokens are null and the reply is stamped provider-disabled.
- The benchmark copy of world.json is the repository file plus the existing playthrough reset. It does not rebuild a pristine world from git.
- No historical compatibility adapter is implemented.

## Pre-existing baseline

- Playability scoring, semantic calibration, protected replay, and replay failure classification keep their existing authorities.
- Curfew hours, stew price, diegetic time passage, compound multi-action execution, and richer pronoun continuity remain outside current authored behavior.
- docs/NEXT_SESSION.md product orientation remains the 2026-09-26 PR-BL closeout. Later PR-EG history remains unreconciled.

# Missing Concepts / Future Capabilities

- A live-provider baseline and a completed human score sheet for that transcript.
- A provider price table. Cost stays unavailable until a run supplies prices and the host records token counts.
- An unexposed held-out environment. The current held-out turns were visible in the ATGB-01 review.
- A historical-build adapter. Older revisions are not comparable unless they can boot the same isolated store.

# What This Campaign Does NOT Prove

- That player-AI-DM communication improved.
- An Ashen Thrones Gameplay Benchmark performance result.
- That the scenarios would pass on the current build under a live model.
- Independent generalization from the held-out partition.
- Mechanical correctness of combat, inventory, economy, character creation, equipment, or advancement.
- That playability PASS and ATGB acceptability are the same judgment.
- That deterministic host behavior is natural conversational competence.
- That the PR-BL session orientation and later PR-EG history agree.

# Recommended Next Step

Stop. Review this infrastructure before any live ATGB baseline. Do not report a gameplay-performance result from the provider-disabled runs. Do not modify production gameplay to improve benchmark results, and do not start another Product Realization campaign from this package.

# Review Bundle Contents

Bundle file count: `35`
Bundle ZIP size: `000000156497` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/reports/atgb_02_implementation.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/reports/atgb_02_implementation.md`.
- `support/development/reports/atgb_02_benchmark_specification.md`: Adopted scope, the S07 partition move, the 25/4/8 counts, and the previously exposed held-out status. Canonical source: `development/reports/atgb_02_benchmark_specification.md`.
- `support/development/reports/atgb_02_execution.md`: How fixtures, isolation, provider-disabled mode, live budgets, results, and future environments work. Canonical source: `development/reports/atgb_02_execution.md`.
- `support/development/reports/atgb_01_scenario_catalog.md`: Behavioral source for the fixtures. Its index still lists S07 as development-visible. Canonical source: `development/reports/atgb_01_scenario_catalog.md`.
- `support/development/reports/atgb_01_conversational_benchmark_design.md`: Rubric atgb-rubric-01. The body is the historical proposal; ATGB-02 does not rewrite it. Canonical source: `development/reports/atgb_01_conversational_benchmark_design.md`.
- `support/development/reports/atgb_01_implementation_feasibility.md`: The reuse boundaries the driver kept: chat, isolated storage, and no second scorer. Canonical source: `development/reports/atgb_01_implementation_feasibility.md`.
- `support/data/validation/atgb/README.md`: How visible and held-out fixture directories are organized. Canonical source: `data/validation/atgb/README.md`.
- `support/data/validation/atgb/corpus.json`: Version, expected counts, and the written S07 discrepancy. Canonical source: `data/validation/atgb/corpus.json`.
- `support/data/validation/atgb/visible/S01.json`: Development-visible fixture. Behavioral criteria, not an exact reply. Canonical source: `data/validation/atgb/visible/S01.json`.
- `support/data/validation/atgb/visible/S02.json`: Development-visible fixture. Canonical source: `data/validation/atgb/visible/S02.json`.
- `support/data/validation/atgb/visible/S03.json`: Development-visible fixture. Canonical source: `data/validation/atgb/visible/S03.json`.
- `support/data/validation/atgb/visible/S04.json`: Development-visible fixture. Canonical source: `data/validation/atgb/visible/S04.json`.
- `support/data/validation/atgb/visible/S05.json`: Development-visible fixture. Canonical source: `data/validation/atgb/visible/S05.json`.
- `support/data/validation/atgb/visible/S06.json`: Development-visible IC/OOC fixture used by the host probe. Canonical source: `data/validation/atgb/visible/S06.json`.
- `support/data/validation/atgb/visible/S08.json`: Related-variation fixture. Not independent generalization. Canonical source: `data/validation/atgb/visible/S08.json`.
- `support/data/validation/atgb/held_out/S07.json`: Held-out by the ATGB-02 partition move. Previously exposed in the ATGB-01 review. Canonical source: `data/validation/atgb/held_out/S07.json`.
- `support/data/validation/atgb/held_out/S09.json`: Held-out fixture. Previously exposed. Canonical source: `data/validation/atgb/held_out/S09.json`.
- `support/data/validation/atgb/held_out/S10.json`: Held-out fixture. Previously exposed. Canonical source: `data/validation/atgb/held_out/S10.json`.
- `support/tests/test_atgb_infrastructure.py`: Provider-disabled and isolation checks. Not a gameplay score. Canonical source: `tests/test_atgb_infrastructure.py`.
- `support/tools/run_atgb.py`: Operator entry point. Live mode is refused without an explicit confirmation and ceilings. Canonical source: `tools/run_atgb.py`.
- `support/tools/atgb/__init__.py`: Version constants. Canonical source: `tools/atgb/__init__.py`.
- `support/tools/atgb/fixtures.py`: Fixture loader and count check. Canonical source: `tools/atgb/fixtures.py`.
- `support/tools/atgb/isolation.py`: Data-directory safeguard. Reset is refused until the store is isolated. Canonical source: `tools/atgb/isolation.py`.
- `support/tools/atgb/budget.py`: Call, token, time, and optional cost ceilings. No default dollar budget. Canonical source: `tools/atgb/budget.py`.
- `support/tools/atgb/driver.py`: Scenario order, simulated double, and subprocess launch. Canonical source: `tools/atgb/driver.py`.
- `support/tools/atgb/chat_worker.py`: Imports the game only after isolation and posts to POST /api/chat. Canonical source: `tools/atgb/chat_worker.py`.
- `support/tools/atgb/results.py`: Result schema and the report order that keeps critical failures visible. Canonical source: `tools/atgb/results.py`.
- `support/tools/atgb/worksheet.py`: Human worksheet. Three judgments stay separate. Canonical source: `tools/atgb/worksheet.py`.
- `support/docs/validation_evidence_standard.md`: ATGB claim boundary after the corpus was implemented. Infrastructure validation is not a performance result. Canonical source: `docs/validation_evidence_standard.md`.
- `support/docs/playability_validation.md`: Playability remains evaluate_playability. ATGB does not become a second scorer. Canonical source: `docs/playability_validation.md`.
- `support/docs/NEXT_SESSION.md`: Points at ATGB-02 and leaves the PR-BL versus PR-EG discrepancy unresolved. Canonical source: `docs/NEXT_SESSION.md`.
- `support/artifacts/atgb/atgb_02_infrastructure/report.md`: Simulated 37-turn package. Gameplay performance claim is false. Canonical source: `artifacts/atgb/atgb_02_infrastructure/report.md`.
- `support/artifacts/atgb/atgb_02_host_probe/report.md`: Provider-disabled host transcript summary for S06. Not a gameplay result. Canonical source: `artifacts/atgb/atgb_02_host_probe/report.md`.

## Explicit omissions

No explicitly requested file was omitted.

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
