# Confirmed Baseline Repair

## Executive Summary

Seven of the eight confirmed root-cause clusters are complete. RC-04 is partial: its production facade bypass is repaired, but its aggregate guard remains red because it also reports two test-only imports assigned to the frozen validation-cleanup queue. The full suite moved from 36 to 23 failures solely through confirmed product and architecture repairs. No stale expectation, fixture, governance registry, policy decision, evaluator threshold, or validation-authority classification was changed.

## Starting Baseline

The authoritative pre-repair JUnit baseline recorded 6,445 collected, 6,310 passed, 36 failed, and 99 skipped. Its failure set exactly matches the completed triage registry. The campaign also launched a reconfirmation run before editing; the preserved pre-repair artifact is the immediately preceding authoritative JUnit baseline so it cannot contain mid-campaign filesystem scans.

## Repair Queue

| RC | Type | Priority | Outcome |
| --- | --- | --- | --- |
| RC-17 | Product | P0 | COMPLETED |
| RC-12 | Product | P1 | COMPLETED |
| RC-01 | Architecture | P1 | COMPLETED |
| RC-04 | Architecture | P1 | PARTIAL: production repaired; aggregate test retains cleanup-only violations |
| RC-19 | Architecture | P1 | COMPLETED |
| RC-23 | Architecture | P1 | COMPLETED |
| RC-15 | Architecture | P2 | COMPLETED |
| RC-16 | Product | P2 | COMPLETED |

## Product Repairs

- **RC-17:** the undefined social prompt call now uses the current early-resolution helper. Failed NPC pursuit is selected through the owned neutral nonprogress fallback before strict-social prose can be accepted. Runtime evidence is now `Nothing confirms progress toward that lead yet—the moment stays unresolved.` with source `npc_pursuit_neutral_fallback`; the path no longer crashes.
- **RC-12:** valid resolved travel uses the existing destination-grounded arrival renderer. `Old Milestone` survives into emitted narration instead of the blank-scene placeholder.
- **RC-16:** rows created by the protected assertion bridge carry their existing failed-invariant identity into recurrence routing and are committed to protected history. Ordinary ephemeral diagnostic rows remain in the diagnostic lane.

## Architecture Repairs

| RC | Violated boundary | Repair | Authority | Verified |
| --- | --- | --- | --- | --- |
| RC-01 | Canonical mutation evidence taxonomy | FEM mutation-lineage evidence is recorded as direct `final_emission_mutation` attribution | CO96/CU3 attribution contract | Yes |
| RC-04 | Non-owner direct FEM write import | Policy mutation packaging moved behind final-emission finalize owner | BV2C facade boundary | Production clean; aggregate test partial |
| RC-19 | Visibility owner writes bypass stamping | Metadata preparation is pure; canonical visibility fallback owner performs paired stamping | BU9 ownership contract | Yes |
| RC-23 | Narrative-authenticity dependency direction | NA telemetry is consumed through metadata read facade, not repair layer | Validation-layer separation | Yes |
| RC-15 | Retired replay projection alias | Removed obsolete alias while preserving canonical projection function | Replay projection closeout | Yes |

## Per-Repair Verification

All thirteen directly repairable failing nodes passed unchanged. Broader focused verification covered social fallback, destination transitions, attribution contracts and guards, visibility enforcement, narrative authenticity, replay projection, protected recurrence, and validation-layer tests. Two broader-suite reds remained intentionally: RC-18 ownership registry drift and RC-24’s stale evaluator allowlist.

The machine-readable details, files, tests, and outcomes are in `artifacts/confirmed_baseline_repair/repair_ledger.json`.

## Runtime Verification

RC-17 no longer raises `NameError`; it reaches the canonical neutral NPC-pursuit fallback with unresolved-state wording. RC-12 emits a destination-bearing arrival line from the resolved scene envelope. Neither verification requires model invocation or nondeterministic generation.

## Contradictions and Blockers

No classification was contradicted. RC-04 exposed the mixed nature already documented by triage: the production bypass is fixed, but one aggregate test also owns validation-cleanup findings. It remains PARTIAL rather than weakening or editing those tests.

One intermediate full run reported the combat transcript sequence red. It passed immediately in isolation and disappeared on the clean final rerun, so it is recorded as transient shared-state/order coupling, not absorbed into a repair cluster.

## Ending Baseline

The final JUnit baseline is 6,445 collected, 6,323 passed, 23 failed, and 99 skipped. Thirteen failures became green and no new failures remain.

## Failure Delta

- RC-01: six failures resolved.
- RC-12: two failures resolved.
- RC-15, RC-16, RC-17, RC-19, and RC-23: one failure resolved each.
- RC-04: production violation removed, but its single aggregate test remains red for two frozen test-only imports.
- Unexpected permanent greens: none.
- New final failures: none.

## Remaining Red Baseline

The 23 remaining failures comprise one partial confirmed architecture aggregate, three validation defects, eight stale expectations, one stale fixture, four governance-drift cases, four policy-decision cases, and two unresolved cases. RC-10 and RC-21 remain undecided. RC-11 and RC-13 remain unresolved.

## What Was Deliberately Not Changed

No validation cleanup, stale fixture modernization, governance registry repair, replay consolidation, evaluator-policy change, semantic calibration, validation authority change, RC-10/RC-21 decision, or RC-11/RC-13 investigation was performed. Automated playability remains supporting evidence, behavioral gauntlet remains diagnostic, protected replay remains authoritative, and semantic calibration remains calibration authority.

## Commands Executed

```powershell
python -m pytest -q --tb=no --junitxml=artifacts/confirmed_baseline_repair/pre_repair_suite.xml
python -m pytest <cluster node IDs> -q --tb=short
python -m pytest <broader repair suites> -q --tb=short
python -m pytest -q --tb=no --junitxml=artifacts/confirmed_baseline_repair/post_repair_suite.xml
python tools/build_confirmed_baseline_repair.py
python tools/build_review_handoff.py --config data/validation/review_handoffs/confirmed_baseline_repair.json
```

## Limitations

RC-04 cannot become fully green without performing separately authorized validation cleanup. The full suite retains shared mutable-state sensitivity demonstrated by one transient transcript result, though the final rerun contains no new failure.

## Recommended Next Campaign

Review this repair boundary, then run Validation Cleanup and Governance Repair against the 23-test baseline. Keep policy decisions and unresolved investigations separate unless explicitly authorized.
