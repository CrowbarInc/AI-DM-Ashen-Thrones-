# CT5 Projection Fidelity Audit

## Executive Summary

CT5 verifies the current fallback incidence baseline against runtime evidence without adding trigger-time instrumentation.

Result: projection fidelity is high for the representative families that already carry explicit runtime/FEM trigger stamps. The production FEM projector matches explicit runtime evidence for `fallback_kind`, selection/content owner, owner bucket, report owner, route, governed classification, and compatibility status across the projectable split-owner matrix rows.

Measured mismatch inventory:

- None remaining for family, owner, owner bucket, route, governed classification, or compatibility status.
- Source fields are partly non-comparable by design: runtime fixture events often omit `source`, while FEM projection can derive `source` from `final_emitted_source` or sanitizer/fallback provenance fields.
- No projected family, owner, owner-bucket, route, governed classification, or compatibility-status mismatches were found where explicit runtime evidence exists.

Overall confidence: High for incidence family/owner/owner-bucket/route/compatibility, Medium for source-level attribution.

## Projection Inventory

Projection owner: `game.final_emission_replay_projection.build_fem_runtime_lineage_events`.

| Projection source | Originating runtime module | Projected family/kind | Projected owner | Projected route/stage | Compatibility status | Explicit or inferred |
| --- | --- | --- | --- | --- | --- | --- |
| `sanitizer_strict_social_fallback_used is True` | `game/output_sanitizer.py` | `sanitizer_strict_social` | `game.output_sanitizer` | sanitizer | active_governed | explicit_runtime |
| `sanitizer_empty_fallback_used or sanitizer_lineage_empty_fallback_used is True` | `game/output_sanitizer.py` | `sanitizer_empty_output` | `game.output_sanitizer` | sanitizer | unknown_unclassified unless governed family is present | explicit_runtime |
| `opening_fallback_failed_closed` flag, repair, or source evidence | `game/final_emission_opening_fallback.py` | `opening_failed_closed` | `game.final_emission_gate` | gate/opening_failed_closed | active_governed | mixed |
| `opening_recovered_via_fallback is True` or `final_emitted_source=opening_deterministic_fallback` | `game/final_emission_opening_fallback.py` | `scene_opening` | `game.final_emission_gate` | gate/opening_fallback | active_governed | mixed |
| `upstream_prepared_emission_used` plus answer/action repair kind | `game/final_emission_response_type.py` | `response_type_prepared_emission` | `game.final_emission_gate` | gate/prepared_repair | active_governed | explicit_runtime |
| `final_emitted_source=minimal_social_emergency_fallback` | `game/social_exchange_emission.py` | `minimal_social_emergency_fallback` | `game.final_emission_gate` | gate/strict_social_emergency | active_governed | inferred_projection |
| recognized strict-social final source or `strict_social_dialogue_repair` | `game/social_exchange_emission.py` | `strict_social_fallback` | `game.final_emission_gate` | gate/strict_social_fallback | active_governed | mixed |
| `visibility_replacement_applied is True` | `game/final_emission_visibility_fallback.py` | `visibility_hard_replacement` | `game.final_emission_gate` | gate/visibility_hard_replaced | active_governed | explicit_runtime |
| `first_mention_replacement_applied is True` | `game/final_emission_visibility_fallback.py` | `first_mention_hard_replacement` | `game.final_emission_gate` | gate/first_mention_hard_replaced | active_governed | explicit_runtime |
| `referential_clarity_replacement_applied is True` | `game/final_emission_visibility_fallback.py` | `referential_clarity_hard_replacement` | `game.final_emission_gate` | gate/referential_clarity_hard_replaced | active_governed | explicit_runtime |
| `fallback_provenance_trace.source=fallback` | `game/fallback_provenance_debug.py` | `upstream_fast_fallback` | `game.api` | retry/unknown | active_governed | explicit_runtime |
| `final_route=replaced` plus social-interlocutor source | `game/final_emission_sealed_fallback.py` | `sealed_social_interlocutor_fallback` | `game.final_emission_gate` | gate/replaced_or_sealed | active_governed | inferred_projection |
| `final_route=replaced` plus passive-pressure source/kind | `game/final_emission_sealed_fallback.py` | `sealed_passive_scene_pressure_fallback` | `game.final_emission_gate` | gate/replaced_or_sealed | active_governed | inferred_projection |
| `final_route=replaced` plus NPC-pursuit source/kind | `game/final_emission_sealed_fallback.py` | `sealed_npc_pursuit_neutral_fallback` | `game.final_emission_gate` | gate/replaced_or_sealed | active_governed | inferred_projection |
| `final_route=replaced` plus anti-reset source/kind | `game/final_emission_sealed_fallback.py` | `sealed_anti_reset_continuation_fallback` | `game.final_emission_gate` | gate/replaced_or_sealed | active_governed | inferred_projection |
| `final_route=replaced` plus recognized global source/kind | `game/final_emission_sealed_fallback.py` | `sealed_global_scene_fallback` | `game.final_emission_gate` | gate/replaced_or_sealed | active_governed | inferred_projection |
| `final_route=replaced` with unrecognized terminal replacement | `game/final_emission_sealed_fallback.py` | `sealed_unknown_replacement` | `game.final_emission_gate` | gate/replaced_or_sealed | active_governed when governed family is present | inferred_projection |

## Fidelity Matrix

| Family | Runtime evidence available | Projection evidence available | Inference required | Confidence | Recommended action |
| --- | --- | --- | --- | --- | --- |
| opening fallback | Yes: `opening_recovered_via_fallback`, fail-closed flag, owner bucket/authorship fields | Yes: `scene_opening`, `opening_failed_closed`, split owners, bucket | Mixed; source fallback can infer from final source | High | Keep projection baseline; no new instrumentation needed for incidence. |
| retry fallback | Partial: drift watch sees retry terminal routes, but fallback-selected projection requires provenance trace | Partial: `upstream_fast_fallback` when `fallback_provenance_trace.source=fallback` | Yes when provenance trace is absent | Medium | Preserve provenance trace for retry-terminal cases. |
| upstream fast fallback | Yes: `fallback_provenance_trace.source=fallback` | Yes: `upstream_fast_fallback`, owner `game.api`, owner bucket `retry`, content owner `game.gm_retry` | Low | High | Current projection is sufficient. |
| visibility replacement | Yes: replacement boolean and visibility owner bucket | Yes: `visibility_hard_replacement` | Low | High | Current projection is sufficient. |
| referential clarity replacement | Yes: replacement boolean and visibility owner bucket | Yes: `referential_clarity_hard_replacement`; local substitution is mutation, not fallback-selected | Low | High | Current projection is sufficient; keep local substitution outside fallback incidence. |
| sealed replacement | Partial: terminal `final_route=replaced` and final source identify emitted replacement | Yes: sealed subkind projection and split owners | Yes; mostly derived from finalized terminal source | Medium | Sufficient for baseline incidence; trigger-time instrumentation would mainly improve causality timing. |
| sanitizer fallback | Yes: sanitizer fallback-used flags and trace owner/source fields | Yes: sanitizer strict-social/empty-output projection | Low | High | Current projection is sufficient; classify empty-output as governed only when realization family is present. |

## Runtime vs Projection Comparison

Synthetic projectable split-owner matrix rows compare explicit runtime lineage events against production FEM projection.

CT6 root cause: upstream-fast projection was selected by `fallback_provenance_trace.source=fallback`, and `_fem_selected_fallback_projection` already classified the event as retry-stage `upstream_fast_fallback`. The loss occurred one step later in `_fem_preserved_fallback_owner_bucket`, which preserved opening, visibility, and sealed buckets but had no upstream-fast branch. The fix preserves `fallback_owner_bucket="retry"` for that already-classified upstream-fast projection without adding metadata or changing family, owner, source, route, governed classification, or compatibility status.

Aligned fields:

- `fallback_kind`
- event owner
- `fallback_selection_owner`
- `fallback_content_owner`
- `fallback_owner_bucket`
- report `family`
- report `owner`
- report `route`
- report `compatibility_status`
- report `governed_classification`

Non-comparable source cases:

- Opening, visibility, sanitizer, and sealed rows often have runtime events with no `source`, while projection derives source from finalized FEM. This is a source-vocabulary coverage difference, not an incidence mismatch.

Mismatches:

| Row | Field | Runtime evidence | Projection evidence | Impact |
| --- | --- | --- | --- | --- |
| _none_ | _none_ | _none_ | _none_ | No remaining family, owner, owner-bucket, route, governed-classification, or compatibility-status mismatches. |

## Confidence Assessment

Projection-based incidence is sufficient for the current CT baseline when the baseline is interpreted as family/owner/owner-bucket/route/compatibility incidence over finalized turns.

Explicit trigger-time instrumentation would materially improve:

- source-vocabulary parity, especially distinguishing event source from final emitted source;
- causal timing for sealed replacements inferred from terminal finalized state.

It would not materially improve:

- opening fallback incidence;
- visibility/referential replacement incidence;
- sanitizer fallback incidence;
- upstream-fast incidence when provenance trace survives;
- upstream-fast owner-bucket attribution when provenance trace survives;
- split-owner family and compatibility reporting for projectable matrix rows.

## Recommendations

1. Keep the projection-based fallback incidence baseline as the primary deterministic baseline.
2. Do not add new runtime instrumentation solely for CT incidence baseline acceptance.
3. If future analysis needs trigger-time causality rather than finalized-turn incidence, instrument sealed replacement and retry paths first.
