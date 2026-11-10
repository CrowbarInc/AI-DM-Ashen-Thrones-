# Campaign

Campaign: AT-OPT-02 Unresolved Retreat Routing and Verification Budget Enforcement
Identifier: `at_opt_02`
Date: 2026-11-08
Generated: 2026-11-08T17:57:10.817574+00:00
Purpose: Stop a simple unresolved retreat from entering primary narration when physical adjudication is off, and make the F3 HTTP verification profile enforce a 3000-token total before provider dispatch.

# Executive Summary

Verdict A/PASS. Failure class: implementation defect. With physical adjudication off, I step back from the notice board now returns the existing unsupported sentence, does not enter call_gpt, and is an operational refusal. Turn, position, and last_publication stay unchanged. With physical adjudication on, the existing retreat commit still sets position kind back. Unrelated unresolved speech, scene questions, and Gate Guard host speech keep their owners. The F3 HTTP script now calls apply_verification_budget before importing the app. A missing total is 3000. Total 200000 without a recorded override is rejected. An oversized estimate is refused before the fake provider runs. The bytes/3 estimate does not prove every admitted actual total stays under 3000. The historical 23377-token call was not repeated. Live provider calls: 0. New tests 20/20. Adjacent tests 118/118. Frozen holdout cases 28/28. Protected files 150/150. Do not start AT-OPT-03.

Objective status: `A/PASS`.

# Changes Made

## Production changes

- game/physical_adjudication.py recognizes a clear simple retreat and returns the existing unsupported sentence only when physical adjudication is disabled.
- game/api.py returns that refusal before the turn increment and blocks primary narration at the existing skip fall-through.
- game/publication_contract.py records the retreat refusal and a provider-budget refusal as operational refusals, so they do not become completed gameplay.
- game/verification_budget.py installs the verification ceiling into the existing admission environment variables.
- artifacts/pr_play_79df3/http_acceptance.py calls that profile instead of writing a 200000 total.

## Validation changes

- Added tests/test_at_opt_02_retreat_and_budget.py. 20 passed.
- Adjacent classification, publication-integration, and physical tests: 118 passed.
- Frozen 79D-F3 holdout cases: 28 passed when results were written under artifacts/at_opt_02. Direct pytest of that file stops on the historical-results write guard.

## Tooling changes

- artifacts/at_opt_02/rerun_holdout.py reruns the frozen holdout without writing the historical results file.

## Documentation changes

- Added the AT-OPT-02 reports under development/campaigns/product_realization/at_opt_02/.
- Prepended the AT-OPT-02 result to docs/NEXT_SESSION.md. Prior handoff history remains.

## Generated artifacts

- Added routing, regression, holdout, and protected-file JSON under artifacts/at_opt_02/.
- Generated this review handoff. The archive digest sidecar is written after the zip is sealed.

# What Was Tested

- **Focused tests:** pytest tests/test_at_opt_02_retreat_and_budget.py: 20 passed, 0 failed, 0 skipped.
- **Broader relevant tests:** pytest classification (27), 79b integration (81), flag-off physical (1), and 79c physical publication (9): 118 passed, 0 failed.
- **Full suite:** Not run. The historical focused 1065 suite was not launched.
- **Runtime validation:** Provider-free HTTP chat turns through the production chat route, physical commit on the enabled path, and admit_request against a fake invoke. No campaign opening.
- **Model/runtime boundary:** Live provider calls: 0. Narration and interpretation were patched or refused by admission. The bytes/3 estimate is not a provider tokenizer count.
- **New regressions:** No new failure in the 20, the 118, or the 28 holdout cases. No new protected-file identity.
- **Pre-existing failures:** Direct pytest of tests/test_pr_play_79df3_holdout.py cannot write artifacts/pr_play_79df3/holdout_results.jsonl because the storage guard blocks that historical path. The cases themselves passed in the redirected runner. The worktree was already dirty at entry.
- **Self-contained bundle review:** The bundle contains the five AT-OPT-02 reports, the routing and regression JSON, the redirected holdout result, and the protected-file rehash. No live play was produced.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Do not start AT-OPT-03 from this handoff.
- Do not treat the 3000 verification total as a production opening cap. Recorded openings are about 25294 input tokens.
- Do not read the historical 23377-token F3 call as a saving measured in this cycle.

# Known Problems / Unresolved Findings

## Campaign-specific

- Compounds, step-back-to, questions, quotations, and third-person step-back wording still use their previous route when physical adjudication is off.
- The pre-dispatch estimate can disagree with actual provider usage. A fitting estimate is not proof the actual total stays under 3000.
- The HTTP script's continuation_advances check still describes the pre-correction publication. The script was not re-run.

## Pre-existing baseline

- Primary narration payloads remain opening-scale when a turn is still eligible for that route.
- The classification harness still passes explicit 100000/200000 ceilings when a test asks for them.
- HEAD does not uniquely identify the executable source because the worktree was already dirty.

# Missing Concepts / Future Capabilities

- A live measurement of the token delta for this retreat, which this cycle deliberately did not take.
- Pre-dispatch logging of the input estimate, which was already noted in AT-OPT-01 and was not added here.

# What This Campaign Does NOT Prove

- It does not prove a newly measured token saving against the historical 23377-token request.
- It does not prove that every admitted provider request stays under 3000 actual tokens.
- It does not prove the retreat pattern covers every physical sentence.
- It does not prove a Gameplay Benchmark result. No benchmark was run.
- The new routing tests were authored with the fix. They are not independent held-out evidence. The frozen 28-case holdout does not include this retreat sentence.

# Recommended Next Step

Stop. Do not start AT-OPT-03. Do not open PR-PLAY-80. Do not put the 3000 verification total on production openings.

# Review Bundle Contents

Bundle file count: `13`
Bundle ZIP size: `000000062674` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/campaigns/product_realization/at_opt_02/SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/campaigns/product_realization/at_opt_02/SUMMARY.md`.
- `support/development/campaigns/product_realization/at_opt_02/ROUTING_CHANGE.md`: Routing boundary, before and after, and the preserved enabled path. Canonical source: `development/campaigns/product_realization/at_opt_02/ROUTING_CHANGE.md`.
- `support/development/campaigns/product_realization/at_opt_02/BUDGET_ENFORCEMENT.md`: Verification ceiling path, admission behavior, and estimate uncertainty. Canonical source: `development/campaigns/product_realization/at_opt_02/BUDGET_ENFORCEMENT.md`.
- `support/development/campaigns/product_realization/at_opt_02/REGRESSION_RESULTS.md`: Commands, counts, and the holdout write-guard note. Canonical source: `development/campaigns/product_realization/at_opt_02/REGRESSION_RESULTS.md`.
- `support/development/campaigns/product_realization/at_opt_02/INTEGRITY.md`: Branch, dirty-tree preservation, and the zero-provider confirmation. Canonical source: `development/campaigns/product_realization/at_opt_02/INTEGRITY.md`.
- `support/artifacts/at_opt_02/baseline_routing.json`: Provider-free eligibility before the routing edit. Canonical source: `artifacts/at_opt_02/baseline_routing.json`.
- `support/artifacts/at_opt_02/routing_after.json`: Route selected after the correction, including negative controls. Canonical source: `artifacts/at_opt_02/routing_after.json`.
- `support/artifacts/at_opt_02/regression_results.json`: Machine-readable pass counts and budget decisions. Canonical source: `artifacts/at_opt_02/regression_results.json`.
- `support/artifacts/at_opt_02/holdout_rerun.json`: Frozen 28-case holdout redirected away from the historical results file. Canonical source: `artifacts/at_opt_02/holdout_rerun.json`.
- `support/artifacts/at_opt_02/protected_rehash.json`: 150 protected files unchanged. Canonical source: `artifacts/at_opt_02/protected_rehash.json`.
- `support/docs/NEXT_SESSION.md`: Authoritative orientation after this cycle. Prior sections are preserved. Canonical source: `docs/NEXT_SESSION.md`.

## Explicit omissions

No explicitly requested file was omitted.

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
