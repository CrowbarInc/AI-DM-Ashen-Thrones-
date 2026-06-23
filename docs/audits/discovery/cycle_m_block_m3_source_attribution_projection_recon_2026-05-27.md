# Cycle M Block M3 - Source Attribution Projection Recon / Contract Lock

Date: 2026-05-27

Scope: characterize source-family, owner-bucket, authorship, and emitted-source ownership without changing runtime behavior.

Recommendation: defer implementation. Treat the current contracts as locked, with `game/final_emission_meta.py` already serving as the canonical owner for fallback owner-bucket vocabularies and opening fallback owner-bucket projection.

## Current Owner Map

| Surface | Current owner | Runtime decision or read-side projection | Notes |
| --- | --- | --- | --- |
| Opening owner bucket values | `game/final_emission_meta.py` | Read-side projection vocabulary | Defines `OPENING_FALLBACK_OWNER_*` constants and `OPENING_FALLBACK_OWNER_BUCKETS`. |
| Opening owner bucket inference | `game/final_emission_meta.py` | Read-side projection | `opening_fallback_owner_bucket_from_fields()` and `opening_fallback_owner_bucket_from_meta()` map existing evidence into buckets. |
| Sealed owner bucket values | `game/final_emission_meta.py` | Projection vocabulary used by runtime stamping | Defines `SEALED_FALLBACK_OWNER_*` constants and allowed bucket set. |
| Sealed owner bucket stamping | `game/final_emission_sealed_fallback.py` | Runtime metadata mutation | `stamp_sealed_fallback_realization_family()` chooses sealed owner bucket while preparing route metadata. |
| Visibility owner bucket values | `game/final_emission_meta.py` | Projection vocabulary | Defines `VISIBILITY_FALLBACK_OWNER_*` constants and allowed bucket set. No separate broad projection owner found in this block. |
| Opening fallback family/source metadata | `game/final_emission_opening_fallback.py`, `game/diegetic_fallback_narration.py` | Runtime selection/classification metadata | Opening fallback builds accepted/fail-closed metadata and uses diegetic fallback template metadata. |
| `fallback_authorship_source` | `game/final_emission_meta.py`, upstream opening evidence | Read-side lineage field sourced from runtime evidence | FEM lineage events preserve authorship source when present; M2 fixtures centralize repeated test setup. |
| `final_emitted_source` | Gate/opening/sealed fallback route metadata, then FEM projection | Runtime branch/source identifier | Used as a branch/source contract, not just display metadata. |
| Runtime lineage event attribution | `game/runtime_lineage_telemetry.py` | Read-side diagnostic normalization | `make_runtime_lineage_event()` carries `fallback_authorship_source` and `fallback_owner_bucket`; M1 summary helper aggregates these fields. |
| Failure classifier `source_family` | `tests/helpers/failure_classifier.py`, `tests/failure_classification_contract.py` | Test/report triage taxonomy | Separate reporting taxonomy. It intentionally points failures at likely owners and should not be merged into FEM runtime attribution. |
| Opening fallback test evidence | `tests/helpers/opening_fallback_evidence.py` | Test-only fixture ownership | M2 centralized successful and fail-closed opening evidence setup. |

## Defined Or Inferred Values

`game/final_emission_meta.py` is the strongest canonical production owner today. It defines the owner-bucket constants and allowed sets for opening, sealed, and visibility fallback families. It also owns the opening owner-bucket inference function, including mappings for upstream-prepared, retry, strict-social, sealed-gate fail-closed, and unknown/ambiguous evidence.

`game/final_emission_sealed_fallback.py` imports sealed owner constants from FEM and stamps `sealed_fallback_owner_bucket` while constructing route metadata. This is runtime metadata mutation at the integration point, not a detached read-side report.

`game/final_emission_opening_fallback.py` decides opening fallback success/fail-closed metadata and uses the diegetic fallback template registry for opening fallback classification. This is selection/route evidence, not merely projection.

`game/runtime_lineage_telemetry.py` normalizes already-selected evidence into lineage events. After M1, it also owns canonical read-side aggregation for authorship and owner-bucket frequencies.

`tests/helpers/failure_classifier.py` maps observed fields to diagnostic `source_family`, `investigate_first`, and classifier output fields. These are report/triage projections, not runtime source attribution decisions.

## Duplicated Or Near-Duplicated Mappings

The owner-bucket production mapping is not meaningfully duplicated. Tests repeat literal bucket/source values mostly as contract assertions:

- `tests/test_opening_fallback_owner_bucket.py` locks the opening bucket mapping and allowed values.
- `tests/test_final_emission_meta.py` verifies FEM runtime-lineage projection preserves opening source, authorship, and owner-bucket fields.
- `tests/test_golden_replay.py` verifies replay/debug projection keeps final emitted source and fallback evidence intact.
- `tests/test_failure_classifier.py` verifies classifier rows include expected source family and fallback attribution fields.
- `tests/helpers/opening_fallback_evidence.py` now centralizes repeated opening evidence setup while importing production owner constants where appropriate.

The real near-duplication is conceptual rather than code-level:

- Production FEM attribution uses owner buckets.
- Failure classification uses `source_family` and `investigate_first` taxonomy.
- Replay and dashboard tests assert the projected fields.

Those surfaces refer to overlapping evidence but serve different contracts. Collapsing them into one table now would risk mixing runtime route evidence, read-side lineage projection, and test/report ownership policy.

## Proposed Canonical Owner

No new owner should be introduced in M3.

Current safe ownership:

- Owner-bucket vocabulary and opening bucket inference: `game/final_emission_meta.py`
- Runtime lineage event normalization and aggregation: `game/runtime_lineage_telemetry.py`
- Runtime opening fallback selection/classification evidence: `game/final_emission_opening_fallback.py`
- Runtime sealed fallback route stamping: `game/final_emission_sealed_fallback.py`
- Test-only opening fallback evidence fixtures: `tests/helpers/opening_fallback_evidence.py`
- Failure triage/report taxonomy: `tests/helpers/failure_classifier.py` plus `tests/failure_classification_contract.py`

Future implementation should only introduce a tiny canonical table if a later change adds more owner-bucket signal groups and would otherwise edit multiple tests and projection helpers. If that happens, the safest owner is still `game/final_emission_meta.py`, limited to read-side owner-bucket constants and mapping inputs. It should not absorb classifier `source_family` rules or runtime fallback selection policy.

## Risk Assessment

Risk level for immediate consolidation: medium.

Why:

- `final_emitted_source` values are runtime route/source identifiers, not pure reporting labels.
- Sealed fallback owner buckets are stamped while route metadata is prepared.
- Opening fallback metadata is tied to selection/fail-closed behavior.
- Classifier `source_family` values are diagnostic report categories and intentionally differ from FEM fallback families.
- Some test literals are useful contract locks; replacing all of them with helper constants could make drift harder to notice.

Low-risk future change:

- Add narrowly scoped constants or a frozen signal table in `game/final_emission_meta.py` only for opening owner-bucket source groups if those groups expand again.
- Extend `tests/helpers/opening_fallback_evidence.py` to reuse any new constants in setup payloads while keeping assertion literals where they lock external contracts.

High-risk change to avoid:

- A single global table combining `source_family`, `owner_bucket`, `fallback_family`, `fallback_authorship_source`, `final_emitted_source`, replay metadata, and classifier investigation targets.

## Files-Touched-Per-Fix Impact

Consolidation would reduce future files touched only if future work repeatedly changes the same opening owner-bucket signal groups. M2 already reduced the larger repeated setup cost by centralizing opening fallback evidence fixtures.

At this point, further consolidation would likely shift edits rather than remove them:

- Runtime source identifiers would still require behavior tests.
- Classifier/report taxonomy would still require classifier tests.
- Replay schema/debug contracts would still require replay tests.
- Contract assertions should remain explicit in several consumers.

Expected reduction from immediate implementation: low.

Expected risk of accidental semantic coupling: medium.

## Recommendation

Defer implementation. Lock this as a recon/contract artifact.

Do not perform a production extraction in M3. The existing ownership boundaries are mostly healthy after M1 and M2:

- M1 made runtime-lineage aggregation canonical in `game/runtime_lineage_telemetry.py`.
- M2 made opening fallback evidence setup canonical in `tests/helpers/opening_fallback_evidence.py`.
- FEM already owns owner-bucket constants and opening bucket projection.

The next useful implementation should happen only when a concrete source-attribution fix proves that the same mapping needs edits in multiple places.

## Future Implementation Files

If a later block consolidates owner-bucket signal groups, touch only these files first:

- `game/final_emission_meta.py`
- `tests/test_opening_fallback_owner_bucket.py`
- `tests/helpers/opening_fallback_evidence.py`
- `tests/test_final_emission_meta.py`
- `tests/test_golden_replay.py`
- `tests/test_failure_classifier.py`

Only include these if the future change explicitly adjusts classifier/report taxonomy:

- `tests/helpers/failure_classifier.py`
- `tests/failure_classification_contract.py`

Avoid touching these unless the future block is explicitly about runtime route metadata or fallback selection:

- `game/final_emission_opening_fallback.py`
- `game/final_emission_sealed_fallback.py`
- `game/final_emission_gate.py`

## Validation

Report-only block. No code or test files were changed, so no test run is required by the M3 validation rule.
