# Architecture Ownership Ledger

This ledger is the repo-facing declaration of ownership for ambiguous seams.

## Operator Note

Ownership declarations do **not** prove the code is already clean.

They establish the cleanup target: future moves, trims, and test/doc realignment should converge toward the owners declared here.

If current code shape still contradicts a declaration, treat that contradiction as cleanup work to reduce, not as a reason to blur the boundary again.

## Response Policy Contracts

- Concern name: `response policy contracts`
- Canonical owner module: `game/response_policy_contracts.py`
- Non-owner supporting modules: `game/final_emission_repairs.py`, `game/final_emission_gate.py`, `game/prompt_context.py`
- Forbidden owner interpretations: `game/final_emission_repairs.py` is not the contract authority; `game/final_emission_gate.py` is not the place to redefine contract rules; `game/prompt_context.py` is not the canonical home for post-prompt contract resolution helpers.
- Belongs here: response-policy contract shape builders, resolution helpers, and read-only contract accessors that tell downstream layers what was shipped.
- Does not belong here: validator verdicts, repair strategies, layer ordering, or final-emission metadata packaging.
- Compatibility residue still allowed: private compatibility accessors may remain importable, and top-level `fallback_behavior` / `social_response_structure_contract` fallbacks may remain supported for older payload shapes.
- Compatibility residue interpretation: these paths are tolerated read-side residue, not equal semantic homes or a reason to re-center authority on repair, gate, validator, or prompt-adjacent modules.
- Practical primary direct-owner suite: `tests/test_response_policy_contracts.py`
- Secondary response-policy coverage only: `tests/test_fallback_shipped_contract_propagation.py`, `tests/test_response_delta_requirement.py`, `tests/test_final_emission_gate.py`, `tests/test_social_exchange_emission.py`, `tests/test_final_emission_validators.py`, `tests/test_interaction_continuity_contract.py`, `tests/test_interaction_continuity_validation.py`
- Governance note: docs should describe this seam as `runtime owner -> direct-owner suite -> downstream secondary coverage`, not as repair-, validator-, or gate-centered co-ownership.
- Current state: `targeted cleanup in progress`

## Prompt Contracts

- Concern name: `prompt contracts`
- Canonical owner module: `game/prompt_context.py`
- Non-owner supporting modules: `game/prompt_context_leads.py`, `game/response_policy_contracts.py`
- Forbidden owner interpretations: `game/prompt_context_leads.py` is not a second prompt-contract owner; `game/response_policy_contracts.py` is not the owner of the full prompt-context bundle.
- Belongs here: prompt-context assembly, prompt-facing contract bundling, and deterministic export of the contract payload that narration receives.
- Does not belong here: extracted lead-only helper logic as a rival owner, validator/repair policy, or emit-order orchestration.
- Compatibility residue still allowed: support-only extraction residue may remain in `game/prompt_context_leads.py`, and exported consumer paths may continue to consume prompt-owned bundles without becoming prompt owners themselves.
- Compatibility residue interpretation: those paths are support/consumption residue, not equal semantic homes or a reason to re-center prompt authority away from `game/prompt_context.py`.
- Practical primary direct-owner suite: `tests/test_prompt_context.py`
- Secondary prompt coverage only: `tests/test_prompt_compression.py`, `tests/test_prompt_and_guard.py`, `tests/test_dialogue_interaction_establishment.py`, `tests/test_fallback_shipped_contract_propagation.py`, `tests/test_social_escalation.py`, `tests/test_social_interaction_authority.py`, `tests/test_social_speaker_grounding.py`, `tests/test_social_topic_anchor.py`, `tests/test_stale_interlocutor_invalidation_block3.py`, `tests/test_strict_social_answer_pressure_cashout.py`, `tests/test_synthetic_sessions.py`, `tests/test_answer_completeness_rules.py`, `tests/test_turn_pipeline_shared.py`, plus relevant gate/emission/transcript suites such as `tests/test_final_emission_gate.py`, `tests/test_social_exchange_emission.py`, and `tests/test_narration_transcript_regressions.py`
- Governance note: docs should describe this seam as `runtime owner -> direct-owner suite -> downstream secondary coverage`, not as several equal prompt authorities.
- Current state: `targeted cleanup in progress`

## Strict-social Exchange Emission Seam

- Concern name: `strict-social exchange emission seam`
- Canonical owner module: `game/social_exchange_emission.py`
- Non-owner supporting modules: `game/final_emission_gate.py`, `game/gm.py`, `game/gm_retry.py`
- Forbidden owner interpretations: `game/gm.py` is not the semantic owner of terminal strict-social dialogue application; `game/gm_retry.py` is not a second authority for the seam just because retry-terminal wiring passes through it; `game/final_emission_gate.py` is not the place to redefine strict-social exchange emission semantics.
- Belongs here: downstream strict-social exchange emission normalization, ownership filtering, deterministic fallback shaping, and terminal dialogue application once the dialogue-contract verdict is already known.
- Does not belong here: canonical response-policy contract resolution, general repair governance, or top-level gate orchestration.
- Compatibility residue still allowed: the legacy `repair_strict_social_terminal_dialogue_fallback_if_needed(...)` helper may remain importable as an explicit compatibility alias.
- Compatibility residue interpretation: historical-path coverage for that alias should stay labeled as compatibility evidence, not as a reason to treat retry/repair-heavy suites as co-equal semantic owners.
- Practical primary direct-owner suite: `tests/test_social_exchange_emission.py`
- Secondary strict-social exchange coverage only: `tests/test_strict_social_emergency_fallback_dialogue.py`, `tests/test_social_emission_quality.py`, `tests/test_dialogue_interaction_establishment.py`
- Governance note: docs should describe this seam as `runtime owner -> direct-owner suite -> downstream secondary / compatibility coverage`, not as mixed emission-vs-repair co-ownership.
- Current state: `targeted cleanup in progress`

## Final Emission Gate Orchestration

- Concern name: `final emission gate orchestration`
- Canonical owner module: `game/final_emission_gate.py`
- Non-owner supporting modules: `game/final_emission_repairs.py`, `game/final_emission_meta.py`
- Forbidden owner interpretations: `game/final_emission_meta.py` is not the orchestration owner; `game/final_emission_repairs.py` is not the top-level layer-order authority.
- Belongs here: final-emission layer ordering, gate-level integration, last-mile finalize flow, and calls into validators, repairs, sanitizer, and metadata packaging.
- Does not belong here: canonical metadata schema ownership, standalone contract-authority logic, or telemetry ownership.
- Compatibility residue still allowed: `game/final_emission_meta.py` may remain as metadata packaging / read-side support, and retry / observability / pipeline-adjacent consumers may continue to pass through the gate without becoming orchestration owners.
- Compatibility residue interpretation: metadata packaging/read-side helpers and retry/telemetry/pipeline adjacency are support-only residue, not equal orchestration homes.
- Practical primary direct-owner suite: `tests/test_final_emission_gate.py`
- Secondary downstream coverage only: `tests/test_social_exchange_emission.py`, `tests/test_turn_pipeline_shared.py`, `tests/test_stage_diff_telemetry.py`, `tests/test_social_emission_quality.py`, `tests/test_dead_turn_detection.py`, plus transcript/regression suites such as `tests/test_narration_transcript_regressions.py`
- Governance note: docs should describe this seam as `runtime owner -> direct-owner suite -> downstream secondary / support coverage`, not as mixed gate/meta/telemetry/pipeline co-ownership.
- Current state: `targeted cleanup in progress`

## Final Emission Metadata Packaging

- Concern name: `final emission metadata packaging`
- Canonical owner module: `game/final_emission_meta.py`
- Non-owner supporting modules: `game/final_emission_gate.py`, `game/final_emission_repairs.py`
- Forbidden owner interpretations: `game/final_emission_gate.py` is not the metadata-schema owner; `game/final_emission_repairs.py` is not the place to define durable `_final_emission_meta` field shapes.
- Belongs here: metadata-only field defaults, merge helpers, slimming/coercion helpers, and stable packaging/read-side helpers for `_final_emission_meta`.
- Does not belong here: gate sequencing, validator decisions, repair control flow, or prompt-contract ownership.
- Current state: `targeted cleanup in progress`

## Stage Diff Telemetry

- Concern name: `stage diff telemetry`
- Canonical owner module: `game/stage_diff_telemetry.py`
- Non-owner supporting modules: `game/turn_packet.py`, `game/final_emission_gate.py`
- Forbidden owner interpretations: `game/turn_packet.py` is not the telemetry owner; `game/final_emission_gate.py` is not a parallel telemetry schema authority.
- Belongs here: bounded stage snapshots, transition records, compact previews/fingerprints, and telemetry merge/write helpers.
- Does not belong here: canonical packet contract definition, engine truth, or narration-policy ownership.
- Current state: `targeted cleanup in progress`

## Turn Packet Contract Boundary

- Concern name: `turn packet contract boundary`
- Canonical owner module: `game/turn_packet.py`
- Non-owner supporting modules: `game/stage_diff_telemetry.py`, `game/final_emission_gate.py`
- Forbidden owner interpretations: `game/stage_diff_telemetry.py` is not the packet-contract owner; `game/final_emission_gate.py` is not a second packet schema home.
- Belongs here: compact versioned packet construction, packet accessors, packet fallback resolution, and the declared packet lookup order for consumers.
- Does not belong here: telemetry ownership, gate orchestration, or validator/repair behavior.
- Current state: `targeted cleanup in progress`

## Test Inventory And Governance Docs

- Concern name: `test inventory / governance docs`
- Canonical owner module: `tests/TEST_AUDIT.md`
- Non-owner supporting modules: `tests/README_TESTS.md`, `tests/TEST_CONSOLIDATION_PLAN.md`, `tools/test_audit.py`
- Forbidden owner interpretations: `tests/README_TESTS.md` is not the canonical governance map; `tools/test_audit.py` is not the prose authority for suite governance by itself; `tests/TEST_CONSOLIDATION_PLAN.md` is not the day-to-day ownership ledger.
- Belongs here: canonical ownership map for test themes, overlap-hotspot guidance, and governance language about where new tests should live.
- Does not belong here: procedural command reference, implementation details of inventory generation, or long-range consolidation execution steps.
- Authority note: these docs are subordinate governance maps. They should mirror runtime owners and practical direct-owner suites rather than act as a second authority layer above them.
- Prompt-governance note: for prompt contracts, `tests/TEST_AUDIT.md` should point first to `game/prompt_context.py` and `tests/test_prompt_context.py`, then classify `tests/test_prompt_compression.py`, `tests/test_prompt_and_guard.py`, `tests/test_strict_social_answer_pressure_cashout.py`, `tests/test_synthetic_sessions.py`, `tests/test_answer_completeness_rules.py`, `tests/test_turn_pipeline_shared.py`, `tests/test_final_emission_gate.py`, `tests/test_social_exchange_emission.py`, and `tests/test_narration_transcript_regressions.py` as secondary coverage.
- Current state: `targeted cleanup in progress`
