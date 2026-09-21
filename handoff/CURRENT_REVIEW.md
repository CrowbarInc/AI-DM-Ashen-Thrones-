# Campaign

Campaign: RC-10 / RC-21 Policy Implementation
Identifier: `rc10_rc21_policy_implementation_20260919`
Date: 2026-09-19
Generated: 2026-09-19T20:35:00Z
Purpose: Implement the settled human decisions RC-10 = A and RC-21 = B + C, reconcile only directly implied residue, and establish the clean post-policy baseline.

# Executive Summary

RC-10 = A and RC-21 = B + C are implemented. The retired opening token now has one test-side home. Social redirects follow authored scene evidence into the canonical lead registry; spoken Lirael no longer instantiates emergent_town_crier. Directly implied residue in clues.py and defaults.py was cleaned. Intent-parser pursuit and compat_pending_lead_needed were deferred. Player-facing opening and destination-extractor behavior did not change. The four former policy reds are green. Full suite: 6,450 collected, 6,351 passed, 0 failed, 99 skipped.

Objective status: `ACHIEVED`.

# Changes Made

## Production changes

- Corrected the stale game/clues.py comment that claimed frontier_gate still authors Lirael.
- Removed leftover Lirael authorship from default_scene('frontier_gate') discoverables.

## Validation changes

- Routed the incidence-report fixture through legacy_compatibility_local_opening_authorship_source().
- Updated the three RC-21 tests to lock authored notice-board follow-up, registry ownership, merge, and milestone distinction.

## Tooling changes

- No changes in this category.

## Documentation changes

- Recorded RC-10 = A and RC-21 = B + C as settled in the dossier, policy summary, NEXT_SESSION, CR-01, state-authority model, and current-focus deferral notes.

## Generated artifacts

- Added focused and full-suite JUnit, baseline comparison, residue deferral, and command record.

# What Was Tested

- **Focused tests:** RC-10/opening family: 216 passed. RC-21/leads family: 118 passed. Replay/ownership/scene-canon family: 30 passed.
- **Broader relevant tests:** Incidence-report classification, opening-fallback metadata, social lead landing, lead registry, qualified pursuit, and state-authority suites passed.
- **Full suite:** Pre: 6,450 collected, 6,347 passed, 4 failed, 99 skipped. Post: 6,450 collected, 6,351 passed, 0 failed, 99 skipped. Collection unchanged; one RC-21 test was renamed, not deleted.
- **Runtime validation:** No live destination-extractor or opening-path change. Protected-replay opening projection and scene-canon hygiene passed.
- **Model/runtime boundary:** No external model invocation; deterministic test stubs only.
- **New regressions:** None remaining. First full-suite pass had one Windows PermissionError in BY2 temp combat.json rename; isolated re-run and second full suite passed.
- **Pre-existing failures:** None. The four former RC-10/RC-21 policy reds are green.
- **Self-contained bundle review:** PASS: report, settled decisions, residue deferral, exact baselines, commands, and focused evidence are bundled.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

No human decision is required before the next planned step.

# Known Problems / Unresolved Findings

## Campaign-specific

- None reported.

## Pre-existing baseline

- None reported.

# Missing Concepts / Future Capabilities

- compat_pending_lead_needed still keys off scene targets only.
- Intent parsing still reads pending_leads as the pursuit surface.
- Broader lead/clue overlap reduction remains deferred.
- Calibration Round 2, State-to-Narration Consistency, and new Product Realization features are out of scope.

# What This Campaign Does NOT Prove

- That Lirael pursuit should be restored as authored content.
- That pending_leads consumers have all migrated to the registry.
- That semantic playability or live-model quality improved.

# Recommended Next Step

Review this clean post-policy baseline. After review, begin Calibration Round #2 or State ↔ Narration Consistency. Do not start a general lead-system refactor.

# Review Bundle Contents

Bundle file count: `14`
Bundle ZIP size: `000000287871` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/docs/rc10_rc21_policy_implementation.md`: Primary campaign standard/report used to orient the review. Canonical source: `docs/rc10_rc21_policy_implementation.md`.
- `support/docs/NEXT_SESSION.md`: Active session brief with settled decisions and exact baseline. Canonical source: `docs/NEXT_SESSION.md`.
- `support/docs/rc10_rc21_policy_resolution_dossier.md`: Preserves the analysis history and now records the made decisions. Canonical source: `docs/rc10_rc21_policy_resolution_dossier.md`.
- `support/artifacts/policy_resolution/policy_decision_summary.md`: Short settled-decision record. Canonical source: `artifacts/policy_resolution/policy_decision_summary.md`.
- `support/artifacts/policy_implementation/residue_deferral.md`: Shows what was cleaned versus deliberately deferred. Canonical source: `artifacts/policy_implementation/residue_deferral.md`.
- `support/artifacts/policy_implementation/baseline_comparison.json`: Reconciles exact pre/post suite counts. Canonical source: `artifacts/policy_implementation/baseline_comparison.json`.
- `support/artifacts/policy_implementation/commands_executed.md`: Preserves exact verification commands. Canonical source: `artifacts/policy_implementation/commands_executed.md`.
- `support/artifacts/policy_resolution/pre_policy_baseline.xml`: Authoritative four-red starting baseline. Canonical source: `artifacts/policy_resolution/pre_policy_baseline.xml`.
- `support/artifacts/policy_implementation/post_implementation_suite.xml`: Authoritative clean ending baseline. Canonical source: `artifacts/policy_implementation/post_implementation_suite.xml`.
- `support/artifacts/policy_implementation/focused_rc10_opening.xml`: Opening fallback, incidence, and RC-10 fence verification. Canonical source: `artifacts/policy_implementation/focused_rc10_opening.xml`.
- `support/artifacts/policy_implementation/focused_rc21_leads.xml`: Social redirect, registry, and projection verification. Canonical source: `artifacts/policy_implementation/focused_rc21_leads.xml`.
- `support/artifacts/policy_implementation/focused_replay_ownership.xml`: Opening replay projection, ownership, and scene-canon verification. Canonical source: `artifacts/policy_implementation/focused_replay_ownership.xml`.

## Explicit omissions

No explicitly requested file was omitted.

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
