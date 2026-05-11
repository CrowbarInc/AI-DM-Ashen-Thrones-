# Failure Hotspots

Repo-wide searches were performed for: `fallback`, `sanitize`, `normalize`, `repair`, `rewrite`, `speaker`, `route`, `projection`, `validator`, `evaluator`, `continuity`, `drift`, `mutation`, `emit`, `emission`, `scaffold`, `safe response`, `stock line`, `alias`, `transition`.

## Hotspots

| Hotspot | Files | Pattern | Risk |
|---|---|---|---|
| Final emission gate | `game/final_emission_gate.py` | Large orchestration stack; selects fallback, applies validators/repairs, stamps FEM, runs late finalization. | CRITICAL: late output mutation can mask upstream route/planner/speaker causes. |
| Final emission validators/repairs split | `game/final_emission_validators.py`, `game/final_emission_repairs.py` | Deterministic validators plus repair layers for answer completeness, fallback behavior, response delta, social structure, referents. | RISKY: split is architecturally good but dashboard must distinguish validator cause from repair effect. |
| Output sanitizer | `game/output_sanitizer.py` | Strip-only default plus legacy sentence rewrite/recovery paths; many internal/procedural phrase patterns. | CRITICAL: sanitizer can either miss leaks or rewrite meaning late. |
| Speaker contract enforcement | `game/speaker_contract_enforcement.py` | Detects emitted speaker signature, validates against contract, repairs canonical/narrator-neutral. | CRITICAL: speaker mutation is user-visible and late. |
| Interaction context/routing | `game/interaction_context.py` | Dense route/target/continuity/vocative/declared-switch logic. | CRITICAL: earliest owner for many wrong route/speaker symptoms. |
| Interaction continuity | `game/interaction_continuity.py` | Continuity contract validation and minimal repairs for speaker switches. | CRITICAL: can repair or truncate speaker ownership in final text. |
| Dialogue social plan | `game/dialogue_social_plan.py` | Structural-only social plan with alias acceptance fields. | RISKY: missing alias metadata causes downstream speaker failures. |
| Upstream response repairs | `game/upstream_response_repairs.py` | Upstream-prepared emission and opening fallback payloads. | CRITICAL: fallback substitution can be authored upstream but selected downstream. |
| Diegetic fallback narration | `game/diegetic_fallback_narration.py` | Central fallback family/template metadata and deterministic fallback renderers. | RISKY: repeated stock-line and fallback family locality. |
| Opening deterministic fallback | `game/opening_deterministic_fallback.py` | Shared opening fallback composer. | RISKY: fallback authorship split between upstream-prepared and gate compatibility paths. |
| Stage diff telemetry | `game/stage_diff_telemetry.py` | Compare-ready snapshots and transitions. | SAFE/RISKY: valuable locality signal, but not yet per-layer enough. |
| FEM metadata | `game/final_emission_meta.py` | Canonical read/write/normalization/events for final emission metadata. | SAFE: strong dashboard substrate. |
| Scenario spine eval | `game/scenario_spine_eval.py` | Offline failures/warnings/classification for branch/session health. | SAFE: evaluator-owned, but can be mistaken for runtime owner. |
| Schema normalization | `game/schema_contracts.py` | Many `normalize_*`, `adapt_legacy_*`, `validate_*` helpers. | SAFE/RISKY: deterministic but can hide legacy shape errors if dashboard only sees normalized output. |
| State authority | `game/state_authority.py` | Domain owner guards and mutation traces. | SAFE: explicit ownership registry. |
| Narration seam guards | `game/narration_seam_guards.py` | CTIR/plan/prompt invariant and emergency/nonplan output metadata. | RISKY: emergency scaffold/fallback paths are locality-critical. |

## Repeated Patterns

- `build_*_contract` / `validate_*` / `repair_*` appears across final emission, tone, anti-railroading, context separation, player-facing purity, acceptance quality, interaction continuity.
- Most validators return structured `failure_reasons` or `warnings`; many repairs then merge a layer-specific meta block into FEM.
- Fallback source/family is carried through FEM fields, diegetic fallback metadata, and stage-diff/fallback provenance.
- Route/speaker evidence appears in multiple places: `resolution.social.npc_id`, `trace.canonical_entry`, `turn_trace.social_contract_trace`, speaker contracts, interaction context.
- Normalized read-side telemetry is centralized in `final_emission_meta.py`, while raw write-side telemetry is scattered across gate, stage diff, fallback provenance, and validators.

## Duplicated or Overlapping Logic

- Text normalization helpers exist in several modules (`final_emission_text`, sanitizer, validators, evaluators, schema-ish helpers). Most are local-purpose, but dashboard should not infer owner from normalization helper name alone.
- Speaker/target concepts are duplicated across canonical entry, social contract trace, speaker selection contract, dialogue social plan, and final text signature detection.
- Fallback behavior is represented as prompt/policy contract, validator failure, repair layer, fallback family metadata, and final source stamping.
- Evaluator and runtime validators both detect debug/scaffold/internal leakage. Evaluator signals should remain advisory; sanitizer/validator own live legality.

## Suspicious Cross-Layer Coupling

- `game/final_emission_gate.py` imports and orchestrates many policy modules, repairs, fallback selection, metadata stamping, and final packaging. It is the largest locality risk.
- `game/output_sanitizer.py` imports strict-social emission helpers to create context-aware fallback lines; useful but cross-cuts sanitizer and social emission.
- `game/final_emission_meta.py` assembles evaluator/stage/FEM observability bundles; this is read-side and documented, but future dashboard must avoid turning it into live policy.
- Text-derived post-GM state updates (emergent enrollment, journal/lead supplements noted in prior CITR audit docs) can affect future routing and should be flagged if a replay failure appears one turn later.

## Hidden Repair Logic

- Response-type repair selection inside final emission gate.
- Strict-social terminal fallback and speaker canonical rewrite.
- Fallback behavior repair layer.
- Player-facing narration purity minimal repair.
- Interaction continuity repair.
- Acceptance quality terminal sentence drop.
- Output sanitizer diegetic fallback rewrite/recovery.
- Opening fallback stub recovery / upstream-prepared fallback attach.
- Destination binding reconciliation of transition targets.
- Schema adapters moving unknown keys into metadata.

## Dashboard Implication

The first dashboard implementation should ingest existing signals, not scan text ad hoc. The most useful high-signal fields are:

- `trace.canonical_entry`
- `turn_trace.social_contract_trace`
- raw and normalized FEM
- `stage_diff_telemetry`
- golden drift rows
- validator failure reasons
- sanitizer/scaffold predicates
- evaluator failures/warnings as secondary context

