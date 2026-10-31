# Campaign

Campaign: PR-BR — Full 4×10 Synthetic Playability Gate
Identifier: `pr-br-full-4x10-synthetic-gate`
Date: 2026-10-01
Generated: 2026-10-02T03:02:43.819136+00:00
Purpose: Release-candidate 4x10 synthetic playability gate after Continuation 20. No behavior changes. No repair. No rerun. PR-BR remains open.

# Executive Summary

Four isolated frontier-gate sessions, 40/40 gameplay turns, no product edits. Final manual PASS 32/40. Initial manual PASS 32/40. Contracts: 6 correct, 18 partial, 16 incorrect. Partial contracts all still played. Incorrect contracts failed play on 6 turns. Accepted text matched emitted text on all 40 turns. Post-seal mismatches: 0. Unsupported consequential entities: 0. Stale binding fallbacks: 0. Rejected-response commits: 0. Structured-output leaks: 0. Two recurrent gameplay mechanisms: ordinary inspections replaced by one wear sentence (C10, D3), and a sealed speaker who is not the person addressed (B2, B9, C8). Sentence fragments were bound as incidental people in every persona. One roster name, Eldrin Voss, was emitted as a posted fact. DECISION: PR-BR SYNTHETIC GATE FAILED — MULTIPLE SYSTEMIC DEFECTS REMAIN. HUMAN PLAYTEST: NOT AUTHORIZED. PR-BR: STILL OPEN. HEAD d31beb7d73dd4fda0f22184a6a69b947b5f470ff.

Objective status: `OPEN`.

# Changes Made

## Production changes

- No changes in this category.

## Validation changes

- No changes in this category.

## Tooling changes

- artifacts/pr_br_full_gate/run_gate_session.py is a validation harness only. It does not change gameplay behavior.

## Documentation changes

- docs/audits/PR-BR_post_generation_transformation_boundary_discovery.md gains the full 4x10 gate section.

## Generated artifacts

- artifacts/pr_br_full_gate/20261002T021950Z holds four isolated sessions, transcripts, contracts, and the audit.

# What Was Tested

- **Focused tests:** Not a deterministic band. This cycle is the 4x10 synthetic gate.
- **Broader relevant tests:** Not run.
- **Full suite:** Not run.
- **Runtime validation:** 40/40 gameplay turns in four isolated sessions. Opening plus chat through the product API. No early stop. No rerun.
- **Model/runtime boundary:** Opening generation 4. Gameplay initial 40. Gameplay retry 8. Interpretation 15. Product synthetic-player calls 0. Evaluator model calls 0. Operator player-selection calls outside the product: 40.
- **New regressions:** No product patch. Live manual failures: 8/40 final. Recurrent: wear-sentence safe fallback; wrong speaker including one catalog grimace.
- **Pre-existing failures:** Not re-scored. The gate did not replay prior failure strings.
- **Self-contained bundle review:** Not performed.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- The manual pass count is 32/40, at the approximate strong-pass line, while two mechanisms recurred across personas. The decision is FAILED — MULTIPLE SYSTEMIC DEFECTS REMAIN rather than a pass.
- A reviewer may instead treat the wear-sentence pair as the only narrow defect and the wrong-speaker turns as isolated. That would be decision B, still not a pass.
- PR-BR remains open. Do not start PR-BS. Do not implement a repair from this cycle. Human playtest is not authorized.

# Known Problems / Unresolved Findings

## Campaign-specific

- C10 and D3 emitted the same safe line about the wear after both inspection candidates were rejected as interaction-incomplete.
- B2 sealed a captain reply to a player who was still questioning the runner.
- B9 replaced the generated answer with a catalog grimace before the immutable seal.
- C8 turned a look into stranger speech.
- Every persona stored at least one sentence fragment as an incidental person.
- D1 stated Eldrin Voss as the roster name of the missing patrol leader.

## Pre-existing baseline

- The local evaluator marked 16 manually acceptable turns as failures and passed 5 manual failures.

# Missing Concepts / Future Capabilities

- None recorded.

# What This Campaign Does NOT Prove

- Does not prove the stack is ready for a human playtest.
- Does not prove contract correctness. Correct contracts were 6/40.
- Does not authorize a repair or Continuation 21.
- Does not prove the authority classifier catches every consequential sentence. It missed the Eldrin Voss roster line.

# Recommended Next Step

External review. Do not repair, rerun, or playtest with a human from this cycle. Do not close PR-BR. Do not start PR-BS.

# Review Bundle Contents

Bundle file count: `85`
Bundle ZIP size: `000000430597` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/docs/audits/PR-BR_post_generation_transformation_boundary_discovery.md`: Primary campaign standard/report used to orient the review. Canonical source: `docs/audits/PR-BR_post_generation_transformation_boundary_discovery.md`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/audit.md`: Gate audit: contracts, manual review, authority, discourse, and the decision. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/audit.md`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/freeze.json`: HEAD, worktree, model names, and file hashes frozen before Session A. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/freeze.json`.
- `support/artifacts/pr_br_full_gate/personas/persona_a.md`: Player persona. No contracts, validators, or prior-session findings. Canonical source: `artifacts/pr_br_full_gate/personas/persona_a.md`.
- `support/artifacts/pr_br_full_gate/personas/persona_b.md`: Player persona. No contracts, validators, or prior-session findings. Canonical source: `artifacts/pr_br_full_gate/personas/persona_b.md`.
- `support/artifacts/pr_br_full_gate/personas/persona_c.md`: Player persona. No contracts, validators, or prior-session findings. Canonical source: `artifacts/pr_br_full_gate/personas/persona_c.md`.
- `support/artifacts/pr_br_full_gate/personas/persona_d.md`: Player persona. No contracts, validators, or prior-session findings. Canonical source: `artifacts/pr_br_full_gate/personas/persona_d.md`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_a/visible.md`: Persona A direct/practical player-visible opening and ten turns. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_a/visible.md`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_a/isolation.json`: Persona A direct/practical session id and empty discourse before Turn 1. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_a/isolation.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_a/opening.json`: Persona A direct/practical product opening text. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_a/opening.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_a/review_index.json`: Persona A direct/practical contracts, routing, hard validation, and discourse slots. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_a/review_index.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_a/preflight.json`: Persona A direct/practical HEAD and model configuration at session start. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_a/preflight.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_a/summary.json`: Persona A direct/practical generation and interpretation counts. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_a/summary.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_a/generation_calls.json`: Persona A direct/practical opening and gameplay model texts. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_a/generation_calls.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_a/interpretation_calls.json`: Persona A direct/practical structured interpretation outputs. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_a/interpretation_calls.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_a/inbox.jsonl`: Persona A direct/practical turn-by-turn player lines. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_a/inbox.jsonl`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_a/turns/turn_01.json`: Persona A direct/practical turn 1 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_a/turns/turn_01.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_a/turns/turn_02.json`: Persona A direct/practical turn 2 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_a/turns/turn_02.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_a/turns/turn_03.json`: Persona A direct/practical turn 3 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_a/turns/turn_03.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_a/turns/turn_04.json`: Persona A direct/practical turn 4 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_a/turns/turn_04.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_a/turns/turn_05.json`: Persona A direct/practical turn 5 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_a/turns/turn_05.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_a/turns/turn_06.json`: Persona A direct/practical turn 6 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_a/turns/turn_06.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_a/turns/turn_07.json`: Persona A direct/practical turn 7 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_a/turns/turn_07.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_a/turns/turn_08.json`: Persona A direct/practical turn 8 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_a/turns/turn_08.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_a/turns/turn_09.json`: Persona A direct/practical turn 9 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_a/turns/turn_09.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_a/turns/turn_10.json`: Persona A direct/practical turn 10 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_a/turns/turn_10.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_b/visible.md`: Persona B social/curious player-visible opening and ten turns. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_b/visible.md`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_b/isolation.json`: Persona B social/curious session id and empty discourse before Turn 1. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_b/isolation.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_b/opening.json`: Persona B social/curious product opening text. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_b/opening.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_b/review_index.json`: Persona B social/curious contracts, routing, hard validation, and discourse slots. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_b/review_index.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_b/preflight.json`: Persona B social/curious HEAD and model configuration at session start. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_b/preflight.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_b/summary.json`: Persona B social/curious generation and interpretation counts. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_b/summary.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_b/generation_calls.json`: Persona B social/curious opening and gameplay model texts. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_b/generation_calls.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_b/interpretation_calls.json`: Persona B social/curious structured interpretation outputs. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_b/interpretation_calls.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_b/inbox.jsonl`: Persona B social/curious turn-by-turn player lines. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_b/inbox.jsonl`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_b/turns/turn_01.json`: Persona B social/curious turn 1 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_b/turns/turn_01.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_b/turns/turn_02.json`: Persona B social/curious turn 2 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_b/turns/turn_02.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_b/turns/turn_03.json`: Persona B social/curious turn 3 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_b/turns/turn_03.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_b/turns/turn_04.json`: Persona B social/curious turn 4 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_b/turns/turn_04.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_b/turns/turn_05.json`: Persona B social/curious turn 5 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_b/turns/turn_05.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_b/turns/turn_06.json`: Persona B social/curious turn 6 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_b/turns/turn_06.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_b/turns/turn_07.json`: Persona B social/curious turn 7 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_b/turns/turn_07.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_b/turns/turn_08.json`: Persona B social/curious turn 8 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_b/turns/turn_08.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_b/turns/turn_09.json`: Persona B social/curious turn 9 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_b/turns/turn_09.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_b/turns/turn_10.json`: Persona B social/curious turn 10 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_b/turns/turn_10.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_c/visible.md`: Persona C exploratory player-visible opening and ten turns. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_c/visible.md`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_c/isolation.json`: Persona C exploratory session id and empty discourse before Turn 1. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_c/isolation.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_c/opening.json`: Persona C exploratory product opening text. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_c/opening.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_c/review_index.json`: Persona C exploratory contracts, routing, hard validation, and discourse slots. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_c/review_index.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_c/preflight.json`: Persona C exploratory HEAD and model configuration at session start. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_c/preflight.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_c/summary.json`: Persona C exploratory generation and interpretation counts. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_c/summary.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_c/generation_calls.json`: Persona C exploratory opening and gameplay model texts. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_c/generation_calls.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_c/interpretation_calls.json`: Persona C exploratory structured interpretation outputs. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_c/interpretation_calls.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_c/inbox.jsonl`: Persona C exploratory turn-by-turn player lines. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_c/inbox.jsonl`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_c/turns/turn_01.json`: Persona C exploratory turn 1 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_c/turns/turn_01.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_c/turns/turn_02.json`: Persona C exploratory turn 2 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_c/turns/turn_02.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_c/turns/turn_03.json`: Persona C exploratory turn 3 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_c/turns/turn_03.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_c/turns/turn_04.json`: Persona C exploratory turn 4 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_c/turns/turn_04.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_c/turns/turn_05.json`: Persona C exploratory turn 5 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_c/turns/turn_05.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_c/turns/turn_06.json`: Persona C exploratory turn 6 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_c/turns/turn_06.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_c/turns/turn_07.json`: Persona C exploratory turn 7 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_c/turns/turn_07.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_c/turns/turn_08.json`: Persona C exploratory turn 8 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_c/turns/turn_08.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_c/turns/turn_09.json`: Persona C exploratory turn 9 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_c/turns/turn_09.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_c/turns/turn_10.json`: Persona C exploratory turn 10 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_c/turns/turn_10.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_d/visible.md`: Persona D action-oriented player-visible opening and ten turns. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_d/visible.md`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_d/isolation.json`: Persona D action-oriented session id and empty discourse before Turn 1. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_d/isolation.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_d/opening.json`: Persona D action-oriented product opening text. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_d/opening.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_d/review_index.json`: Persona D action-oriented contracts, routing, hard validation, and discourse slots. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_d/review_index.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_d/preflight.json`: Persona D action-oriented HEAD and model configuration at session start. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_d/preflight.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_d/summary.json`: Persona D action-oriented generation and interpretation counts. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_d/summary.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_d/generation_calls.json`: Persona D action-oriented opening and gameplay model texts. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_d/generation_calls.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_d/interpretation_calls.json`: Persona D action-oriented structured interpretation outputs. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_d/interpretation_calls.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_d/inbox.jsonl`: Persona D action-oriented turn-by-turn player lines. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_d/inbox.jsonl`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_d/turns/turn_01.json`: Persona D action-oriented turn 1 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_d/turns/turn_01.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_d/turns/turn_02.json`: Persona D action-oriented turn 2 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_d/turns/turn_02.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_d/turns/turn_03.json`: Persona D action-oriented turn 3 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_d/turns/turn_03.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_d/turns/turn_04.json`: Persona D action-oriented turn 4 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_d/turns/turn_04.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_d/turns/turn_05.json`: Persona D action-oriented turn 5 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_d/turns/turn_05.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_d/turns/turn_06.json`: Persona D action-oriented turn 6 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_d/turns/turn_06.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_d/turns/turn_07.json`: Persona D action-oriented turn 7 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_d/turns/turn_07.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_d/turns/turn_08.json`: Persona D action-oriented turn 8 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_d/turns/turn_08.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_d/turns/turn_09.json`: Persona D action-oriented turn 9 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_d/turns/turn_09.json`.
- `support/artifacts/pr_br_full_gate/20261002T021950Z/persona_d/turns/turn_10.json`: Persona D action-oriented turn 10 candidate, contract, validation, and emission. Canonical source: `artifacts/pr_br_full_gate/20261002T021950Z/persona_d/turns/turn_10.json`.

## Explicit omissions

- `docs/audits/PR-BR_post_generation_transformation_boundary_discovery.md`: duplicate content of docs/audits/PR-BR_post_generation_transformation_boundary_discovery.md; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
