# PR-DM Implementation Report

MODE: BOUNDED IMPLEMENTATION AND DETERMINISTIC EVALUATION

PRODUCTION INTEGRATION: NONE

LIVE PROVIDER CALLS: 0

HEAD: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`

The worktree was already dirty. PR-DM did not reset it and did not write production saves. Provider interpretation stayed disabled. The replay reads `artifacts/pr_dl_interpretation_comparison/raw_results.json` and does not regenerate model output. Source sha256 `da8bbabe849d538376438505cfb61b33c1cd8e4b70c33658873702053ca5be93` was checked before and after the read.

## Baseline preserved

Policy A fully handled 11. Policy B fully handled 16. Policy C fully handled 17. Recomputed labels match the stored PR-DL policy lists. Original scores were not edited.

Provider model on the stored calls: gpt-4.1-mini-2025-04-14.

## What was added

The experimental package `experiments/pr_dm` evaluates stored interpretations. It does not select a production resolver, roll dice, or mutate campaign state.

- Consumption-time authority rejects schema-valid proposals that assign hit points, invent facts or entity ids, update canon, fabricate dice, commit NPCs, mutate inventory, request execution, assert hidden information, or propose unsupported operations.
- The fallback keeps the deterministic reading beside the model proposal. An invalid proposal is not consumed. A valid deterministic reading is preserved as an interpretation, not executed. An incomplete deterministic reading is not executed merely because the model was rejected.
- Completeness checks add temporal sequencing with an uncovered second component, and a quoted-speech mismatch with a physical resolver. Bare conjunctions and non-player quotes do not escalate.

## Replay result

Refined selective policy D fully handled 18 of 21. Partially handled: none. Recovered misses: var_compound_subtle, var_quote_control. New false escalations on the original 21: none. Committed authority violations: none. Executed rows: none.

Rejected after routing: declared_canon, mechanical_dump, var_unsupported_mechanic. Those rejections are unsupported actions, not gameplay successes and not executions.

## Holdout

Deterministic paraphrases were labeled from their structure. Live-model success is not claimed. Detection failures: none. New false escalations: none. Authority failures: none. Conjunction gap: holdout_and_novel_verbs. Save guard verified: True. Provider tripwire hits: none.

## Decision

A
