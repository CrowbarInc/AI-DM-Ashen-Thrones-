# CF7 — Synthetic Row / Classifier Evidence Bridge

## Executive Summary

Synthetic replay observations are **explicit evidence adapters**, not alternate projection implementations. Cycle AO4 consolidated hand-built rows into `synthetic_observed_replay_row()`; CF7 documents the evidence chain from runtime production → live projection → synthetic overlays → classifier consumption.

**Primary finding:** Classifiers consume **shape-compatible** observed dicts that may be (a) live-projected via `project_turn_observation`, or (b) hand-built from `observed_projection_schema_defaults()` plus probe overlays. Only (a) is **acceptance authority**. Synthetic rows intentionally supply neutral defaults and probe literals so classifier/dashboard contracts can run without executing golden replay scenarios.

**Synthetic Evidence Separation (primary metric):** Every builder has a documented owner; overlay-derived fields are enumerated; live FEM projection parity is validated separately for split-owner matrix rows via `project_split_owner_matrix_row()`.

**Runtime behavior unchanged.** Registry and tests only.

---

## Synthetic Builder Inventory

| Builder | Owner | Consumer | Classification |
|---|---|---|---|
| `synthetic_observed_replay_row` | `replay_observed_row_fixtures` | classifier + dashboard probes; CF2/CF5 | **synthetic** — canonical AO4 factory |
| `observed_failure_row` | same | `failure_classifier`; classification sync | **synthetic** — `classifier_probe` alias |
| `observed_dashboard_probe_row` | same | `failure_dashboard_fixtures` | **synthetic** — `dashboard_probe` + empty presence dicts |
| `failure_classification_sync.observed_*` | `failure_classification_sync` | contract sync; split-owner matrix | **synthetic_overlay** — domain field injection |
| `project_synthetic_turn` | `golden_replay_fixtures` | split-owner FEM parity; integration | **live_projection** — via `project_turn_observation` |
| `observed_turn_from_gate_output` | `golden_replay_fixtures` | direct-seam golden replay | **live_projection** — acceptance path |
| `synthetic_rerun_turn` | `replay_observed_row_fixtures` | rerun scorecard tests | **partial_synthetic** — not classifier input |
| `protected_speaker_failure_turn` | `replay_observed_row_fixtures` | failure report rendering | **synthetic_diagnostic** |
| `owner_drift_classification_fixture` | `replay_drift_taxonomy` | drift report tests | **classifier_output** — not observed input |

Machine registry: `tests/helpers/synthetic_replay_evidence_bridge.py::synthetic_replay_builder_inventory()`.

---

## Evidence Matrix

Legend: **shared** = same key in live projection and synthetic defaults; **overlay_derived** = injected by probe overlay or specialty builder; **synthetic_only** = probe literals with no live equivalent in hand-built rows.

| Field | Live Source | Synthetic Source | Classifier Consumer | Notes |
|---|---|---|---|---|
| Flat protected paths (not in overlay) | `project_turn_observation` extraction | `observed_projection_schema_defaults()` | protected classifier overlap (32 fields) | **shared** — neutral defaults mask absent producers |
| `route_kind`, `selected_speaker_id`, `final_text`, … | runtime trace/snap/FEM extractors | `_CLASSIFIER_PROBE_OVERLAY` | category/owner rules | **overlay_derived** |
| `trace` | payload/snap debug assembly | overlay canonical_entry + social_contract_trace | speaker/route investigation | **overlay_derived** |
| `scenario_id` | replay runner stamp | `probe` / `controlled_probe` | classification row | **synthetic_only** |
| `final_text_hash` | `golden_text_hash(final_text)` | `hash123` / `probehash` | classification row | **synthetic_only** |
| `raw_signal_presence`, `normalized_signal_presence` | `_build_projection_status` | dashboard profile `{}` | dashboard evidence column | **synthetic_only** (dashboard profile) |
| `fallback_selection_owner`, `repair_kind`, … (16 extension fields) | runtime lineage on live projection | specialty `observed_*` / matrix overlays | optional classifier evidence | **overlay_derived** |
| `category`, `severity`, `primary_owner`, … | N/A (classifier output) | `classify_replay_failure` | dashboard markdown | **diagnostic_only** |

Full matrix: `classifier_evidence_bridge_matrix()` (overlay + defaults + profile + extension rows).

Classifiers **do not** distinguish synthetic vs live at runtime — distinction is **test/governance responsibility**. Probes use known-bad drift rows with documented synthetic observed shapes.

---

## Overlay Findings

| Overlay | Injected Fields | Purpose | Risk |
|---|---|---|---|
| `_CLASSIFIER_PROBE_OVERLAY` | route, speaker, final_text, trace, response_type, sanitizer nulls, … | Stable classifier/dashboard probe baseline | **Medium** — can be mistaken for live output if overrides omitted |
| `_DASHBOARD_PROBE_DEFAULTS` | scenario_id, hash, empty presence dicts | Dashboard contract parity (BL3/AK3) | **Low** — explicit empty `{}` signals synthetic dashboard shape |
| `failure_classification_sync.observed_*` | domain fields per fallback family | Taxonomy sync without golden replay | **Low** when used with drift rows; matrix rows dual-path with live FEM |
| `protected_speaker_failure_turn` | narrative + lineage event | Report rendering fixture | **Low** — not used for acceptance |
| Legacy matrix `sealed_or_global_replacement_legacy` | synthetic vocabulary only | Classifier accepts legacy token | **Documented** — no FEM projection; synthetic-only |

**Absent producers → synthetic defaults:** `observed_projection_schema_defaults()` applies `None`/`False`/`""` for all flat protected paths (CF2). Synthetic rows therefore **do not** populate `unavailable` or `missing_source_by_field` unless explicitly overridden (e.g. `observed_opening_projection_missing_row`).

**Overlays augment, not replace live projection:** Hand-built rows skip `project_turn_observation`. Live paths (`project_synthetic_turn`, `observed_turn_from_gate_output`, golden replay runner) always use the assembler.

---

## Evidence Provenance

| Field | Runtime Owner | Projection Owner | Synthetic Owner | Classifier Owner |
|---|---|---|---|---|
| FEM flat fields | `game.final_emission_meta` | `golden_replay_projection_extractors` | `golden_replay_projection_fields` (defaults) | `failure_classifier` |
| Route/speaker | trace/snap/resolution producers | extractors / `golden_replay_projection_speaker` | `_CLASSIFIER_PROBE_OVERLAY` | `failure_classifier` |
| Fallback family / buckets | gate/sanitizer/realization | `golden_replay_projection_fallbacks` + runtime lineage | `failure_classification_sync` specialty rows | `failure_classifier` |
| Classifier extension fields | attribution / lineage telemetry | `final_emission_replay_projection` | matrix/specialty overlays | `failure_classifier` + contract |
| Classification output | N/A | N/A | N/A | `failure_classifier::classify_replay_failure` |

**Evidence chain:** Runtime FEM/trace → `project_turn_observation` (acceptance) **or** synthetic factory (probes) → `classify_replay_failure(observed_turn, drift_rows)` → dashboard/report rows via `_copy_manifest_observed_evidence`.

---

## Parity Findings

| Area | Live Authority | Synthetic Role | Status |
|---|---|---|---|
| Golden replay protected scenarios | `pytest -m golden_replay` + `project_turn_observation` | None | **Live only** — acceptance |
| Protected manifest 41 fields | registry + live projection | defaults in synthetic base | **Live authoritative** for semantics |
| Split-owner matrix (15 rows) | `project_split_owner_matrix_row()` | `split_owner_observed_row_from_matrix_row()` | **Dual path** — live FEM parity tested |
| Legacy matrix row (1) | excluded | synthetic classifier vocabulary | **Intentional divergence** |
| Classifier contract probes | optional live; mostly synthetic + drift | primary input surface | **Synthetic convenience** — not acceptance |
| Dashboard controlled failures | synthetic observed + exact drift | renders classification | **Diagnostic** |
| Rerun scorecard | N/A | `synthetic_rerun_turn` partial dict | **Non-classifier** |

**Where divergence is intentional:** probe scenario IDs, hash literals, dashboard empty presence dicts, legacy sealed vocabulary row, specialty rows that omit unavailable routing unless testing projection gaps.

**Where parity is expected:** `project_split_owner_matrix_row` vs matrix owner buckets and lineage events; golden replay structural invariants; CF1–CF4 precedence contracts on live projection.

---

## Tests Added

| Test module | Tests |
|---|---|
| `tests/test_cf7_synthetic_row_classifier_evidence_bridge.py` | 14 tests — builder inventory, AO4 single authority, overlay injection, dashboard presence, protected defaults, live adapter, acceptance invariant, legacy matrix exclusion, matrix live vs synthetic parity (3 parametrized), evidence matrix coverage, classifier overlap documentation, partial rerun turn, evidence kind enum |

Supporting export: `synthetic_classifier_probe_overlay_paths()` in `replay_observed_row_fixtures.py`.

Registry: `tests/helpers/synthetic_replay_evidence_bridge.py`.

---

## Behavior Changes

**Expected default: none.**

No changes to `project_turn_observation`, classifier rules, or synthetic row shapes. Added read-side registry, one overlay path export, and governance tests.

---

## Remaining Risks

1. **Neutral defaults in synthetic rows** still mask absent-source distinctions unless tests override `unavailable` / `missing_source_by_field` (CF2 documented).
2. **Classifiers cannot auto-detect synthetic rows** — no `evidence_source` stamp on observed dicts; governance relies on test boundaries.
3. **Dual matrix path** — reviewers must know whether a failure is from live FEM projection or hand-built matrix row.
4. **`protected_speaker_failure_turn`** hand-builds trace/lineage — keep out of acceptance paths.
5. **Dashboard probes** remain opt-in (`failure_dashboard_probe` marker) — correct boundary, but local runs can still confuse synthetic output with live replay failures.

---

## Recommended Closeout

**The Replay Projection Responsibility Audit (CF) can be considered complete** for characterization purposes:

| CF block | Status |
|---|---|
| CF discovery | Responsibility map + drift sources |
| CF1 | Precedence matrices |
| CF2 | Protected field routing |
| CF3 | Raw/normalized FEM matrix |
| CF4 | Trace nest dotted paths |
| CF5 | Test failure locality |
| CF6 | Generated artifact governance |
| CF7 | Synthetic/classifier evidence bridge |

**Optional post-CF work (not blocking):**

1. Add optional `evidence_adapter: "synthetic_probe" | "live_projection"` metadata key for debug builds only (would require explicit user approval — changes observed shape).
2. Untrack high-churn diagnostic artifacts (CF6 recommendation).
3. Retire `.bak` facade oracle (CF5 recommendation).

CF7 acceptance criteria met:

- [x] Every synthetic replay builder has a documented owner
- [x] Classifier-visible fields have evidence chain in bridge matrix
- [x] Live replay remains sole acceptance authority
- [x] Synthetic overlays explicitly distinguished from projection
- [x] Focused evidence tests added
- [x] Runtime behavior unchanged
- [x] Replay Projection Responsibility Risk fully characterized
