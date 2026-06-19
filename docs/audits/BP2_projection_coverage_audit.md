# BP2 Fallback Projection Coverage Audit

**Date:** 2026-06-17  
**Scope:** Audit only. No projection rule, fallback behavior, runtime semantics, emitted text, FEM write path, or replay pass/fail behavior changed.

## Executive Summary

BP2 evaluated the existing `build_fem_runtime_lineage_events()` projector against a deterministic catalog of **19 canonical strong finalized-FEM evidence shapes**. Fifteen shapes produce exactly one `event_kind == "fallback_selected"` event and four do not.

| Metric | Value |
|---|---:|
| Projection candidates | 19 |
| Projected fallback shapes | 15 |
| Unprojected fallback shapes | 4 |
| Shape-level projection coverage | **78.95%** |

This is **shape coverage**, not runtime incidence. The denominator contains one canonical example of each strong finalized evidence combination audited by BP2. Eight availability-only, attribution-only, explicit non-use, and policy-repair shapes are documented separately and excluded because they do not prove fallback selection.

The strongest suspected gaps are three retry-terminal routes written by `game/gm_retry.py`: `forced_retry_fallback`, `social_fallback_minimal`, and `nonsocial_fallback_minimal`. If these route/family combinations survive together on finalized FEM, the current projector emits no fallback event. The fourth gap, `gpt_budget_or_provider_failure` without `fallback_provenance_trace`, is ambiguous: its governed family is strong fallback evidence, but the projector intentionally requires a provenance trace for the upstream-fast path.

Machine-readable results are in `artifacts/golden_replay/projection_coverage_report.json` and are reproducible with:

```powershell
python tools/fallback_projection_coverage_audit.py --output artifacts/golden_replay/projection_coverage_report.json
```

## Current Projection Vocabulary

The authoritative decision tree is `_fem_selected_fallback_projection()` in `game/final_emission_replay_projection.py`; `build_fem_runtime_lineage_events()` packages its result through `game.runtime_lineage_telemetry.make_runtime_lineage_event()`.

| Fallback kind | Event owner | FEM family evidence in canonical shape | Projection source |
|---|---|---|---|
| `sanitizer_strict_social` | `game.output_sanitizer` | diegetic `social`; realization `strict_social_deterministic_fallback` | `sanitizer_strict_social_fallback_used is True` |
| `sanitizer_empty_output` | `game.output_sanitizer` | none required | sanitizer empty/lineage-empty used flag |
| `opening_failed_closed` | `game.final_emission_gate` | `scene_opening`; `gate_terminal_repair` | opening fail-closed flag, repair kind, or source |
| `scene_opening` | `game.final_emission_gate` | `scene_opening`; `upstream_prepared_emission` | opening recovered flag or opening deterministic source |
| `response_type_prepared_emission` | `game.final_emission_gate` | realization `upstream_prepared_emission` | prepared emission used plus supported answer/action repair |
| `minimal_social_emergency_fallback` | `game.final_emission_gate` | `social`; `strict_social_deterministic_fallback` | exact final emitted source |
| `strict_social_fallback` | `game.final_emission_gate` | `social`; `strict_social_deterministic_fallback` | recognized strict-social source or dialogue repair |
| `visibility_or_scene_replacement` | `game.final_emission_gate` | `action`; `gate_terminal_repair` | visibility/first-mention/referential replacement flag |
| `upstream_fast_fallback` | `game.api` | realization `retry_terminal_fallback` in the canonical shape | `fallback_provenance_trace.source == fallback` |
| `sealed_social_interlocutor_fallback` | `game.final_emission_gate` | `social`; `strict_social_deterministic_fallback` | replaced route plus sealed source/kind refinement |
| `sealed_passive_scene_pressure_fallback` | `game.final_emission_gate` | `action`; `gate_terminal_repair` | replaced route plus sealed source/kind refinement |
| `sealed_npc_pursuit_neutral_fallback` | `game.final_emission_gate` | `action`; `gate_terminal_repair` | replaced route plus sealed source/kind refinement |
| `sealed_anti_reset_continuation_fallback` | `game.final_emission_gate` | `action`; `gate_terminal_repair` | replaced route plus sealed source/kind refinement |
| `sealed_global_scene_fallback` | `game.final_emission_gate` | `observe`; `gate_terminal_repair` | replaced route plus sealed source/kind refinement |
| `sealed_unknown_replacement` | `game.final_emission_gate` | realization `gate_terminal_repair` in the canonical shape | any otherwise-unrecognized `final_route == replaced` |

`project_sealed_replacement_subkind_from_fem()` also defines `sealed_opening_fallback`. In the full projector, opening source/recovery evidence has higher precedence and emits `scene_opening`; therefore `sealed_opening_fallback` is helper vocabulary but not a distinct reachable fallback kind in this canonical full-builder audit.

Family fields do not enter the runtime-lineage event envelope. This is intentional: lineage stores `fallback_kind`, and BP1 joins `fallback_family_used` and `realization_fallback_family` from the containing turn's FEM. The fields remain separate.

## Fallback Evidence Without Projection

| Evidence shape | Source | Why fallback-related | Assessment |
|---|---|---|---|
| `final_route=forced_retry_fallback`, `fallback_kind=retry_escape_hatch`, realization family `retry_terminal_fallback` | `game/gm_retry.py::force_terminal_retry_fallback` | Terminal route, local kind, and governed family all identify emitted retry fallback | Suspected false negative **if this combination is present on finalized FEM** |
| `final_route=social_fallback_minimal`, `fallback_kind=social_empty_resolution_repair`, realization family `retry_terminal_fallback` | `game/gm_retry.py::ensure_minimal_social_resolution` | Explicit final route and governed retry family | Suspected false negative if present on finalized FEM |
| `final_route=nonsocial_fallback_minimal`, `fallback_kind=nonsocial_empty_resolution_repair`, realization family `retry_terminal_fallback` | `game/gm_retry.py::ensure_minimal_nonsocial_resolution` | Explicit final route and governed retry family | Suspected false negative if present on finalized FEM |
| realization family `gpt_budget_or_provider_failure` without `fallback_provenance_trace` | `game/api.py`, `game/gm.py` | Canonical governed family explicitly denotes provider/budget fallback | Ambiguous: family is strong, but trace may be intentionally required to prove selected final content |

The retry functions write their route fields on GM output. `_attach_retry_terminal_family()` mirrors the governed family into existing FEM, but does not itself mirror the retry `final_route` or `fallback_kind`. BP2 therefore does not claim these combinations always occur in stored FEM. It identifies a projection gap conditional on co-presence and recommends an empirical persistence audit before any rule addition.

## Coverage Metrics

The complete deterministic metrics, including every bucket, are in the JSON artifact. Key slices:

### By fallback kind

- Fifteen current runtime fallback kinds each have 1/1 canonical shape coverage.
- Four strong shapes have no runtime fallback kind and are grouped under the audit-only `<unprojected>` label: 0/4.
- `<unprojected>` is not a proposed runtime classification.

### By owner bucket

- Canonical `sealed-gate` and `strict-social-sealed` evidence shapes project fallback events.
- The four unprojected shapes have no canonical fallback owner bucket.
- Runtime lineage currently places generic `fallback_owner_bucket` on opening projections only. Sealed and visibility owner-bucket evidence remains on FEM, while explicit selection/content owners reach sealed lineage events. This is a metadata-reach gap, not a selection-event gap.

### By diegetic family

| Diegetic family | Projected / candidates | Coverage |
|---|---:|---:|
| `action` | 4 / 4 | 100% |
| `observe` | 1 / 1 | 100% |
| `scene_opening` | 2 / 2 | 100% |
| `social` | 4 / 4 | 100% |
| absent | 4 / 8 | 50% |

The absent-family bucket contains legitimate projections that need no diegetic template family plus all four unprojected shapes.

### By realization family

| Realization family | Projected / candidates | Coverage |
|---|---:|---:|
| `gate_terminal_repair` | 7 / 7 | 100% |
| `strict_social_deterministic_fallback` | 4 / 4 | 100% |
| `upstream_prepared_emission` | 2 / 2 | 100% |
| `retry_terminal_fallback` | 1 / 4 | 25% |
| `gpt_budget_or_provider_failure` | 0 / 1 | 0% |
| absent | 1 / 1 | 100% |

The governed-family view concentrates the possible gap: ordinary gate/opening/social families are fully represented, while retry/provider families depend on the narrower upstream provenance path.

## Suspected False Negatives

1. **Retry terminal route family:** `forced_retry_fallback` plus `retry_terminal_fallback` has stronger selection semantics than family-only evidence, but no branch in `_fem_selected_fallback_projection()`.
2. **Social minimal retry route:** `social_fallback_minimal` plus the retry family is similarly unprojected.
3. **Non-social minimal retry route:** `nonsocial_fallback_minimal` plus the retry family is similarly unprojected.
4. **Provider failure without trace:** `gpt_budget_or_provider_failure` is unprojected unless a separate `fallback_provenance_trace.source=fallback` survives. This may be conservative by design rather than a defect.

The first three are conditional suspected false negatives because the route fields may remain on the outer GM output rather than the finalized FEM sidecar consumed by the projector. BP2 did not modify packaging to test that hypothesis.

## Intentional Omissions

Eight audited shapes correctly produce no `fallback_selected` event and are excluded from the 19-shape denominator:

- diegetic family metadata alone;
- prepared emission valid/available but not used;
- opening authorship metadata with recovery false;
- visibility fallback candidate metadata with replacement false;
- sealed owner bucket alone;
- sanitizer fallback explicitly marked unused;
- `dialogue_minimal_repair` without fallback selection proof;
- fallback-behavior policy repair metadata.

These fields describe content classification, candidate availability, attribution, explicit non-use, or policy compliance. Treating them as selected fallback evidence would create false positives and inflate BP1 incidence.

## Recommended Projection Additions (if any)

No projection addition is made or recommended unconditionally in BP2.

The three retry route shapes are credible candidates for a later change **only after** an empirical artifact audit confirms that `final_route` and `realization_fallback_family` coexist on finalized FEM and that no existing `fallback_provenance_trace` already covers those turns. If confirmed, a future block could add narrowly conjunctive retry-route branches rather than family-only inference.

Do not project on `fallback_family_used`, `realization_fallback_family`, owner buckets, prepared availability, or fallback-behavior repair alone. Those are intentionally insufficient proof.

For provider failure, preserve the trace requirement unless empirical artifacts demonstrate finalized provider-fallback turns consistently lose the trace. A family-only branch would risk classifying provenance metadata as emitted fallback selection.

## Risks

- **Catalog bias:** 78.95% measures the checked canonical shape vocabulary, not frequency in a production or replay corpus.
- **Packaging uncertainty:** retry route fields may not coexist with the mirrored family on finalized FEM; suspected gaps are conditional until persisted artifacts are sampled.
- **Projection precedence:** higher-priority opening/visibility branches can shadow sealed sub-kind vocabulary. Tests lock actual full-builder results.
- **False positives:** broad family-only or bucket-only inference would violate the projector's "proven selection" contract.
- **Metadata reach versus event reach:** families and most bucket fields remain on FEM by design. Their absence from the event object is not itself evidence that the fallback event is missing.
- **Schema drift:** the catalog must be updated deliberately when `_fem_selected_fallback_projection()` gains or removes branches.
- **No semantic coupling:** this audit must remain advisory and must not become a replay pass/fail gate without a separate governance decision.

## BP3 Recommendation

BP3 should be an **empirical finalized-FEM persistence audit** over recorded scenario-spine/golden-replay turn artifacts. It should scan for the four BP2 unprojected evidence combinations, report how often their fields actually coexist, and distinguish:

1. packaging gaps (selection evidence never reaches FEM),
2. projection gaps (evidence reaches FEM but no event is emitted), and
3. trace gaps (provider/retry provenance fails to survive finalization).

Only observed projection gaps should become candidates for new projection rules. This keeps BP3 read-only while converting BP2's conditional findings into repository-corpus evidence.
