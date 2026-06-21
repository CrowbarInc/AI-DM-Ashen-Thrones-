# BV12 — Decomposition Projection

**Date:** 2026-06-21  
**Baseline:** BV11 smoke bridge combined FI **95**  

---

## FI projection

| Stage | replay_smoke FI | gate_integration FI | Combined | Δ vs current |
| --- | --- | --- | --- | --- |
| Current (BV11) | 56 | 39 | 95 | — |
| After Phase 1 | ~53 | ~37 | 90 | −5 |
| After Phase 2 (range) | 8–12 | 6–10 | 38–48 | −47 to −57 |
| After Phase 3 (target) | ≤12 | ≤10 | ≤22 legacy + domain facades | −73 net legacy |

## Domain facade FI distribution (Phase 2 steady state, estimate)

| Facade | Projected FI | Notes |
| --- | --- | --- |
| replay_fem_read_smoke | 40–48 | Largest slice — acceptance + observability |
| gate_orchestration_smoke | 22–28 | Integration gate runs |
| fallback_bridge_smoke | 5–6 | Dual-bridge fallback suites |
| replay_projection_smoke | 6–8 | Transcript/golden-adjacent |
| gate_validation_smoke | 6–9 | Gate owner suites |
| pipeline_debug_notes_smoke | 3 | Isolated in Phase 1 |
| gate_fixture_smoke | 2 | Isolated in Phase 1 |

## Replay risk assessment

| Factor | Risk | Mitigation |
|---|---|---|
| Bridge symbols are pure delegates | **Low** | No assertion logic relocation |
| Gate orchestration touches runtime | **Medium** | Migrate orchestration consumers in isolated wave |
| Golden-replay projection boundary | **Low-medium** | Keep `golden_replay_projection` separate; projection facade is FEM-read only |
| Fallback dual-bridge suites | **Medium** | Dedicated `fallback_bridge_smoke`; migrate last |

## Scorecard impact (projected post-Phase 2)

| Dimension | Projected delta |
| --- | --- |
| Maintenance drag | +0.5 |
| Operational simplicity | +0.5 |
| Maintenance economics | +0.5 |
| Ownership clarity | +0.25 |

## Success criteria

A **clear decomposition path exists**: Phase 1 is immediately actionable (5 migrations, low replay risk). Phase 2 reduces legacy bridge combined FI by **~50–60** while preserving BV7/BV10 governance intent.

