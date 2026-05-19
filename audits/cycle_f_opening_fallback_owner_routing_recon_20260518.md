# Cycle F.F Opening Fallback Owner Routing Recon

Date: 2026-05-18

Scope: recon-only review of opening-fallback failure triage. No runtime code, tests, classifier logic, dashboard rendering, owner labels, `investigate_first` values, comments, or assertions were changed.

## Strongest Finding

Current failure routing is intentionally broad: any opening-fallback drift classified as category `fallback` routes to `game/final_emission_gate.py`, even when the observed evidence is specifically an owner-bucket mapping, replay projection, dashboard rendering, or upstream-prepared payload symptom.

That gate bias is legitimate for selection/order/final output failures, but over-centralized for read-side and projection-only symptoms. The next move should be a reviewed classifier policy decision, not an incidental cleanup.

## Current Routing Table

| Failure/symptom | Current investigate_first | Current primary_owner | Evidence/test |
|---|---|---|---|
| `opening_recovered_via_fallback` mismatch | `game/final_emission_gate.py` | `fallback` | `tests/helpers/failure_classifier.py` classifies `opening_recovered_via_fallback` under `opening_fallback` -> category `fallback`; `tests/test_failure_classifier.py` expects gate for the opening fallback sublayer. |
| `opening_fallback_authorship_source` mismatch | `game/final_emission_gate.py` | `fallback` | Same `opening_fallback` category rule; canonical/legacy/fail-closed cases in `tests/test_failure_classifier.py` use opening authorship evidence but still inherit fallback routing. |
| `opening_fallback_owner_bucket` mismatch | `game/final_emission_gate.py` | `fallback` | `tests/test_failure_dashboard_controlled_failures.py` controlled case `opening_fallback_owner_bucket` expects `investigate_first: game/final_emission_gate.py`. |
| `final_emitted_source` is an opening fallback source | `game/final_emission_gate.py` | `fallback` | `FIELD_TARGET_OVERRIDES` forces `final_emitted_source` to the gate; opening final source participates in `tests/test_golden_replay.py` direct seam and classifier projection rows. |
| `fallback_family` / `fallback_temporal_frame` with `scene_opening` | `game/final_emission_gate.py` | `fallback` | General fallback category and `fallback` field override route to the gate. `tests/test_failure_classifier.py` uses `fallback_family="scene_opening"` for opening rows. |
| Fail-closed opening fallback bucket/source | `game/final_emission_gate.py` | `fallback` | `tests/test_failure_classifier.py` and `tests/test_golden_replay.py` lock fail-closed sealed-gate bucket projection, while live routing remains gate-biased. |
| Canonical upstream-prepared opening fallback observed as compatibility-local | `game/final_emission_gate.py` | `fallback` | `tests/test_failure_classifier.py` classifies compatibility-local as opening fallback with unknown-ambiguous bucket; `tests/test_golden_replay.py` direct seam asserts canonical path is not compatibility-local. |
| Opening owner evidence rendered in dashboard | `game/final_emission_gate.py` in row; dashboard renders that value | `fallback` | `tests/helpers/failure_dashboard_report.py` only renders `investigate_first`; `tests/test_failure_dashboard_controlled_failures.py` expects the gate-routed row and `opening_owner=upstream-prepared`. |
| Opening owner bucket allowed-value violation | Row validation error, not an alternate target | `fallback` row if classified | `tests/test_failure_classification_contract.py` and `tests/test_failure_classifier.py` validate invalid opening owner buckets, but do not route them to `game/final_emission_meta.py`. |
| Golden replay observed turn missing/projecting opening owner bucket | Usually `tests/helpers/golden_replay.py` only when category is projection; opening-field mismatches route to gate | `projection` only for unavailable/missing observation categories | `tests/test_golden_replay.py` owns projection tests; classifier category rules still treat explicit opening fields as fallback. |

## Proposed Symptom-Specific Routing Table

| Failure/symptom | Proposed investigate_first | Proposed primary_owner | Touch final gate? | Reason |
|---|---|---|---|---|
| Gate emits a fallback instead of accepted/generated opening candidate | `game/final_emission_gate.py` | `fallback` | Yes | Gate owns selection/order/final output. Keep current route. |
| Gate ignores usable upstream-prepared opening payload | `game/final_emission_gate.py` | `fallback` | Yes | Selection preference is gate-owned. Keep current route. |
| Empty curated facts produce generic opening prose instead of fail-closed marker | `game/final_emission_gate.py` | `fallback` | Yes | Gate owns fail-closed path and no local composer invocation when no basis exists. |
| Final FEM missing `opening_recovered_via_fallback` after gate replacement | `game/final_emission_gate.py` | `emission` or `fallback` | Yes | This is final output packaging, not pure projection. |
| Deterministic fallback wording/basis is wrong | `game/opening_deterministic_fallback.py` | `fallback` | Usually no | Composer owns curated facts to prose and basis consistency. Gate should not be first unless selection is wrong. |
| `opening_final_fallback_basis` diverges from selector facts | `game/opening_deterministic_fallback.py` | `fallback` | Usually no | Composer validates selector/basis match; API/source selection may be second. |
| Upstream prepared opening payload absent, partial, or malformed before gate | `game/upstream_response_repairs.py` | `upstream_prepared_emission` or `fallback` | Maybe | Prepared snapshot packaging and attach preconditions live upstream; gate only consumes usable payloads. |
| `opening_fallback_authorship_source` wrong in prepared payload | `game/upstream_response_repairs.py` | `upstream_prepared_emission` or `fallback` | Maybe | Authorship originates in upstream payload; gate may be second if it overwrites during merge. |
| `opening_fallback_owner_bucket` maps upstream/fail-closed/compatibility-local incorrectly | `game/final_emission_meta.py` | `normalization` or `fallback` | No | Read-side owner bucket mapping lives in final emission meta and direct tests in `tests/test_opening_fallback_owner_bucket.py`. |
| Allowed opening owner bucket values change or reject valid bucket | `game/final_emission_meta.py` plus `tests/failure_classification_contract.py` | `normalization` | No | Contract values are metadata/schema locks, not gate routing. |
| Golden replay observed turn omits opening owner bucket while raw FEM has fields | `tests/helpers/golden_replay.py` | `projection` | No | Replay projection owns observed row shape. |
| Golden replay direct seam canonical path reports compatibility-local | `game/upstream_response_repairs.py`, then `game/final_emission_gate.py` | `fallback` | Maybe | If raw gate output is wrong, gate/upstream are real owners; if only observed row is wrong, replay helper owns it. |
| Classifier row categorizes opening owner-bucket drift incorrectly | `tests/helpers/failure_classifier.py` | `projection` or `fallback` depending policy | No | Classifier owns category, primary owner, source family, severity, and target. |
| Dashboard omits or misformats `opening_owner=...` evidence | `tests/helpers/failure_dashboard_report.py` | `projection` | No | Dashboard only renders row fields; it does not own runtime or classifier decisions. |
| Controlled dashboard expected row disagrees with classifier output | `tests/test_failure_dashboard_controlled_failures.py` / `tests/helpers/failure_classifier.py` | `projection` | No | Controlled rows lock dashboard/classifier contract, not gate behavior. |

## Gate-Routed Cases That Are Legitimate

| Symptom | Why gate routing is legitimate |
|---|---|
| Final emitted source is unexpectedly an opening fallback | The gate owns final route/output selection and `final_emitted_source` stamping. |
| Usable upstream-prepared opening payload is not selected | The gate owns preference/selection once payload is usable. |
| Text-only prepared stub is accepted as canonical | Gate selector rejects partial payloads, while upstream rebuilds; both may matter, but gate is a legitimate first stop if acceptance happened. |
| Empty curated facts do not fail closed | Gate owns the sealed fail-closed/no local composer path for missing basis. |
| Gate output drops opening fallback FEM fields | The gate owns final FEM merge/wiring after selection. |

## Over-Centralized Gate Routes

| Symptom | Better first target | Why current gate route is probably too broad |
|---|---|---|
| Opening fallback prose or basis changed | `game/opening_deterministic_fallback.py` | Composition is explicitly extracted from the gate. |
| Upstream prepared opening payload shape/authorship is absent or malformed | `game/upstream_response_repairs.py` | Payload packaging and auto-attach are upstream responsibilities. |
| Owner bucket is wrong for upstream-prepared/fail-closed/compatibility-local cases | `game/final_emission_meta.py` | Bucket mapping is read-side metadata logic. |
| Golden observed row lacks opening owner bucket but raw FEM is present | `tests/helpers/golden_replay.py` | Projection helper owns observed-turn extraction. |
| Classifier gives wrong category/owner/severity/source family for opening fields | `tests/helpers/failure_classifier.py` | Classifier owns triage policy. |
| Dashboard text omits `opening_owner=...` | `tests/helpers/failure_dashboard_report.py` | Dashboard renderer only formats classifier rows. |
| Controlled dashboard row expects stale `investigate_first` | `tests/test_failure_dashboard_controlled_failures.py` | Test locks policy; changing it is a reviewed contract update. |

## Risk Classification

| Proposed routing change | Risk classification | Notes |
|---|---|---|
| Route opening prose/basis symptoms to `game/opening_deterministic_fallback.py` | Classifier policy change, needs review | Would require more symptom-specific target logic than current category-level `fallback` route. |
| Route malformed/absent upstream prepared opening payload to `game/upstream_response_repairs.py` | Classifier policy change, needs review | Current taxonomy has `upstream_prepared_emission`, but current investigation target still points to the gate. |
| Route owner-bucket mapping drift to `game/final_emission_meta.py` | Classifier policy change, needs review | Aligns with existing direct owner tests, but changes current dashboard/classifier expectations. |
| Route missing replay projection fields to `tests/helpers/golden_replay.py` | Safe wording/comment-only later if only docs; classifier policy change if behavior changes | Existing projection category already does this, but explicit opening fields do not. |
| Route classifier category/owner mistakes to `tests/helpers/failure_classifier.py` | Safe wording/comment-only later for docs; classifier policy change if row behavior changes | Good as documentation; implementation would alter contract behavior. |
| Route dashboard evidence formatting mistakes to `tests/helpers/failure_dashboard_report.py` | Dashboard-only change, needs review | Renderer-only symptoms should not involve the gate. |
| Keep gate route for final source/selection/fail-closed/FEM merge symptoms | Do not change | Gate route is correct for final output orchestration. |
| Add new primary owner labels for opening composer/upstream opening payload | Do not change | User explicitly said not to change owner labels, and the contract currently lacks these as owner labels. |
| Split `opening_fallback` category into subcategories | Unclear / needs more evidence | May improve routing but expands taxonomy and tests; not justified by this recon alone. |

## Candidate Next Blocks

| Block | Label | Target files | Intended drag reduction | Risk | Tests to run | Parallelizable? |
|---|---|---|---|---|---|---|
| F.G Routing Policy Decision Memo | Recon only | `audits/failure_owner_matrix.md`, `audits/cycle_f_opening_fallback_owner_routing_recon_20260518.md` | Decide whether symptom-specific routing is desired before any classifier edits. | Low. No behavior changes. | No tests required; optional `pytest tests/test_failure_classification_contract.py -q` if docs are contract-read. | Yes. |
| F.H Opening Routing Wording Pass | Comments-only | `tests/helpers/failure_classifier.py`, `tests/test_failure_classifier.py`, `tests/test_failure_dashboard_controlled_failures.py` | Clarify that current gate routing is policy, not runtime ownership. | Low, but user approval needed because comments were disallowed in this block. | `pytest tests/test_failure_classifier.py tests/test_failure_dashboard_controlled_failures.py -q` | Yes. |
| F.I Symptom-Specific Target Prototype | Possible classifier policy change, needs human review | `tests/helpers/failure_classifier.py`, `tests/test_failure_classifier.py`, `tests/test_failure_dashboard_controlled_failures.py`, `tests/failure_classification_contract.py` | Route opening owner-bucket/projection/payload symptoms to their first owner instead of the gate. | Medium to high. Changes dashboard rows and public triage contract. | `pytest tests/test_failure_classifier.py tests/test_failure_dashboard_controlled_failures.py tests/test_failure_classification_contract.py -q` | No. Shared classifier contract. |
| F.J Opening Projection Fixture Helper | Possible projection helper extraction, needs human review | `tests/test_golden_replay.py`, `tests/test_failure_classifier.py`, `tests/test_failure_dashboard_controlled_failures.py`, possible `tests/helpers/` | Reduce repeated literal opening fallback fields without changing routing policy. | Medium. Helper can hide projection intent if too broad. | `pytest tests/test_golden_replay.py tests/test_failure_classifier.py tests/test_failure_dashboard_controlled_failures.py -q` | Partially. |
| F.K Keep Gate-Biased Routing Freeze | Do not touch yet | `tests/helpers/failure_classifier.py`, `tests/helpers/failure_dashboard_report.py` | Avoid churn while owner taxonomy remains coarse. | Low short-term; preserves known over-centralization. | No tests. | Yes. |

## Recommendation

`investigate_first` should become symptom-specific eventually, but not as a drive-by cleanup. The strongest near-term recommendation is to keep current behavior until a reviewed classifier policy block decides how far to split opening fallback routing while preserving the existing owner-label taxonomy.

The safest next block is F.G Routing Policy Decision Memo: document whether the project wants coarse category routing for dashboard simplicity or first-fault routing for lower gate drag.
