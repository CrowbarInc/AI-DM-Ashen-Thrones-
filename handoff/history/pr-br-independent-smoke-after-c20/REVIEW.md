# Campaign

Campaign: PR-BR — Independent 10-Turn Synthetic Smoke After Continuation 20
Identifier: `pr-br-independent-smoke-after-c20`
Date: 2026-10-01
Generated: 2026-10-02T01:37:35.076133+00:00
Purpose: Independent 10-turn playability smoke of the product as it exists after Continuation 20. No behavior changes. No repair. No 4x10 gate. PR-BR remains open.

# Executive Summary

One isolated frontier-gate session, ten gameplay turns, no product edits. Final manual PASS 8/10. Initial manual PASS 7/10. Contracts: 5 correct, 3 partial, 2 incorrect. Accepted text matched emitted text on all 10 turns. Unsupported authoritative facts emitted: 0. Incidental bindings: 0. Stale-interlocutor fallbacks: 0. Consequential unsupported entities: 0. Rejected-response commits: 0. Two manual failures, different mechanisms, each once: a JSON document sealed as a hard-valid reply, and a leading-clause act that dropped the player's questions. Authority watchlist repeated incidental misclassification: NO. READINESS: READY FOR FULL 4x10 SYNTHETIC GATE. The gate was not run. HUMAN PLAYTEST: NOT AUTHORIZED. PR-BR: STILL OPEN. HEAD d31beb7d73dd4fda0f22184a6a69b947b5f470ff.

Objective status: `OPEN`.

# Changes Made

## Production changes

- No changes in this category.

## Validation changes

- No changes in this category.

## Tooling changes

- artifacts/pr_br_independent_smoke/run_post_c20_session.py is a validation harness only. It does not change gameplay behavior.

## Documentation changes

- docs/audits/PR-BR_post_generation_transformation_boundary_discovery.md gains the independent smoke section.

## Generated artifacts

- artifacts/pr_br_independent_smoke/20261002T012905Z holds the isolated session, transcript, contracts, candidates, and audit.

# What Was Tested

- **Focused tests:** Not a deterministic band. This cycle is the independent smoke.
- **Broader relevant tests:** Not run.
- **Full suite:** Not run.
- **Runtime validation:** 10/10 gameplay turns in one isolated session. Opening plus chat through the product API. No early stop. No rerun.
- **Model/runtime boundary:** Opening generation 1. Gameplay response generations 12, including 2 regenerations. Interpretation calls 8. Synthetic-player model calls 0. Evaluator model calls 0.
- **New regressions:** No product patch, so no new regression suite result. Live manual failures: turn 8 raw JSON sealed as valid; turn 9 questions dropped by leading-clause segmentation.
- **Pre-existing failures:** Not re-scored. The smoke did not replay prior failure strings.
- **Self-contained bundle review:** Not performed.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Readiness judgment is READY FOR FULL 4x10 SYNTHETIC GATE despite contract correctness of 5/10, because manual play is 8/10 and the critical architectural counters are zero. A reviewer may instead treat the two contract misses as a narrow defect and hold the gate.
- Do not start a focused continuation solely for the two imperfect turns unless external review rejects that judgment.
- PR-BR remains open. Do not start PR-BS. Do not run the 4x10 gate in this cycle. Human playtest is not authorized.

# Known Problems / Unresolved Findings

## Campaign-specific

- Turn 8 emitted a JSON document and hard validation sealed it.
- Turn 9 committed only 'I follow their glance.' and did not answer the questions.
- Turn 5's contract stayed an unresolved clarification on the guard, while the accepted prose did read the board.
- Discourse: active_claim labels are fragments, the turn 10 interlocutor label stayed 'Threadbare watcher' after the id moved to gate_serjeant, and the notice board never became active_inspected.

## Pre-existing baseline

- The local evaluator marked five manually acceptable turns as player_intent_addressed failures.

# Missing Concepts / Future Capabilities

- None recorded.

# What This Campaign Does NOT Prove

- Does not prove 4x10 synthetic-gate health. The gate was not run.
- Does not prove contract correctness at the strong-evidence bar of 8/10.
- Does not authorize a human playtest.
- Does not prove the authority classifier never misses a consequential sentence. It shows no repeated incidental-bucket family in this session.

# Recommended Next Step

External review. If the readiness judgment stands, the next cycle may run the full 4x10 synthetic gate. Do not run it from this cycle. Do not close PR-BR. Do not start PR-BS. Do not playtest with a human.

# Review Bundle Contents

Bundle file count: `25`
Bundle ZIP size: `000000191770` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/docs/audits/PR-BR_post_generation_transformation_boundary_discovery.md`: Primary campaign standard/report used to orient the review. Canonical source: `docs/audits/PR-BR_post_generation_transformation_boundary_discovery.md`.
- `support/artifacts/pr_br_independent_smoke/20261002T012905Z/audit.md`: Smoke audit: contracts, candidates, authority, persistence, and the readiness decision. Canonical source: `artifacts/pr_br_independent_smoke/20261002T012905Z/audit.md`.
- `support/artifacts/pr_br_independent_smoke/20261002T012905Z/visible.md`: Full player-visible opening and ten-turn transcript. Canonical source: `artifacts/pr_br_independent_smoke/20261002T012905Z/visible.md`.
- `support/artifacts/pr_br_independent_smoke/20261002T012905Z/review_index.json`: Per-turn contracts, routing, hard validation, discourse slots, and authority flags. Canonical source: `artifacts/pr_br_independent_smoke/20261002T012905Z/review_index.json`.
- `support/artifacts/pr_br_independent_smoke/20261002T012905Z/isolation.json`: Clean-session proof before Turn 1. Canonical source: `artifacts/pr_br_independent_smoke/20261002T012905Z/isolation.json`.
- `support/artifacts/pr_br_independent_smoke/20261002T012905Z/preflight.json`: HEAD, working-tree status, and upstream preflight. Canonical source: `artifacts/pr_br_independent_smoke/20261002T012905Z/preflight.json`.
- `support/artifacts/pr_br_independent_smoke/20261002T012905Z/summary.json`: Model-call accounting for the scored session. Canonical source: `artifacts/pr_br_independent_smoke/20261002T012905Z/summary.json`.
- `support/artifacts/pr_br_independent_smoke/20261002T012905Z/opening.json`: Player-visible opening and authoritative initial state. Canonical source: `artifacts/pr_br_independent_smoke/20261002T012905Z/opening.json`.
- `support/artifacts/pr_br_independent_smoke/20261002T012905Z/generation_calls.json`: Opening, initial, and regeneration model texts. Canonical source: `artifacts/pr_br_independent_smoke/20261002T012905Z/generation_calls.json`.
- `support/artifacts/pr_br_independent_smoke/20261002T012905Z/interpretation_calls.json`: Structured interpretation outputs. Canonical source: `artifacts/pr_br_independent_smoke/20261002T012905Z/interpretation_calls.json`.
- `support/artifacts/pr_br_independent_smoke/20261002T012905Z/persona.md`: Player instructions. No C18-C20 findings. Canonical source: `artifacts/pr_br_independent_smoke/20261002T012905Z/persona.md`.
- `support/artifacts/pr_br_independent_smoke/20261002T012905Z/inbox.jsonl`: Turn-by-turn player lines and the reason each was chosen. Canonical source: `artifacts/pr_br_independent_smoke/20261002T012905Z/inbox.jsonl`.
- `support/artifacts/pr_br_independent_smoke/20261002T012905Z/turns/turn_01.json`: Turn 1 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_independent_smoke/20261002T012905Z/turns/turn_01.json`.
- `support/artifacts/pr_br_independent_smoke/20261002T012905Z/turns/turn_02.json`: Turn 2 candidate, rejected first attempt, and regeneration. Canonical source: `artifacts/pr_br_independent_smoke/20261002T012905Z/turns/turn_02.json`.
- `support/artifacts/pr_br_independent_smoke/20261002T012905Z/turns/turn_03.json`: Turn 3 candidate, contract, and emission. Canonical source: `artifacts/pr_br_independent_smoke/20261002T012905Z/turns/turn_03.json`.
- `support/artifacts/pr_br_independent_smoke/20261002T012905Z/turns/turn_04.json`: Turn 4 candidate, contract, and emission. Canonical source: `artifacts/pr_br_independent_smoke/20261002T012905Z/turns/turn_04.json`.
- `support/artifacts/pr_br_independent_smoke/20261002T012905Z/turns/turn_05.json`: Turn 5 invented rule, rejection, and accepted reading. Canonical source: `artifacts/pr_br_independent_smoke/20261002T012905Z/turns/turn_05.json`.
- `support/artifacts/pr_br_independent_smoke/20261002T012905Z/turns/turn_06.json`: Turn 6 candidate, contract, and emission. Canonical source: `artifacts/pr_br_independent_smoke/20261002T012905Z/turns/turn_06.json`.
- `support/artifacts/pr_br_independent_smoke/20261002T012905Z/turns/turn_07.json`: Turn 7 candidate, unresolved gate binding, and emission. Canonical source: `artifacts/pr_br_independent_smoke/20261002T012905Z/turns/turn_07.json`.
- `support/artifacts/pr_br_independent_smoke/20261002T012905Z/turns/turn_08.json`: Turn 8 JSON candidate sealed as hard-valid. Canonical source: `artifacts/pr_br_independent_smoke/20261002T012905Z/turns/turn_08.json`.
- `support/artifacts/pr_br_independent_smoke/20261002T012905Z/turns/turn_09.json`: Turn 9 leading-clause contract and unanswered questions. Canonical source: `artifacts/pr_br_independent_smoke/20261002T012905Z/turns/turn_09.json`.
- `support/artifacts/pr_br_independent_smoke/20261002T012905Z/turns/turn_10.json`: Turn 10 serjeant answer, discourse label, and authority rows. Canonical source: `artifacts/pr_br_independent_smoke/20261002T012905Z/turns/turn_10.json`.
- `support/artifacts/pr_br_independent_smoke/20261002T012905Z/isolated_data/data/session.json`: Final discourse, threadbare runtime slot, and claim fragments. Canonical source: `artifacts/pr_br_independent_smoke/20261002T012905Z/isolated_data/data/session.json`.

## Explicit omissions

- `docs/audits/PR-BR_post_generation_transformation_boundary_discovery.md`: duplicate content of docs/audits/PR-BR_post_generation_transformation_boundary_discovery.md; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
