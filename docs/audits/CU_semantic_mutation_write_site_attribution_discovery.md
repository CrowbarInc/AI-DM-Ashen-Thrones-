# CU - Semantic Mutation Write-Site Attribution Discovery

Discovery date: 2026-06-28

Scope: evidence gathering only. No runtime behavior, sanitizer/repair/fallback logic, replay schema, or protected assertions were changed.

## Summary

The repo already has strong evidence that text changed and often has good after-the-fact attribution, but runtime write-site attribution is still incomplete. The most important existing mechanism is the BY semantic mutation probe in `tests/helpers/semantic_mutation_attribution.py`: it records ordered before/after checkpoints across policy, sanitizer, fallback, repair, final-emission, and replay boundaries, and BY4 reports 100% first-source coverage for a compact protected/synthetic corpus. That probe is test/replay-only and uses monkeypatch wrappers, so it proves the instrumentation shape but does not make production semantic mutation ownership write-site attributable.

Current production-facing evidence is distributed across `_final_emission_meta`, sanitizer trace/lineage, stage-diff telemetry, fallback provenance snapshots, runtime-lineage projections, and replay/failure-classifier rows. These surfaces can say "the final text changed", "this final source/family/owner bucket was observed", or "a projected mutation event exists", but they often cannot say "this exact write site first changed the active text stream" without BY's test probe or read-side inference.

Recommended next block: add passive write-site attribution at a small set of first-write candidates, reusing existing trace/FEM/runtime-lineage shapes. Start with metadata/event stamping only, not behavior changes or protected replay promotion.

## Current Mutation Surfaces

| Surface | Classification | File/function | Evidence and notes |
|---|---|---|---|
| Prompt/context/policy assembly | prompt/policy mutation surface | `game/api.py::_run_resolved_turn_pipeline`, `game/api_turn_support._finalize_player_facing_for_turn`, `game/response_policy_enforcement.py::apply_response_policy_enforcement` | Prompt context and response policy can shape or rewrite candidate text before final emission. BY already treats response-policy output as a first-change bucket. |
| Upstream prepared emission/opening repair | repair and fallback mutation surface | `game/upstream_response_repairs.py::merge_upstream_prepared_emission_into_gm_output`, `build_upstream_prepared_opening_fallback_payload`, `maybe_attach_upstream_prepared_opening_fallback_payload` | Creates prepared answer/action/opening fallback candidates and writes opening authorship source once on successful prepared payloads. Prepared candidates should not count as emitted mutation until selected. |
| Retry and upstream fast fallback | fallback mutation surface | `game/api.py::_fast_fallback_for_upstream_error`, `game/gm_retry.py::force_terminal_retry_fallback`, `game/fallback_provenance_debug.py::attach_upstream_fast_fallback_provenance` | API/gm_retry can replace text before final emission; provenance records selector snapshots and later containment hints but not a universal mutation write-site record. |
| Sanitizer boundary | sanitizer mutation surface | `game/output_sanitizer.py::sanitize_player_facing_output`, `_sanitize_player_facing_output_strip_only` | Strip-only mode drops illegal chunks and can emit sanitizer empty/strict-social fallbacks. `sanitizer_trace` records lineage and producer attribution, but first-write semantics are not carried in production as ordered before/after entries. |
| Final emission orchestration | repair/fallback/final-emission metadata surface | `game/final_emission_gate.py::apply_final_emission_gate` | Canonical orchestration owner. It sequences stacks and terminal/finalize paths but intentionally delegates behavior to owner modules. |
| Non-strict and strict-social stacks | repair/fallback mutation surface | `game/final_emission_non_strict_stack.py`, `game/final_emission_strict_social_stack.py`, `game/social_exchange_emission.py::build_final_strict_social_response` | Can compose strict-social output or run repair layers. BY wraps several of these checkpoints; production evidence remains layer flags/FEM lineage. |
| Repair layers | repair mutation surface | `game/final_emission_repairs.py` helpers such as `_apply_fallback_behavior_layer`, `_apply_referent_clarity_emission_layer`; adjacent policy modules for tone/authority/anti-railroading/context/anchor/purity/answer-shape | Many layer flags and repair modes exist, but read-side lineage may collapse generic repair mutations to broad `repair_only_mutation` style evidence unless a path-specific token is available. |
| Opening fallback selection | fallback mutation surface | `game/final_emission_opening_fallback.py` | Selects upstream-prepared opening fallback or fail-closed marker. Success authorship is upstream-prepared; gate/opening adapter mirrors metadata. |
| Visibility/sealed/terminal fallback | fallback mutation surface | `game/final_emission_visibility_fallback.py`, `game/final_emission_sealed_fallback.py`, `game/final_emission_terminal_pipeline.py` | Hard replacement paths stamp route/source/family/owner bucket evidence. These are strong first-write candidates when they assign `player_facing_text`. |
| Finalize packaging | final-emission metadata/projection and possible mutation surface | `game/final_emission_finalize.py::finalize_emission_output`, `fallback_provenance_debug.finalize_upstream_fallback_overwrite_containment`, `final_emission_opening_fallback.reassert_scene_opening_accepted_candidate` | Sanitizes/strips at the final boundary, refreshes mutation lineage, may contain upstream fallback overwrite, and may reassert accepted opening text. Boundary semantic repair is disabled, but stripping/reassertion can still change emitted meaning. |
| FEM packaging and lineage projection | final-emission metadata/projection surface | `game/final_emission_meta.py`, `game/final_emission_replay_projection.py::build_fem_runtime_lineage_events` | Packages and projects finalized facts. Useful transport, but projection derives from finalized FEM and is not the first write-site. |
| Golden replay projection/classifier | observer/test-only surface | `tests/helpers/golden_replay_projection.py::project_turn_observation`, `tests/helpers/failure_classifier.py::classify_replay_failure` | Observes final text/hash, FEM, sanitizer, lineage, stage diff, and drift rows. It classifies or projects after the fact. |
| BY semantic mutation probe | observer/test-only surface | `tests/helpers/semantic_mutation_attribution.py` | Best existing model for ordered before/after first-source detection. It is not production instrumentation. |

Unrelated or mostly observer-only surfaces found during search include architecture/governance audit tools, dashboard renderers, static ownership registries, and historical audit artifacts under `artifacts/`.

## Output Lifecycle Map

Current effective lifecycle:

```text
user input / action
-> game.api chat/action routing and state mutation
-> prompt/context construction and model call / retry fallback
-> game.api_turn_support._finalize_player_facing_for_turn
-> upstream prepared emission merge
-> sanitizer pre-gate path for non-strict turns
-> game.final_emission_runtime.finalize_player_facing_emission
-> game.final_emission_gate.apply_final_emission_gate
-> strict or non-strict final-emission stack
-> terminal enforcement pipeline
-> final_emission_finalize.finalize_emission_output
-> API payload/snapshot final text
-> tests.helpers.golden_replay_projection.project_turn_observation
-> golden replay drift assertions and failure classification
```

Important ordering details:

- `api_turn_support._finalize_player_facing_for_turn` promotes usable upstream-prepared opening text before gate entry and calls `sanitize_player_facing_output` before the gate for non-strict turns.
- `final_emission_gate.apply_final_emission_gate` is the orchestration entry, but most text writes happen in stack/terminal/finalize helpers.
- `final_emission_terminal_pipeline.run_gate_terminal_enforcement_pipeline` can apply visibility, strict-social emergency, fallback-behavior, referent clarity, NMO, and N4 paths.
- `final_emission_finalize.finalize_emission_output` refreshes FEM mutation lineage and can perform final packaging-time text changes.
- `golden_replay_projection.project_turn_observation` reads `snap.gm_text` and runtime metadata; it does not own runtime mutation.

## Current Attribution Gaps

1. `post_gate_mutation_detected` in FEM compares pre-gate/final normalized text but does not localize the first changing layer.
2. `final_emission_mutation_lineage` and runtime-lineage mutation events describe finalized evidence; they are not ordered write-site records.
3. `stage_diff_telemetry` has ordered snapshots/transitions with fingerprints and route/fallback/repair flags, but checkpoints are coarse and do not carry a universal writer/source/before/after semantic hash.
4. `fallback_provenance_debug` can detect upstream-fast fallback divergence and containment, but `mutation_hint` is intentionally broad (`mutation_before_or_during_gate_entry`, `mutation_inside_gate_or_finalize`, `mutation_unknown`).
5. Golden replay drift/classifier rows infer owner/source family from final output, FEM, sanitizer trace, and runtime lineage. They are useful triage evidence, not first-write proof.
6. BY/BY2/BY3/BY4 close the gap for test/protected replay measurement, but not for production write-site attribution because their checkpoints are installed by monkeypatch wrappers.
7. Prepared fallback candidates and selected fallback outputs are not always separated in downstream evidence; next instrumentation must count only selected active-stream mutations.

## Existing Trace/Event/Log Infrastructure

| Mechanism | File path | Records today | Facing | Can carry write-site attribution? |
|---|---|---|---|---|
| BY semantic mutation trace | `tests/helpers/semantic_mutation_attribution.py` | Ordered checkpoint entries with bucket, source, owner, before/after hashes, first mutation, risk summary | Test/replay-only | Yes as model/schema; not directly production without moving or duplicating passive hooks. |
| Protected semantic mutation reports | `tests/helpers/protected_semantic_mutation_measurement.py`, `artifacts/by2`, `artifacts/by3`, `artifacts/by4` | Corpus-level first-source coverage, gaps, non-interference | Test/governance | Yes for fixture/report consumption. |
| Final emission meta | `game/final_emission_meta.py` | `_final_emission_meta`, final route/source, repair flags, owner buckets, producer repair kind, mutation lineage | Runtime metadata | Yes, safest transport for passive per-turn attribution summaries if bounded. |
| Runtime lineage events | `game/runtime_lineage_telemetry.py`, `game/final_emission_replay_projection.py` | Fallback/repair/mutation/gate events, recurrence keys, owner/split-owner fields | Runtime/read-side diagnostic | Yes, especially as optional event fields or sibling mutation attribution events. |
| Sanitizer trace/lineage | `game/output_sanitizer.py`, `game/output_sanitizer_lineage.py` | Sanitizer boundary mode, strip/drop/rewrite/fallback evidence, sanitizer producer attribution | Runtime metadata | Yes, strong candidate for sanitizer family write-site fields. |
| Stage-diff telemetry | `game/stage_diff_telemetry.py` | Bounded snapshots/transitions, text fingerprints, route/fallback/repair/retry flags, observability events | Runtime diagnostic | Yes for coarse checkpoints; insufficient alone for precise first writer. |
| Fallback provenance | `game/fallback_provenance_debug.py` | Upstream-fast fallback selector snapshot, gate entry/exit fingerprints, overwrite containment metadata | Runtime diagnostic | Yes for upstream-fast fallback and containment attribution; currently too family-specific. |
| Golden replay projection | `tests/helpers/golden_replay_projection.py` | Protected observation fields, final text hash, FEM/sanitizer/runtime lineage projection, BY summary fields when provided | Test-only acceptance | Yes as consumer, not runtime writer. |
| Failure classifier/dashboard | `tests/helpers/failure_classifier.py`, dashboard/report helpers | Drift category, owner/source family, repair kind, mutation source, investigation target | Test/governance | Consumer only; should prefer write-site fields when present. |
| State/debug traces | `game/storage.py::append_debug_trace`, `game/state_authority.py::build_state_mutation_trace`, API turn trace helpers | Turn debug and state mutation traces | Runtime debug | Possible, but broader than final emitted text and less focused for CU. |

## Recommended Minimal Instrumentation Points

Prefer one small passive helper/API reused by each point, for example a bounded `semantic_mutation_write_sites` list under FEM or a runtime-lineage sibling event. Fields should be optional and ignored by protected replay until explicitly promoted.

| Candidate | Mutation family | Why first-write candidate | Fields to record | Consumers | Runtime risk |
|---|---|---|---|---|---|
| `game.response_policy_enforcement.apply_response_policy_enforcement` | prompt/policy | First post-model policy surface before sanitizer/final gate; BY has a policy checkpoint. | `mutation_id`, `write_site_family=prompt_policy`, file/function, owner, before/after semantic hash, reason/policy id, trace/turn id | BY tests, response-policy tests, golden projection diagnostics | Low if metadata-only and optional. |
| `game.output_sanitizer.sanitize_player_facing_output` and `_sanitize_player_facing_output_strip_only` | sanitizer | Sanitizer can strip/drop/rewrite or select empty/strict-social fallback before gate. | family, file/function, sanitizer mode, source, owner, before/after hash, fallback_family if selected, compatibility status | `tests/test_output_sanitizer.py`, golden replay sanitizer projection, BY/BY2 | Low-medium: avoid storing full text; use hashes and existing trace. |
| `game.upstream_response_repairs.merge_upstream_prepared_emission_into_gm_output` plus selected response-type repair point | repair/fallback candidate vs selected | Prepared candidates are authored here; selected prepared text becomes mutation later. Stamp candidate separately from selected write. | candidate id, owner, source, route, compatibility status; selected flag only when promoted/selected | response-type/opening tests, fallback classifier | Medium if candidate/selected semantics are confused; keep separate fields. |
| `game.final_emission_terminal_pipeline.run_gate_terminal_enforcement_pipeline` and direct patch helpers | fallback/repair | Central terminal point where active `player_facing_text` is assigned for visibility, strict-social emergency, fallback behavior, NMO, N4, referent clarity pre-finalize. | family, exact helper/source, route, speaker/source if relevant, before/after hash, repair/fallback kind | final-emission terminal, visibility/sealed, BY tests | Low-medium; many branches, but one helper can reduce fanout. |
| `game.final_emission_visibility_fallback.apply_visibility_enforcement` / first-mention / referential paths | fallback/repair | Strong path-specific hard replacement and local substitution writers. | fallback_kind, owner bucket, selection/content owner, repair_kind if local, before/after hash | visibility fallback tests, runtime lineage projection | Low if attached to existing FEM/meta patch. |
| `game.final_emission_sealed_fallback.prepare_sealed_replacement_route_meta` and N4 route meta helper | fallback/projection metadata | Shared sealed replacement metadata write point after active replacement selection. | fallback_family, final route/source, owner bucket, write_site family/file/function | sealed fallback/meta tests | Low; metadata-only, but may not have before hash unless caller supplies it. |
| `game.final_emission_finalize.finalize_emission_output` | final-emission | Final packaging can sanitize, strip contamination, contain overwrite, and reassert opening accepted candidate. | final-emission family, operation (`sanitize_html_to_text`, `strip_route_illegal`, containment, opening reassertion), before/after hash, mutation reason | final-emission boundary tests, golden replay projection | Low-medium; avoid changing boundary assertions. |
| `game.fallback_provenance_debug.finalize_upstream_fallback_overwrite_containment` | fallback/final-emission containment | Explicit write site restoring selector snapshot when divergence is detected. | upstream-fast fallback family, selector snapshot hash, current hash, containment reason, source/owner | upstream-fast fallback projection tests | Low; already computes fingerprints. |
| `tests/helpers/golden_replay_projection.project_turn_observation` | final projection/observer | Consumer for optional write-site fields and BY summaries. | Projection of already-recorded fields only; no inference override unless field absent | golden replay projection tests | Low; test-only. |

## Candidate Tests/Fixtures

Use the smallest existing corpus first:

- No mutation: BY synthetic no-change record and any protected replay turn with `semantic_mutation_trace_complete` false/no changed entries.
- Repair mutation: `tests/test_by_first_semantic_mutation_attribution.py::test_by_repair_first_mutation_via_dialogue_strip` and focused `tests/test_final_emission_repairs.py` cases.
- Fallback mutation: BY visibility hard replacement fixture; `tests/test_final_emission_visibility_fallback.py`; golden fallback projection tests.
- Sanitizer mutation: BY sanitizer integration fixture; `tests/test_output_sanitizer.py` strip-only and empty fallback cases.
- Final projection/metadata mutation: BY finalize fixture and `tests/test_final_emission_boundary_no_semantic_repair.py` / final-emission boundary suites.
- Prompt/policy mutation: BY policy fixture and `tests/test_response_policy_enforcement_mutation.py`.
- Protected replay corpus: `tests/helpers/protected_semantic_mutation_measurement.py` already runs an 8-turn, 6-scenario corpus and verifies probe non-interference.

Do not create a large new replay corpus. Extend BY synthetic fixtures and the compact protected corpus only after a write-site field exists to assert.

## Risks And Non-Goals

- Non-goal: changing sanitizer, repair, fallback, or final-emission behavior.
- Non-goal: promoting BY trace fields to protected replay schema in CU's first implementation block.
- Risk: double-counting prepared candidates as emitted mutations. Instrument candidate creation separately from selected active-stream writes.
- Risk: storing full before/after text in runtime metadata. Prefer bounded hashes and short previews only when existing conventions allow.
- Risk: conflating selection owner, content owner, projection owner, and first writer. Keep separate fields.
- Risk: adding fields in too many branch-specific files. Prefer a tiny shared metadata helper and a small number of call sites.
- Risk: treating projection-derived lineage as proof of write-time order. Projection should consume write-site evidence when present and fall back to existing inference only as diagnostic.

## Proposed Next Implementation Block

Implement a passive semantic mutation write-site attribution envelope and wire it into the smallest high-value surfaces:

1. Add a bounded helper, likely under final-emission metadata or a small dedicated runtime module, that appends one attribution record with `mutation_id`, `write_site_family`, `write_site_file`, `write_site_function`, `owner`, `route`, `source`, `speaker`, optional before/after semantic hashes, `mutation_reason`, `compatibility_status`, `fallback_family`, and replay/turn identifiers when available.
2. Wire first to sanitizer, terminal fallback/repair assignment, and finalize packaging, because these are active-stream writers and map cleanly to existing BY cases.
3. Project the optional records through `project_turn_observation` as diagnostic fields only, leaving `PROTECTED_OBSERVATION_FIELDS` unchanged.
4. Extend BY/protected semantic mutation tests to assert that first-write records agree with BY first-source detection for sanitizer, fallback, repair, and final-emission cases.
5. Add prompt/policy instrumentation only after the active-stream final-emission cases are stable, because policy touches earlier model/prompt surfaces and candidate-vs-selected semantics are easier to confuse.

## Validation Commands Run

- `rg -n -i "sanitize|repair|fallback|projection|final|emission|metadata|replace|rewrite|normalize|canonical|policy|prompt|mutation|route|speaker|source|authorship" .`
  - Result: broad repo search completed but was noisy due to historical docs/artifacts.
- `rg -n -i --glob 'game/**' --glob 'tests/**' --glob 'tools/**' --glob 'scripts/**' "sanitize|repair|fallback|projection|final|emission|metadata|replace|rewrite|normalize|canonical|policy|prompt|mutation|route|speaker|source|authorship" .`
  - Result: identified live mutation/projection surfaces in `game/`, `tests/`, `tools/`, and `scripts/`.
- `rg -n -i --glob 'game/**' --glob 'tests/**' --glob 'tools/**' --glob 'scripts/**' "event_log|trace|audit|diagnostic|provenance|owner|write_site|reason|source|fallback_family|compatibility|route|replay" .`
  - Result: identified runtime lineage, stage-diff, sanitizer, fallback provenance, and replay diagnostic mechanisms.
- `rg -n -i --glob 'docs/**' --glob 'audits/**' --glob '!docs/archive/**' "semantic mutation|write-site|write site|semantic replacement|attribution|mutation attribution|projection-inferred|final emission|fallback authorship" .`
  - Result: found BY, BS, runtime-lineage, fallback-authorship, and projection prior art.
- Focused `rg`/`Get-Content` reads of `game/final_emission_runtime.py`, `game/api_turn_support.py`, `game/final_emission_gate.py`, `game/final_emission_terminal_pipeline.py`, `game/final_emission_finalize.py`, `game/final_emission_meta.py`, `game/output_sanitizer.py`, `game/upstream_response_repairs.py`, `game/final_emission_replay_projection.py`, `game/runtime_lineage_telemetry.py`, `game/stage_diff_telemetry.py`, `tests/helpers/semantic_mutation_attribution.py`, `tests/helpers/protected_semantic_mutation_measurement.py`, `tests/helpers/golden_replay_projection.py`, and `tests/helpers/failure_classifier.py`.
  - Result: confirmed lifecycle, current attribution surfaces, and the test-only nature of BY first-source attribution.

No pytest run was needed for this discovery-only document; references were validated by targeted search and file reads.
