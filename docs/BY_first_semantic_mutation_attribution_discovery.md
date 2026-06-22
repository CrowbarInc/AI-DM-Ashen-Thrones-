# BY - First Semantic Mutation Attribution Discovery

Discovery date: 2026-06-22

Scope: text-changing layers from policy enforcement through replay projection. Discovery only; no runtime behavior or golden output changed.

## A. Executive Summary

The repository can detect that text changed, and it can often infer the eventual repair, fallback, or emission owner, but it cannot reliably identify the **first** text-changing source. Current evidence is split across response-policy metadata, sanitizer traces, final-emission metadata (FEM), stage-diff fingerprints, runtime-lineage events, and replay failure classification. `post_gate_mutation_detected` compares gate input with final normalized output; it does not localize the first change. Stage-diff telemetry is ordered but has only coarse checkpoints. BS attribution classifies applied replacements after the fact. BT's test-only `post_speaker_finalize_probe` is the only existing structure that records ordered before/after normalized text at individual layer boundaries and returns the first divergence.

The largest gap is the join between those facilities: no one record carries ordered text snapshots plus a stable source and one of the requested buckets (`policy`, `sanitizer`, `fallback`, `repair`, `final_emission`, `unknown`). This is especially visible inside the final-emission gate, where strict/non-strict composition, repairs, hard fallbacks, visibility enforcement, and finalize-only stripping can all change `player_facing_text` before replay sees only `snap.gm_text`.

Recommended implementation shape: build BY1 as a **test/replay-only probe** modeled on `tests/helpers/post_speaker_finalize_probe.py`. Wrap the existing major mutation boundaries, capture normalized before/after text with source and bucket, select the first normalized change, and pass the resulting diagnostic record into `project_turn_observation`. Reuse FEM, sanitizer trace, stage-diff, and runtime-lineage fields for attribution enrichment. Do not rewrite runtime layers or make the new fields protected golden fields initially. This yields Semantic Mutation Risk without broad production fan-out.

For BY, define per-turn **Semantic Mutation Risk** as a transparent diagnostic score, not semantic equivalence:

```text
first_source_unknown = 0 if first changed entry has a non-unknown bucket and source, else 1
later_unattributed_changes = count(changed entries after the first with missing/unknown source)
cross_bucket_changes = number of distinct non-unknown buckets among changed entries

risk = min(100,
    60 * first_source_unknown
  + 10 * min(later_unattributed_changes, 2)
  + 10 * min(max(cross_bucket_changes - 1, 0), 2)
)
```

Also report raw counts and the first-source coverage rate. The score should not claim that two different strings are semantically unequal; it measures risk from normalized text divergence and missing attribution.

## B. Candidate Mutation Points Table

`player_facing_text` is the dominant shared field. Local `text` values below are eventually assigned to it.

| bucket | file | function/class | input text field | output text field | mutation type | confidence | notes |
|---|---|---|---|---|---|---|---|
| policy | `game/response_policy_enforcement.py` | `apply_response_policy_enforcement` orchestration | `gm.player_facing_text` | `gm.player_facing_text` | Runs the policy mutators below in order | high | Pre-final-gate owner; manifest already declares mutating subpaths. |
| policy | `game/response_policy_enforcement.py` | `enforce_question_resolution_rule`, `enforce_npc_response_contract` | reply text | `player_facing_text` | Adds grounded answer/next-step prose | high | Can materially add claims or actions. |
| policy | `game/response_policy_enforcement.py` | `enforce_no_validator_voice`, `enforce_forbidden_generic_phrases` | `player_facing_text` | `player_facing_text` | Removes/replaces validator or stock prose | high | Validator rewrite may invoke fallback rendering. Primary bucket remains policy; retain fallback detail. |
| policy | `game/response_policy_enforcement.py` | `guard_gm_output`, topic/passive/scene momentum helpers | `player_facing_text` | `player_facing_text` | Secret-leak replacement; appended/replaced pressure beat | high | Manifest marks these fallback/provenance-relevant mutations. |
| sanitizer | `game/output_sanitizer.py` | `sanitize_player_facing_output` | raw writer text | returned string | Payload extraction, fragment stripping, sentence drop/rewrite, empty-output fallback | high | Strip-only is default; legacy sentence rewrite remains diagnostic/test-only. Trace records changed/dropped counts and fallback owners. |
| sanitizer | `game/output_sanitizer.py` | `_sanitize_player_facing_output_strip_only` | text/chunks | returned string | Drops unrecoverable/non-diegetic chunks; may select empty fallback | high | Empty fallback is also a fallback event; first owner should remain sanitizer with fallback subsource. |
| fallback | `game/gm_retry.py` | retry deterministic/terminal fallback writers | candidate/retry text | `out.player_facing_text` | Hard terminal replacement | high | Existing stage snapshots cover retry entry/result and deterministic fallback transitions. |
| fallback | `game/social_exchange_fallback_catalog.py` | standard-mode retry payload floor paths | retry payload | `out.player_facing_text` | Social retry fallback replacement | high | Occurs upstream of final gate. |
| fallback | `game/upstream_response_repairs.py` | prepared opening/answer builders and `apply_spoken_state_refinement_cash_out` | player input, resolution, emitted text | prepared payload or `out.player_facing_text` | Authors replacement candidates; cash-out may append/replace spoken text | medium-high | Prepared candidates do not count until selected. |
| fallback | `game/final_emission_strict_social_stack.py` | `build_final_strict_social_response` and emergency branches | pre-gate candidate | local `text`, then `player_facing_text` | Composes normalized social response or deterministic emergency line | high | `details.final_emitted_source`, pool, and kind identify selected prose. |
| fallback | `game/final_emission_generic_exit.py` | `run_generic_replace_exit` | rejected candidate | `out.player_facing_text` | Whole-text sealed replacement | high | Strong FEM route/source/family evidence. |
| fallback | `game/final_emission_visibility_fallback.py` | visibility, first-mention, referential fallback enforcement | current `player_facing_text` | `out.player_facing_text` | Whole-text hard replacement | high | Owner bucket and selection metadata exist; local referential substitution is repair, not fallback. |
| fallback | `game/final_emission_terminal_pipeline.py` | `apply_strict_social_emergency_fallback_patch`, NMO emergency, acceptance-quality N4 | current text | `out.player_facing_text` | Terminal sealed/emergency replacement | high | FEM mutation lineage and final source are available. |
| repair | `game/final_emission_non_strict_stack.py` | `run_non_strict_layer_stack` | local `text` | local `text` / `out.player_facing_text` | Response-type enforcement followed by policy/quality layers | high | Central non-strict ordering boundary; several internal owners are currently collapsed. |
| repair | `game/final_emission_strict_social_stack.py` | `run_strict_social_composition_trunk` | local `text` | local `text` / `out.player_facing_text` | Answer, delta, structure, authenticity, tone, purity, context, anchor, dialogue-strip, speaker repairs | high | BT probe already wraps many of these exact functions. |
| repair | `game/final_emission_repairs.py` | `_apply_answer_completeness_layer`, `_apply_answer_exposition_plan_layer`, `_apply_response_delta_layer` | local `text` | returned text | Adds/rewrites answer content and response delta | high | Repair metadata exists per layer. |
| repair | `game/final_emission_repairs.py` | `_apply_social_response_structure_layer`, `_apply_narrative_authenticity_layer` | local `text` | returned text | Flattens formatting, restructures, or rewrites narrative content | high | Can be semantic, not merely formatting. |
| repair | `game/final_emission_repairs.py` | `repair_fallback_behavior`, `_apply_fallback_behavior_layer` | local `text` | returned text | Removes meta voice/fabricated authority and downgrades certainty | high | FEM carries repaired flag/kind/mode. |
| repair | `game/final_emission_referential_clarity.py` and `game/final_emission_visibility_fallback.py` | local referent/pronoun repair paths | current text | repaired text / `player_facing_text` | Local semantic substitution | high | BS found this is not always marked as whole-text replacement. |
| repair | `game/speaker_contract_enforcement.py` via strict-social stack | candidate text | repaired text | Local rebind, canonical rewrite, or narrator-neutral rewrite | high | BT/BX provide checkpoint and owner structures. |
| repair | `game/final_emission_acceptance_quality.py` | `apply_acceptance_quality_n4_floor_seam` | `out.player_facing_text` | `out.player_facing_text` | Quality repair, then possible N4 fallback | high | Preserve whether the selected result is repair or fallback. |
| final emission | `game/final_emission_finalize.py` | `finalize_emission_output` | `out.player_facing_text` | public `player_facing_text` | HTML/text sanitization, route-illegal sentence stripping, whitespace assignment, opening reseal | high | Boundary semantic recomposition is explicitly disabled, but sentence stripping can change meaning. |
| final emission | `game/final_emission_opening_fallback.py` | `reassert_scene_opening_accepted_candidate` | final candidate and accepted opening | `out.player_facing_text` | Restores accepted opening after late mutation | high | Absolute late write inside finalize path. |
| final emission | `game/fallback_provenance_debug.py` | overwrite containment/finalize containment | current output and selector snapshot | `out.player_facing_text` | Restores prior selector text when fingerprint diverges | high | Can overwrite a later mutation; source is currently provenance containment. |
| final emission | `game/api_turn_support.py` | `_prepare_player_facing_emission` paths | raw/sanitized/gated text | finalized GM output | Chooses sanitizer-before-gate order and records pre/post lengths | high | Non-strict: sanitizer then gate. Strict social: gate handles its own preflight sanitizer path. |
| unknown | `game/storage.py` | repeated-description summary path | stored/repeated description | `gm.player_facing_text` | Replaces repeated description with canonical summary | medium | Upstream scope; include only if protected replay traverses this branch. |
| unknown | `game/adjudication.py` | engine-voice neutralization | adjudication text | `out.player_facing_text` | Voice rewrite | medium | Earlier producer boundary; likely policy, but not stamped with the response-policy owner. |

Formatting primitives in `game/final_emission_text_formatting.py` (`_normalize_text`, paragraph normalization, `_sanitize_output_text`, punctuation/capitalization helpers) are mutation mechanisms, not independent semantic owners. Attribute them to the calling layer. `game/narration_state_consistency.reconcile_final_text_with_structured_state` reads final text and repairs structured state/debug metadata; it does not normally rewrite player-facing text.

## C. Current Replay / Projection Flow

### Runtime to replay

1. `game.api._apply_narration_hub_policy_handoff` calls `apply_response_policy_enforcement`; retry/fallback producers may already have authored text.
2. `game.api_turn_support` selects raw or upstream-prepared text. Non-strict paths call `sanitize_player_facing_output` before `apply_final_emission_gate`; strict-social paths enter the gate with raw text and may sanitize during strict-social preflight.
3. `apply_final_emission_gate` records `final_emission_gate_entry`, then dispatches to `run_non_strict_layer_stack` or `run_strict_social_composition_trunk`.
4. Accept/replace exits run `run_gate_terminal_enforcement_pipeline`, which can apply visibility replacement, interaction-continuity/fallback-behavior repair, referential repair, NMO emergency fallback, and N4 replacement.
5. `finalize_emission_output` records `final_emission_gate_exit`, performs packaging-time sanitization/stripping/containment/reseal, stamps final speaker observation, and projects public/debug/author channels.
6. The API snapshot exposes final text as `snap.gm_text`. `tests.helpers.golden_replay.run_golden_replay` builds a turn payload and calls `tests.helpers.golden_replay_projection.project_turn_observation`.
7. `project_turn_observation` reads final text, FEM, sanitizer trace/debug, stage diff, routing/speaker trace, and runtime-lineage events. It emits `final_text`, `final_text_hash`, route, speaker, fallback, repair, sanitizer, and projection-status diagnostics. Golden comparison/classification runs afterward.

### Existing metadata

- **Route/finalization:** FEM `final_route`, `final_emitted_source`, `post_gate_mutation_detected`, `final_text_preview`, `output_sanitization_applied`, finalize strip flags, mutation-lineage tokens.
- **Fallback:** fallback kind/pool/family/frame, opening/sealed/visibility owner buckets, selector/prose owners, sanitizer empty/strict-social fallback sources.
- **Repair:** response-type repair kind, fallback-behavior repaired/kind/mode, narrative-authenticity mode, layer-specific FEM flags, speaker enforcement reason.
- **Speaker:** final speaker observation, selected speaker ID/source, replay parity fields from BX.
- **Ordering:** `metadata.stage_diff_telemetry.snapshots` and transitions; retry, gate entry, post-strict-composition, and gate exit are covered. Snapshots store text fingerprint/preview, not full normalized text or mutation owner.
- **Read-side attribution:** `build_fem_runtime_lineage_events` synthesizes fallback/mutation events and recurrence keys; `failure_classifier` infers `mutation_source` only after drift exists.

### Partial first-change attribution already present

- `tests/helpers/post_speaker_finalize_probe.py`: ordered `LayerTextDelta` rows with normalized input/output and `first_normalized_divergence`; strongest reusable implementation pattern.
- `tests/helpers/speaker_contract_risk.py`: checkpoint records, first text/speaker divergence, source/owner fields, and a risk score; reusable reporting shape.
- `game/stage_diff_telemetry.py`: bounded ordered snapshots, fingerprints, transitions, repair flags, route/fallback fields; reusable transport, but checkpoints are too coarse for exact first owner.
- BS/BS2/BS3/BS5: canonical replacement attribution vocabulary, direct versus inferred origins, producer stamps, and replay convergence rules.
- BT: first divergence checkpoint/layer model across speaker finalization.
- BW: protected replay window, deterministic rerun comparison, and report conventions.
- BX: final speaker observation and projection parity joins final emission to replay.
- `tests/helpers/failure_classifier.py`: `mutation_source` and post-gate lineage inference. This classifies a drift's likely source, not the first observed mutation.

No existing field named first mutation/source carries an ordered cross-layer text comparison. Existing `first_divergence_*` fields are speaker-contract-test diagnostics only.

## D. Recommended Instrumentation Design

### Insertion point

Add `tests/helpers/semantic_mutation_attribution.py` and install its probe around replay execution, following the monkeypatch wrapper pattern in `post_speaker_finalize_probe`. Begin with coarse but owner-clean boundaries:

1. writer/raw candidate,
2. response-policy output,
3. sanitizer output,
4. retry/fallback output when present,
5. response-type/strict-social composition,
6. named repair layers,
7. visibility/sealed/N4 fallback,
8. finalize input/output,
9. replay `final_text`.

Feed the completed diagnostic record to `project_turn_observation` through an optional payload key such as `semantic_mutation_trace`. Projection should normalize/validate it and expose summary fields, but the first implementation should not add them to `PROTECTED_OBSERVATION_FIELDS`. This confines BY to tests/replay and avoids runtime API changes. Existing stage diff and FEM enrich or backfill missing owners; they should not be treated as proof of ordering beyond their recorded sequence.

### Proposed trace entry

```python
@dataclass(frozen=True)
class SemanticMutationTraceEntry:
    sequence: int
    checkpoint_id: str
    bucket: Literal[
        "policy", "sanitizer", "fallback", "repair",
        "final_emission", "unknown"
    ]
    source: str
    input_field: str
    output_field: str
    before_normalized: str
    after_normalized: str
    before_hash: str
    after_hash: str
    normalized_changed: bool
    mutation_kind: str | None = None
    owner: str | None = None
    evidence: dict[str, object] | None = None
```

Use bounded text (for example 512 characters) in report artifacts and full normalized text only in in-memory test objects. Hashes should use the existing deterministic golden/probe hash helpers.

### Buckets

The canonical list should be exactly:

```text
policy
sanitizer
fallback
repair
final_emission
unknown
```

Use `unknown` as the serialized token for the requested "unknown / unclassified" bucket. Keep detailed `source`, `mutation_kind`, and `owner` separate so mixed cases such as policy-selected fallback or sanitizer empty fallback retain both facts. Bucket by the boundary that first changed text; store the nested fallback as evidence rather than changing the primary bucket.

### Comparison and selection rules

1. Convert missing values to `""` and normalize both sides with the same existing `_normalize_text` rule used by BT/FEM. Do not use previews for equality.
2. `raw_changed = before != after`; `normalized_changed = normalize(before) != normalize(after)`.
3. BY's semantic-risk event is `normalized_changed=True`. Raw-only whitespace/HTML formatting differences remain traceable but do not select the first semantic mutation.
4. Order entries by explicit sequence assigned at wrapper invocation; never infer order from owner precedence.
5. The first semantic mutation is the earliest changed entry whose `before_normalized` equals the previous checkpoint's `after_normalized`. If continuity is broken, select the earliest changed entry but mark `trace_continuity=false` and bucket it `unknown` unless independent ordered evidence repairs the join.
6. Prepared candidates do not count. A fallback counts only when selected into the active text stream.
7. Replay-only normalization differences should be attributed to `final_emission` only when the projection itself transforms text; current projection copies `snap.gm_text`, so an unexplained mismatch is `unknown`.

### Proposed turn/report fields

```text
semantic_mutation_trace
semantic_mutation_trace_complete
first_semantic_mutation_sequence
first_semantic_mutation_checkpoint_id
first_semantic_mutation_bucket
first_semantic_mutation_source
first_semantic_mutation_owner
first_semantic_mutation_kind
first_semantic_mutation_before_hash
first_semantic_mutation_after_hash
semantic_mutation_changed_count
semantic_mutation_cross_bucket_count
semantic_mutation_unknown_count
semantic_mutation_risk_score
semantic_mutation_risk_band
```

Aggregate reports should show total turns, mutated turns, attributable first mutations, first-source coverage, bucket/source frequencies, unknown count, mean/max risk, and representative scenario/turn IDs. Preserve behavior by asserting final text/hash equality with and without the probe.

## E. Proposed Tests

### New file

`tests/test_by_first_semantic_mutation_attribution.py`

- `test_by_trace_selects_policy_as_first_normalized_change`
- `test_by_trace_ignores_formatting_only_change_for_first_semantic_mutation`
- `test_by_trace_selects_sanitizer_strip_before_gate_repair`
- `test_by_trace_attributes_selected_empty_output_fallback_to_sanitizer_with_fallback_evidence`
- `test_by_trace_selects_repair_before_later_final_emission_strip`
- `test_by_trace_selects_fallback_for_visibility_hard_replacement`
- `test_by_trace_marks_broken_checkpoint_continuity_unknown`
- `test_by_risk_scores_missing_first_source_and_later_unknown_changes`
- `test_by_probe_preserves_final_text_and_final_text_hash`
- `test_by_projected_summary_round_trips_through_golden_observation`

### Existing tests to extend

- `tests/test_golden_replay_projection.py`: optional trace projection, defaults when absent, no protected-field change.
- `tests/test_stage_diff_telemetry.py`: prove ordered fingerprints can enrich but cannot override explicit probe order.
- `tests/test_output_sanitizer.py`: strip-only drop, legacy rewrite, serialized payload extraction, and empty fallback fixtures.
- `tests/test_response_policy_enforcement_mutation.py`: policy first-change fixtures and unchanged-policy control.
- `tests/test_final_emission_visibility_fallback.py`: visibility, first-mention, local referential repair, and hard fallback distinction.
- `tests/test_final_emission_repairs.py`, `tests/test_fallback_behavior_repairs.py`: named repair attribution.
- `tests/test_final_emission_boundary_no_semantic_repair.py`: finalize formatting-only control.
- `tests/test_final_emission_boundary_convergence.py`: sanitizer/final-boundary ordering and unchanged final output.
- `tests/test_block_u_finalize_stack_divergence.py`, `tests/test_speaker_contract_risk.py`: reuse BT ordered layer cases and first-divergence expectations.
- `tests/test_golden_replay_structural_invariants.py`: run at least sanitizer scaffold leakage, wrong-speaker strict social, and thin answer/action outcome with probe enabled.
- `tests/test_golden_replay_fallback_projection.py`: validate fallback owner enrichment.

Existing useful corpus cases are the six short protected structural scenarios, particularly `sanitizer_scaffold_leakage`, `wrong_speaker_strict_social_emission`, and `thin_answer_action_outcome_final_emission`. BT fixtures already demonstrate dialogue-plan stripping and post-speaker mutation. BX guard/captain fixtures demonstrate text/speaker checkpoint joins. A small synthetic fixture is still needed for a clean ordering chain with: policy change -> sanitizer no-op -> repair change -> finalize strip, plus a broken-continuity case.

## F. Files Needed For Next Step

Pass these files for implementation guidance:

1. `docs/BY_first_semantic_mutation_attribution_discovery.md`
2. `docs/BS_semantic_replacement_attribution_discovery.md`
3. `docs/BS3_canonical_attribution_contract.md`
4. `docs/audits/BT_speaker_finalization_divergence_discovery.md`
5. `docs/BW_protected_replay_trend_window_discovery.md`
6. `docs/reports/BX_speaker_identity_end_to_end_parity_discovery.md`
7. `tests/helpers/post_speaker_finalize_probe.py`
8. `tests/helpers/speaker_contract_risk.py`
9. `tests/helpers/golden_replay.py`
10. `tests/helpers/golden_replay_projection.py`
11. `tests/helpers/golden_replay_fixtures.py`
12. `game/stage_diff_telemetry.py`
13. `game/api_turn_support.py`
14. `game/response_policy_enforcement.py`
15. `game/response_policy_enforcement_manifest.py`
16. `game/output_sanitizer.py`
17. `game/final_emission_gate.py`
18. `game/final_emission_non_strict_stack.py`
19. `game/final_emission_strict_social_stack.py`
20. `game/final_emission_terminal_pipeline.py`
21. `game/final_emission_generic_exit.py`
22. `game/final_emission_repairs.py`
23. `game/final_emission_visibility_fallback.py`
24. `game/final_emission_acceptance_quality.py`
25. `game/final_emission_finalize.py`
26. `game/final_emission_replay_projection.py`
27. `tests/test_golden_replay_projection.py`
28. `tests/test_golden_replay_structural_invariants.py`
29. `tests/test_output_sanitizer.py`
30. `tests/test_response_policy_enforcement_mutation.py`
31. `tests/test_final_emission_visibility_fallback.py`
32. `tests/test_final_emission_boundary_no_semantic_repair.py`
33. `tests/test_block_u_finalize_stack_divergence.py`
34. The generated BY JSON/Markdown risk report sample after BY1 exists.

The recommended next implementation block is BY1 only: add the test-only ordered trace helper, its unit tests, and optional unprotected replay projection fields. Defer production stamps and protected golden schema changes until first-source coverage is measured on the protected corpus.
