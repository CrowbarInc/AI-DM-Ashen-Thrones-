# CB3 Caution Domain Guardrails

**Block:** CB3 — Caution Domain Guardrail Template  
**Registry:** [`CB_feature_boundary_registry.json`](CB_feature_boundary_registry.json)  
**Guardrail catalog:** [`CB_feature_boundary_guardrails.md`](CB_feature_boundary_guardrails.md)  
**Safe pilot precedent:** [`CB2_safe_domain_pilot.md`](CB2_safe_domain_pilot.md)  
**Generated:** 2026-06-23

This document converts **caution**-domain feature work from ad hoc review into repeatable governance. Every caution domain has a minimum validation bundle, replay-smoke decision rules, and escalation criteria.

---

## Guardrail matrix

| Domain | Risk Level | Required Tests | Replay Smoke Required | Protected Field Review Required | Escalation Trigger | Approval Path |
|---|---|---|---|---|---|---|
| `world_scenes_affordances` | **Medium** | Unit: `tests/test_world_*.py`, `tests/test_affordance_*.py`, `tests/test_scene_*.py`. Integration: `tests/test_exploration_resolution.py`, `tests/test_clue_*.py`, `tests/test_lead_*.py`. Ownership: `tests/test_world_simulation_backbone_ownership.py` when backbone touched. | **Conditional** — required when player-visible choices, affordances, or scene state in replay fixtures change | **Conditional** — when prompt context or long-session fixture observations may shift (`resolution_kind`, scene-derived facts) | Import or edit `game/final_emission*`, `game/fallback*`, `game/speaker*`, `game/response_policy*`; changes `data/scenes/**` used by protected golden replay spines | Owner review → replay smoke if triggered → audit if protected fixture drift |
| `state_storage_persistence` | **Medium–High** | Unit: `tests/test_state_authority.py`, `tests/test_state_channels.py`. Integration: `tests/test_save_load.py`, `tests/test_snapshots.py`, `tests/test_campaign_*.py`, `tests/test_runtime_persistence_regression_suite_obj14.py`. Ownership: `tests/test_state_authority.py` guard contract | **Conditional** — required when reset/storage/default semantics or replay harness storage layout change | **Conditional** — when session persistence affects turn observations loaded by replay (`final_text` indirect via state publication) | Broad `game/defaults.py` churn; schema change without rollback plan; import `game/final_emission*` or replay helpers | Owner review + rollback tests → replay smoke if harness semantics move → audit for default-state churn |
| `prompt_ctir_planning` | **Medium–High** | Unit: `tests/test_prompt_context*.py`, `tests/test_ctir_*.py`, `tests/test_turn_packet_*.py`. Integration: `tests/test_planner_*.py`, `tests/test_narrative_*.py`, `tests/test_ctir_pipeline_integration.py`. Boundary: `tests/test_prompt_context_ctir_boundary.py`, `tests/test_ctir_turn_packet_boundary.py`. Ownership: ledger prompt + CTIR direct-owner suites | **Conditional** — required when resolved-turn meaning, prompt bundle fields, or narration inputs change | **Yes** when changes can reach `final_text`, `resolution_kind`, `response_type_*`, or mutation lineage fields | Silent semantic rewrite at prompt/final-emission boundary; new imports from `game/final_emission*`, `game/response_policy*` | Owner review + contract map → replay smoke when turn meaning shifts → **prohibited** if editing gate/emission modules |
| `social_interaction_routing` | **High** | Unit: `tests/test_social*.py`, `tests/test_interaction_*.py`, `tests/test_dialogue_*.py`. Integration: `tests/test_broadcast_open_call_social.py`, `tests/test_directed_social_routing.py`, `tests/test_social_exchange_emission.py`. Ownership: `tests/test_social_exchange_emission.py` for strict-social seam | **Yes** for route/speaker/target changes; **conditional** for context-only edits with documented negative case | **Yes** for `selected_speaker_id`, `route_kind`, `trace.social_contract_trace.route_selected`, `trace.canonical_entry.*` | Any edit to `game/speaker*`, `game/final_emission*`, fallback shaping on social path; strict-social emission behavior change | Owner review + social direct-owner suite → **mandatory** targeted golden structural scenario(s) → prohibited if speaker contract modules touched |
| `api_turn_orchestration` | **High** | Unit: focused `tests/test_api_*.py` slices. Integration: `tests/test_turn_pipeline_shared.py`, `tests/test_start_campaign_api.py`, transcript/gauntlet neighbors per `tests/TEST_AUDIT.md`. Ownership: `tests/test_ownership_registry.py` when moving orchestration | **Yes** for orchestration, retry, or finalization path edits; **conditional** for narrow API surface additions delegating to leaf modules | **Yes** when change touches finalization entrypoints, retry/fallback routing, or post-emission adoption | New logic in `game/gm.py` / `game/gm_retry.py` for policy/fallback/sanitizer; import prohibited modules; broad `game/api.py` refactor | Owner review → prefer leaf-module implementation → replay smoke via pipeline integration → **prohibited** if emit-path cores edited |
| `telemetry_diagnostics_audit` | **Low–Medium** | Unit: `tests/test_stage_diff_telemetry.py`, `tests/test_runtime_lineage_telemetry.py`. Integration: `tests/test_attribution_*.py`, `tests/test_*report*.py`. Ownership: report contract tests for touched tooling | **Conditional** — required when metrics feed protected replay trend windows (BW/BZ), recurrence history, or bug-locality measurements | **Conditional** — when attribution reads owner/fallback/policy metadata consumed by protected projection | Edit `tests/helpers/golden_replay*`, `tools/run_protected_replay_trend.py`, recurrence schema, or `PROTECTED_OBSERVATION_FIELDS` source | Owner review → CB5 metric-stability check for schema/history → **prohibited** if replay governance paths touched |

---

## Per-domain minimum validation bundles

Each bundle satisfies **CAUTION_G1** (scope) and **CAUTION_G3** (high-coupling contract). **CAUTION_G2** (replay smoke) applies per matrix column above.

### 1. `world_scenes_affordances`

| Category | Requirement |
|---|---|
| **Primary owners** | `game/world.py`, `game/affordances.py`, `game/exploration.py`; world progression seam per `docs/system_overview.md` |
| **Primary tests** | `tests/test_world_*.py`, `tests/test_scene_*.py`, `tests/test_affordance_*.py`, `tests/test_clue_*.py`, `tests/test_lead_*.py`, `tests/test_exploration_resolution.py` |
| **Replay dependencies** | Scene/world state feeds prompt context and long-session fixtures (`frontier_gate_social_inquiry_25_turn` source material) |
| **Protected observation deps** | Indirect: `resolution_kind`, scene-derived player-visible facts; not primary owner of `final_text` |
| **Speaker dependencies** | Moderate via interaction context and social continuity visible-fact selection |
| **Fallback dependencies** | Moderate via fallback visible-fact selection paths |
| **Required tests — unit** | At least one direct-owner suite matching touched module (`test_affordance_*`, `test_world_*`, etc.) |
| **Required tests — integration** | `tests/test_exploration_resolution.py` when exploration/affordance resolution changes |
| **Required tests — replay smoke** | See [Replay smoke standard](#replay-smoke-standard); e.g. `tests/test_narration_transcript_regressions.py` slice or long-session subset when fixture-adjacent |
| **Required tests — ownership** | `tests/test_world_simulation_backbone_ownership.py` when world backbone invariants touched |
| **Required evidence** | Files touched; imports added; data fixture refs (`data/scenes/**`, `data/world.json`); replay-smoke decision note |
| **Required review** | Domain owner review; audit review if protected long-session source data changes |

### 2. `state_storage_persistence`

| Category | Requirement |
|---|---|
| **Primary owners** | `game/state_authority.py` (registry + guards only), `game/storage.py`, `game/session.py`, `game/campaign_state.py` |
| **Primary tests** | `tests/test_state_authority.py`, `tests/test_save_load.py`, `tests/test_snapshots.py`, `tests/test_runtime_persistence_regression_suite_obj14.py` |
| **Replay dependencies** | Golden replay harness storage layout, reset semantics, campaign/session bootstrap |
| **Protected observation deps** | Indirect via persisted state loaded into replay turns |
| **Speaker dependencies** | Low direct; moderate via `interaction_context` persistence |
| **Fallback dependencies** | Low direct; session state may influence fallback triggers upstream |
| **Required tests — unit** | `tests/test_state_authority.py` for guard/registry edits; `tests/test_state_channels.py` for channel semantics |
| **Required tests — integration** | `tests/test_save_load.py` + `tests/test_snapshots.py` for persistence; `tests/test_campaign_*.py` for campaign lifecycle |
| **Required tests — replay smoke** | Required when `game/defaults.py`, `game/storage.py`, or reset paths change; run persistence regression suite + optional `python -m pytest -m golden_replay -q` spot check |
| **Required tests — ownership** | `tests/test_state_authority.py` documents deferrals and guard adoption |
| **Required evidence** | Rollback plan; replay-harness awareness note; no broad schema churn statement |
| **Required review** | Owner review; audit review for `defaults.py` or cross-domain write allow-list changes |

### 3. `prompt_ctir_planning`

| Category | Requirement |
|---|---|
| **Primary owners** | `game/prompt_context.py`, `game/ctir.py`, `game/ctir_runtime.py`, `game/turn_packet.py`; `game/api.py` for CTIR build timing |
| **Primary tests** | `tests/test_prompt_context.py`, `tests/test_ctir_pipeline_integration.py`, `tests/test_prompt_context_ctir_boundary.py`, `tests/test_ctir_turn_packet_boundary.py` |
| **Replay dependencies** | CTIR and prompt changes shift replay output and trend windows |
| **Protected observation deps** | `final_text`, `resolution_kind`, `response_type_*`, `final_emission_mutation_lineage` (downstream) |
| **Speaker dependencies** | Moderate via prompt social grounding and dialogue contracts |
| **Fallback dependencies** | Moderate via response-policy reads in prompt bundle |
| **Required tests — unit** | Direct-owner suite for touched owner (`test_prompt_context*`, `test_ctir_*`, `test_turn_packet_*`) |
| **Required tests — integration** | `tests/test_ctir_pipeline_integration.py`, `tests/test_planner_*` when planning packaging changes |
| **Required tests — replay smoke** | Required when resolved-turn shape or prompt exports change; `tests/test_prompt_context_ctir_consumption.py` minimum, plus transcript or golden slice if player-visible |
| **Required tests — ownership** | Boundary suites (`test_prompt_context_ctir_boundary.py`, `test_ctir_turn_packet_boundary.py`) |
| **Required evidence** | Contract test map; CTIR vs prompt adapter framing; protected-field impact on `final_text` / `resolution_kind` |
| **Required review** | Owner review per ledger seam; audit if convergence toward final-emission boundary |

### 4. `social_interaction_routing`

| Category | Requirement |
|---|---|
| **Primary owners** | `game/social_exchange_emission.py` (strict-social seam), `game/interaction_context.py` |
| **Primary tests** | `tests/test_social_exchange_emission.py`, `tests/test_interaction_*.py`, `tests/test_directed_social_routing.py`, `tests/test_broadcast_open_call_social.py` |
| **Replay dependencies** | Protected scenarios: `directed_npc_question`, `vocative_override_after_prior_continuity`, `wrong_speaker_strict_social_emission`, `lead_followup_with_dialogue_lock`, `frontier_gate_social_inquiry_25_turn` |
| **Protected observation deps** | `selected_speaker_id`, `route_kind`, `trace.social_contract_trace.route_selected`, `trace.canonical_entry.target_actor_id`, `trace.canonical_entry.target_source`, `trace.canonical_entry.reason` |
| **Speaker dependencies** | **High** — adjacent to prohibited `speaker_identity_adoption` domain |
| **Fallback dependencies** | **High** — strict-social fallback shaping, `sanitizer_strict_social_*` fields |
| **Required tests — unit** | `tests/test_social*.py`, `tests/test_dialogue_*.py` matching touched behavior |
| **Required tests — integration** | `tests/test_social_exchange_emission.py` for emission seam; routing tests for target/route changes |
| **Required tests — replay smoke** | **Mandatory** for route/speaker changes — at least one matching `tests/test_golden_replay_structural_invariants.py` scenario |
| **Required tests — ownership** | `tests/test_social_exchange_emission.py`; no new co-equal emission owners |
| **Required evidence** | Route/speaker/fallback field impact assessment; protected replay probe plan |
| **Required review** | Owner review; audit review when strict-social or protected speaker scenarios affected |

### 5. `api_turn_orchestration`

| Category | Requirement |
|---|---|
| **Primary owners** | `game/api.py` (orchestration), `game/gm.py`, `game/gm_retry.py` (compatibility surfaces) |
| **Primary tests** | `tests/test_turn_pipeline_shared.py`, `tests/test_start_campaign_api.py`, focused `tests/test_api_*.py` |
| **Replay dependencies** | E2E replay and transcript tests flow through API/GM lane |
| **Protected observation deps** | **High** — orchestration chooses narration, retry, fallback, sanitizer, and finalization entrypoints |
| **Speaker dependencies** | **High** — post-emission adoption and narration path selection |
| **Fallback dependencies** | **High** — retry and fallback lane selection |
| **Required tests — unit** | Narrow `tests/test_api_*` module for the specific endpoint or helper changed |
| **Required tests — integration** | `tests/test_turn_pipeline_shared.py` minimum; transcript suite when turn output changes |
| **Required tests — replay smoke** | Required for orchestration/retry/finalization edits; `python -m pytest tests/test_turn_pipeline_shared.py -q` plus golden slice or `-m golden_replay` subset |
| **Required tests — ownership** | `tests/test_ownership_registry.py` when moving orchestration; verify no BA-7 magnet imports |
| **Required evidence** | Leaf-module delegation plan; emit-path entrypoint unchanged statement or escalation note |
| **Required review** | Owner review; audit if retry/fallback/finalization wiring moves |

### 6. `telemetry_diagnostics_audit`

| Category | Requirement |
|---|---|
| **Primary owners** | `game/stage_diff_telemetry.py`, `game/runtime_lineage_telemetry.py`, `tools/test_audit.py`, `tests/TEST_AUDIT.md` |
| **Primary tests** | `tests/test_stage_diff_telemetry.py`, `tests/test_runtime_lineage_telemetry.py`, `tests/test_attribution_*.py` |
| **Replay dependencies** | Trend windows (BW/BZ), recurrence history, bug-locality measurements when schema changes |
| **Protected observation deps** | Low for additive reports; **high** if editing projection or manifest refresh tooling |
| **Speaker dependencies** | Moderate when attribution reads speaker/fallback owner metadata |
| **Fallback dependencies** | Moderate when attribution reads fallback incidence or owner buckets |
| **Required tests — unit** | Direct-owner telemetry suite for touched module |
| **Required tests — integration** | Report contract test (`tests/test_*report*.py`) for new/changed report fields |
| **Required tests — replay smoke** | Not required for additive read-only reports; **required** when touching `tools/*trend*`, `tools/*recurrence*`, or artifacts consumed by BZ/BW |
| **Required tests — ownership** | Verify tooling does not become alternate replay authority |
| **Required evidence** | Additive vs schema-changing classification; append-only / trend-window impact note |
| **Required review** | Owner review; audit (CB5) for metric history or trend-window schema changes |

---

## Escalation rules (Caution → Prohibited)

Stop caution workflow and switch to **PROHIBITED_G1–G3** when any of the following occur:

| # | Escalation trigger | Prohibited domain entered | Required action |
|---|---|---|---|
| E1 | Diff touches `game/final_emission*.py` (except constant-only imports — see CB2 note) | `final_emission_core` | Named audit approval; protected replay; ownership review |
| E2 | Diff touches `game/fallback_behavior.py`, `game/output_sanitizer.py`, `game/upstream_response_repairs.py`, or `game/final_emission_*fallback*.py` | `fallback_sanitizer_repairs` | BV1 incidence note; protected replay; audit approval |
| E3 | Diff touches `game/speaker_contract_enforcement.py`, `game/emitted_speaker_signature.py`, `game/post_emission_speaker_adoption.py` | `speaker_identity_adoption` | BX/BT parity evidence; golden replay |
| E4 | Diff touches `game/response_policy_contracts.py`, `game/response_policy_enforcement.py`, or manifest | `response_policy_contracts` | Mutation snapshots; protected replay |
| E5 | Diff touches `tests/helpers/golden_replay*.py`, `tests/helpers/protected_replay_registry.py`, `tests/test_golden_replay*.py`, manifest refresh tools | `replay_governance` | Manifest-governed change; full `python -m pytest -m golden_replay -q` |
| E6 | Change alters any of the 41 `PROTECTED_OBSERVATION_FIELDS` paths without going through prohibited approval | `replay_governance` + affected emit domain | Manifest refresh; trend-window impact; audit |
| E7 | Introduces new fallback behavior, sanitizer mode, or repair strategy on the emit path | `fallback_sanitizer_repairs` | Stabilization block only |
| E8 | Modifies response policy enforcement or post-GPT mutation | `response_policy_contracts` | Policy block approval |

**Tripwire imports** (in caution-domain files — escalate immediately):

```
game.final_emission*
game.fallback*
game.output_sanitizer
game.upstream_response_repairs
game.speaker_contract_enforcement
game.emitted_speaker_signature
game.post_emission_speaker_adoption
game.response_policy_enforcement
game.response_policy_contracts
tests.helpers.golden_replay*
tests.helpers.protected_replay*
```

**Exception (CB2 refinement):** Importing path constants from caution modules (e.g. `SCENES_DIR` from `game.storage`) does not alone escalate — document constant-only use in PR evidence.

---

## Replay smoke standard

### Purpose

Replay smoke is a **bounded** acceptance check for caution-domain changes that may move player-visible or protected-adjacent observations — without requiring full prohibited-domain approval for every caution edit.

### When required

| Situation | Replay smoke |
|---|---|
| Player-visible choices, affordances, or scene state change | **Required** |
| Resolved-turn / CTIR / prompt export changes | **Required** |
| Social route, target, or speaker selection changes | **Required** (targeted golden scenario) |
| API/GM orchestration, retry, or finalization path changes | **Required** |
| Persistence reset, defaults, or storage layout changes | **Required** |
| Additive telemetry report with no schema/history change | **Not required** |
| Narrow refactor with documented negative protected-field impact | **Not required** (must file negative case in PR) |

### Qualifying replay suites

| Tier | Command / suite | Use when |
|---|---|---|
| **R1 — Targeted structural** | `python -m pytest tests/test_golden_replay_structural_invariants.py::<scenario> -q` | Social route/speaker, sanitizer adjacency, directed dialogue |
| **R2 — Direct seam** | `python -m pytest tests/test_golden_replay_direct_seam.py::<scenario> -q` | Gate-adjacent social alias / dialogue-plan boundaries |
| **R3 — Long session** | `python -m pytest tests/test_golden_replay_long_session.py::test_golden_replay_frontier_gate_social_inquiry_25_turn_structural_stability -q` | Sustained-play / world+social fixture changes |
| **R4 — Pipeline integration** | `python -m pytest tests/test_turn_pipeline_shared.py -q` | API orchestration changes without full golden run |
| **R5 — Transcript slice** | `python -m pytest tests/test_narration_transcript_regressions.py -q` (or named subset) | Prompt/narration context changes |
| **R6 — Full protected** | `python -m pytest -m golden_replay -q` | Escalation to prohibited workflow; pre-merge stabilization |

Pick the **lowest tier** that covers the affected observation families. Document the tier and scenario id in PR evidence.

### Pass/fail criteria

| Result | Criteria |
|---|---|
| **PASS** | Selected suite(s) exit 0; no new protected observation drift in targeted fields |
| **TRIAGE** | Failure in unsupported scenario — document mismatch, confirm out-of-scope, or expand suite tier |
| **FAIL (block)** | Failure in scenario covering the changed behavior; fix or escalate to prohibited approval |
| **ESCALATE** | Drift in `PROTECTED_OBSERVATION_FIELDS` — switch to PROHIBITED_G2 workflow |

### Evidence format

Include in PR or `docs/audits/` note:

```markdown
## Replay smoke (CB3)

- **Domain:** <registry id>
- **Tier:** R1 | R2 | R3 | R4 | R5 | R6
- **Command:** `<exact pytest command>`
- **Observation families at risk:** <field list or "none — negative case">
- **Result:** PASS | TRIAGE | FAIL
- **Output excerpt:** <last 20 lines or link to CI run>
```

---

## PR checklist (caution domains)

Copy into caution-domain PRs:

- [ ] Registry domain id declared (`content_lint_validation` = safe only; one of six caution ids)
- [ ] CAUTION_G1: scoped description + data/fixture refs
- [ ] CAUTION_G3: contract test map + ledger owner cited
- [ ] CAUTION_G2: replay-smoke decision (positive or negative case)
- [ ] Imports scanned against escalation tripwires
- [ ] Protected-field impact assessment completed
- [ ] Minimum validation bundle tests run and listed
- [ ] Owner review obtained (audit review if matrix requires)
