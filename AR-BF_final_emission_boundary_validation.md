# AR-BF Final Emission Boundary Validation

Campaign: Campaign 4 - Boundary Reconciliation

Scope: validation of the Final Emission boundary against the doctrine recovered in AR-BE, AR-BD, AR-BB, `docs/architecture_ownership_ledger.md`, and `docs/state_authority_model.md`. This report does not redesign Final Emission, rename concepts, or modify production code.

Evidence posture: prior campaign outputs are treated as governing doctrine unless contradicted by source, tests, or ownership ledgers. No contradiction requiring architectural redesign was found.

## 1. Executive Summary

Final Emission appears architecturally durable.

Confirmed fact: the repository expresses Final Emission as a last-mile boundary for player-facing output legality, selection, packaging, FEM/metadata construction, terminal exception handling, and sealing. The strongest evidence is `game/final_emission_gate.py:1`, `game/final_emission_runtime.py:1`, `game/final_emission_boundary_contract.py`, `game/final_emission_finalize.py:1`, `docs/architecture_ownership_ledger.md:106`, and AR-BB's responsibility map.

Confirmed fact: Final Emission does not present itself as domain simulation, runtime orchestration, prompt construction, replay authority, persistence authority, or provenance owner. It receives already-produced candidate output and authoritative context, then applies deterministic legality/packaging/fallback-selection rules before persistence, logging, response, and replay observation.

Strong inference: the remaining overlap with validators, repairs, sanitizers, fallback, provenance, and replay projection is intentional and mostly well fenced. The principal live risk is not architectural uncertainty but continued drift-watch for transitional semantic repair residue: old boundary repair functions, legacy sanitizer rewrite mode, and compatibility metadata for fallback/provenance projection.

No genuine architectural responsibility leakage was found. Several implementation-local or transitional surfaces remain, but they are named, tested, and generally marked as disabled, upstream-owned, compatibility-only, or diagnostic-only.

## 2. Permanent Responsibility Inventory

| Permanent Final Emission responsibility | Repository evidence | Why it belongs inside Final Emission |
|---|---|---|
| Gate orchestration and layer order | `game/final_emission_gate.py:1`, `apply_final_emission_gate`; `docs/architecture_ownership_ledger.md:106`; `tests/test_final_emission_gate_orchestration_order.py`; `tests/test_gate_delegate_closeout_locks.py` | The final gate is the only boundary with enough complete candidate, contract, strict-social, visibility, repair, sanitizer, and metadata context to decide last-mile ordering. Neighboring modules own predicates/helpers, but not the whole exit sequence. |
| Production-facing finalization delegate | `game/final_emission_runtime.py:1`, `finalize_player_facing_emission` | Runtime/API callers need one stable entrypoint that delegates to the gate without importing internal gate machinery. This is boundary stabilization, not new authority. |
| Legality enforcement and fail-closed mutation taxonomy | `game/final_emission_boundary_contract.py`; `PACKAGING_ALLOWED`, `LEGALITY_ALLOWED`, `SEMANTIC_DISALLOWED`, `assert_final_emission_mutation_allowed`; `tests/test_final_emission_boundary_contract.py` | Final Emission is where candidate text becomes shippable player text. The mutation taxonomy is permanent because it prevents final-boundary behavior from silently expanding into semantic authoring. |
| Player-facing output selection | `game/final_emission_gate.py:81`; `game/final_emission_generic_exit.py`; `game/final_emission_strict_social_stack.py`; `game/final_emission_opening_fallback.py:526`; `game/final_emission_sealed_fallback.py` | Selection is last-mile choice among candidate, upstream-prepared text, sealed fallback, strict-social fallback, and opening fallback. Content authorship may live elsewhere; final selection belongs at the boundary. |
| Output packaging and final text normalization | `game/final_emission_finalize.py:153`, `strip_appended_route_illegal_contamination_sentences`, `_sanitize_output_text`, `package_emission_channel_sidecar`; `game/final_emission_boundary_contract.py` packaging allow-list | Packaging converts selected text into final response-safe shape. It is explicitly not sentence recomposition or semantic repair; metadata records semantic repair disabled. |
| FEM construction and metadata packaging | `game/final_emission_meta.py`, `game/final_emission_fem_assembly.py`, `ensure_final_emission_meta_dict`, `merge_gate_layer_metas_into_fem`, `package_emission_channel_sidecar`; `tests/test_final_emission_meta.py`, `tests/test_final_emission_fem_assembly_pre_terminal_debug.py` | FEM is the canonical sealed record for the final-emission decision. It must be packaged where all gate-layer outcomes are known. |
| Terminal exception handling | `game/final_emission_terminal_pipeline.py:62`, `apply_strict_social_emergency_fallback_patch`; `game/final_emission_sealed_fallback.py`; `game/final_emission_visibility_fallback.py`; `game/final_emission_boundary_contract.py` legality allow-list | When normal candidate output cannot legally ship, final emission owns terminal replacement/exception selection. It must stamp traceability while preserving content-owner distinctions. |
| Emission sealing and channel projection | `game/final_emission_finalize.py:153`; `project_public_payload`, `project_author_payload`, `project_debug_payload`; `tests/test_final_emission_channel_separation.py` | The final output must remove gate caches, package debug/author sidecars, and expose a public player-facing payload. This is final-boundary responsibility because downstream persistence/response should observe sealed surfaces. |
| Final-emission mutation lineage refresh | `game/final_emission_finalize.py:_refresh_output_mutation_lineage`; `game/final_emission_meta.py:append_semantic_mutation_write_site`; `game/final_emission_replay_projection.py` | Final Emission records what it did for downstream evidence. Recording lineage does not make Final Emission the owner of fallback content or replay interpretation. |
| Boundary diagnostics for disabled semantic repair | `game/final_emission_gate.py:8`, `game/final_emission_finalize.py:213`, `game/final_emission_repairs.py:986`, policy modules with `*_boundary_semantic_repair_disabled` | Because the architecture forbids ordinary semantic repair at final emission, the boundary permanently owns explicit failure/disabled markers when it declines to repair. |

## 3. Neighboring Boundary Matrix

| Neighbor | Permanent responsibility | Explicit exclusions | Interaction with Final Emission | Authority relationship | Long-term stability |
|---|---|---|---|---|---|
| Validators | Deterministic pass/fail predicates, reason codes, and evidence for response contracts, visibility, referential clarity, fallback behavior, narrative mode, and related legality surfaces. | Final selection, prose repair, fallback authorship, FEM packaging, runtime truth. | Called by gate/stacks/repair layers to determine whether candidate or replacement can ship. | Predicate authority only; Final Emission owns orchestration/application. | Stable. AR-BB and `docs/architecture_ownership_ledger.md` explicitly separate validators from gate ordering. |
| Repairs | Bounded deterministic correction and repair-layer metadata where legality-preserving; currently also a transitional home for watched residue. | Ordinary content generation, planner intent, fallback-family authorship, domain truth. | Gate/stacks call `game.final_emission_repairs` layer helpers and merge repair metadata into FEM/debug. | Delegated helper authority; gate decides sequence and final text application. | Stable concept with transitional implementation residue. |
| Sanitizers | Strip/package/drop cleanup of internal contamination, serialized payload leakage, unsafe prefixes, and route-illegal artifacts; sanitizer lineage. | General diegetic rewrite, narrative repair, default fallback authorship. | Pre-/near-gate text firewall; finalization copies sanitizer attribution into FEM. | Cleanup authority; Final Emission may consume sanitizer result and record it. | Stable strip-only boundary; `legacy_sentence_rewrite` is compatibility/test-only. |
| Fallback | Bounded substitute behavior when normal output cannot safely ship, with split content/selection/application/provenance/observer axes. | Single-owner fallback authority, untraceable narrative invention, replay authority. | Final Emission selects/applies some fallback surfaces and stamps final route/FEM. Content may be upstream, strict-social, opening, retry, sanitizer, or sealed-gate. | Multi-axis by design. Gate selection is not content authorship. | Stable with transitional vocabulary fields. |
| Provenance | Metadata and trace vocabulary explaining source, family, owner, selection, and mutation lineage. | Selecting fallback, authoring text, changing runtime result. | Final Emission packages provenance into FEM and mutation write-site records. | Read/write metadata explanation; behavior authority remains with owning subsystem. | Stable with dual fallback-family compatibility pressure. |
| Replay Projection | Read-side projection of finalized FEM/runtime lineage into diagnostic or replay-observable forms. | Runtime mutation, final selection, acceptance projection schema ownership. | Consumes sealed FEM and logs after runtime; never feeds gate behavior. | Downstream observer. | Stable. `tests/test_replay_boundary_governance.py` locks runtime projection vs acceptance projection split. |

## 4. Remaining Transitional Overlaps

| Overlap | Files and symbols | Classification | Justification | Expected retirement |
|---|---|---|---|---|
| Final-boundary semantic repair residue | `game/final_emission_repairs.py`, `game/final_emission_*` policy modules, `docs/architecture_ownership_ledger.md:125` | Transitional implementation | Ledger names answer-completeness reordering, response-delta reordering/compression, spoken refinement cash-out, social-response density edits, and fallback synthesis as boundary semantic pressure. Current code often marks these disabled. | Retire or keep disabled as upstream-owned repairs become complete. |
| Response-type answer/action fallback consumption | `game/final_emission_response_type.py:_resolve_upstream_prepared_answer_action_repair`, `game/upstream_response_repairs.py:build_upstream_prepared_emission_payload` | Defensive orchestration plus upstream-owned repair | Gate consumes prepared text and validates it; upstream owns construction. Tests assert gate does not mint fallback prose. | Permanent as handoff pattern; upstream-prepared compatibility fields may be simplified later. |
| Opening fallback selection | `game/final_emission_opening_fallback.py`, `game/upstream_response_repairs.py:build_upstream_prepared_opening_fallback_payload`, `game/opening_deterministic_fallback.py` | Permanent architectural overlap | Opening prose is composed upstream/opening owner, packaged upstream, selected by final emission. Gate must not re-author opening prose. | No retirement expected; maintain owner-bucket clarity. |
| Sanitizer `legacy_sentence_rewrite` mode | `game/output_sanitizer.py:197`, `sanitize_player_facing_output` branch after strip-only | Compatibility support / transitional implementation | Default is strip-only. Legacy sentence rewrite is explicit opt-in for tests/rare diagnostics and has C2 owner-audit comments saying diegetic rewrites belong upstream or strict-social owner. | Retire when no tests/diagnostics require it. |
| Fallback behavior strip-only repair | `game/final_emission_repairs.py:937`, `repair_fallback_behavior` | Defensive orchestration with transitional history | Live behavior strips meta/fabricated/overcertain surfaces and records semantic synthesis skipped. Old template synthesis tests are skipped. | Keep strip-only permanently; retire skipped historical synthesis tests if no longer useful. |
| Referent clarity local substitution | `game/final_emission_repairs.py:_apply_referent_clarity_emission_layer`, `game/final_emission_referential_clarity.py` local repair helpers, `game/final_emission_terminal_pipeline.py:_apply_referent_clarity_pre_finalize` | Defensive normalization / legality overlap | Replacement is constrained to safe explicit labels from referent artifacts and can be disabled with `allow_semantic_text_repair=False`; terminal pre-finalize preserves candidate text when disabled. | Keep only where strict validation proves legality; move broader semantic cases upstream. |
| Visibility/sealed hard replacements | `game/final_emission_visibility_fallback.py`, `game/final_emission_sealed_fallback.py`, `game/final_emission_terminal_pipeline.py` | Permanent architectural overlap | Final emission owns terminal legality replacement; content/prose owner can be visibility, strict-social, opening, acceptance-quality, or sealed fallback source. | No architectural retirement; keep provenance/owner buckets explicit. |
| Dual fallback-family vocabulary | `game/realization_provenance.py`, `game/final_emission_replay_projection.py`, `game/final_emission_meta.py` | Compatibility support | `realization_fallback_family` is governed provenance taxonomy; `fallback_family_used` is diegetic/runtime legacy. Replay projection documents precedence and does not choose behavior. | Possible future field precedence documentation or schema simplification. |
| Runtime diagnostic projection vs protected replay projection | `game/final_emission_replay_projection.py`, `tests/helpers/golden_replay_projection.py`, `tests/test_replay_boundary_governance.py` | Permanent architectural overlap | Runtime lineage projection derives diagnostics from finalized FEM; acceptance projection is test/governance-owned. Tests assert "do not merge". | No retirement expected. |
| Compatibility import/test facades | `tests/ownership_closeout_delegate_locks.py`, `tests/test_gate_delegate_closeout_locks.py`, `tests/test_compat_import_governance.py` | Compatibility support | Tests keep old gate import/monkeypatch patterns from regrowing and verify extracted owner modules are called directly. | Retire only after compatibility surfaces disappear. |

No overlap was classified as a genuine architectural concern.

## 5. Dependency Map

### Incoming Responsibilities

Final Emission receives:

1. Candidate expression from AI/realization: `game.gm.call_gpt`, retry/fallback output, or deterministic fallback paths.
2. Authoritative runtime context from API/domain owners: `resolution`, `session`, `scene`, `world`, `scene_id`.
3. Contract/policy data from prompt/response policy/turn packet surfaces: `game.response_policy_contracts`, `game.turn_packet`, response debug metadata.
4. Upstream-prepared repair/fallback text from `game.upstream_response_repairs`.
5. Strict-social/visibility/referential clarity owner outputs from specialized final-emission-adjacent modules.

Authority direction: upstream systems decide truth, contracts, candidate content, and prepared repair text before the final boundary. Final Emission may validate, reject, select, package, or hard-replace; it does not re-decide domain truth.

### Outgoing Responsibilities

Final Emission produces:

1. Sealed public `player_facing_text`.
2. `_final_emission_meta` / FEM fields.
3. Mutation lineage and provenance packaging.
4. Public/debug/author sidecar projection in final response payload.
5. Finalized surfaces for persistence/log/response and later replay/evidence observation.

Authority direction: downstream persistence, logs, replay, diagnostics, and governance observe finalized output. They do not feed back into the live gate.

### Dependency Direction Findings

Confirmed compliant:

- `game/final_emission_runtime.py` delegates into `game.final_emission_gate`, giving runtime/API one stable entrypoint.
- `game/final_emission_gate.py` imports owner modules for validators/repairs/stacks rather than re-exporting broad helper authority.
- `game/final_emission_terminal_pipeline.py` calls visibility, acceptance-quality, referential clarity, interaction-continuity, fallback, and finalization owners directly.
- `game/final_emission_replay_projection.py` states it must not select fallbacks, mutate output, or stamp write-time FEM.
- `tests/test_replay_boundary_governance.py` asserts runtime lineage projection and acceptance projection remain separate.

No dependency was found that violates the architectural model. Apparent exceptions are defensive or transitional:

- `append_semantic_mutation_write_site` records diagnostic evidence for several final text changes. This is provenance packaging, not behavior ownership.
- Final-emission modules import upstream/fallback/social helpers for selection and stamping. Those imports support final-boundary orchestration and owner-bucket clarity, not collapse of content authorship.
- The finalization path calls state-channel projection helpers to package response lanes; this is output sealing, not UI state authority.

## 6. Semantic Repair Inventory

Classification key: legality enforcement, formatting, packaging, defensive normalization, compatibility behavior, semantic authoring.

| Location | Symbols | Text-changing behavior | Classification | Evidence and status |
|---|---|---|---|---|
| Mutation taxonomy | `game/final_emission_boundary_contract.py` | Does not change text; classifies allowed/disallowed mutation kinds. | Legality enforcement | Permanent. Tests assert semantic-disallowed kinds fail and unknown kinds fail closed. |
| Final output sanitize/route strip | `game/final_emission_finalize.py:finalize_emission_output`, `_sanitize_output_text`, `strip_appended_route_illegal_contamination_sentences` | Sanitizes HTML/text and strips known route-illegal stock sentence when mixed with valid text. | Formatting / defensive normalization | Permanent packaging. Metadata records `final_emission_finalize_semantic_repair_used=False`. |
| Final output reseal strip | `game/final_emission_finalize.py` reseal block | Re-applies narrow route-illegal strip after fallback overwrite containment. | Defensive normalization | Permanent containment; allow-listed as `strip_route_illegal_contamination`. |
| Opening accepted candidate reseal | `game/final_emission_finalize.py`, `game/final_emission_opening_fallback.py:reassert_scene_opening_accepted_candidate` | Restores previously accepted opening candidate after later boundary drift. | Compatibility behavior / defensive normalization | Allow-listed as `restore_accepted_scene_opening_candidate`; not opening prose authorship. |
| Answer completeness | `game/final_emission_repairs.py:_apply_answer_completeness_layer` | Does not reorder/author; records unsatisfied boundary failure. | Transitional disabled semantic repair | `answer_completeness_boundary_semantic_repair_disabled=True`; tests assert no boundary reorder. |
| Answer exposition plan | `game/final_emission_repairs.py:_apply_answer_exposition_plan_layer` | May safely move an existing answer sentence to front when required facts already appear; otherwise records failure. | Defensive normalization / formatting | Uses `assert_final_emission_mutation_allowed("reorder_answer_to_front")`; no missing fact synthesis. |
| Response delta | `game/final_emission_repairs.py:_apply_response_delta_layer` | Does not reorder/compress; records unsatisfied boundary failure. | Transitional disabled semantic repair | `response_delta_boundary_semantic_repair_disabled=True`; tests assert no boundary reorder. |
| Social response structure | `game/final_emission_repairs.py:apply_social_response_structure_repair`, `_apply_social_response_structure_layer` | Historical flatten/collapse helpers exist; final boundary blocks list-to-prose/cadence/dialogue repairs. | Transitional disabled semantic repair / compatibility helper | Code comments mark SEMANTIC_DISALLOWED; tests assert disabled boundary repair for list-like dialogue. |
| Narrative authenticity | `game/final_emission_repairs.py:_apply_narrative_authenticity_layer` | Does not repair semantics; records failure/trace. | Transitional disabled semantic repair | Records `semantic_repair_must_occur_upstream`. |
| Fallback behavior | `game/final_emission_repairs.py:repair_fallback_behavior` | Strips meta fallback voice, fabricated authority, overcertain claim spans; does not synthesize missing shape. | Defensive normalization | `assert_final_emission_mutation_allowed` for strip/trim kinds; records `fallback_behavior_boundary_semantic_synthesis_skipped=True`. |
| Referent clarity in repairs | `game/final_emission_repairs.py:_apply_referent_clarity_emission_layer` | Optional replacement of risky pronoun with safe explicit label from referent artifact; can be disabled. | Defensive normalization with semantic-adjacent risk | Safe only under full artifact/validation; terminal pipeline calls with `allow_semantic_text_repair=False` for pre-finalize. |
| Response-type enforcement | `game/final_emission_response_type.py` | Selects strict-social fallback or upstream-prepared answer/action repair text; rejects malformed prepared text. | Legality enforcement / defensive orchestration | Gate consumes upstream-prepared text; tests assert no boundary synthesis. |
| Opening fallback adapter | `game/final_emission_opening_fallback.py` | Selects upstream-prepared opening fallback or sealed fail-closed marker. | Defensive orchestration / compatibility support | Module docstring states it does not author opening prose; selection is permanent overlap. |
| Strict-social emergency fallback patch | `game/final_emission_terminal_pipeline.py:apply_strict_social_emergency_fallback_patch` | Applies already-authored strict-social fallback and stamps FEM. | Legality enforcement / terminal exception | Permanent terminal exception; content owner is strict-social catalog/projection, not gate prose generation. |
| Fallback behavior inside terminal pipeline | `game/final_emission_terminal_pipeline.py` strict-social path | Applies result of `_apply_fallback_behavior_layer` and records repair metadata. | Defensive orchestration | Text change authority belongs to repair helper; pipeline applies and stamps. |
| Referent clarity pre-finalize | `game/final_emission_terminal_pipeline.py:_apply_referent_clarity_pre_finalize` | Calls referent layer with semantic repair disabled, then preserves candidate text and metadata. | Packaging / validation annotation | Uses `assert_final_emission_mutation_allowed("preserve_candidate_text")`; diagnostic write-site only. |
| Visibility fallback/replacement | `game/final_emission_visibility_fallback.py` | May hard-replace or apply local pronoun substitution under visibility/referential constraints. | Legality enforcement / defensive normalization | Uses boundary assertion and semantic write-site records; should remain guarded by visibility/referential tests. |
| Sealed fallback | `game/final_emission_sealed_fallback.py` | Applies selected sealed fallback data and stamps lineage. | Terminal exception handling | Data object states it carries prose selected by existing owners and does not author it. |
| Acceptance quality floor | `game/final_emission_acceptance_quality.py` | Hard replacement/repair only under N4 floor predicates; does not broaden semantic-rewrite authority. | Legality enforcement / terminal exception | Uses boundary assertion; docstring says it does not broaden repair authority or semantic rewrite. |
| Narrative authority | `game/final_emission_narrative_authority.py:repair_narrative_authority_narrow` | Narrow repair helper exists, but boundary records semantic repair disabled. | Transitional disabled semantic repair | `narrative_authority_boundary_semantic_repair_disabled=True`. |
| Tone escalation | `game/final_emission_tone_escalation.py:repair_tone_escalation_narrow` | Narrow repair helper exists, but boundary records semantic repair disabled. | Transitional disabled semantic repair | `tone_escalation_boundary_semantic_repair_disabled=True`. |
| Anti-railroading | `game/final_emission_anti_railroading.py:repair_anti_railroading_narrow` | Narrow repair helper exists, but boundary records semantic repair disabled. | Transitional disabled semantic repair | `anti_railroading_boundary_semantic_repair_disabled=True`. |
| Context separation | `game/final_emission_context_separation.py:repair_context_separation_narrow` | Narrow repair helper exists, but boundary records semantic repair disabled. | Transitional disabled semantic repair | `context_separation_boundary_semantic_repair_disabled=True`. |
| Player-facing narration purity | `game/final_emission_player_facing_narration_purity.py` | Boundary repair disabled. | Transitional disabled semantic repair | `player_facing_narration_purity_boundary_semantic_repair_disabled=True`. |
| Answer shape primacy | `game/final_emission_answer_shape_primacy.py` | Boundary repair disabled. | Transitional disabled semantic repair | `answer_shape_primacy_boundary_semantic_repair_disabled=True`. |
| Scene state anchor | `game/final_emission_scene_state_anchor.py` | Narrow repair helpers exist, but boundary repair disabled. | Transitional disabled semantic repair | `scene_state_anchor_boundary_semantic_repair_disabled=True`. |
| Fast fallback neutral composition | `game/final_emission_fast_fallback_composition.py` | Boundary repair disabled for upstream fast-fallback malformed composition. | Transitional disabled semantic repair | `fast_fallback_neutral_composition_boundary_semantic_repair_disabled=True`. |
| Output sanitizer strip-only | `game/output_sanitizer.py:_sanitize_player_facing_output_strip_only` | Extracts serialized `player_facing_text`, strips prefixes/fragments, drops non-diegetic rewrite candidates, uses strict-social or upstream-prepared empty fallback if empty. | Defensive normalization / packaging | Default mode. Explicit docstring says no diegetic template substitution except strict-social owner fallbacks. |
| Output sanitizer legacy rewrite | `game/output_sanitizer.py:sanitize_player_facing_output` legacy branch | Atomic diegetic rewrites and stock empty fallback under `legacy_sentence_rewrite`. | Compatibility behavior / transitional semantic authoring | Explicit opt-in; C2 owner-audit says move upstream or strict-social owner. |
| Upstream-prepared answer/action/opening/fallback text | `game/upstream_response_repairs.py` | Constructs deterministic repair/fallback text before Final Emission. | Not Final Emission semantic repair | Upstream-owned; Final Emission validates/selects. |
| Legacy final-emission text repair module | `game/final_emission_text_legacy_semantic_repair.py`; imported by `game/final_emission_text.py` | Participial fragment repair helpers. | Compatibility behavior / historical semantic authoring | Finalize path disables participial/fragment/micro-smoothing; module remains legacy/test-only surface. |

Conclusion: live Final Emission semantic authoring is either absent, explicitly upstream-owned, terminal/legality-driven, or compatibility/test-only. The only semantic-adjacent live areas requiring continued watch are referential/visibility local substitutions and acceptance/terminal fallback replacement, both already constrained by validators and provenance.

## 7. Architectural Stability Assessment

### Architecturally Complete

Confirmed fact: Final Emission has a stable permanent responsibility set: gate orchestration, legality enforcement, selection, packaging, FEM/meta construction, terminal exception handling, sealing, and traceability.

Confirmed fact: neighboring boundaries are defined strongly enough for long-term implementation. Validators predicate, repairs correct bounded known failures, sanitizers strip/package/drop, fallback supplies bounded substitute behavior, provenance records, replay projection observes.

Strong inference: future Final Emission work should mostly affect implementation, test coverage, and compatibility retirement, not architecture.

### Remaining Architectural Questions

No remaining Final Emission architectural question blocks long-term stability.

The nearest architectural questions now live outside Final Emission:

- ruleset identity/version/adapter boundary;
- AI backend/provider adapter boundary;
- public UI/tooling facade and capability/version bundle.

### Remaining Implementation Work

- Continue retiring or keeping disabled old semantic repair helpers in policy modules.
- Keep sanitizer default strip-only and constrain legacy rewrite mode.
- Maintain direct-owner tests so gate orchestration does not reacquire helper ownership.
- Keep referential/visibility local substitution under strict validation and provenance.
- Preserve upstream-prepared repair handoff tests for answer/action/opening paths.

### Remaining Documentation Work

- Maintain a concise table of allowed final-emission mutation kinds and their owner rationale.
- Document field precedence for `realization_fallback_family`, `fallback_family_used`, and projected replay `fallback_family`.
- Keep `docs/architecture_ownership_ledger.md` aligned with any retired compatibility paths.

## 8. Recommended Next Cycle

Recommended next cycle: `AR-BG Ruleset, Backend, and Version-Provenance Boundary Inventory`.

Why it follows naturally: AR-BE identified ruleset identity and provider-neutral AI backend boundaries as the highest remaining local architecture seams after Final Emission. AR-BF validates that Final Emission is stable enough not to block that work. The next useful campaign should therefore move upstream of Final Emission and examine the version/provenance bundle required for alternate rulesets and additional AI backends without changing the runtime transaction spine.

Expected focus:

- ruleset identity/version/selection contract;
- backend provider adapter boundary;
- fake backend/test seam;
- provenance/version fields spanning ruleset, backend/model, prompt/policy, CTIR, and final-emission schema;
- explicit non-goals around generic plugin systems or simultaneous multi-ruleset execution unless product evidence requires them.

## 9. Files Required For External Review

### Required

- `AR-BF_final_emission_boundary_validation.md`
- `AR-BE_boundary_reconciliation_discovery_and_evidence_inventory.md`
- `AR-BD_concept_map_synthesis_and_campaign_closeout.md`
- `AR-BB_defensive_runtime_boundary_reconciliation.md`
- `AR-AI_final_vision_compatibility_closeout.md`
- `AR-AG_final_vision_compatibility_discovery.md`
- `game/model_routing.py`
- `game/gm.py`
- `game/upstream_response_repairs.py`
- `game/realization_provenance.py`
- `game/final_emission_replay_projection.py`
- `game/combat.py`
- `game/skill_checks.py`
- `game/noncombat_resolution.py`
- `docs/architecture_ownership_ledger.md`

### Conditional

- `game/prompt_context.py`
- `game/ctir.py`
- `game/ctir_runtime.py`
- `game/response_policy_contracts.py`
- `game/final_emission_boundary_contract.py`
- `game/final_emission_meta.py`
- `tests/test_model_routing_config.py`
- `tests/test_model_routing_runtime.py`
- `tests/test_ctir_noncombat_consumption.py`
- `tests/test_noncombat_runtime_integration.py`
- `tests/test_final_emission_boundary_contract.py`
- `tests/test_replay_boundary_governance.py`

### Not Needed Unless Requested

- Full `game/final_emission_*` module set, because AR-BF summarizes the boundary validation.
- Full golden replay corpus and generated replay refresh artifacts.
- Full `tests/` directory.
- Large `artifacts/` and `audits/` trees.
- Static UI files, unless the next cycle expands into public UI/tooling facade work.
