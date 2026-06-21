# BV13 — Usage Classification

**Date:** 2026-06-21

---

## Consumer groups (BV13 taxonomy)

| Usage class | Importers | Share | Typical symbols |
| --- | --- | --- | --- |
| **gate** | 28 | 48% | `_normalize_text` (e.g. `game/final_emission_acceptance_quality.py` …) |
| **tests** | 13 | 22% | `_normalize_text` (e.g. `tests/helpers/post_speaker_finalize_probe.py` …) |
| **finalization** | 10 | 17% | `_normalize_text` (e.g. `game/acceptance_quality.py` …) |
| **diagnostics** | 6 | 10% | `_normalize_text` (e.g. `game/fallback_provenance_debug.py` …) |
| **ownership** | 1 | 1% | governance scans (e.g. `tests/test_ownership_registry.py` …) |

> **Note:** Importers may appear in multiple classes (e.g. gate test suites = `gate` + `tests`). Totals sum to **58** tag assignments across **52** files.

## Gate cluster (28 tagged)

Gate owner, preflight modules (BN9 extractions), pipeline layers, and gate test suites. **Dominant import:** `_normalize_text` only (24/28 gate-tagged files).

Representative: `final_emission_gate`, `final_emission_gate_preflight_*`, `final_emission_validators`, `final_emission_repairs`, `final_emission_strict_social_stack`.

## Finalization cluster (10 tagged)

Upstream narrative/social modules outside the gate trunk: `acceptance_quality`, `dialogue_social_plan`, `speaker_contract_enforcement`, `narrative_mode_contract`, `upstream_response_repairs`.

## Diagnostics cluster (6 tagged)

Fallback provenance, visibility/sealed/opening fallback, fast fallback composition. Mix of normalize + sanitize + stock-line wrapper.

## Tests cluster (13 importers)

Integration regressions, gate boundary suites, speaker helpers, diegetic fallback block4. One legacy-repair suite (`test_final_emission_visibility`).

## Ownership cluster (1)

`tests/test_ownership_registry.py` — BN9 pregate-text import guard + BJ-111/112 delegate verification (module import + synthetic string fixtures).

## Replay / observability

**No direct replay importers.** Replay suites consume normalized text **indirectly** via gate orchestration smoke and golden fixtures. Text normalization at replay boundary is embedded in production gate/finalize path — **replay risk is behavioral**, not import-graph.

## Ownership bucket cross-cut

| Bucket | Importers |
| --- | --- |
| normalize-primitive | 36 |
| validator-pattern | 4 |
| fallback-content-bridge | 3 |
| formatting-punctuation | 3 |
| formatting-sanitize | 2 |
| policy-constant | 2 |
| legacy-semantic-repair | 1 |
| ownership-governance | 1 |
