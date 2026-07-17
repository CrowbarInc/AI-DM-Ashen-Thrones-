# CK — Fallback Authorship Contraction (Closeout)

**Date:** 2026-06-26  
**Status:** Complete  
**Discovery:** [CK_fallback_authorship_contraction_discovery.md](./CK_fallback_authorship_contraction_discovery.md)  
**Prior cycle:** [docs/audits/closeouts/cycle_ap_fallback_authorship_resolution_closeout.md](./docs/audits/closeouts/cycle_ap_fallback_authorship_resolution_closeout.md)

**Primary metric:** Fallback Surface Pressure = fallback-reference concentration × ownership ambiguity × multi-file update pressure.

---

## A. Executive Recommendation

**Close CK as successful.**

Opening fallback authorship contraction is complete for the scoped CK cycle. Blocks 1–9 established an explicit ownership partition for opening fallback metadata, quarantined retired compat-local authorship to test/evidence helpers, separated projection from telemetry and fail-closed diagnostics, and resolved RTD merge ambiguity without changing gate selection or protected replay values.

Remaining pressure is **non-blocking** and concentrated in other fallback families (visibility breadth, sealed tuple adapters, dual-family replay collapse, stale docs/artifacts). Those concerns exceed CK’s opening-focused scope and warrant a **new cycle** if pursued—not another CK block.

---

## B. Success Criteria Assessment

### Ownership partition (owner / downstream consumer / compatibility layer)

| Layer | Opening fallback state after CK | Assessment |
|-------|----------------------------------|------------|
| **Runtime owner** | Selection: `game/final_emission_opening_fallback.py`. Success authorship write: `game/upstream_response_repairs.py`. Content: `game/opening_deterministic_fallback.py`. Bucket vocabulary: `game/final_emission_ownership_schema.py` + `game/final_emission_owner_bucket_views.py`. FEM contract: `game/final_emission_meta.py`. | **Explicit** |
| **Downstream consumer** | Gate orchestration (`final_emission_response_type.py`, `final_emission_gate.py`), FEM assembly, replay projection (`final_emission_replay_projection.py`), classifier rows (`tests/helpers/failure_classification_builders.py`), lineage telemetry. | **Explicit read-side; no selection authority** |
| **Compatibility layer** | Retired compat-local authorship read mapping; re-export facades (`attribution_read_views.py`); legacy tuple adapters (sealed/visibility—outside CK scope); canonical legacy inject token retained for read compatibility. | **Narrowed and documented** |

### Dimensional assessment

| Dimension | After CK |
|-----------|----------|
| **Runtime fallback ownership** | Opening success path has one authorship writer; fail-closed leaves authorship absent; retired gate-local composer fenced in boundary taxonomy. |
| **Metadata projection** | `OPENING_FALLBACK_PROJECTION_FIELDS` is the sole projection contract; telemetry and diagnostics are explicitly out-of-band. |
| **Replay observation** | Protected golden replay paths exclude out-of-band telemetry and fail-closed diagnostics; dual-family collapse unchanged (AP6). |
| **Compatibility residue** | Canonical legacy inject token `compatibility_local_opening_deterministic` retained read-only; short token `compatibility_local` retired from active registry; production static locks enforce no live writes. |

---

## C. Fallback Surface Pressure Assessment

Qualitative ratings: **High** / **Medium** / **Low** / **Closed**.

| Pressure axis | Before CK (discovery baseline) | After CK Blocks 1–9 |
|---------------|-------------------------------|----------------------|
| Opening authorship ambiguity | **High** — retired gate-local composer overlapped upstream-prepared and legacy read paths | **Closed** — single success writer; fail-closed null authorship; bucket mapping explicit |
| Compat-local token exposure | **High** — raw tokens scattered; short alias in registry; classifier helpers duplicated | **Low** — raw token boundary in `opening_fallback_evidence.py`; short token retired; static AST/re regex locks |
| Classifier/replay fixture pressure | **Medium** — legacy rows and deprecated aliases co-mingled with canonical rows | **Low** — legacy evidence isolated to `legacy_compatibility_local_*` builders; deprecated aliases removed |
| Projection/telemetry ambiguity | **High** — disabled flags and diagnostics mixed with projection fields | **Closed** — three-way metadata classification partition with parity guards |
| Fail-closed diagnostic ambiguity | **Medium** — diagnostic keys present but unclassified relative to projection | **Closed** — `OPENING_FALLBACK_FAIL_CLOSED_DIAGNOSTIC_FIELDS` + RTD merge defaults locked |
| RTD merge ambiguity | **Medium** — two disabled telemetry keys; comments implied both reached FEM | **Closed** — Block 9 quarantine: only `opening_fallback_compatibility_local_disabled` RTD-merges; alias composition-meta-only |

**Overall opening-family Fallback Surface Pressure:** **Low** (was **High** at discovery).

---

## D. Runtime Behavior Summary

### Did runtime behavior change during CK?

**No intentional runtime behavior change** across Blocks 1–9 for opening fallback selection, prose, gate routes, or protected golden replay field **values**. Work was classification, documentation, read-side mapping, telemetry packaging clarity, and contract tests.

### Intentionally narrowed read-compatibility behavior

| Change | Effect |
|--------|--------|
| Short token `compatibility_local` removed from `OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES` (Block 5) | No longer maps via opening authorship legacy registry; retained as documented retired constant only |
| Deprecated classifier builder aliases removed (Block 3) | `observed_legacy_opening_fallback_row`, `observed_opening_authorship_compat_row` no longer exported |
| Raw compat-local literals quarantined to evidence helper (Block 4) | Tests/classifier must use `legacy_compatibility_local_opening_authorship_source()` accessor |
| RTD merge quarantine (Block 9) | `opening_fallback_local_composition_disabled` no longer implied to reach FEM; was already absent from merge defaults |

### Strictly additive telemetry behavior

| Addition | Notes |
|----------|-------|
| `opening_fallback_local_composition_disabled` | Additive alias co-stamped with `opening_fallback_compatibility_local_disabled` on composition_meta (Block 6); composition-meta / RTD-debug only |
| Fail-closed diagnostic registry formalization (Block 8) | Keys existed on paths; classification and parity guards added—no new runtime stamps |
| Metadata registry surfaces | `opening_fallback_metadata_field_registry_surface()`, parity error functions—diagnostic only |

---

## E. Tests and Guards Added

Major guard categories by block:

| Guard category | Blocks | Representative tests / surfaces |
|----------------|--------|-----------------------------------|
| Production never emits legacy compat-local authorship | 1 | `test_production_game_modules_never_assign_compatibility_local_opening_authorship`, `test_canonical_opening_paths_never_emit_either_legacy_compat_local_authorship_token` |
| Legacy evidence isolated to explicit helpers | 2 | `test_compat_local_raw_token_boundary_is_opening_fallback_evidence_only`, `test_failure_classification_builders_compat_local_literals_only_in_legacy_helpers`, `legacy_compatibility_local_opening_classifier_row` |
| Deprecated aliases removed | 3 | `test_failure_classifier` — `observed_legacy_opening_fallback_row` / `observed_opening_authorship_compat_row` absent |
| Raw token boundary enforced | 4 | `legacy_compatibility_local_opening_authorship_source()` sole accessor; AST literal scan |
| Short token retired | 5 | `test_retired_short_compat_local_authorship_not_in_legacy_registry` |
| Disabled telemetry non-authorship enforced | 6 | `test_opening_fallback_compatibility_local_disabled_is_telemetry_not_authorship`; `SEMANTIC_DISALLOWED` includes `compose_opening_fallback_compatibility_local` |
| Projection vs telemetry separation enforced | 7 | `test_opening_fallback_out_of_band_telemetry_excluded_from_projection_registry`, `test_apply_opening_fallback_projection_fields_omits_out_of_band_telemetry` |
| Metadata classification parity enforced | 8 | `opening_fallback_metadata_classification_parity_errors()`, `test_opening_fallback_emitted_metadata_fields_partition_is_complete_and_disjoint`, `test_opening_fallback_fail_closed_diagnostic_keys_are_classified_and_constant_aligned` |
| RTD merge quarantine enforced | 9 | `test_opening_fallback_local_composition_disabled_is_composition_meta_only_not_rtd_merged`, `test_opening_fallback_local_composition_disabled_quarantined_from_fem_rtd_merge`, parity check alias absent from RTD defaults |

Additional cross-cutting guards:

- Owner-bucket mapping ignores telemetry and diagnostics (`test_opening_fallback_owner_bucket_ignores_disabled_telemetry_fields`, `test_opening_fallback_owner_bucket_ignores_fail_closed_diagnostic_fields`)
- Protected replay excludes out-of-band fields (`test_protected_replay_observation_excludes_out_of_band_disabled_telemetry`)

---

## F. Remaining Residual Pressure

Non-blocking pressure outside CK’s opening contraction scope:

| Residual | Rating | Notes |
|----------|--------|-------|
| Visibility fallback breadth | **High** | Largest live selector surface; tuple adapters; multi-concern file |
| Sealed fallback compatibility adapters | **Medium** | `from_legacy_tuple` / `as_legacy_tuple` at gate boundary |
| Sanitizer / retry / upstream-fast ownership surfaces | **Medium** | Distinct families; partially addressed in Cycle AP5; not re-contracted in CK |
| Dual-family replay collapse | **Medium** | AP6 documented precedence; FEM still carries `fallback_family_used` + `realization_fallback_family` |
| Stale docs / artifacts | **Low–Medium** | `docs/gate_cleanup_inventory.md`, `artifacts/**` replay payloads reference pre-CK shapes |
| Canonical legacy inject token retained | **Low** | `compatibility_local_opening_deterministic` read-only for classifier/replay negative invariants; removable only after matrix migration |

---

## G. Recommendation For Next Cycle

**No further CK blocks.**

CK achieved its opening-focused authorship contraction goal. Recommended follow-on (pick one when scheduling):

1. **New cycle — visibility/sealed fallback breadth** (highest runtime pressure; selector + adapter retirement inventory before code removal)
2. **New cycle — replay projection / dual-family collapse** (if protected observations can migrate to single observed `fallback_family` without FEM write-time collapse)
3. **Documentation cleanup cycle** (align gate cleanup inventory and architecture audit excerpts with CK registries; archive generated artifact references)

Do **not** extend CK for visibility/sealed work—the discovery doc explicitly flagged those as higher-risk, broader-scope contractions.

---

## Completed Blocks Summary (1–9)

| Block | Focus | Outcome |
|-------|-------|---------|
| **1** | Legacy opening authorship partition | Retired compat-local tokens read-only; production never emits; maps to `unknown-ambiguous` |
| **2** | Classifier/replay evidence quarantine | Legacy fixtures centralized in `opening_fallback_evidence.py` + `legacy_compatibility_local_*` builders |
| **3** | Deprecated alias retirement | Removed stale classifier row builder aliases |
| **4** | Raw-token boundary | Single accessor; AST/static locks on literals and constant imports |
| **5** | Short-token retirement | `compatibility_local` out of active legacy registry |
| **6** | Disabled telemetry clarification | Co-stamped telemetry keys; non-authorship; boundary taxonomy residue |
| **7** | Opening projection registry audit | Out-of-band telemetry disjoint from projection |
| **8** | Metadata classification completion | Three-way partition + emitted-metadata union + parity errors |
| **9** | RTD merge quarantine | Canonical key RTD-merged; alias composition-meta-only |

---

## Verification Commands

### Closeout run (2026-06-26)

```powershell
python -m pytest tests/test_final_emission_meta.py tests/test_final_emission_opening_fallback.py tests/test_opening_fallback_owner_bucket.py -q
python -m pytest tests/test_failure_classifier.py tests/test_golden_replay_fallback_opening_projection.py tests/test_golden_replay_projection_fallback_integration.py tests/test_runtime_lineage_telemetry.py -q
```

**Result:** All tests passed (185 tests combined).

### Recommended ongoing regression slice

```powershell
python -m pytest tests/test_opening_fallback_owner_bucket.py tests/test_final_emission_meta.py tests/test_final_emission_opening_fallback.py tests/test_golden_replay_fallback_opening_projection.py tests/test_golden_replay_projection_fallback_integration.py tests/test_failure_classifier.py -q
```

---

## Bottom Line

CK reduced opening fallback Fallback Surface Pressure from **High** to **Low** by making ownership, metadata classification, and telemetry packaging explicit and test-locked. The cycle is **complete** for its scope. Further fallback contraction should begin a new cycle targeting visibility/sealed breadth or replay projection—not another CK block.
