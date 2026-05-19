# Cycle F.K Opening Projection Fixture Helper Recon

Date: 2026-05-18

Scope: recon-only review of repeated opening-fallback projection literals. No runtime code, tests, helpers, assertions, classifier behavior, or dashboard rendering were changed.

## Strongest Finding

The repeated opening-fallback literals are not one kind of duplication. They currently lock four distinct surfaces:

- Golden replay projection from FEM into observed turn rows.
- Direct owner-bucket mapping behavior in `game.final_emission_meta`.
- Classifier routing/evidence behavior after Cycle F.I.
- Dashboard-visible triage rows after Cycle F.J.

A shared helper would reduce some literal churn, but a broad fixture helper would also hide the intent of each surface at the exact moment routing semantics are still fresh. Helperization should be deferred until routing churn settles; if it happens later, prefer local helpers or very narrow builder helpers over a universal opening-fallback fixture.

## Repeated Field Inventory

| Field | Where repeated | Duplication classification | Helper recommendation |
|---|---|---|---|
| `opening_fallback_owner_bucket` | `tests/test_golden_replay.py`, `tests/test_failure_classifier.py`, `tests/test_failure_dashboard_controlled_failures.py`, `tests/test_failure_classification_contract.py`, `tests/test_opening_fallback_owner_bucket.py`, `tests/helpers/failure_classifier.py`, `tests/helpers/golden_replay.py` | Owner-bucket contract lock, intentional projection lock, dashboard visibility lock, classifier routing lock | Do not broad-helperize now. Possible narrow helper later for classifier/dashboard controlled rows only. |
| `opening_fallback_authorship_source` | Golden replay projection tests, classifier routing tests, dashboard controlled rows, owner-bucket direct tests, classifier/golden helpers | Intentional projection lock and classifier routing lock; upstream payload symptom marker | Possible helper candidate only for row construction after routing stabilizes. Keep explicit in direct owner-bucket tests. |
| `opening_recovered_via_fallback` | Golden replay projection rows, classifier rows, dashboard controlled rows, owner-bucket mapper tests, helper evidence detection | Intentional projection lock and gate-routing lock | Do not helperize broadly. This field distinguishes true opening fallback evidence from generic fallback evidence. |
| `opening_final_fallback_basis` | New classifier/dashboard routing checks, API/gate-adjacent surfaces outside this recon, classifier marker logic | Classifier routing lock for composition/basis symptoms | Do not helperize yet. The field is used to prove routing to the deterministic composer, so explicitness is useful. |
| `fallback_family` | Golden replay, classifier, dashboard controlled rows, owner-bucket direct tests, classifier/golden helpers | Projection lock and source-family context; sometimes generic fallback evidence, sometimes opening-specific `scene_opening` evidence | Do not helperize broadly. It has non-opening meanings across the same files. |
| `fallback_temporal_frame` | Golden replay opening projection, classifier/dashboard canonical rows, owner-bucket non-opening contrast | Projection lock and opening classification context | Possible local helper candidate for canonical upstream-prepared opening rows, but not shared globally. |
| `final_emitted_source` | Golden replay projection, classifier fallback source routing, dashboard forced fallback and opening rows, owner-bucket direct tests, helper projection code | Gate selection/final output lock, projection lock, classifier routing lock | Do not helperize broadly. This field is deliberately overloaded across gate selection, fallback source, and projection cases. |

## Surface-by-Surface Notes

| Surface | What literals prove | Helper risk |
|---|---|---|
| `tests/test_golden_replay.py` | FEM fields are projected into observed turn rows; canonical opening path is upstream-prepared and not compatibility-local. | A shared classifier/dashboard fixture could obscure replay projection ownership. Keep explicit or use only local helpers. |
| `tests/test_failure_classifier.py` | Category/source-family stay stable while `investigate_first` changes by symptom. New Cycle F.I rows intentionally exercise owner-bucket, authorship payload, composition basis, raw-present projection omission, and gate selection. | A shared fixture could hide which field is being varied to trigger routing. Local builders per routing family may be safe later. |
| `tests/test_failure_dashboard_controlled_failures.py` | Dashboard rows expose classifier targets to users, including the new `final_emission_meta`, `upstream_response_repairs`, `opening_deterministic_fallback`, and `golden_replay` targets. | A broad helper could make controlled rows less readable. Local constants or tiny local builders might help after expectations settle. |
| `tests/test_failure_classification_contract.py` | Allowed owner-bucket values and row schema remain valid. | Do not helperize. This is a schema/contract test and benefits from direct literals. |
| `tests/test_opening_fallback_owner_bucket.py` | Direct mapping behavior for upstream-prepared, fail-closed sealed-gate, compatibility-local ambiguous, strict-social, retry, and missing metadata. | Do not helperize with projection tests. This is the direct semantic owner for bucket mapping. |
| `tests/helpers/failure_classifier.py` | Runtime-free classifier extraction, owner-bucket mapping call, evidence detection, and symptom-specific `investigate_first` routing. | Helperizing tests around this too soon could hide classifier inputs that should remain visible during policy churn. |
| `tests/helpers/golden_replay.py` | Observed turn projection fields and debug rendering from FEM. | No test fixture helper should leak into production-ish helper code. |

## Maintenance Drag vs Test Intent

Helperization would reduce repeated canonical literals such as:

- `final_emitted_source="opening_deterministic_fallback"`
- `opening_recovered_via_fallback=True`
- `opening_fallback_authorship_source="upstream_prepared_opening_fallback"`
- `fallback_family="scene_opening"`
- `fallback_temporal_frame="first_impression"`

But those same literals are currently used to prove different things in different files. In golden replay they prove projection; in owner-bucket tests they prove read-side mapping; in classifier tests they prove routing; in dashboard tests they prove user-facing triage output. A single shared fixture would save typing while making failures harder to localize.

The one plausible future helper is not a global fixture, but a local test-only builder for classifier/dashboard rows, such as a small canonical opening observed-turn dict used only where the test is not about individual field variation. That should wait until Cycle F routing expectations stop changing.

## Recommendation

Recommendation: defer until more routing churn is complete.

Do not introduce a shared fixture helper in `tests/helpers/` now. Do not helperize direct owner-bucket tests. If maintenance drag remains after the classifier/dashboard policy stabilizes, consider local helpers only:

- `tests/test_failure_classifier.py`: local observed-turn builders for canonical upstream-prepared, compatibility-local, fail-closed, and projection-missing cases.
- `tests/test_failure_dashboard_controlled_failures.py`: local controlled-case builders only if row definitions become unwieldy.

Avoid a cross-file shared helper until there is a stable, narrow contract that all consumers actually share.

## Field Classification Summary

| Field | Classification |
|---|---|
| `opening_fallback_owner_bucket` | Owner-bucket contract lock; dashboard visibility lock; classifier routing lock; possible local helper candidate later; do not shared-helperize now. |
| `opening_fallback_authorship_source` | Intentional projection lock; classifier routing lock; possible local helper candidate later. |
| `opening_recovered_via_fallback` | Intentional projection lock and gate-routing lock; do not helperize broadly. |
| `opening_final_fallback_basis` | Classifier routing lock for composition/basis symptoms; do not helperize yet. |
| `fallback_family` | Intentional projection/source-family lock; do not helperize broadly because it is not opening-specific. |
| `fallback_temporal_frame` | Intentional projection lock; possible local canonical-row helper later. |
| `final_emitted_source` | Gate selection and projection lock; do not helperize broadly. |

## Next Block

Recommended next block: no-op / close Cycle F.

Cycle F has moved from ownership mapping to routing policy, then to classifier/dashboard proof. The helper question should pause until there is evidence of ongoing maintenance pain after the new routing has lived for a bit. If the cycle must continue, the safest next block is comments-only: clarify that helperization is intentionally deferred and direct literals remain part of the contract.
