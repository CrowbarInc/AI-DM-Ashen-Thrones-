# BP3 Projection Gap Reality Audit

**Date:** 2026-06-17  
**Scope:** Repository artifact audit only. Projection rules, fallback behavior, runtime semantics, fallback classifications, and replay scoring were not changed.

## Executive Summary

BP3 scanned **3,798 JSON/JSONL artifacts** under `artifacts/` and `data/`, including golden-replay reports, stored sessions, session logs, validation artifacts, runtime hygiene captures, and projection audit output. The scanner found **107 canonical finalized FEM instances** and no parse errors.

None of BP2's four uncovered shapes occurs on canonical finalized FEM:

| Gap shape | Raw occurrences | Turns | Artifacts | Finalized FEM occurrences | Classification |
|---|---:|---:|---:|---:|---|
| `forced_retry_fallback` | 90 | 30 | 30 | 0 | C. Packaging-only |
| `social_fallback_minimal` | 0 | 0 | 0 | 0 | D. Unreachable in scanned corpus |
| `nonsocial_fallback_minimal` | 2 | 1 | 1 | 0 | C. Packaging-only |
| `gpt_budget_or_provider_failure` without trace | 0 | 0 | 0 | 0 | D. Unreachable in scanned corpus |

The apparent retry gap is a lifecycle effect, not an observed projection failure. Stored turns show retry routes on outer GM output and stage-diff snapshots, followed by final gate replacement. The canonical FEM records the terminal `replaced` outcome and is already recognized by the existing sealed/visibility projector.

Across the 107 stored finalized FEM instances, the current projector derives **74 fallback-selected instances**. Expanding projection for the four BP2 shapes would add **0** fallback instances in this corpus, so estimated fallback incidence is unchanged and BP2 shape coverage remains 15/19 (78.95%). There are no persisted runtime-lineage event rows in this older corpus; the count of 74 is derived read-only from stored FEM with the current projector.

## Gap Inventory

| Shape | BP2 concern | Reality-audit result |
|---|---|---|
| `forced_retry_fallback` | Strong retry route + kind + family might reach FEM without projection | Route is active before/during gate, but does not survive as finalized FEM route in 30 observed turns |
| `social_fallback_minimal` | Minimal social retry route might reach FEM | No recorded occurrence anywhere in scanned artifacts |
| `nonsocial_fallback_minimal` | Minimal non-social retry route might reach FEM | One active session turn records it on outer GM/stage metadata only; finalized FEM uses a different terminal route |
| provider-failure family without trace | Governed family might reach FEM without upstream provenance trace | No recorded occurrence; trace-less finalized provider-family shape remains unsupported by evidence |

The audit uses only mappings stored under `_final_emission_meta` or `final_emission_meta` as canonical finalized FEM. Outer `gm_output`, metadata, and stage snapshots are inventoried but cannot establish a projection false negative.

## Artifact Evidence

### Forced retry

`forced_retry_fallback` appears in 30 `artifacts/scene_canon_hygiene_runtime/*/data/session_log.jsonl` files. Each turn contributes three matches:

1. outer `$.gm_output.final_route`;
2. retry-terminal result stage snapshot;
3. final-emission gate-entry stage snapshot.

Representative evidence:

- `artifacts/scene_canon_hygiene_runtime/05a837b7639645449d247767ea131d9d/data/session_log.jsonl`
- turn timestamp `2026-06-11T00:49:45.196009Z`
- route kind `observe`
- outer GM route `forced_retry_fallback`
- outer realization family `retry_terminal_fallback`
- no persisted `fallback_selected` event
- final gate exit changes route to `replaced`
- canonical finalized FEM does **not** contain `forced_retry_fallback`

This same three-context pattern accounts for all 90 matches. Full paths, timestamps, route kinds, context paths, and metadata fields are in `projection_gap_reality_report.json`.

### Non-social minimal retry

`nonsocial_fallback_minimal` appears twice in one turn in `data/session_log.jsonl`:

- turn timestamp `2026-05-06T00:23:07.470532Z`
- route kind `observe`
- outer `$.gm_output.final_route=nonsocial_fallback_minimal`
- one stage snapshot repeats that route
- no persisted `fallback_selected` event
- neither match is inside canonical finalized FEM

### Social minimal retry

No exact `final_route=social_fallback_minimal` occurrence was found in finalized FEM, outer GM records, stage snapshots, golden-replay reports, scenario-spine artifacts, session data, or validation artifacts.

### Provider failure without trace

No finalized or packaging occurrence of `realization_fallback_family=gpt_budget_or_provider_failure` without a same-mapping `fallback_provenance_trace.source=fallback` was found. The BP2 projection coverage report contains a synthetic evidence shape for this case and was deliberately recorded as an audit reference, not counted as runtime evidence.

## Reachability Classification

### `forced_retry_fallback`: C. Packaging-only

The code path is active and repeatedly observed, so it is not code-level unreachable or merely historical. It is packaging-only for projection purposes: the retry route describes an intermediate GM result, then the gate replaces the terminal emission and finalized FEM records `replaced`.

**Recommendation:** Leave unprojected.

### `social_fallback_minimal`: D. Unreachable in scanned corpus

The route exists in runtime source but has no stored artifact evidence. Corpus absence does not prove formal code unreachability.

**Recommendation:** Needs further investigation only if future runtime artifacts produce it; do not add projection now.

### `nonsocial_fallback_minimal`: C. Packaging-only

One current `data/session_log.jsonl` turn proves the path is reachable before finalization. It does not survive to FEM, so it does not represent missing finalized fallback projection.

**Recommendation:** Leave unprojected.

### Provider failure family without trace: D. Unreachable in scanned corpus

No recorded trace-less family occurrence exists. Existing upstream-fast projection requires positive provenance trace evidence, which remains the safer selection proof.

**Recommendation:** Leave unprojected.

No gap qualifies as A (Confirmed active on finalized FEM), B (Historical finalized FEM only), or E (Ambiguous finalized evidence).

## Frequency Analysis

| Shape | `shape_occurrence_count` | `shape_turn_count` | `shape_artifact_count` | Packaging-only | Finalized FEM |
|---|---:|---:|---:|---:|---:|
| `forced_retry_fallback` | 90 | 30 | 30 | 90 | 0 |
| `social_fallback_minimal` | 0 | 0 | 0 | 0 | 0 |
| `nonsocial_fallback_minimal` | 2 | 1 | 1 | 2 | 0 |
| provider failure without trace | 0 | 0 | 0 | 0 | 0 |

Raw occurrence counts intentionally include multiple lifecycle contexts within one turn. Turn counts prevent the retry result, gate entry, and outer GM copies from being misread as three fallback turns.

Corpus coverage:

- artifact files considered: 3,798;
- artifacts containing any gap evidence: 31;
- canonical finalized FEM instances: 107;
- parse failures: 0;
- BP2/BP3 audit JSON reports: scanned as audit references and excluded from occurrence metrics.

## Projection Impact Estimate

| Impact metric | Value |
|---|---:|
| Current fallback instances derived from finalized FEM | 74 |
| Persisted fallback-selected turn rows | 0 |
| Additional finalized fallback instances if four gaps were projected | 0 |
| Estimated adjusted projected fallback count | 74 |
| Estimated relative fallback-count increase | 0.00% |
| BP2 canonical shape coverage before | 78.95% |
| Confirmed gap shapes | 0 |
| Estimated adjusted shape coverage | 78.95% |

The older stored corpus predates persisted runtime-lineage rows, so `current_projected_fallback_count` is obtained by applying the unchanged read-side projector to each stored FEM. This does not modify artifacts or claim that all 74 events were persisted at capture time.

Adding branches for outer retry routes would not improve finalized-FEM coverage. If applied outside FEM, it could double-count an intermediate retry choice and the later gate replacement that actually reached final emission.

## Recommendation Per Gap

| Gap | Recommendation | Reason |
|---|---|---|
| `forced_retry_fallback` | **Leave unprojected** | Active but intermediate; final FEM already reflects the replacement that won |
| `social_fallback_minimal` | **Needs further investigation** | Source path exists, but no artifact evidence supports a projection branch |
| `nonsocial_fallback_minimal` | **Leave unprojected** | Observed only on outer/stage packaging, never finalized FEM |
| provider failure without trace | **Leave unprojected** | No evidence; provenance trace remains the safe positive selection signal |

No dead path should be removed on BP3 evidence alone. The retry paths are runtime-reachable even when their temporary routes do not survive finalization.

## Risks

- Repository artifacts are a finite, test-heavy corpus and do not represent all production executions.
- Classification D means unobserved in the scanned corpus, not mathematically unreachable code.
- The 30 forced-retry turns are scene-canon hygiene captures and may overrepresent one validation pattern.
- A future packaging change could preserve retry routes on FEM and convert a packaging-only shape into a true projection gap.
- Applying the current projector to historical FEM estimates present-day projection behavior, not historical persisted telemetry.
- Raw occurrence counts include lifecycle duplication; turn and finalized-FEM counts are the appropriate incidence signals.
- Audit reports containing synthetic evidence must remain excluded from runtime occurrence totals.

## BP4 Recommendation

BP4 should add a **read-only projection-gap watch section** to the BP1 report or scenario-spine aggregate output. It should track the four exact finalized-FEM conjunctions over newly generated artifacts and distinguish outer/stage evidence from canonical FEM. No projection expansion is justified now.

The watch should alert only when a gap shape first appears on finalized FEM without a `fallback_selected` event. This converts BP3's one-time corpus audit into longitudinal evidence while preserving current projection semantics.
