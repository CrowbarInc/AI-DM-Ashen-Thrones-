# Cycle AR — Block AR1: Replay Drift Taxonomy Consolidation

**Date:** 2026-06-06  
**Scope:** Design artifact only. No code, test, manifest, or runtime changes.

**Prerequisite:** [`cycle_ar_replay_drift_classification_recon.md`](cycle_ar_replay_drift_classification_recon.md)

---

## 1. Purpose

Consolidate replay drift signals from two existing layers into one **canonical owner-oriented drift taxonomy**:

| Layer | Vocabulary | Role today |
| --- | --- | --- |
| **Measurement drift buckets** | `exact_drift`, `structural_drift`, `semantic_drift` | How an observation diverged from expectation (golden turn comparison) |
| **Failure taxonomy** | `category`, `replay_tags`, `primary_owner` | Symptom classification for investigation routing |

Cycle AR introduces a third axis — **owner drift bucket** — that is stable for operators and tooling:

`route_drift` | `speaker_drift` | `fallback_drift` | `ownership_drift` | `emission_drift` | `semantic_drift` | `lineage_drift` | `projection_drift` | `replay_drift_unclassified`

This document defines that taxonomy, owner mapping, and the recommended implementation seam for Block AR2.

---

## 2. Existing drift inventory

### 2.1 Single-run measurement buckets (`classify_golden_drift`)

Produced in `tests/helpers/golden_replay.py::classify_golden_drift` from `_evaluate_golden_expectation` and opt-in exact-text hash comparison. Bucket assignment for protected field paths uses `tests/helpers/golden_replay_projection.py::protected_observation_drift_bucket`.

| Existing Signal | Current Bucket | Current Consumer |
| --- | --- | --- |
| Opt-in `final_text` hash mismatch (`exact_text` / `expectation["exact_text"]`) | `exact_drift` | `classify_golden_drift` summary; drift row → `classify_replay_failure` → `failure_classifications[]`; optional `record_failure_dashboard_rows` (env); `render_golden_replay_markdown_report`; protected assertion side-channel via `record_protected_replay_assertion_failure` |
| Protected field invariant mismatch (39 paths: route, speaker, FEM, sanitizer trace, trace.*) | `structural_drift` | Same as above; `protected_observation_drift_bucket` registry; `docs/testing/protected_replay_manifest.md` (generated table); `tools/refresh_protected_replay_manifest.py --check`; `tests/test_failure_classifier.py` registry summary |
| `scaffold_leakage` predicate failure | `semantic_drift` | Same as above; classifier → `category=sanitizer`, tag `scaffold_leakage` |
| `final_text` semantic predicates (`semantic.*`, forbidden fragments) | `semantic_drift` | Same as above; classifier → `category=semantic_mutation`, tag `semantic_mutation` |
| Per-row `drift_bucket` on drift rows passed to classifier | `exact_drift` / `structural_drift` / `semantic_drift` (copied into `replay_tags`) | `failure_classifier._replay_tags`, `classify_failure_category`, severity/confidence heuristics |
| Aggregated `failure_classifications` | Derived `category` + `primary_owner` (not owner drift bucket yet) | `render_protected_replay_failure_report`; `render_failure_dashboard_markdown`; CI artifact `artifacts/golden_replay/replay_failure_report.md` (via `tests/conftest.py::pytest_sessionfinish`) |
| `status` / `summary` counts | Pass/fail over measurement buckets | `render_golden_replay_markdown_report`; long-session probes; unit tests in `tests/test_golden_replay.py` |

### 2.2 Rerun comparison deltas (`compare_golden_replay_reruns`)

Produced in `tests/helpers/golden_replay.py::compare_golden_replay_reruns`. Always `report_only: true`; never raises; no `failure_classifications` today.

| Existing Signal | Current Bucket | Current Consumer |
| --- | --- | --- |
| `selected_speaker_id` change between runs | Rerun delta key `speaker` (+ `summary.speaker_delta_count`) | Scorecard JSON; `render_rerun_drift_scorecard_markdown`; `record_rerun_drift_scorecard` → `write_rerun_drift_scorecard_artifacts` (opt-in via `--write-rerun-drift-scorecard` / env); `tests/test_golden_replay.py` rerun tests |
| `route_kind` change | Rerun delta key `route` (+ `summary.route_delta_count`) | Same |
| `fallback_family` and/or fallback owner change | Rerun delta key `fallback` (+ `summary.fallback_delta_count`); owner from `_fallback_owner_for_rerun_turn` (turn fields + lineage `fallback_selected` events) | Same; `frequencies.fallback_families`, `frequencies.fallback_owners` |
| Normalized `final_text` hash change | Rerun delta key `text_fingerprint` (+ `summary.text_fingerprint_delta_count`) | Same |
| `scaffold_leakage` predicate change | Rerun delta key `scaffold` (+ `summary.scaffold_delta_count`) | Same |
| Runtime lineage summary change (`build_runtime_lineage_summary`) | Rerun delta key `runtime_lineage` (+ `summary.runtime_lineage_delta_count`) | Same; `frequencies.runtime_lineage` |
| `response_delta_*` field changes | Rerun delta key `response_delta` (+ `summary.semantic_delta_frequency_delta_count`) | Same; `frequencies.response_delta` (checked/failed/repaired/kinds/echo bands) |
| Turn-count mismatch (extra previous/current turns) | Scorecard metadata (`extra_*_turn_count`); not a drift bucket | Scorecard JSON/markdown only |
| Aggregate frequency deltas (speakers, routes, fallback families/owners) | `frequencies.*` | Scorecard markdown frequency sections |

### 2.3 Adjacent signals (not separate drift buckets today)

| Signal | Source | Consumer |
| --- | --- | --- |
| Long-session route/speaker/fallback **counts** (single run) | `summarize_long_session_replay_observations`, `summarize_fallback_escalation_observations` | Supporting golden replay tests; not classified |
| Runtime lineage events on pass | `record_runtime_lineage_events` (dashboard opt-in) | Dashboard lineage section; excluded from drift classification (`test_golden_drift_classification_ignores_runtime_lineage_diagnostics`) |
| Scenario-spine artifact diff | `tools/compare_scenario_spine_reruns.py` | Advisory operator artifact; outside golden rerun scorecard |

---

## 3. Terminology guardrail

To avoid collision with existing measurement vocabulary:

| Term | Values | Layer |
| --- | --- | --- |
| **Measurement drift bucket** | `exact_drift`, `structural_drift`, `semantic_drift` | Unchanged; assigned by `protected_observation_drift_bucket` / `classify_golden_drift` |
| **Failure category** | `route`, `speaker`, `fallback`, `emission`, … | Unchanged; `failure_classification_contract.py` |
| **Owner drift bucket** (new) | `route_drift`, `speaker_drift`, … | Cycle AR canonical taxonomy; field name **`owner_drift_bucket`** recommended on enriched rows |

Measurement `semantic_drift` and owner drift bucket `semantic_drift` share a label but operate at different layers. AR2 should store the new axis as `owner_drift_bucket` in JSON rows to keep layers distinct.

---

## 4. Proposed canonical owner drift taxonomy

### 4.1 Bucket definitions

#### `route_drift`

| Attribute | Detail |
| --- | --- |
| **Triggering fields** | `route_kind`, `resolution_kind`, `trace.social_contract_trace.route_selected`, `trace.canonical_entry.*`; continuity fields when route/interaction shape breaks: `dialogue_lock`, `active_interaction`, `current_interlocutor`; rerun `deltas.route` |
| **Intended owner** | Route / interaction-context surface (`primary_owner=route`) |
| **Source telemetry** | Observed turn projection; social contract trace; interaction continuity contract |
| **Examples** | Expected `dialogue`, observed `social`; missing route metadata with raw absent (`missing_route_metadata`); legal rerun route flip on long-session branch |

#### `speaker_drift`

| Attribute | Detail |
| --- | --- |
| **Triggering fields** | `selected_speaker_id`, `reply_owner`, `visible_grounded_speaker`, speaker-related trace paths; rerun `deltas.speaker` |
| **Intended owner** | Speaker contract (`primary_owner=speaker`) |
| **Source telemetry** | FEM + `trace.social_contract_trace`; speaker contract enforcement lineage |
| **Examples** | Wrong speaker on strict-social turn; vocative override not applied; rerun speaker sequence change across legal runs |

#### `fallback_drift`

| Attribute | Detail |
| --- | --- |
| **Triggering fields** | `fallback_family`, `fallback_temporal_frame`, `final_emitted_source`, `opening_recovered_via_fallback`; rerun `deltas.fallback` when family changes |
| **Intended owner** | Fallback behavior / gate terminal path (`primary_owner=fallback`) |
| **Source telemetry** | Projected `fallback_family` (diegetic-first from FEM); `final_emitted_source`; diegetic + provenance FEM fields (raw, not collapsed) |
| **Examples** | `fallback_family_mismatch`; forced global scene fallback; rerun fallback family frequency shift |

#### `ownership_drift`

| Attribute | Detail |
| --- | --- |
| **Triggering fields** | `opening_fallback_owner_bucket`, `opening_fallback_authorship_source`, `sealed_fallback_owner_bucket`, `visibility_fallback_owner_bucket`, `visibility_fallback_pool`, `visibility_fallback_kind`, `visibility_replacement_applied`; rerun `deltas.fallback` when **owner** changes but family stable; `fallback_selection_owner` / `fallback_content_owner` split conflicts |
| **Intended owner** | Fallback ownership / authorship surface (`primary_owner=fallback`; `investigate_first` may route to `game/final_emission_meta.py`, `game/opening_deterministic_fallback.py`, or gate) |
| **Source telemetry** | `game/final_emission_meta.py` bucket registries; opening fallback authorship stamps; runtime lineage selection/content owners (diagnostic) |
| **Examples** | Compatibility-local opening ownership on canonical opening path; sealed vs visibility bucket mismatch; rerun fallback owner oscillation without family change |

#### `emission_drift`

| Attribute | Detail |
| --- | --- |
| **Triggering fields** | `response_type_repair_used`, `response_type_repair_kind`, `response_type_required`, `response_type_candidate_ok`, `post_gate_mutation_detected`, `stage_diff`, `final_emission_mutation_lineage`, `upstream_prepared_emission_*`; rerun `deltas.response_delta` |
| **Intended owner** | Final emission gate / repairs (`primary_owner=emission`; upstream subcase → `upstream_prepared_emission`) |
| **Source telemetry** | FEM gate metadata; stage-diff telemetry; response-delta validator fields |
| **Examples** | Unexpected thin_answer repair; post-gate mutation detected; response-delta repair frequency shift across reruns |

#### `semantic_drift`

| Attribute | Detail |
| --- | --- |
| **Triggering fields** | `scaffold_leakage`, `final_text` semantic predicates, `semantic.*` paths; measurement bucket `semantic_drift`; rerun `deltas.scaffold` |
| **Intended owner** | Sanitizer (`scaffold_leakage`) or semantic mutation (`final_text` predicates) → classifier uses `primary_owner=sanitizer` or `semantic_mutation` |
| **Source telemetry** | Output sanitizer trace; stage-diff / final_text observation |
| **Examples** | Scaffold term leak; forbidden fragment in `final_text`; scaffold predicate flip between reruns |

#### `lineage_drift`

| Attribute | Detail |
| --- | --- |
| **Triggering fields** | Rerun `deltas.runtime_lineage` only (frequency/event-count deltas); **not** protected observation field mismatches |
| **Intended owner** | Diagnostic replay/read-side (`primary_owner=replay` for reporting); gate/fallback owners surfaced in lineage summaries for context only |
| **Source telemetry** | `fem_runtime_lineage_events` via `game/final_emission_replay_projection.py`; `game/runtime_lineage_telemetry.py` summaries |
| **Examples** | Gate-path frequency shift; fallback_selection_owner frequency delta; recurrence key change — **advisory only**, excluded from protected acceptance per AO5 manifest |

#### `projection_drift`

| Attribute | Detail |
| --- | --- |
| **Triggering fields** | `unavailable`, missing observation (`missing_observation` tag), `trace.*` unavailable, normalization-adjacent projection gaps (`missing_source_kind=projection_missing_raw_present`); schema/normalization fields when normalized view missing |
| **Intended owner** | Golden replay projection (`primary_owner=projection` or `normalization`) |
| **Source telemetry** | `project_turn_observation` extraction registry; `unavailable[]` on observed turn |
| **Examples** | Route metadata present in raw but missing from normalized observation; unexpected unavailable protected field |

#### `replay_drift_unclassified`

| Attribute | Detail |
| --- | --- |
| **Triggering fields** | Measurement `exact_drift`; rerun `deltas.text_fingerprint`; unmatched field paths (`category=replay_drift` fallback); evaluator warnings; continuity/evaluator edge cases not mapped above |
| **Intended owner** | Replay tooling (`primary_owner=replay`) |
| **Source telemetry** | Opt-in exact hash; text fingerprint; catch-all classifier path |
| **Examples** | Exact prose hash mismatch (report-only policy); legal prose fingerprint change between reruns; evaluator probe failure |

### 4.2 Mapping from existing layers → owner drift bucket

Priority-ordered decision table for AR2 implementation:

| Condition (first match wins) | Owner drift bucket |
| --- | --- |
| Rerun delta `runtime_lineage` | `lineage_drift` |
| Rerun delta `speaker` OR field_path matches speaker needles OR `category=speaker` | `speaker_drift` |
| Rerun delta `route` OR field_path matches route needles OR `category=route` | `route_drift` |
| Field_path matches ownership needles (owner buckets, authorship, visibility/sealed buckets) OR rerun fallback owner-only delta | `ownership_drift` |
| Field_path matches fallback family/source needles OR rerun fallback family delta OR `category=fallback` (non-ownership) | `fallback_drift` |
| Field_path matches emission/repair/stage_diff/upstream needles OR rerun `response_delta` OR `category` ∈ `{emission, validator, upstream_prepared_emission}` | `emission_drift` |
| `scaffold_leakage`, semantic final_text, measurement `semantic_drift`, rerun `scaffold` OR `category` ∈ `{sanitizer, semantic_mutation}` | `semantic_drift` |
| `category=projection` OR `category=normalization` OR missing observation / unavailable | `projection_drift` |
| Measurement `exact_drift`, rerun `text_fingerprint`, `category=replay_drift`, `category=evaluator`, `category=continuity` (if not routed above) | `replay_drift_unclassified` |

**Note:** `category=continuity` defaults to `route_drift` when continuity needles match; otherwise `replay_drift_unclassified`.

---

## 5. Canonical owner mapping

Owner drift buckets reuse **existing** owner signals already copied onto classification rows. No new runtime owner computation in AR1/AR2.

### 5.1 Owner signal inventory

| Signal | Source function / module | Canonical or derived | On classification row today? |
| --- | --- | --- | --- |
| `primary_owner` | `failure_classifier.determine_primary_owner` | Derived from category + `missing_source_kind` + `prepared_emission_owner` override | Yes (required) |
| `secondary_owner` | `failure_classifier.determine_secondary_owner` | Derived from category + projection/normalization context | Yes (optional) |
| `opening_fallback_owner_bucket` | `game/final_emission_meta.opening_fallback_owner_bucket_from_meta` → projection | Canonical bucket | Yes |
| `sealed_fallback_owner_bucket` | FEM → projection | Canonical bucket | Yes |
| `visibility_fallback_owner_bucket` | visibility fallback module → projection | Canonical bucket | Yes |
| `fallback_selection_owner` | `final_emission_replay_projection` / lineage events | Derived | Yes |
| `fallback_content_owner` | `final_emission_replay_projection` / lineage events | Derived | Yes |
| `prepared_emission_owner` | Classifier `_prepared_emission_owner` from upstream telemetry | Derived; can override `primary_owner` | Yes |

### 5.2 Drift bucket → owner source mapping

| Drift Bucket | Primary Owner Source | Secondary Owner Source |
| --- | --- | --- |
| `route_drift` | `primary_owner` → `route` | `secondary_owner` → `projection` when route metadata missing/projection gap |
| `speaker_drift` | `primary_owner` → `speaker` | `secondary_owner` → `emission` |
| `fallback_drift` | `primary_owner` → `fallback` | `secondary_owner` → `emission`; use `fallback_family` / `final_emitted_source` for investigate context |
| `ownership_drift` | `primary_owner` → `fallback` (unchanged coarse owner) | Prefer **`opening_fallback_owner_bucket`**, **`sealed_fallback_owner_bucket`**, or **`visibility_fallback_owner_bucket`** as attribution hint; **`fallback_selection_owner`** / **`fallback_content_owner`** when split; `secondary_owner` → `emission` |
| `emission_drift` | `primary_owner` → `emission` or `upstream_prepared_emission` when `prepared_emission_owner` set | `secondary_owner` → `validator`; **`prepared_emission_owner`** when upstream subcase |
| `semantic_drift` | `primary_owner` → `sanitizer` (scaffold) or `semantic_mutation` (final_text) | `secondary_owner` → `emission` |
| `lineage_drift` | `primary_owner` → `replay` (reporting-only) | **`fallback_selection_owner`** / **`fallback_content_owner`** from lineage frequency deltas for operator context; not acceptance-blocking |
| `projection_drift` | `primary_owner` → `projection` or `normalization` | `secondary_owner` → `route` when runtime-missing-route-metadata; else `None` |
| `replay_drift_unclassified` | `primary_owner` → `replay` | `secondary_owner` → `emission` when text/hash adjacent |

**Policy:** Owner drift bucket does **not** replace `primary_owner` / `secondary_owner`. It groups failures for dashboards; existing owner fields remain authoritative for investigation routing (`investigate_first` unchanged in AR2 unless explicitly scoped).

---

## 6. Implementation seam evaluation

### 6.1 Candidates

| Location | Pros | Cons |
| --- | --- | --- |
| **`tests/helpers/golden_replay.py`** | Owns drift row creation and rerun deltas | Mixes orchestration with taxonomy; rerun and single-run paths diverge; higher regression surface on runner |
| **`tests/helpers/failure_classifier.py`** | Already maps drift rows → categories, owners, tags; single enrichment point for `failure_classifications` | Must add parallel entry for rerun delta dicts (no observed turn row today) |
| **`tests/helpers/failure_dashboard_report.py`** | All artifacts flow through renderers | Too late — classification should be independent of rendering; would duplicate logic if mapping only at render time |
| **New module `tests/helpers/replay_drift_taxonomy.py`** | Isolated pure functions; contract-friendly; testable without runner | One extra import hop; must be called from classifier + rerun adapter |

### 6.2 Recommendation (canonical seam)

**Primary seam:** new module **`tests/helpers/replay_drift_taxonomy.py`** containing:

- `ALLOWED_OWNER_DRIFT_BUCKETS` (or re-export from contract in AR2)
- `classify_owner_drift_bucket(*, field_path, category, measurement_drift_bucket, replay_tags, rerun_delta_key | None) -> str`
- `classify_rerun_delta_owner_drift_bucket(delta_key: str, delta_payload: Mapping) -> str`

**Integration points (AR2, not AR1):**

1. **`failure_classifier.classify_replay_failure`** — after category/owners resolved, set `owner_drift_bucket` on each row (non-breaking additive field).
2. **`golden_replay.compare_golden_replay_reruns`** — optional parallel list `owner_drift_classifications` built from `per_turn_deltas` via taxonomy helper (scorecard stays `report_only: true`).

**Do not** map only in dashboard renderers — consumers need structured JSON on rows/scorecards.

**Do not** change `classify_golden_drift` measurement buckets or assertion paths.

---

## 7. Risks

| Risk | Mitigation |
| --- | --- |
| Name collision: measurement vs owner `semantic_drift` | Store new axis as `owner_drift_bucket`; document both layers in contract |
| `ownership_drift` vs `fallback_drift` ambiguity on combined rerun fallback delta | Split: family change → `fallback_drift`; owner-only change → `ownership_drift`; both → emit two logical rows or primary=fallback with ownership tag (AR2 decision) |
| Lineage promoted to acceptance drift | Keep `lineage_drift` advisory; manifest addendum required for any gate promotion |
| Contract drift | Add `ALLOWED_OWNER_DRIFT_BUCKETS` to `tests/failure_classification_contract.py` + sync test in AR2 |
| Breaking existing dashboards | Additive field only; existing columns unchanged |
| Scope creep into runtime | Taxonomy module imports no `game.*` gate modules; read-only replay side |

---

## 8. Governance confirmation

| Constraint | AR1 status |
| --- | --- |
| No replay expansion | **Confirmed** — taxonomy maps existing signals only |
| No new protected scenarios | **Confirmed** |
| No runtime behavior changes | **Confirmed** — design-only |
| No acceptance criteria changes | **Confirmed** — measurement buckets and assertions untouched |
| Classification/reporting only | **Confirmed** |
| Existing diagnostics continue to work | **Confirmed** — additive `owner_drift_bucket`; no removal of `category`, `replay_tags`, measurement buckets |
| Protected path count (41) | **Unchanged** |
| CI gate (`pytest -m golden_replay`) | **Unchanged** |
| Rerun scorecards advisory | **Unchanged** — `lineage_drift` explicitly report-only |
| AO5 runtime vs acceptance boundary | **Respected** — `lineage_drift` from rerun/lineage summaries only, not protected field promotion |

---

## 9. AR2 recommendation (concise)

**Block AR2 should implement the taxonomy, not reinterpret governance.**

1. Add `tests/helpers/replay_drift_taxonomy.py` with bucket constants + `classify_owner_drift_bucket()` / rerun delta adapter per §6.2 mapping table.
2. Extend `tests/failure_classification_contract.py` with `ALLOWED_OWNER_DRIFT_BUCKETS` and optional row field `owner_drift_bucket`.
3. Enrich `classify_replay_failure` output with `owner_drift_bucket` (additive; all existing fields preserved).
4. Enrich `compare_golden_replay_reruns` return value with `owner_drift_classifications[]` per non-empty `per_turn_deltas` entry (still `report_only: true`).
5. Add focused unit tests in `tests/test_replay_drift_taxonomy.py` (or extend `tests/test_failure_classifier.py`) covering each bucket + unclassified fallback + ownership vs fallback split.
6. Optionally add `owner_drift_bucket` column to `render_protected_replay_failure_report` and rerun scorecard markdown (display-only).
7. Add Cycle AR addendum to `docs/testing/protected_replay_manifest.md` documenting owner drift buckets as reporting vocabulary (no gate promotion).

**Defer to later blocks:** manifest threshold policy, longitudinal drift storage, collapsing `category` into owner drift bucket, promoting lineage to protected drift.
