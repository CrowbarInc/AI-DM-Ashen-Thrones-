# Architecture Ownership Ledger

This ledger is the repo-facing declaration of ownership for ambiguous seams.

## Operator Note

Ownership declarations do **not** prove the code is already clean.

They establish the cleanup target: future moves, trims, and test/doc realignment should converge toward the owners declared here.

If current code shape still contradicts a declaration, treat that contradiction as cleanup work to reduce, not as a reason to blur the boundary again.

## Validation layer separation (phase contract)

Cross-cutting **phase responsibilities** (truth vs structure vs expression vs legality vs offline scoring) are declared in `docs/validation_layer_separation.md`. The machine-readable, import-light registry lives in `game/validation_layer_contracts.py` (stable layer ids, governed domains, pure predicates). It **does not** replace this ledger’s **module** owners; it constrains how new concerns should map onto existing owners without inventing a parallel policy stack.

**Governed seam:** Treat validation-layer separation as **review discipline**, not a second runtime policy engine. Canonical phase ownership is the pair **prose contract + registry** above. **Block B** runtime clarifications (NA non-owning shadow read of `response_delta`, gate split across multiple files, offline evaluator naming, NA numeric diagnostics vs gate scoring) are **first-class**; they should not be silently regressed. **Multiple modules under one canonical layer** does not imply duplicate ownership when the split is intentional (see `docs/validation_layer_separation_block_b_residue.md`).

**Drift audit:** `tools/validation_layer_audit.py` runs heuristic checks (imports and a few wording patterns) to help catch ownership mistakes early. It is a maintainer aid; see `docs/validation_layer_audit.md` for how to run it and how to read “benign split” vs “likely drift.” Block B residue is **monitored** by the audit output, not ignored.

## Standard seam presentation

Each governed seam below uses the same four rows (plus boundary notes where helpful):

1. **Runtime owner** — canonical `game/` module for the invariant.
2. **Practical primary direct-owner suite** — pytest module that should own direct semantic assertions first.
3. **Secondary downstream suites** — integration, smoke, validators, transcripts, or compatibility consumers; they exercise shipped behavior but are not alternate semantic homes.
4. **Compatibility / support residue** — supported read paths, historical aliases, or extracted helpers that may remain importable without re-opening co-equal ownership.

**Current governance read:** Major emit-path seams below are **resolved at the ownership level** (singular runtime owner + direct-owner suite + intentional downstream consumers). Remaining work is **drift-watch**, audit heuristics, archaeology/coupling on the scorecard, and keeping `tests/TEST_AUDIT.md` / inventory artifacts aligned—not unresolved split ownership between co-equal test homes.

## Response Policy Contracts

- Canonical owner module: `game/response_policy_contracts.py`
- Non-owner supporting modules: `game/final_emission_repairs.py`, `game/final_emission_gate.py`, `game/prompt_context.py`
- Current state: `governance-aligned; drift-watch`
- **Concern name:** `response policy contracts`
- **Runtime owner:** `game/response_policy_contracts.py`
- **Practical primary direct-owner suite:** `tests/test_response_policy_contracts.py`
- **Secondary downstream suites:** `tests/test_fallback_shipped_contract_propagation.py`, `tests/test_response_delta_requirement.py`, `tests/test_final_emission_gate.py`, `tests/test_social_exchange_emission.py`, `tests/test_final_emission_validators.py`, `tests/test_interaction_continuity_contract.py`, `tests/test_interaction_continuity_validation.py`
- **Compatibility / support residue:** private compatibility accessors may remain importable; top-level `fallback_behavior` / `social_response_structure_contract` fallbacks may remain supported for older payload shapes. Interpret as read-side tolerance, not equal semantic homes.
- **Non-owner adjacent modules:** `game/final_emission_repairs.py`, `game/final_emission_gate.py`, `game/prompt_context.py` (must not become the contract authority, gate rule source, or post-prompt resolver owner).
- **Belongs in runtime owner:** response-policy contract shape builders, resolution helpers, and read-only accessors that tell downstream layers what was shipped.
- **Does not belong in runtime owner:** validator verdicts, repair strategies, layer ordering, final-emission metadata packaging.
- **Governance note:** describe as `runtime owner → direct-owner suite → downstream suites`, not repair-, validator-, or gate-centered parallel authority.

## Prompt Contracts

- Canonical owner module: `game/prompt_context.py`
- Non-owner supporting modules: `game/prompt_context_leads.py`, `game/response_policy_contracts.py`
- Current state: `governance-aligned; drift-watch`
- **Concern name:** `prompt contracts`
- **Runtime owner:** `game/prompt_context.py`
- **Practical primary direct-owner suite:** `tests/test_prompt_context.py`
- **Secondary downstream suites:** `tests/test_prompt_compression.py`, `tests/test_prompt_and_guard.py`, `tests/test_dialogue_interaction_establishment.py`, `tests/test_fallback_shipped_contract_propagation.py`, `tests/test_social_escalation.py`, `tests/test_social_interaction_authority.py`, `tests/test_social_speaker_grounding.py`, `tests/test_social_topic_anchor.py`, `tests/test_stale_interlocutor_invalidation_block3.py`, `tests/test_strict_social_answer_pressure_cashout.py`, `tests/test_synthetic_sessions.py`, `tests/test_answer_completeness_rules.py`, `tests/test_turn_pipeline_shared.py`, plus gate/emission/transcript suites such as `tests/test_final_emission_gate.py`, `tests/test_social_exchange_emission.py`, and `tests/test_narration_transcript_regressions.py`
- **Compatibility / support residue:** support-only extraction in `game/prompt_context_leads.py`; exported consumer paths may consume prompt-owned bundles without becoming prompt owners.
- **Non-owner adjacent modules:** `game/prompt_context_leads.py`, `game/response_policy_contracts.py` (not rival owners of the full prompt bundle).
- **Belongs in runtime owner:** prompt-context assembly, prompt-facing contract bundling, deterministic export of the contract payload narration receives.
- **Does not belong in runtime owner:** extracted lead-only logic as a rival owner, validator/repair policy, emit-order orchestration.
- **Governance note:** describe as `runtime owner → direct-owner suite → downstream suites`, not several equal prompt authorities.

## CTIR (resolved-turn meaning) and prompt adapter

- Canonical owner modules: `game/ctir.py` (normalized meaning shape), `game/ctir_runtime.py` (session attach + stamp + ensure), `game/api.py` (build timing after authoritative mutation and hygiene)
- Non-owner consumers: `game/prompt_context.py` (reads session CTIR once per narration-context build; maps via adapter helpers only), `game/turn_packet.py` (separate contracts/debug packet—must not embed CTIR)
- **Concern name:** `resolved-turn CTIR vs prompt-context adapter`
- **Runtime owner:** `game/ctir.py` + `game/ctir_runtime.py` for the meaning object; `game/api.py` for orchestration of detach → mutate → hygiene → attach
- **Practical primary direct-owner suites:** `tests/test_ctir_pipeline_integration.py`, `tests/test_prompt_context_ctir_consumption.py`, `tests/test_ctir_runtime_lifecycle.py`, `tests/test_ctir_retry_stability.py`, `tests/test_ctir_turn_packet_boundary.py`, `tests/test_ctir_snapshot_examples.py`, `tests/test_prompt_context_ctir_boundary.py`
- **Secondary downstream suites:** prompt and pipeline suites that assume post-resolution payloads remain stable
- **Compatibility / support residue:** when CTIR is absent, `prompt_context` may fall back to caller `resolution` / `intent`; bounded canonical reads remain for data CTIR does not own (see module comments)
- **Design reference:** `docs/ctir_prompt_adapter_architecture.md`
- **Governance note:** `prompt_context` is not a second semantic authority over the resolved turn when CTIR is present; `turn_packet` is not CTIR.

## Strict-social Exchange Emission Seam

- Canonical owner module: `game/social_exchange_emission.py`
- Non-owner supporting modules: `game/final_emission_gate.py`, `game/gm.py`, `game/gm_retry.py`
- Current state: `governance-aligned; drift-watch`
- **Concern name:** `strict-social exchange emission seam`
- **Runtime owner:** `game/social_exchange_emission.py`
- **Practical primary direct-owner suite:** `tests/test_social_exchange_emission.py`
- **Secondary downstream suites:** `tests/test_strict_social_emergency_fallback_dialogue.py`, `tests/test_social_emission_quality.py`, `tests/test_dialogue_interaction_establishment.py`
- **Compatibility / support residue:** legacy `repair_strict_social_terminal_dialogue_fallback_if_needed(...)` may remain importable as an explicit compatibility alias; historical-path tests should label alias coverage as compatibility, not semantic ownership.
- **Non-owner adjacent modules:** `game/final_emission_gate.py`, `game/gm.py`, `game/gm_retry.py` (not owners of terminal strict-social dialogue semantics).
- **Belongs in runtime owner:** strict-social exchange emission normalization, ownership filtering, deterministic fallback shaping, terminal dialogue application once the dialogue-contract verdict is known.
- **Does not belong in runtime owner:** canonical response-policy resolution, general repair governance, top-level gate orchestration.
- **Governance note:** describe as `runtime owner → direct-owner suite → downstream / compatibility coverage`, not mixed emission-vs-repair parallel authority.

## Final Emission Gate Orchestration

- Canonical owner module: `game/final_emission_gate.py`
- Non-owner supporting modules: `game/final_emission_repairs.py`, `game/final_emission_meta.py`
- Current state: `governance-aligned; drift-watch`
- **Concern name:** `final emission gate orchestration`
- **Runtime owner:** `game/final_emission_gate.py`
- **Practical primary direct-owner suite:** `tests/test_final_emission_gate.py`
- **Secondary downstream suites:** `tests/test_social_exchange_emission.py`, `tests/test_turn_pipeline_shared.py`, `tests/test_stage_diff_telemetry.py`, `tests/test_social_emission_quality.py`, `tests/test_dead_turn_detection.py`, `tests/test_interaction_continuity_speaker_bridge.py`, `tests/test_interaction_continuity_validation.py`, `tests/test_interaction_continuity_repair.py`, plus transcript/regression suites such as `tests/test_narration_transcript_regressions.py`
- **Compatibility / support residue:** `game/final_emission_meta.py` as metadata packaging / read-side support; retry / observability / pipeline consumers may pass through the gate without owning orchestration order.
- **Non-owner adjacent modules:** `game/final_emission_repairs.py`, `game/final_emission_meta.py` (not layer-order or orchestration authorities).
- **Belongs in runtime owner:** final-emission layer ordering, gate-level integration, last-mile finalize flow, calls into validators, repairs, sanitizer, metadata packaging.
- **Does not belong in runtime owner:** canonical metadata schema ownership, standalone contract-authority logic, telemetry field semantics.
- **Governance note:** describe as `runtime owner → direct-owner suite → downstream suites`, not mixed gate/meta/telemetry/pipeline parallel ownership.

## Final Emission Repairs

- Canonical owner module: `game/final_emission_repairs.py`
- Non-owner supporting modules: `game/final_emission_gate.py`, `game/final_emission_meta.py`
- Current state: `governance-aligned; drift-watch`
- **Concern name:** `final emission repairs`
- **Runtime owner:** `game/final_emission_repairs.py`
- **Practical primary direct-owner suite:** `tests/test_final_emission_repairs.py`
- **Secondary downstream suites:** `tests/test_fallback_behavior_repairs.py`, `tests/test_fallback_behavior_gate.py`, `tests/test_bounded_partial_quality.py`, `tests/test_social_fallback_leak_containment.py` — fallback, gate, retry, quality, and leak **consumers** of repaired outputs and metadata only.
- **Compatibility / support residue:** downstream suites may call `repair_fallback_behavior(...)` as a black box or observe repair-shaped metadata without re-owning derivation helpers.
- **Governance note:** repair derivation and private helper semantics stay in the direct-owner suite; adjacent files stay framed as downstream consumption.

## Final Emission Metadata Packaging

- Canonical owner module: `game/final_emission_meta.py`
- Non-owner supporting modules: `game/final_emission_gate.py`, `game/final_emission_repairs.py`
- Current state: `governance-aligned; drift-watch`
- **Concern name:** `final emission metadata packaging`
- **Runtime owner:** `game/final_emission_meta.py`
- **Practical primary direct-owner suite:** `tests/test_final_emission_meta.py`
- **Secondary downstream suites:** gate, validator, and emission suites that assert packaged `_final_emission_meta` outcomes without owning merge/schema policy.
- **Compatibility / support residue:** historical tests may touch both gate and meta; treat meta helpers as write-time/read-side packaging, subordinate to gate orchestration.
- **Non-owner adjacent modules:** `game/final_emission_gate.py`, `game/final_emission_repairs.py` (not metadata-schema owners).
- **Belongs in runtime owner:** metadata-only field defaults, merge helpers, slimming/coercion, stable packaging/read-side helpers for `_final_emission_meta`.
- **Does not belong in runtime owner:** gate sequencing, validator decisions, repair control flow, prompt-contract ownership.

## Stage Diff Telemetry

- Canonical owner module: `game/stage_diff_telemetry.py`
- Non-owner supporting modules: `game/turn_packet.py`, `game/final_emission_gate.py`
- Current state: `governance-aligned; drift-watch`
- **Concern name:** `stage diff telemetry`
- **Runtime owner:** `game/stage_diff_telemetry.py`
- **Practical primary direct-owner suite:** `tests/test_stage_diff_telemetry.py`
- **Secondary downstream suites:** `tests/test_turn_packet_stage_diff_integration.py`, `tests/test_narrative_authenticity_aer4.py`
- **Compatibility / support residue:** `game.stage_diff_telemetry.resolve_gate_turn_packet(...)` as a compatibility wrapper over packet-owned resolution; packet/gate/retry consumers may read emitted telemetry without owning snapshot/diff helper semantics.
- **Packet-boundary owner (related seam):** `game/turn_packet.py` owns the packet contract; it is not the telemetry semantic owner.
- **Non-owner adjacent modules:** `game/turn_packet.py`, `game/final_emission_gate.py` (not parallel telemetry schema authorities).
- **Belongs in runtime owner:** bounded stage snapshots, transition records, compact previews/fingerprints, telemetry merge/write helpers.
- **Does not belong in runtime owner:** canonical packet contract definition, engine truth, narration-policy ownership.
- **Governance note:** describe as `runtime owner → direct-owner suite → downstream suites`, with `game/turn_packet.py` explicit as packet-boundary owner, not telemetry co-owner.

## Turn Packet Contract Boundary

- Canonical owner module: `game/turn_packet.py`
- Non-owner supporting modules: `game/stage_diff_telemetry.py`, `game/final_emission_gate.py`
- Current state: `governance-aligned; drift-watch`
- **Concern name:** `turn packet contract boundary`
- **Runtime owner:** `game/turn_packet.py`
- **Practical primary direct-owner suite:** focused packet tests (e.g. `tests/test_turn_packet_accessors.py` and related modules per `tests/TEST_AUDIT.md` / inventory).
- **Secondary downstream suites:** gate, telemetry integration, and narrative-authenticity suites that consume resolved packets without owning packet schema policy.
- **Compatibility / support residue:** telemetry compatibility wrappers that delegate packet resolution to this owner.
- **Non-owner adjacent modules:** `game/stage_diff_telemetry.py`, `game/final_emission_gate.py` (not packet-contract owners).
- **Belongs in runtime owner:** compact versioned packet construction, accessors, packet fallback resolution, declared packet lookup order.
- **Does not belong in runtime owner:** telemetry ownership, gate orchestration, validator/repair behavior.

## Unified State Authority Model

- Canonical owner module: `game/state_authority.py`
- Non-owner supporting modules: `game/storage.py`, `game/world.py`, `game/interaction_context.py`, `game/narration_visibility.py`, `game/scene_state_anchoring.py`, `game/prompt_context.py`, `game/journal.py`, `game/api.py` (domain mutators, lazy session roots, and publication paths remain in these modules; `state_authority` stays **registry + guard helpers only**)
- Current state: `governance-aligned; Objective #3 shipped—registry/guards locked by tests/test_state_authority.py; further call sites are drift-watch only`
- **Concern name:** `unified state authority (runtime domains)`
- **Runtime owner:** `game/state_authority.py` for domain ids, `StateDomainSpec` registry, read matrix, cross-domain write allow-list, and deterministic guard helpers (`assert_owner_can_mutate_domain`, `assert_cross_domain_write_allowed`, `build_state_mutation_trace`)
- **Practical primary direct-owner suite:** `tests/test_state_authority.py` — registry shape, read matrix, allow-list operations (including `journal_merge_revealed_hidden_facts` and `interaction_state` → `scene_state` edges), pseudo-owner rejection, and **documented deferrals** (`_scene_state` lazy init, `get_interaction_context` first-touch init)
- **Secondary downstream suites:** domain-owner suites (`tests/test_interaction_context.py`, `tests/test_world_state.py`, `tests/test_validation_journal_affordances.py`, `tests/test_world_updates_and_clue_normalization.py`, `tests/test_prompt_context.py`, pipeline suites) own runtime behavior; they assert guards where wired without replacing the registry contract
- **Compatibility / support residue:** lazy session-root helpers may materialize dicts before guarded owner entry points; that is an **intentional scope boundary**, not a second policy home—see `docs/state_authority_model.md` *Shipped guard adoption* / *Intentionally deferred*
- **Non-owner adjacent modules:** `game/prompt_context.py`, `game/gm.py` (must not become alternate declarative owners of domain policy; prompts, narration text, and model I/O stay non-authoritative for mutating authoritative domains)
- **Belongs in runtime owner:** domain constants, `StateDomainSpec` rows, `can_domain_read_domain`, cross-domain write allow-list entries, `StateAuthorityError` messages, compact mutation trace builder
- **Does not belong in runtime owner:** world/scene/session persistence logic, prompt assembly, visibility math, CTIR semantics, emission repairs
- **Publication seam (owner adjacent):** `game/journal.py` — `hidden_state` → `player_visible_state` via `journal_merge_revealed_hidden_facts` (cross-domain) plus same-domain `player_visible_state` owner check for `journal_known_facts_merge` traces; `known_facts` remains derived only
- **Governance note:** describe as `runtime owner (registry + guards) → tests/test_state_authority.py → guarded canonical mutators / publication seams`, not prompt-centered or GPT-centered state policy

## Test Inventory And Governance Docs

- Canonical owner module: `tests/TEST_AUDIT.md`
- Non-owner supporting modules: `tests/README_TESTS.md`, `tests/TEST_CONSOLIDATION_PLAN.md`, `tools/test_audit.py`
- Current state: `governance map; refresh inventory with tools/test_audit.py`
- **Concern name:** `test inventory / governance docs`
- **Runtime owner:** (prose contract) `tests/TEST_AUDIT.md` — canonical **map** of where pytest coverage should land by theme.
- **Practical primary direct-owner suite:** governance tables and notes in `tests/TEST_AUDIT.md`; regenerate numbers via `tools/test_audit.py` → `tests/test_inventory.json`.
- **Secondary downstream suites:** `tests/README_TESTS.md` (how to run), `tests/TEST_CONSOLIDATION_PLAN.md` (campaign / execution history), `tools/test_audit.py` (inventory generator only).
- **Compatibility / support residue:** dated markdown snapshots coexisting with JSON inventory until refreshed; heuristic tags may over-count files touching a theme—interpret as spread diagnostics, not proof of duplicate tests.
- **Forbidden owner interpretations:** README is not the canonical governance map; `test_audit.py` is not the prose authority for suite semantics; consolidation plan is not the day-to-day ledger.
- **Belongs here:** ownership map for test themes, overlap-hotspot guidance, language for where new tests should live.
- **Does not belong here:** long procedural command reference (defer to README), inventory implementation details, long-range consolidation execution steps.
- **Authority note:** subordinate maps must mirror runtime owners and practical direct-owner suites from this ledger, not compete as a higher authority layer.
- **Prompt pointer:** for prompt contracts, `tests/TEST_AUDIT.md` points first to `game/prompt_context.py` and `tests/test_prompt_context.py`, then lists downstream suites as consumers.
