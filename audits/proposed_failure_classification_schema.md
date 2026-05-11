# Proposed Failure Classification Schema

Discovery proposal only. Do not implement yet.

## Canonical Failure Categories

| Category | Owner Rule | Typical Evidence |
|---|---|---|
| `route` | Primary when route/lane/target selection is wrong or route metadata is absent from runtime trace. | `route_kind`, `trace.canonical_entry`, `social_contract_trace.route_selected`, route reason. |
| `speaker` | Primary when selected/emitted speaker violates speaker contract or expected reply owner. | `selected_speaker_id`, `speaker_selection_contract`, `speaker_contract_enforcement_reason`. |
| `fallback` | Primary when deterministic fallback/substitute text is selected or fallback family/source is wrong. | `final_emitted_source`, `fallback_family_used`, `realization_fallback_family`, `fallback_temporal_frame`. |
| `emission` | Primary when final-emission packaging/gate selection mutates or stamps output incorrectly. | FEM, `post_gate_mutation_detected`, stage-diff transitions, gate source fields. |
| `semantic_mutation` | Primary when meaning changes after planning, especially late repair/rewrite. | Stage text fingerprint changes, repair flags, semantic predicate failures. |
| `replay_drift` | Primary when exact/structural/semantic expectation fails but runtime owner is not yet inferred. | Golden drift rows. |
| `projection` | Primary when dashboard/replay cannot see fields that raw runtime emitted, or observation helper loses data. | `unavailable`, raw payload comparison. |
| `validator` | Primary when deterministic validator rejects illegal text/shape/schema. | Validator failure reasons, response-type/fallback/answer/referent validation fields. |
| `evaluator` | Primary for advisory score/warning/hard-failure rows from offline/runtime evaluators. | Evaluator score, classification, failures/warnings/events. |
| `continuity` | Primary when active interlocutor, branch/session continuity, or speaker continuity breaks. | Interaction continuity contract, `continuity_status`, evaluator continuity failures. |
| `normalization` | Primary when canonicalization/adaptation changes structure or metadata unexpectedly. | `schema_contracts:*`, normalized-vs-raw differences. |
| `sanitizer` | Primary when internal/scaffold/serialized/procedural text leaks or sanitizer over-rewrites. | Sanitizer debug, scaffold leakage predicate, final text leak terms. |

## Canonical Source-Family Tags

- `api_route`
- `interaction_context`
- `speaker_contract`
- `dialogue_social_plan`
- `interaction_continuity`
- `final_emission_gate`
- `final_emission_meta`
- `response_type`
- `fallback_behavior`
- `strict_social_emission`
- `opening_fallback`
- `output_sanitizer`
- `stage_diff`
- `schema_contracts`
- `state_authority`
- `scenario_spine_eval`
- `playability_eval`
- `narrative_authenticity_eval`
- `behavioral_eval`
- `golden_replay_projection`

## Canonical Replay Tags

- `exact_drift`
- `structural_drift`
- `semantic_drift`
- `missing_observation`
- `dotted_path_mismatch`
- `route_mismatch`
- `speaker_mismatch`
- `fallback_source_mismatch`
- `fallback_family_mismatch`
- `response_type_repair_mismatch`
- `scaffold_leakage`
- `post_gate_mutation`
- `continuity_break`
- `evaluator_failure`
- `evaluator_warning`

## Severity Levels

| Severity | Meaning |
|---|---|
| `critical` | User-facing illegal speaker, semantic mutation, sanitizer leakage, fallback substitution after planning, wrong route/transition, output rewrite after planning. |
| `high` | Structural replay failure with clear owner, missing required metadata that blocks classification, validator hard failure. |
| `medium` | Evaluator hard failure or warning with playable output, repair used unexpectedly but final output remains legal. |
| `low` | Advisory warning, exact-only prose drift where structural/semantic invariants pass, harmless normalization drift. |

## Ownership Rules

1. Use exactly one `primary_owner`.
2. Choose earliest legitimate runtime fault location, not final symptom.
3. Use `secondary_owner` only when evidence crosses a boundary.
4. Do not blame `emission` for upstream route/speaker/planner faults unless the evidence shows late mutation or final source stamping error.
5. Treat `projection` as primary only when raw runtime data exists but replay/dashboard cannot see it.
6. Treat `semantic_mutation` as primary when text meaning changes after planner/route contract is already correct.
7. Treat `evaluator` as primary for score/warning rows unless a replay structural invariant points to an earlier runtime owner.

## Minimal JSON Row

```json
{
  "scenario_id": "directed_npc_question",
  "turn_index": 0,
  "status": "fail",
  "category": "speaker",
  "severity": "critical",
  "primary_owner": "speaker",
  "secondary_owner": "emission",
  "source_family": "speaker_contract",
  "replay_tags": ["structural_drift", "speaker_mismatch"],
  "field_path": "selected_speaker_id",
  "expected": "runner",
  "actual": "merchant",
  "reason": "exact value mismatch",
  "final_text_hash": "abc123",
  "route_kind": "dialogue",
  "selected_speaker_id": "merchant",
  "canonical_target_actor_id": "runner",
  "final_emitted_source": "generated_candidate",
  "fallback_family": null,
  "repair_kind": null,
  "post_gate_mutation_detected": false,
  "unavailable_fields": [],
  "raw_signal_refs": ["trace.canonical_entry", "_final_emission_meta"],
  "classification_confidence": "high",
  "investigate_first": "game/speaker_contract_enforcement.py"
}
```

## Fields Required for <=2 Minute Classification

| Field | Available Now? | Source |
|---|---:|---|
| `scenario_id`, `turn_index`, `player_text` | yes | Golden replay helper |
| `status`, drift bucket counts | yes | `classify_golden_drift` |
| `field_path`, `expected`, `actual`, `reason` | yes | Golden drift rows |
| `route_kind` | mostly | Replay helper / `turn_trace` |
| `canonical_target_actor_id` | mostly | `trace.canonical_entry` |
| `selected_speaker_id` | mostly | Social contract trace / snapshot / resolution |
| `final_emitted_source` | yes when FEM present | `read_final_emission_meta_from_turn_payload` |
| `fallback_family`, `fallback_temporal_frame` | mostly | FEM |
| `response_type_required`, `response_type_repair_used`, `response_type_repair_kind` | yes | FEM |
| `post_gate_mutation_detected` | yes | FEM |
| `stage_diff_last_transition` | partly | `stage_diff_telemetry` |
| `sanitizer_mode`, sanitizer event count | partly/missing | `sanitizer_debug` context-dependent |
| `validator_failure_reasons` | partly | FEM layer metadata, validators |
| `evaluator_failures`, `warnings`, score | yes when evaluator run | Evaluator outputs |
| `classification_confidence` | missing | Dashboard rule output |
| `investigate_first` | missing | Dashboard rule output |

## Missing or Weak Fields

- Per-layer "text changed here" attribution inside the final emission stack.
- Sanitizer run/mode/changed-count fields consistently projected into replay rows.
- Raw-vs-projected comparison marker to distinguish `projection` from runtime missing metadata.
- A canonical owner map table consumed by the future dashboard.

