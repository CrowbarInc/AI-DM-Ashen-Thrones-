# Cycle E Adjacent Fallback Family Ownership Recon - 2026-05-17

## Summary

Recommendation: **stop Cycle E thinning for now**.

The completed `fallback_behavior` slice had clear duplicate downstream
assertion fanout. The adjacent families inspected here do not show the same
low-risk profile. Opening, sealed, visibility, and fast fallback coverage is
mostly owner-bucket/projection contracts, extracted helper ownership, final-gate
orchestration, or named historical regression protection.

No production files or test files were changed by this recon.

## Family Map

| Family | Production owner modules | Owner tests | Downstream / smoke / projection tests | Historical regression tests | Duplicate assertion pattern | Thinning safety |
| --- | --- | --- | --- | --- | --- | --- |
| Opening fallback | `game/opening_deterministic_fallback.py` owns curated-facts-to-text composition; `game/upstream_response_repairs.py` packages canonical upstream-prepared opening payload; `game/final_emission_gate.py` selects payload, compatibility path, and fail-closed behavior; `game/final_emission_meta.py` owns owner-bucket mapping. | `tests/test_opening_fallback_owner_bucket.py`; opening-related owner/helper rows in `tests/test_final_emission_gate.py`; upstream-prepared payload tests in `tests/test_upstream_response_repairs.py` outside this focused file list. | `tests/test_golden_replay.py`, `tests/test_failure_classifier.py`, `tests/test_failure_dashboard_controlled_failures.py`, `tests/test_failure_classification_contract.py`. | Many Block G/H/J/L/M/N and canonical/compatibility-local tests in `tests/test_final_emission_gate.py`. | Repeated checks for `opening_fallback_authorship_source`, `opening_fallback_owner_bucket`, `fallback_family_used=scene_opening`, fail-closed markers, and compatibility-local exclusion. | **Do not thin now.** These assertions are mostly contract locks and historical compatibility-retirement protections. A comments-only ownership pass could be safe later. |
| Sealed fallback | `game/final_emission_sealed_fallback.py` owns metadata/route stamping helpers and explicitly must not author/select prose; `game/final_emission_gate.py` selects/assembles replacement branches through injected prose owners; `game/final_emission_meta.py` owns owner-bucket constants. | Sealed helper tests in `tests/test_final_emission_gate.py`, especially Block AI helper/module tests. | `tests/test_golden_replay.py`, `tests/test_failure_classifier.py`, `tests/test_failure_dashboard_controlled_failures.py`, `tests/test_failure_classification_contract.py`, one visibility pipeline assertion in `tests/test_final_emission_visibility.py`. | Strict-social sealed fallback, N4 sealed replacement, selector snapshot, branch-order, and "helpers do not author prose" tests in `tests/test_final_emission_gate.py`. | Repeated `sealed_fallback_owner_bucket` and `final_emitted_source` assertions across gate, replay, classifier, and dashboard layers. | **Do not thin now.** Repetition is intentional cross-layer projection/contract coverage. The helper module was extracted specifically to preserve no-prose-authoring boundaries. |
| Visibility fallback | `game/final_emission_visibility_fallback.py` owns visibility routing/metadata helper objects and explicitly must not author fallback prose or write final output; `game.final_emission_gate` applies visibility enforcement and final output mutation; `game.narration_visibility` owns first-mention/referential validation predicates. | `tests/test_final_emission_visibility.py` for pipeline visibility/first-mention/referential behavior; visibility helper tests in `tests/test_final_emission_gate.py`. | `tests/test_golden_replay.py`, `tests/test_failure_classifier.py`, `tests/test_failure_dashboard_controlled_failures.py`, `tests/test_failure_classification_contract.py`. | Many first-mention, referential-clarity, visibility hard-replacement, opening-visibility, and route-dispatch tests. | Dense metadata-shape assertions repeat fields such as `visibility_replacement_applied`, `visibility_fallback_owner_bucket`, fallback pool/kind, violation kinds, checked entities/facts. | **Unclear / not safe without a dedicated recon.** There may be future comments-only or metadata-shape consolidation opportunities, but current coverage is broad and interleaves validator, route, final-gate, and historical behavior. |
| Fast fallback | `game/fallback_provenance_debug.py` owns provenance/fingerprint metadata only; `game.api` and `game.gm` own upstream error classification and fast-fallback selection; `game.final_emission_gate.py` owns containment at gate/finalize boundaries. | `tests/test_upstream_fast_fallback_block_l.py` for upstream classification, fast-fallback tagging, provenance, and realignment; `tests/test_fallback_overwrite_containment.py` for overwrite containment. | A few final-gate smoke/regression tests in `tests/test_final_emission_gate.py`. | Block I overwrite containment, Block L upstream error path, manual GPT budget, and provenance realignment tests. | Some repeated provenance checks (`gate_exit_vs_selector_match`, selector text/fingerprint, tag presence), but each appears tied to a different incident boundary. | **Do not thin.** This family is highly historical/incident-driven and small enough that thinning would likely reduce diagnostic value. |

## Test Inventory Notes

Read-only AST inventory over the likely files found these matching surfaces:

- Opening fallback:
  - `tests/test_opening_fallback_owner_bucket.py`: 10 matching tests, 13 assert nodes.
  - `tests/test_final_emission_gate.py`: 51 matching tests, 307 assert nodes.
  - `tests/test_golden_replay.py`: 4 matching tests, 6 assert nodes.
  - `tests/test_failure_classifier.py`: 3 matching tests, 7 assert nodes.
  - Contract/dashboard files carry projection and triage-column checks.
- Sealed fallback:
  - `tests/test_final_emission_gate.py`: 16 matching tests, 85 assert nodes.
  - `tests/test_final_emission_visibility.py`: 1 matching test, 12 assert nodes.
  - Replay/classifier/contract/dashboard tests carry owner-bucket projection.
- Visibility fallback:
  - `tests/test_final_emission_visibility.py`: 42 matching tests, 192 assert nodes.
  - `tests/test_final_emission_gate.py`: 92 matching tests, 298 assert nodes.
  - Replay/classifier/contract/dashboard tests carry projection.
- Fast fallback:
  - `tests/test_fallback_overwrite_containment.py`: 4 matching tests, 12 assert nodes.
  - `tests/test_upstream_fast_fallback_block_l.py`: 4 matching tests, 16 assert nodes.
  - `tests/test_final_emission_gate.py`: 4 matching tests, 19 assert nodes.

These counts are approximate because they match by family terms in function
bodies and names, not by pytest ownership markers.

## Recommended Next Action

Recommended next action: **stop Cycle E thinning after the completed
`fallback_behavior` slice**.

If work continues, the safest follow-up is not thinning. It would be a
comments-only ownership pass for one adjacent family, with priority:

1. Opening fallback comments, because owner buckets are already explicit.
2. Sealed fallback comments, because `final_emission_sealed_fallback.py` has a
   clear "must not author prose" boundary.
3. Fast fallback comments, only if the Block I/Block L historical labels are not
   already clear enough.

Visibility fallback should get a separate, deeper recon before any action. It is
too entangled with first-mention, referential clarity, final-gate replacement,
and projection contracts for a quick thinning block.

## Files To Modify If A Later Comments-Only Block Is Chosen

Potential opening fallback comments-only files:

- `tests/test_opening_fallback_owner_bucket.py`
- opening-fallback sections of `tests/test_final_emission_gate.py`
- `tests/test_golden_replay.py` projection rows for opening owner buckets

Potential sealed fallback comments-only files:

- sealed/helper sections of `tests/test_final_emission_gate.py`
- `tests/test_final_emission_visibility.py` where visibility replacement stamps
  sealed owner bucket

Potential fast fallback comments-only files:

- `tests/test_fallback_overwrite_containment.py`
- `tests/test_upstream_fast_fallback_block_l.py`

## Files That Should Not Be Touched For Thinning Now

- `tests/test_final_emission_gate.py`
  - Contains many Block G/H/J/L/M/N/AI historical and architecture-lock tests.
- `tests/test_final_emission_visibility.py`
  - Dense owner/pipeline coverage for visibility, first-mention, and
    referential-clarity behavior.
- `tests/test_fallback_overwrite_containment.py`
  - Small, focused Block I historical containment suite.
- `tests/test_upstream_fast_fallback_block_l.py`
  - Small, focused Block L upstream error/fast-fallback suite.
- `tests/test_golden_replay.py`
- `tests/test_failure_classifier.py`
- `tests/test_failure_dashboard_controlled_failures.py`
- `tests/test_failure_classification_contract.py`
  - Projection/contract/dashboard surfaces; repeated fields are intentional.

## Verification Commands Run

Inspection commands:

```powershell
rg -n "opening_fallback|opening fallback|opening_deterministic_fallback|OPENING_FALLBACK|scene_opening" <likely test files>
rg -n "sealed_fallback|sealed fallback|SEALED_FALLBACK|hard_replace_illegal_output_with_sealed_fallback|final_emission_sealed_fallback" <likely test files>
rg -n "visibility_fallback|visibility fallback|VISIBILITY_FALLBACK|referential_clarity|first_mention|visibility" <likely test files>
rg -n "fast_fallback|fast fallback|upstream_api_fast_fallback|fallback_provenance|overwrite_containment" <likely test files>
Get-Content game\opening_deterministic_fallback.py -TotalCount 220
Get-Content game\final_emission_sealed_fallback.py -TotalCount 260
Get-Content game\final_emission_visibility_fallback.py -TotalCount 260
Get-Content game\fallback_provenance_debug.py -TotalCount 220
Get-Content tests\test_final_emission_visibility.py -TotalCount 180
Get-Content tests\test_fallback_overwrite_containment.py
Get-Content tests\test_upstream_fast_fallback_block_l.py -TotalCount 390
Get-Content tests\test_opening_fallback_owner_bucket.py
```

Verification command:

```powershell
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest --collect-only -q
```

Normal `python -m pytest` was not used because `python` is unavailable on PATH
in this PowerShell session.
