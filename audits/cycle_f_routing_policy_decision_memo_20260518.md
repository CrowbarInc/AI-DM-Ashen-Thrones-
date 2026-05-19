# Cycle F.G Routing Policy Decision Memo

Date: 2026-05-18

Scope: audit/docs-only policy decision for opening-fallback dashboard/classifier routing. No runtime code, tests, classifier logic, dashboard rendering, `investigate_first` values, owner labels, comments, or helper abstractions were changed.

## Policy Question

Should opening-fallback dashboard/classifier routing remain coarse and gate-biased, or move toward symptom-specific first-fault routing?

## Current State

The live classifier uses coarse category routing. Opening-fallback fields such as `opening_recovered_via_fallback`, `opening_fallback_authorship_source`, and `opening_fallback_owner_bucket` classify as category `fallback`; category `fallback` routes to `game/final_emission_gate.py`. Current classifier/dashboard tests assert that behavior.

The Cycle F owner map and routing recon show a cleaner ownership split:

- Gate selection/final output: `game/final_emission_gate.py`
- Composition/basis: `game/opening_deterministic_fallback.py`
- Upstream prepared payload: `game/upstream_response_repairs.py`
- Owner-bucket mapping: `game/final_emission_meta.py`
- Replay projection: `tests/helpers/golden_replay.py`
- Classifier policy: `tests/helpers/failure_classifier.py`
- Dashboard rendering: `tests/helpers/failure_dashboard_report.py`

`audits/failure_owner_matrix.md` also says primary owner should be the earliest legitimate fault location, not merely the layer where bad prose became visible.

## Option Comparison

| Evaluation axis | Option A: Keep coarse category routing | Option B: Move to symptom-specific first-fault routing |
|---|---|---|
| Maintenance drag impact | Low immediate churn; high ongoing final-gate gravity. Future opening-fallback drift keeps pointing engineers at the largest file first. | Higher short-term churn; lower long-term drag because failures point at the actual owner surface. |
| Diagnostic clarity | Simple and predictable, but imprecise. Good for final-output fallback substitutions, weak for owner-bucket/projection/payload symptoms. | Clearer. Separates selection, composition, payload packaging, metadata mapping, replay projection, classifier policy, and dashboard rendering. |
| Risk to existing classifier/dashboard contracts | None if unchanged. Preserves current `tests/test_failure_classifier.py` and `tests/test_failure_dashboard_controlled_failures.py` expectations. | Medium to high. Current tests assert gate routing for opening-fallback rows, so behavior changes require explicit contract updates. |
| Test update cost | None now. | Moderate. Update classifier tests, controlled dashboard rows, possibly contract docs/tests, and any snapshots that include `investigate_first`. |
| Reduces `final_emission_gate.py` touch pressure | No. Keeps known over-centralization. | Yes. Keeps final gate for selection/order/final-output symptoms while redirecting non-gate symptoms. |
| Taxonomy/schema churn | None. Uses existing category/owner labels. | Potentially low if implemented behind existing labels and only `investigate_first` varies; higher if new categories or owner labels are introduced. |
| Alignment with Cycle F success criteria | Partial. Preserves stability but does not reduce drag. | Stronger alignment if phased: reduces diagnostic drag without moving runtime ownership. |

## Recommendation

Adopt Option B gradually.

Do not change classifier behavior now. The current tests and public dashboard contract intentionally encode gate-biased routing, and changing that in the same breath as the policy decision would blur governance with implementation.

The target policy should become symptom-specific first-fault routing, while preserving current owner labels unless a later reviewed taxonomy block explicitly expands them. In practical terms: keep category `fallback` if needed, but make `investigate_first` smarter for opening-fallback evidence.

## Gradual Adoption Phases

### Phase 1: Documentation/comments only

Capture the policy boundary without behavior changes:

- Gate remains first for final source, gate selection, fail-closed routing, and final FEM merge symptoms.
- Non-gate first-fault surfaces are documented for composition, upstream payload, owner-bucket mapping, replay projection, classifier policy, and dashboard rendering.
- No tests or classifier behavior change in this phase.

### Phase 2: Classifier policy prototype behind existing taxonomy

Prototype symptom-specific `investigate_first` rules without adding owner labels or categories:

- Keep `primary_owner` values within the current contract.
- Keep `source_family` values within the current contract.
- Use field path plus observed evidence to choose more precise investigation targets.
- Preserve gate routing for no-go cases listed below.

### Phase 3: Dashboard expectation updates

Update controlled dashboard/classifier expectations after the policy prototype is reviewed:

- Expected rows for owner-bucket mapping can point to `game/final_emission_meta.py`.
- Replay projection symptoms can point to `tests/helpers/golden_replay.py`.
- Dashboard formatting symptoms can point to `tests/helpers/failure_dashboard_report.py`.
- Final source/selection rows continue to point to `game/final_emission_gate.py`.

### Phase 4: Optional projection helper extraction

Only after routing behavior is stable, consider helper extraction for repeated opening-fallback fixture fields across golden replay, classifier, and dashboard tests. This should reduce duplicated literals without hiding each surface's distinct contract.

## No-Go Criteria

Routing must remain final-gate-owned when:

- The final emitted source is wrong or unexpectedly an opening fallback.
- A usable upstream-prepared opening payload exists but the gate does not select it.
- The gate accepts a partial/text-only prepared opening payload as canonical.
- Empty curated facts do not fail closed or local compatibility composition runs when it should be disabled.
- The accepted/generated opening candidate is replaced incorrectly.
- Final gate output omits or corrupts gate-owned FEM merge fields after selection.
- The failure is about layer order, final route, sealed replacement, or response-type gate orchestration.
- There is no evidence that raw upstream/meta/projection data existed before the gate.

## Future Implementation Blocks

| Block | Label | Target files | Intended drag reduction | Risk | Tests to run | Parallelizable? |
|---|---|---|---|---|---|---|
| F.H Policy Notes Pass | Comments-only | `audits/failure_owner_matrix.md`, possibly headers/comments in `tests/helpers/failure_classifier.py` and `tests/test_failure_classifier.py` | Make current gate bias vs desired first-fault routing explicit before behavior changes. | Low, but requires approval because this task disallowed comments. | `pytest tests/test_failure_classification_contract.py -q` if docs are contract-read; otherwise no tests. | Yes. |
| F.I Opening Target Prototype | Possible classifier policy change, needs human review | `tests/helpers/failure_classifier.py`, `tests/test_failure_classifier.py` | Route owner-bucket, payload, and projection-like opening symptoms to first-fault targets while keeping existing labels. | Medium. Alters row output and test expectations. | `pytest tests/test_failure_classifier.py tests/test_failure_classification_contract.py -q` | No. Shared classifier policy. |
| F.J Dashboard Contract Update | Possible dashboard contract update, needs human review | `tests/test_failure_dashboard_controlled_failures.py`, `tests/helpers/failure_dashboard_report.py` only if rendering expectations need adjustment | Align controlled dashboard rows with symptom-specific routing output. | Medium. Dashboard probes are contract-like and visible. | `pytest tests/test_failure_dashboard_controlled_failures.py tests/test_failure_classifier.py -q` | No, after classifier prototype. |
| F.K Opening Projection Fixture Helper | Possible projection helper extraction, needs human review | `tests/test_golden_replay.py`, `tests/test_failure_classifier.py`, `tests/test_failure_dashboard_controlled_failures.py`, possible `tests/helpers/` | Reduce repeated opening fallback literal fields after routing policy stabilizes. | Medium. Bad helper design could obscure test intent. | `pytest tests/test_golden_replay.py tests/test_failure_classifier.py tests/test_failure_dashboard_controlled_failures.py -q` | Partially. |
| F.L Gate Routing Freeze | Do not touch yet | `game/final_emission_gate.py`, `tests/test_final_emission_gate.py` | Avoid using gate refactors as a substitute for classifier/dashboard policy work. | Low short-term; does not reduce classifier drag by itself. | No tests unless files are touched later. | Yes. |

## Decision

Recommended policy: adopt Option B gradually.

Classifier behavior should change later, not now. The next implementation block should be a reviewed classifier policy prototype that keeps the existing taxonomy and only varies `investigate_first` by opening-fallback symptom.

Safest next implementation block: F.H Policy Notes Pass if comments/docs are approved; otherwise F.I Opening Target Prototype as the first behavior-changing block, with human review before edits.
