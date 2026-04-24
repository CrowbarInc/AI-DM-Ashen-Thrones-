# Test suite audit (Block 15A, post-AER Block C1 boundary)

Diagnostic inventory of `tests/` only. **How to run tests (fast/full lanes, collect-only, Windows):** `tests/README_TESTS.md`.

**Consolidation phase:** Behavioral Gauntlet, Playability Validation, and AER are **complete** as validation tracks. Emit-path **ownership** for prompt, response-policy, gate, repairs, telemetry, and strict-social emission is **governance-resolved** (singular runtime owner + practical direct-owner suite + intentional downstream consumers per `docs/architecture_ownership_ledger.md`). Optional follow-ups: **transcript** duplicate assertion thinning, deferred **lead/clue** batch, and marker tidy—**without** expanding gameplay behavior in doc-only passes. Runtime **orchestration** layout remains in `docs/narrative_integrity_architecture.md`.

**Terminology (use consistently in PRs and reviews):**

- **Canonical owner** — the primary module or file that should own an invariant end-to-end.
- **Smoke overlap** — a thin cross-layer check where a different harness depth is intentional; not a second full legality suite.
- **Deferred** — explicitly postponed work (for example, lead/clue batch until after prompt/sanitizer + social/emission).
- **Orchestration** — ordering and integration of policy layers (especially `apply_final_emission_gate`), distinct from **pure** validators or **metadata-only** helpers.
- **Deterministic / contract-driven** — tests and evaluators that lock shapes, routes, and contracts—not live-model prose.

**Ownership scan legend (governed seams):** When scanning theme rows and governance notes, read four roles the same way as `docs/architecture_ownership_ledger.md`:

| Role | Meaning |
| --- | --- |
| **Runtime owner** | Canonical `game/` module for the contract or orchestration invariant. |
| **Practical primary direct-owner suite** | Pytest module that should own **direct** semantic assertions for that runtime surface first. |
| **Downstream consumer coverage** | Other suites that ship, observe, or regress behavior **through** the owner boundary; they are not alternate semantic homes. |
| **Compatibility residue** | Supported legacy paths, aliases, or read-side helpers that may remain importable without splitting authority. |

**Regenerate artifacts:** from repo root run `py -3 tools/test_audit.py` (or `python tools/test_audit.py`). That refreshes `tests/test_inventory.json` using `pytest --collect-only` (non-quiet, so full nodeids are captured) plus static heuristics. The script prints a one-line summary of **module-level duplicate `test_*` names** (shadowed defs); details are in JSON under `summary.files_with_shadowed_duplicate_test_defs`. It also prints a short **overlap spread** line (themes by distinct file count; heuristic, not semantic duplicate detection).

**Governance pytest:** after regenerating or editing inventory-sensitive paths, run `py -3 -m pytest tests/test_ownership_registry.py -q`. That module encodes required **direct-owner** groups and allowlisted duplicate-name reasons; it complements the audit script and does **not** replace semantic code review.

**`block_b_overlap_clusters`:** JSON clusters (for example `dense_ownership_theme_by_architecture_layer`, `imports_final_emission_gate_and_prompt_context`) are **triage signals**—many files touching a theme or importing the same gate helpers does **not** prove redundant tests. Use them to spot candidates; decide merges or thinnings with the governance tables in this file and `tests/TEST_CONSOLIDATION_PLAN.md`.

**Smoke vs transcript consolidation examples:** `tests/test_c4_narrative_mode_live_pipeline.py` is scoped as **wiring / orchestration smoke** for the C4 narrative-mode path; `tests/test_narration_transcript_regressions.py` stays a **transcript** home for multi-turn narration behavior while avoiding duplicate **direct-legality** matrices owned elsewhere.

**Machine-readable ownership map (first pass):** each `files[]` row now includes `collected_nodeids`, `collected_test_names`, `shadowed_duplicate_test_names`, `game_import_modules` / `game_import_roots`, `likely_ownership_theme`, `likely_architecture_layer` (one of `engine` / `planner` / `gpt` / `gate` / `evaluator` / `smoke` / `transcript` / `gauntlet`), `architecture_layer_scores`, and `overlap_hints`. Each `tests[]` row adds `keyword_overlap_hints`, `file_overlap_hints`, and the same `likely_*` fields for quick filtering. Top-level `cross_file_duplicate_test_names`, `import_hub_modules`, and `block_b_overlap_clusters` summarize Block B–style overlap without maintaining giant markdown tables.

**Validation layer drift (Objective #11):** For the five-layer phase contract (truth / structure / expression / legality / offline scoring), run `py -3 tools/validation_layer_audit.py` and read `docs/validation_layer_audit.md`. The audit uses `game/validation_layer_contracts.py` plus `docs/validation_layer_separation.md` and surfaces Block B residue as tolerated context; it does not replace semantic review. Smoke tests: `tests/test_validation_layer_audit_smoke.py`.

**Counts in this markdown:** detailed per-file tables drift as the suite grows. For live numbers, prefer `pytest --collect-only` plus `tests/test_inventory.json` (regenerate with `tools/test_audit.py`). Dated sanity snapshots in later sections are **illustrative**; `summary.generated_utc` in JSON is the inventory timestamp. For file totals, read the JSON inventory or count collected modules under `tests/` that match `test_*.py`.

---

## Consolidation Block 1 — Canonical ownership map & overlap hotspots

**Purpose:** Decide *where* behavior should be tested so new assertions have an obvious home and redundant overlap can be trimmed safely in later blocks. This section does **not** require rewriting tests by itself.

### Ownership patterns (use a small set)

| Pattern | Owns | Neighbors should… |
| --- | --- | --- |
| **Focused unit / integration** | Detailed invariants (schemas, single-turn API, pure helpers). | Not re-assert the same invariant end-to-end unless adding a **smoke** check. |
| **`*_regressions.py` / named regression modules** | Historical bug locks and narrow repro contracts. | Not become a second home for **broad** behavioral specification; extend focused files instead. |
| **Transcript / gauntlet / multi-turn harness** | Ordering, cross-turn state, harness wiring, narrative milestones. | **Smoke** integration only for gates already owned by smaller tests; avoid duplicate substring locks on player text. |
| **Full `/api/chat` + `/api/action` pipeline** (`test_turn_pipeline_shared.py`) | Full-stack routing behavior, dialogue-lock **HTTP** regressions, turn-trace-adjacent flow, end-to-end resolution. | Prefer `test_dialogue_routing_lock.py` for **pure** table contracts (no `TestClient`); `test_directed_social_routing.py` for directed-social precedence, vocative overrides, segmentation, narrow directed chat, emergent-actor targeting. |

### Routing consolidation — recorded ownership (Block 3)

The routing pass closed with a **three-module contract** (details: `tests/TEST_CONSOLIDATION_PLAN.md` → *Block 3 — Routing*). **Intentional overlap:** the same phrase may appear in pure-routing and full-pipeline tests when locking **different layers** — not an automatic duplicate to delete.

### Runtime narrative integrity — `game/` layout (Block 4)

The **post–Block 3** split of validators, repairs, targeting helpers, and gate orchestration is summarized for maintainers in **`docs/narrative_integrity_architecture.md`** (where routing, commitment breaks, vocative vs authoritative resolution, contracts, validators, repairs, and `final_emission_gate` orchestration live). Test canonical owners in this file and in `tests/TEST_CONSOLIDATION_PLAN.md` remain the contract for **what to assert where**; the architecture note is the contract for **where runtime code should live**.

### Repair / retry consolidation — applied ownership (Block 3 doc, 2026-04-03)

Cluster **closed enough** for this pass: enforced split and intentional overlap are recorded in `tests/TEST_CONSOLIDATION_PLAN.md` → *Repair / retry cluster — Block 3*. **Next batch:** prompt/sanitizer → social/emission → lead/clue (same plan → *Next consolidation order*).

### Canonical owners by theme

**How to read this table:** the middle column names the **practical primary direct-owner suite(s)** (and occasionally a co-listed peer that owns a **different layer** of the same theme, e.g. routing). The right column lists **downstream consumer / smoke** homes only—they should not accumulate new direct contract semantics for seams already owned in the middle column.

| Theme | Primary direct-owner suite(s) | Downstream / smoke only (examples) |
| --- | --- | --- |
| **Routing / turn pipeline** | `test_turn_pipeline_shared.py` — full **`/api/chat`** and **`/api/action`** stack, dialogue-lock HTTP, turn-trace-adjacent flow, end-to-end resolution; `test_dialogue_routing_lock.py` — pure `choose_interaction_route` / dialogue-lock **table** (no `TestClient`); `test_directed_social_routing.py` — directed-social precedence, vocative overrides, segmentation, narrow directed `/api/chat`, emergent-actor targeting; `test_intent_parser.py` / `test_intent_and_runtime.py` — parse/runtime intent. | `test_mixed_state_recovery_regressions.py`, `test_exploration_resolution.py`, `test_social.py` — keep **narrative or scenario-specific** routing checks, not a second copy of table locks. |
| **Prompt-context assembly / prompt-contract bundle** | `test_prompt_context.py` — practical primary direct-owner suite for direct prompt-contract semantics, canonical prompt-facing helper accessors, and exported helper/bundle ownership; `test_prompt_compression.py` — secondary prompt assembly / compression integration once the bundle shape is already owned. | `test_prompt_and_guard.py`, `test_dialogue_interaction_establishment.py`, `test_fallback_shipped_contract_propagation.py`, `test_social_escalation.py`, `test_social_interaction_authority.py`, `test_social_speaker_grounding.py`, `test_social_topic_anchor.py`, `test_stale_interlocutor_invalidation_block3.py`, `test_strict_social_answer_pressure_cashout.py`, `test_synthetic_sessions.py`, `test_answer_completeness_rules.py`, plus relevant gate/emission/transcript suites such as `test_final_emission_gate.py`, `test_social_exchange_emission.py`, and `test_narration_transcript_regressions.py` — downstream consumer, smoke, or regression checks; they may consume shipped prompt contracts but should not read as the semantic owner. |
| **Response-policy contract read side** | `test_response_policy_contracts.py` — practical primary direct-owner suite for canonical `game.response_policy_contracts` accessors and `materialize_response_policy_bundle()` behavior once policy has already been shipped. | `test_fallback_shipped_contract_propagation.py`, `test_response_delta_requirement.py`, `test_final_emission_gate.py`, `test_social_exchange_emission.py`, `test_final_emission_validators.py`, `test_interaction_continuity_contract.py`, `test_interaction_continuity_validation.py` — downstream compatibility, consumer/application, validator, continuity, and integration coverage only; they may consume shipped response-policy contracts but should not read as the semantic owner. |
| **Final-emission gate orchestration** | `test_final_emission_gate.py` — practical primary direct-owner suite for direct `apply_final_emission_gate` layer ordering, final-route integration, continuity-adjacent gate-step semantics, and orchestration semantics. | `test_social_exchange_emission.py`, `test_turn_pipeline_shared.py`, `test_stage_diff_telemetry.py`, `test_social_emission_quality.py`, `test_dead_turn_detection.py`, `test_final_emission_scene_integrity.py`, `test_interaction_continuity_speaker_bridge.py`, `test_interaction_continuity_validation.py`, `test_interaction_continuity_repair.py`, and transcript/regression suites such as `test_narration_transcript_regressions.py` — downstream emission application, API smoke, telemetry observability, metadata consumption, scene-integrity, bridge/validation/repair consumption, or regression coverage only; they may pass through the gate but should not accumulate new **orchestration-order** ownership there. |
| **Objective #7 referent artifact + compact mirror + post-GM clarity** | `test_referent_tracking.py` — artifact construction/schema; `test_prompt_context.py` — full `referent_tracking` on bundle + **four-field** `referent_tracking_compact` only; `test_final_emission_validators.py` — `validate_referent_clarity` + `_apply_referent_clarity_emission_layer`; `test_final_emission_gate.py` — `_apply_referent_clarity_pre_finalize` / FEM merge. | Other suites remain downstream observability only; do not duplicate artifact derivation or imply compact≡full. Player-facing visibility referential clarity stays under `narration_visibility` suites (`test_referential_clarity_*.py`, etc.). |
| **Final-emission repairs** | Repair semantics: runtime `game.final_emission_repairs`; practical owner suite `tests/test_final_emission_repairs.py` (derivation, helper/accessor semantics, materialization). | Downstream consumption coverage only — e.g. `test_fallback_behavior_repairs.py` (fallback/gate/retry consumers of repaired outputs and meta); `test_fallback_behavior_gate.py`, `test_bounded_partial_quality.py`, `test_social_fallback_leak_containment.py` (gate application, quality, leak/regression); they must not re-own derivation or private repair helpers. |
| **Stage-diff telemetry / observability** | `test_stage_diff_telemetry.py` — practical primary direct-owner suite for direct `game.stage_diff_telemetry` helper/accessor semantics, snapshot/transition packaging, bounded telemetry storage, and telemetry-owned observability fields. | `test_turn_packet_stage_diff_integration.py` — downstream turn-packet + gate/retry consumer coverage; `test_narrative_authenticity_aer4.py` — downstream narrative-authenticity regression and evaluator-consumer coverage. They may consume shipped telemetry fields, but should not read as the semantic owner of stage-diff packaging or helper semantics. |
| **Social escalation / emission / quality** | `test_social_exchange_emission.py` — practical primary direct-owner suite for downstream strict-social exchange emission semantics, including terminal dialogue **application** once dialogue-contract resolution is already decided elsewhere; `test_social_escalation.py` — pressure / escalation state machine; `test_social_answer_retry_prioritization.py` — retry vs stall prioritization; `test_social_target_authority_regressions.py` — authority regressions. | `test_social_emission_quality.py` — multi-turn / quality harness (names `test_emission_quality_*` for non-transcript-runner cases; align module-level `transcript` policy in Block 2); `test_dialogue_interaction_establishment.py` — establishment flows; `test_strict_social_emergency_fallback_dialogue.py` — downstream retry-terminal / first-mention / compatibility-alias coverage only; `test_social.py` — **`resolve_social_action` engine + glue** (see module docstring; not strict-social string owner). |
| **Lead lifecycle / clue / pending / registry** | `test_clue_knowledge.py`, `test_clue_idempotence.py` — clue idempotency / gateway; `test_world_updates_and_clue_normalization.py` — normalization; `test_clue_lead_registry_integration.py` — clue↔lead registry wiring; `test_lead_engine_upsert.py` — engine upsert; `test_follow_lead_commitment_wiring.py` — follow/commitment wiring; focused `test_lead_*.py` modules — obsolescence, payoff, NPC authority, resolution endings, etc.; `test_lead_lifecycle_block3_transcript_regression.py` — **multi-turn** lifecycle story. | `test_social_lead_landing.py`, `test_turn_pipeline_shared.py`, `test_prompt_and_guard.py`, `test_social_exchange_emission.py` — **smoke** or cross-cutting hooks, not a second registry spec. |
| **Transcript / gauntlet vs smaller tests** | `test_transcript_regression.py` — general play-loop / sequencing; `test_transcript_gauntlet_*.py` — slice-specific harness contracts; `test_transcript_runner_smoke.py` — runner wiring; `test_gauntlet_regressions.py` — API-style gauntlet regressions (name ≠ transcript harness). | `test_lead_lifecycle_block3_transcript_regression.py`, `test_mixed_state_recovery_regressions.py` — own their **story**; avoid duplicating single-turn gates covered elsewhere. |
| **Repair / fallback / legality / sanitizer** | **`test_contextual_minimal_repair_regressions.py`** — branch-specific repair behavior, `debug_notes` detail, repair-line legality, scene-anchor vs hard-line (nonsocial), payload-shape guards (no unwanted `clues` / `scene_update` / discoverables). **`test_empty_social_retry_regressions.py`** — retry/fallback wiring, `accepted_via`, `targeted_retry_terminal`, `retry_exhausted`, `fallback_kind` / `final_route`, `_final_emission_meta` continuity, `/api/chat` repair integration; nonsocial empty metadata in `test_ensure_minimal_nonsocial_resolution_fills_empty_text`. **`test_output_sanitizer.py`** — emit-time sanitizer; **`test_prompt_and_guard.py`** — prompt + guard; **`test_debug_payload_spoiler_safety.py`** — spoiler/debug safety. | Same helper may appear in **both** repair regression files when **fixtures differ**; phrase checks may split by **branch/layer** — see consolidation plan *Repair / retry cluster — Block 3*. Pipeline/mixed-state **smoke** only, not parallel legality suites. |

### Overlap hotspots (short list)

### Prompt-contract governance note (PC2-R)

For the prompt seam, treat `game/prompt_context.py` as the canonical runtime owner and
`tests/test_prompt_context.py` as the practical primary direct-owner suite. Keep
`test_prompt_compression.py` as secondary prompt-assembly/compression integration coverage, with
direct exported policy, uncertainty, response-delta, and promoted-interlocutor contract assertions
re-centered in `test_prompt_context.py`. Treat `test_final_emission_gate.py`,
`test_social_exchange_emission.py`, `test_narration_transcript_regressions.py`,
`test_prompt_and_guard.py`, `test_dialogue_interaction_establishment.py`,
`test_fallback_shipped_contract_propagation.py`, `test_social_escalation.py`,
`test_social_interaction_authority.py`, `test_social_speaker_grounding.py`, and
`test_turn_pipeline_shared.py` as downstream evidence that shipped prompt contracts are consumed
correctly. In those downstream suites, prefer local shipped fixtures, module-local wrapper
handles, or smoke assertions over re-importing prompt-owner helper builders when the direct
contract semantics are not under test. For `test_turn_pipeline_shared.py` specifically, keep
prompt-adjacent checks framed as request-shipping, sequencing, trace, and endpoint-integration
coverage rather than prompt-bundle derivation ownership.
Keep social-adjacent suites narrow too: `test_social_escalation.py` should read as escalation /
pressure state-machine coverage, `test_social_interaction_authority.py` as downstream authority /
routing consumption, and `test_social_speaker_grounding.py` as downstream speaker-grounding
consumption. Re-center direct follow-up helper, narration-obligation, uncertainty-lock, and
interlocutor-export ownership assertions in `test_prompt_context.py` when those social suites start
sounding like prompt-contract homes.
Keep the remaining social/regression adjacency narrow too: `test_social_topic_anchor.py` should read
as downstream topic-anchor behavior coverage, and
`test_stale_interlocutor_invalidation_block3.py` should read as stale-interlocutor invalidation /
follow-up routing regression coverage. Re-center direct prompt-instruction or canonical-target helper
assertions in `test_prompt_context.py` when those suites start sounding like prompt-contract homes.
Keep the remaining downstream strict-social and harness adjacency narrow too:
`test_strict_social_answer_pressure_cashout.py` should read as strict-social answer-pressure /
spoken cash-out application coverage, `test_synthetic_sessions.py` should read as
synthetic-session harness persistence / transcript regression coverage, and
`test_answer_completeness_rules.py` should read as downstream shipped answer-completeness /
response-delta consumer coverage. Re-center direct answer-pressure helper,
answer-completeness / response-delta bundle derivation, and interlocutor lead-discussion export
assertions in `test_prompt_context.py` when those suites start sounding like prompt-contract homes.
Keep prompt-adjacent establishment and fallback suites narrow too: `test_dialogue_interaction_establishment.py`
should read as dialogue/social establishment flow coverage, and
`test_fallback_shipped_contract_propagation.py` should use local shipped-policy fixtures rather than
prompt-bundle builders when only downstream propagation is under test.
`test_prompt_and_guard.py` remains prompt-adjacent for pre-generation guard behavior, but it is not
the semantic owner of the prompt bundle itself. When adding new prompt-contract semantics, prefer
the direct owner suite first; use broader harnesses only for smoke, orchestration, or historical
regression locks.
Keep lead-adjacent suites narrow too: `test_follow_lead_commitment_wiring.py` should read as
follow/commitment lifecycle wiring, and `test_lead_lifecycle_npc_repeat_suppression.py` should read
as lead-lifecycle repeat-suppression consumption of exported narration context. Re-center direct
prompt-export filtering or prompt-slice ownership assertions in `test_prompt_context.py` when those
lead-adjacent suites start sounding like prompt-contract homes.
Support/compatibility residue may remain in `game/prompt_context_leads.py` and in exported
consumer paths that consume prompt-owned bundles without co-owning them; treat those paths as
support/consumption residue, not equal prompt-semantic homes.

### Response-policy governance note (RP2-R)

For the response-policy seam, treat `game/response_policy_contracts.py` as the canonical
runtime owner and `tests/test_response_policy_contracts.py` as the practical primary
direct-owner suite. Keep `test_fallback_shipped_contract_propagation.py` as secondary
fallback/compatibility coverage, `test_response_delta_requirement.py` as downstream
gate-application coverage, `test_final_emission_gate.py` and
`test_social_exchange_emission.py` as orchestration/emission integration coverage, and
`test_final_emission_validators.py` as validator-side application coverage. When adding
new response-policy accessor or bundle-materialization semantics, prefer the direct owner
suite first; use broader harnesses only for downstream consumption, compatibility-path,
consumer/application, or regression locks.
Keep `test_interaction_continuity_contract.py` as downstream interaction-continuity
contract-consumption coverage and `test_interaction_continuity_validation.py` as
downstream continuity-validation / enforcement coverage. Re-center direct
`game.response_policy_contracts` accessor or shipped-policy materialization assertions in
`test_response_policy_contracts.py` when those continuity suites start sounding like
response-policy owner homes.

Compatibility residue note:

- private compatibility accessors may remain importable;
- top-level `fallback_behavior` fallback remains supported;
- top-level `social_response_structure_contract` fallback remains supported.

Treat that residue as compatibility/adjacency only, not as a reason to reclassify repair,
gate, validator, or emission suites as parallel semantic owners for response-policy accessors.

### Objective #7 referent seam governance note (RT7-R)

For the **prompt-artifact referent pack** and post-GM **referent clarity** layer (Objective #7), treat `game/referent_tracking.py` as the canonical runtime owner for deterministic **full** artifact construction and JSON-safe validation. Treat `game/prompt_context.py` as the canonical attachment point for the full artifact on the shipped prompt bundle, and `game/turn_packet.py` as the packet-boundary owner of the **compact** four-field mirror (`referent_tracking_compact`) — the mirror is **not** a second semantic copy of the full artifact.

Treat `game/final_emission_validators.validate_referent_clarity` as the canonical **post-GM check** surface (full artifact first; compact-only paths record observability and abstain from repair-driving reconstruction). Treat `game/final_emission_repairs._apply_referent_clarity_emission_layer` as the canonical **bounded repair** surface (at most one deterministic pronoun substitution; no forbidden/off-visible name insertion). Treat `game/final_emission_gate._apply_referent_clarity_pre_finalize` as the orchestration hook that runs before final FEM preview / sealing on all finalize paths.

Practical primary direct-owner suites: `tests/test_referent_tracking.py` (artifact construction/schema), `tests/test_prompt_context.py` (bundle + compact mirror shape), `tests/test_final_emission_validators.py` (validator + repair consumer semantics), `tests/test_final_emission_gate.py` (pre-finalize FEM merge + preview coherence). Optional shared stubs: `tests/helpers/objective7_referent_fixtures.py`. Downstream suites may observe shipped fields but must not become parallel owners of artifact derivation or compact-vs-full equivalence.

**Distinction:** `game/narration_visibility.validate_player_facing_referential_clarity` and transcript/gate tests around **player-visible** referential clarity are a **separate** seam from the Objective #7 prompt-artifact pack; do not merge ownership narratives.

### Final-emission orchestration governance note (FG1-R)

For this seam, treat `game/final_emission_gate.py` as the canonical runtime owner and
`tests/test_final_emission_gate.py` as the practical primary direct-owner suite. Keep
direct layer-order, final-route integration, and orchestration assertions there first.
`tests/test_social_exchange_emission.py` should read as downstream strict-social emission
application coverage, `tests/test_turn_pipeline_shared.py` as API-level smoke, and
`tests/test_stage_diff_telemetry.py`, `tests/test_social_emission_quality.py`, and
`tests/test_dead_turn_detection.py` as telemetry, quality, and metadata-consumer coverage.
Keep `tests/test_interaction_continuity_speaker_bridge.py` as downstream continuity
speaker-bridge behavior coverage and `tests/test_interaction_continuity_validation.py`
as downstream continuity-validation coverage; re-center direct
`_apply_interaction_continuity_emission_step(...)` and
`_attach_interaction_continuity_validation(...)` ownership assertions in
`tests/test_final_emission_gate.py` when those continuity-adjacent files start sounding
like gate-orchestration homes.
Keep `tests/test_interaction_continuity_repair.py` as downstream continuity-repair /
gate-consumer coverage only: prefer public emitted outcomes, repair metadata, and
downstream enforcement effects there rather than direct gate-private step imports or
layer-order assertions. Keep any direct continuity-adjacent gate-step ownership in
`tests/test_final_emission_gate.py`.
Keep `tests/test_interaction_continuity_speaker_bridge.py` focused on downstream
consumer behavior for bridge-shaped continuity failures rather than direct
gate-private bridge/heuristic helper semantics.
When adjacent suites need gate setup, prefer consumer framing and shipped/local fixtures over
owner-like `test_final_emission_gate_*` naming unless they are actually asserting orchestration.

### Final-emission repairs governance note (FR1-R)

Repair semantics are owned by runtime `game.final_emission_repairs` and tests
`tests/test_final_emission_repairs.py`. All other suites provide downstream consumption
coverage (fallback, gate, retry, quality, leak). Keep direct helper/accessor semantics,
repair materialization behavior, and `_apply_fallback_behavior_layer(...)` assertions in
`tests/test_final_emission_repairs.py` first. Keep `tests/test_fallback_behavior_repairs.py`
as downstream fallback-consumer coverage only; `tests/test_fallback_behavior_gate.py` as
downstream gate application coverage; `tests/test_bounded_partial_quality.py` as
bounded-partial quality coverage; and `tests/test_social_fallback_leak_containment.py`
as social fallback leak containment coverage. When adjacent suites need repair fixtures,
prefer local shipped contracts, black-box `repair_fallback_behavior(...)` inputs,
repaired-output assertions, or consumer metadata checks over direct
`game.final_emission_repairs` private helper imports unless the helper semantics themselves
are under test in the owner suite.

### Stage-diff telemetry governance note (TD1-R)

For this seam, treat `game/stage_diff_telemetry.py` as the canonical runtime owner and
`tests/test_stage_diff_telemetry.py` as the practical primary direct-owner suite. Keep
direct `snapshot_turn_stage(...)`, `diff_turn_stage(...)`, `record_stage_snapshot(...)`,
`record_stage_transition(...)`, and packet-derived telemetry-field assertions there first.
Keep `tests/test_turn_packet_stage_diff_integration.py` as downstream turn-packet + gate/retry
consumer coverage and `tests/test_narrative_authenticity_aer4.py` as downstream
narrative-authenticity regression / evaluator-consumer coverage. When adjacent suites need
telemetry fixtures, prefer consumer framing and emitted metadata assertions over direct
telemetry-helper imports unless the helper semantics themselves are under test.

### Strict-social exchange emission governance note (SE2-R)

For the downstream strict-social exchange emission seam, treat `game/social_exchange_emission.py`
as the canonical runtime owner and `tests/test_social_exchange_emission.py` as the practical
primary direct-owner suite. Keep `tests/test_strict_social_emergency_fallback_dialogue.py` as
secondary downstream retry-terminal / first-mention / compatibility coverage, with legacy
`repair_*` helper assertions labeled as historical-path coverage rather than semantic ownership.
`tests/test_social_emission_quality.py`, `tests/test_dialogue_interaction_establishment.py`,
and gate/retry-oriented suites may continue to exercise the seam, but they should read as
consumer/application, harness, or regression evidence rather than alternate semantic owners for the same seam.

Heuristic tags (`test_inventory.json` → `feature_areas_by_distinct_files`) show **many files** touching the same themes (breadth diagnostic, not proof of duplicate ownership). For **live** distinct-file counts and import hubs, regenerate the inventory and read `feature_areas_by_distinct_files`, `import_hub_modules`, and `block_b_overlap_clusters` (especially `dense_ownership_theme_by_architecture_layer` and `imports_final_emission_gate_and_prompt_context`). The qualitative hotspots below remain the highest-risk *semantic* overlap areas for double-locking (counts intentionally not duplicated here):

1. **Lead extraction + clue system** — many `test_lead_*.py` modules plus `test_social_lead_landing.py`, `test_clue_lead_registry_integration.py`, pipeline, and prompt/guard.
2. **Resolution / emission** — `test_social_exchange_emission.py`, `test_turn_pipeline_shared.py`, `test_social_emission_quality.py`, `test_social.py`, and several lead payoff modules.
3. **Routing** — pipeline vs `test_directed_social_routing.py` vs exploration/social misc.
4. **Legality / sanitizer + fallback** — repair regressions overlap with sanitizer, prompt/guard, and pipeline.
5. **Social continuity** — `test_social.py`, `test_directed_social_routing.py`, `test_mixed_state_recovery_regressions.py`, `test_turn_pipeline_shared.py`, emission quality.

### Block 2 — concrete files to touch next

Prioritize **marker normalization + overlap trimming** (not mass deletion). **Routing** and **repair/retry** consolidation passes are **closed enough** for their doc blocks (`TEST_CONSOLIDATION_PLAN.md`). **Suggested batch order (Block C1):** align **emit-path `orchestration` / metadata + authenticity `telemetry`** decisions in `docs/narrative_integrity_architecture.md` first where runtime moves are ambiguous, then **prompt/sanitizer** → **social/emission** → **transcript** duplicate assertion thinning → **`deferred` lead/clue** — see *Next consolidation order* in that plan.

| Priority | File(s) | Why |
| --- | --- | --- |
| Done — **routing ownership (Block 3)** | `test_turn_pipeline_shared.py` ↔ `test_directed_social_routing.py` ↔ `test_dialogue_routing_lock.py` | Layer split is recorded. Future **thinning** only with a replacement strategy; some cross-layer phrase overlap remains **intentional**. |
| Done — **repair/retry ownership (Block 3 doc)** | `test_contextual_minimal_repair_regressions.py` ↔ `test_empty_social_retry_regressions.py` | Applied ownership + intentional overlap recorded; cluster **complete enough** — extend each file per `TEST_CONSOLIDATION_PLAN.md` *Repair / retry cluster — Block 3*. |
| High | `test_social.py` ↔ `test_social_exchange_emission.py` ↔ `test_social_escalation.py` | Thematic overlap; migrate strict emission assertions to `test_social_exchange_emission.py`; shrink `test_social.py`. |
| High | `test_transcript_regression.py` ↔ `test_lead_lifecycle_block3_transcript_regression.py` ↔ `test_gauntlet_regressions.py` | Multi-step flows; **weaken** transcript duplicate substring locks where a focused test already owns the gate. |
| Medium | `test_social_emission_quality.py` | Per-test `transcript` marks; **module-level policy** (see `TEST_AUDIT.md` fast-lane section). |
| Medium | `test_prompt_and_guard.py` ↔ `test_output_sanitizer.py` | Symptom-based routing of new cases (post-GM vs messages-to-model). |
| Medium | Lead/clue cluster: `test_social_lead_landing.py`, `test_clue_lead_registry_integration.py`, `test_social_destination_redirect_leads.py` | Reduce duplicate registry/pending assertions after canonical clue/lead owners are respected. |

### What **not** to consolidate in Block 2

- **Broad merges** of large files (`test_prompt_and_guard.py`, `test_turn_pipeline_shared.py`) into one module — **defer**; prefer trimming duplicate assertions and shared helpers.
- **Deleting** regression or transcript tests **without** a nodeid replacement map — **do not**.
- **World/state, save/load, snapshots, schema-only** suites — **leave** unless a clear duplicate appears; low overlap per audit.

**Block 20 — feature ownership:** Inventory `feature_areas` now honor optional per-test `# feature: tag1, tag2` lines (immediately above the test, optionally above `@pytest.mark.*`), module-level `# feature:` before the first top-level `def test_`, and `@pytest.mark.routing|retry|fallback|social|continuity|clues|leads|emission|legality` when present. Tags map into the existing inventory labels (e.g. `clues` → `clue system`, `leads` → `lead extraction`). See `pytest.ini` for registered markers.

**Per-test rows:** `tests/test_inventory.json` — each collected pytest item includes `nodeid`, heuristic `primary_bucket`, `feature_areas`, `historically_motivated`, `assertion_style`, `brittleness`, `redundancy_flag`, `keyword_overlap_hints`, `likely_architecture_layer`, `likely_ownership_theme`, and `file_overlap_hints` (mirrors the owning file row). **Tool tests:** `tests/test_test_audit_tool.py` locks helper behavior without re-running full collection.

---

## Block 1 — Fast lane vs full lane

**Purpose:** Document how **fast** (day-to-day) and **full** (pre-merge / milestone) pytest lanes are run today. Exclusion markers `transcript` and `slow` define fast-lane membership; scope tags `unit` / `integration` / `regression` support inventory and optional filters but **do not** replace that expression. Commands and collect-only expectations: `tests/README_TESTS.md`.

**Ground truth:** `tests/test_inventory.json` (`summary`, `files[].primary_bucket`, `files[].high_brittleness_test_count`). Regenerate with `py -3 tools/test_audit.py`.

### Lane definitions

| Lane | Intent | Selection (current) |
| --- | --- | --- |
| **Full** | Full regression surface, transcript replay, gauntlets, and expensive flows. | `pytest` / `pytest tests/` (no marker filter). |
| **Fast** | Routine local feedback; excludes transcript-harness and explicitly slow items. | `pytest -m "not transcript and not slow"` |

**Optional stricter fast** (if prompt-heavy tests are too noisy locally): `pytest -m "not transcript and not slow and not brittle"`. `brittle` is appropriate on prose- or prompt-shape–sensitive modules (e.g. `test_prompt_and_guard.py`).

### Marker meanings (lane-relevant subset)

Declared in `pytest.ini`. For **lane membership**:

- **`transcript`** — Module uses multi-turn transcript harness / session-log replay patterns (`tests.helpers.transcript_runner`, gauntlet-style flows, or file naming `test_transcript_gauntlet_*`). **Fast lane excludes** these regardless of runtime.
- **`slow`** — Heavier runtime (large turn counts, large pipelines). **Fast lane excludes** these.
- **`unit`**, **`integration`**, **`regression`** — Describe **scope** and signal density; they do **not** imply fast or slow by themselves. Use them for documentation, inventory alignment, and expressions like `pytest -m "regression"` — not as the sole fast-lane gate once exclusion markers are complete.
- **`brittle`** — Optional **fast-lane** exclusion for prompt/prose-sensitive suites; orthogonal to ownership markers below.

**Ownership markers** (`routing`, `retry`, `fallback`, `social`, `continuity`, `clues`, `leads`, `emission`, `legality`) are for feature ownership and inventory only — **do not** use them to define lanes.

### Classification rules (apply per module)

Use this order when tagging in Block 2:

1. **Full-lane anchor (tag `transcript` and usually `slow` if multi-turn or expensive):**  
   - Path matches `test_transcript_gauntlet_*.py` under `tests/`.  
   - Module uses `run_transcript` / transcript runner as the primary harness (`test_transcript_regression.py`, `test_transcript_runner_smoke.py`, `test_mixed_state_recovery_regressions.py`, `test_lead_lifecycle_block3_transcript_regression.py`).  
   - Re-evaluate **`test_social_emission_quality.py`**: some tests already carry `transcript`; align with **module-level** `pytestmark` so behavior matches intent.
2. **Mark `slow` without `transcript` when:** a module is integration-weighted but unusually expensive (many sequential API turns, huge fixtures) and should drop out of fast lane even if not “transcript” by naming.
3. **Fast-eligible default:** all other modules — typical `TestClient` + `tmp_path` + mocks, pure logic, or single-turn API checks — **no** `transcript` / `slow` unless measured otherwise.
4. **Scope markers:** add module-level `pytestmark` with one or more of `unit`, `integration`, `regression` consistent with the majority `primary_bucket` in `test_inventory.json` (heuristic: `unit`-majority files → prefer `unit`; `integration`-majority → `integration`; files already in `tests/*_regressions.py` or regression-majority → include `regression`).

### Module tiers (inventory-informed snapshot)

Tiers describe **expected lane membership** from `transcript` / `slow` (and thus fast vs full), not “everything is green.” Remaining marker work below is mostly **scope** (`unit` / `integration` / `regression`) coverage for inventory — it does not change the fast-lane command.

| Tier | Description | Examples (non-exhaustive) |
| --- | --- | --- |
| **1 — Core / unit-like** | Majority `unit` in JSON; little or no transcript harness. Fast-eligible. | `test_intent_parser.py`, `test_output_sanitizer.py`, `test_exploration_resolution.py`, `test_social_exchange_emission.py`, `test_world_state.py`, `test_skill_checks.py`, … |
| **2 — Routine integration** | Majority `integration`; API/storage/pipeline; still day-to-day friendly if not tagged `slow`/`transcript`. Fast-eligible. | `test_turn_pipeline_shared.py`, `test_prompt_and_guard.py`, `test_directed_social_routing.py`, `test_follow_lead_commitment_wiring.py`, `test_save_load.py`, … |
| **3 — Regression-heavy** | Majority `regression` or `*_regressions.py`; may be fast-eligible unless also `transcript`/`slow`. | `test_empty_social_retry_regressions.py`, `test_contextual_minimal_repair_regressions.py`, `test_social_target_authority_regressions.py`, `test_gauntlet_regressions.py` (API-style; name ≠ transcript marker today). |
| **4 — Transcript / gauntlet / heavy** | `transcript_gauntlet` file pattern or transcript-tagged modules. Full lane (and fast lane **off**). | `test_transcript_gauntlet_actor_addressing.py`, `test_transcript_gauntlet_campaign_cleanliness.py`, `test_transcript_regression.py`, `test_mixed_state_recovery_regressions.py`, `test_transcript_runner_smoke.py`, `test_lead_lifecycle_block3_transcript_regression.py`. |

**Special-purpose / diagnostic:** No separate pytest modules are audit-only; `tools/test_audit.py` is tooling, not collected. `test_clocks_projects_logging_lint.py` is normal integration coverage (scene lint + clocks/projects), not a separate lane.

### Current marker coverage vs target

- **Module-level `pytestmark`:** lane-related marker adoption drifts with the suite. Treat `tests/test_inventory.json` + `pytest.ini` as ground truth; do not rely on stale per-file counts in this markdown unless refreshed alongside `tools/test_audit.py`.
- **Per-test markers:** `test_turn_pipeline_shared.py` adds `unit`+`regression` on one test while the module is `integration`. `test_social_emission_quality.py` marks `transcript` on a subset of tests only — normalize in Block 2.
- **`test_prompt_and_guard.py`:** module is `brittle` only — add `integration` (or `unit`) alongside `brittle` so scope is explicit for inventory and optional filters.

**Optional narrow filter:** `pytest -m "(unit or regression) and not transcript"` is **not** the fast lane — it omits many integration-only modules because most files are not tagged `unit`/`regression` at module level. Re-run `--collect-only` if you need an exact count. **Primary fast lane** remains `pytest -m "not transcript and not slow"` (documented in `tests/README_TESTS.md`).

### Block 2 — files likely needing marker cleanup

1. **All 60 modules without module-level lane `pytestmark`** — add `unit` / `integration` / `regression` per rules above; add `transcript` / `slow` where tier 4 or expensive.
2. **`test_social_emission_quality.py`** — consolidate per-test `transcript` / ownership marks into clear module-level policy.
3. **`test_turn_pipeline_shared.py`** — reconcile module `integration` with the single test that adds `unit`+`regression` (drop redundancy or document dual intent).
4. **`test_prompt_and_guard.py`** — add scope marker(s) in addition to `brittle`.
5. **`test_lead_lifecycle_block3_transcript_regression.py`** — already `transcript`+`regression`; decide if `slow` is warranted from runtime.
6. **`test_gauntlet_regressions.py`** — name suggests gauntlet; implementation is API/integration — either keep fast-eligible (current) or add `transcript`/`slow` only if it truly uses harness-scale replay (verify before tagging).

**Already module-tagged (review only in Block 2):**  
`test_clue_idempotence.py`, `test_clue_knowledge.py`, `test_contextual_minimal_repair_regressions.py`, `test_empty_social_retry_regressions.py`, `test_gauntlet_regressions.py`, `test_intent_parser.py`, `test_lead_lifecycle_block3_transcript_regression.py`, `test_mixed_state_recovery_regressions.py`, `test_project_schema.py`, `test_prompt_and_guard.py`, `test_scene_entity_lock.py`, `test_social_target_authority_regressions.py`, `test_transcript_gauntlet_actor_addressing.py`, `test_transcript_gauntlet_campaign_cleanliness.py`, `test_transcript_regression.py`, `test_transcript_runner_smoke.py`, `test_turn_pipeline_shared.py`, `test_turn_trace_contract.py`.

### New markers?

**Not necessary** for a clean two-lane model: reuse **`transcript`**, **`slow`**, **`brittle`**, and scope markers **`unit` / `integration` / `regression`**. Add a dedicated `fast` marker only if team wants opt-in fast suites instead of “default collect minus exclusions.”

### Block 3 — Fast/full workflow verification (recorded baseline)

Example `pytest --collect-only` check from repo root (replace counts after large suite edits):

| Command | Result |
| --- | --- |
| `pytest --collect-only` | matches `summary.pytest_collected_items` in `tests/test_inventory.json` when inventory was regenerated the same day |
| `pytest --collect-only -m "not transcript and not slow"` | marker-complement fast lane; deselected = `transcript` or `slow` |

Re-run after large suite edits; treat `tests/test_inventory.json` as the inventory ground truth.

---

## Executive counts

| Metric | Latest `test_inventory.json` summary (regenerate locally) | Notes |
| --- | ---: | --- |
| Test files (`tests/` modules matching `test_*.py`) | *see JSON* | `summary.test_file_count` |
| Pytest collected items | *see JSON* | `summary.pytest_collected_items` |
| Cross-file duplicate `test_*` base names | *see JSON* | `summary.cross_file_duplicate_test_name_count` + `cross_file_duplicate_test_names` |
| Fast lane (`not transcript and not slow`) | *(re-run)* | `pytest --collect-only -m "not transcript and not slow"` — counts drift with markers |

**Heuristic breakdowns** (bucket mixes, brittleness histograms, AST duplicate-name summaries): regenerate `tests/test_inventory.json` via `py -3 tools/test_audit.py` and read `summary` / `files` — the suite has outgrown static markdown tables here.

### Counts by test-level primary bucket

Regenerate `tests/test_inventory.json` for current per-item bucket totals (filename hint + body heuristics).

### Counts by file-level primary bucket

Regenerate `tests/test_inventory.json` — `primary_bucket` on each file record is the **majority** bucket among that file’s collected tests. The JSON field `filename_bucket` records path-pattern hints only (`transcript_gauntlet`, `regression`, or `mixed/unclear`).

---

## Module-level duplicate `test_*` names (guardrail)

If the same top-level `def test_foo` appears twice in one module, Python keeps only the last definition; pytest then collects **one** item for that name and earlier bodies never run. **`tools/test_audit.py` detects this** (AST duplicate names per file) and reports it on stdout and in `tests/test_inventory.json` → `summary.files_with_shadowed_duplicate_test_defs`.

`tests/test_exploration_resolution.py` currently has **38** unique top-level `test_*` names, **38** AST def lines (no shadowing), and **42** collected items (one parametrized test adds 4 extra cases). An older version of this audit text incorrectly claimed mass shadowing here; that was **stale documentation** — the live source of truth is `pytest --collect-only` plus the audit JSON.

---

## Top files by count of high-brittleness tests (heuristic)

Snapshot from `test_inventory.json` → `top_high_brittleness_files` (2026-04-03):  
`test_mixed_state_recovery_regressions.py` — 6; `test_transcript_regression.py` — 5; `test_empty_social_retry_regressions.py`, `test_social_emission_quality.py`, `test_transcript_gauntlet_actor_addressing.py` — 4 each; then several files at 3 or 1. Re-run the audit for an updated ordered list.

---

## Top “likely overlap” **areas** (by spread across files)

These are **feature tags** (keyword heuristics), not proof of duplicate tests. High file counts mean trims/consolidation require reading tests, not deleting by tag. **Do not maintain a ranked markdown table here** — it rots immediately. After `py -3 tools/test_audit.py`, read `feature_areas_by_distinct_files` (and `feature_area_primary_counts` for item-weighted totals).

The **general** bucket still indicates tagging debt where modules do not match keyword rules; refine rules or add explicit `# feature:` / markers over time.

---

## Candidate canonical suites by feature area

Use as starting points when deciding where new coverage should live first.

| Area | Strong candidate files |
| --- | --- |
| End-to-end / session transcript flows | `test_transcript_regression.py`, `test_gauntlet_regressions.py` |
| Transcript gauntlet (LTC slice / harness) | `test_transcript_gauntlet_*.py`, `test_transcript_runner_smoke.py` |
| Behavioral gauntlet coverage | `test_behavioral_gauntlet_eval.py`, `test_behavioral_gauntlet_smoke.py`, `docs/manual_gauntlets.md`, `tools/run_manual_gauntlet.py` |
| Mixed-state & social continuity | `test_mixed_state_recovery_regressions.py`, `test_dialogue_interaction_establishment.py` |
| Retry / empty social / terminal fallback | `test_empty_social_retry_regressions.py`, `test_social_answer_retry_prioritization.py` |
| Contextual minimal repair | `test_contextual_minimal_repair_regressions.py` |
| Shared chat/action pipeline | `test_turn_pipeline_shared.py` |
| Social emission / strict social | `test_social_exchange_emission.py` (practical primary direct-owner), `test_social_answer_candidate.py`; keep `test_strict_social_emergency_fallback_dialogue.py` as downstream retry/compatibility coverage only |
| Directed routing & dialogue lock | `test_directed_social_routing.py`, `test_dialogue_routing_lock.py` |
| Clue knowledge & inference | `test_clue_knowledge.py`, `test_world_updates_and_clue_normalization.py` |
| Output / legality | `test_output_sanitizer.py`, `test_prompt_and_guard.py`, `test_debug_payload_spoiler_safety.py` |
| Exploration resolution | `test_exploration_resolution.py`, `test_exploration_skill_checks.py` |

### Behavioral gauntlet stack

The behavioral gauntlet stack is a compact, deterministic adjunct to the broader gauntlet and transcript inventory:

- `tests/helpers/behavioral_gauntlet_eval.py` is the evaluator helper (`evaluate_behavioral_gauntlet(turns, *, expected_axis=None)`).
- `tests/test_behavioral_gauntlet_smoke.py` is the automated smoke lane (`integration` + `regression`), using direct simplified rows plus gauntlet-style payload compatibility slices.
- `docs/manual_gauntlets.md` is the manual source of truth and includes behavioral gauntlets `G9` through `G12`.
- `tools/run_manual_gauntlet.py` can attach advisory `behavioral_eval` data to `summary.json`, along with optional `axis_tags` and `behavioral_eval_warning`.

Manual `behavioral_eval` output is advisory only: it does not replace operator judgment or determine manual pass/fail by itself.

---

## Recommended canonical coverage map

Concrete “source of truth” examples for recurring themes (prefer extending these before adding parallel modules).

| Theme | Canonical example |
| --- | --- |
| Retry termination / empty social repair | `tests/test_empty_social_retry_regressions.py::test_force_terminal_retry_fallback_repairs_empty_social_candidate` |
| Final emission continuity after terminal retry | `tests/test_empty_social_retry_regressions.py::test_force_terminal_retry_fallback_preserves_final_emission_meta_continuity` |
| API-level empty-social repair | `tests/test_empty_social_retry_regressions.py::test_api_repairs_empty_social_after_force_terminal_retry_fallback` |
| Clue idempotency / no double inference | `tests/test_clue_knowledge.py::test_reveal_clue_duplicate_does_not_reinvoke_inference` |
| Authoritative clue gateway dedupe | `tests/test_clue_knowledge.py::test_authoritative_clue_gateway_dedupes_duplicate_writes` |
| Social continuity & routing through mixed narration | `tests/test_mixed_state_recovery_regressions.py::test_approach_visible_figure_then_question_routes_social` |
| No “no new information” dead-end when hook present | `tests/test_mixed_state_recovery_regressions.py::test_social_text_with_hook_cannot_end_with_no_new_information_state` |
| Contextual repair must not inject clue/resolution payloads | `tests/test_contextual_minimal_repair_regressions.py::test_contextual_minimal_repair_does_not_add_clue_or_resolution_payload` |
| Repair lines pass legality | `tests/test_contextual_minimal_repair_regressions.py::test_contextual_repair_lines_pass_legality_checks` |
| Dialogue lock → social lane | `tests/test_turn_pipeline_shared.py::test_chat_dialogue_lock_routes_npc_directed_question_regressions` |
| Final-emission orchestration order | `tests/test_final_emission_gate.py::test_apply_final_emission_gate_runs_response_delta_before_speaker_enforcement` |
| API-level social-output fallback smoke | `tests/test_turn_pipeline_shared.py::test_chat_social_exchange_invalid_blob_is_repaired_before_emit` |
| Retry prioritization (structured vs stall) | `tests/test_social_answer_retry_prioritization.py::test_prioritize_suppresses_scene_stall_when_structured_candidate_exists` |
| Transcript gauntlet: explicit address stability | `tests/test_transcript_gauntlet_actor_addressing.py::test_explicit_address_never_gets_wiped_by_later_validation` |

---

## Safe consolidation candidates (recommendations only)

1. **`test_contextual_minimal_repair_regressions.py` vs `test_empty_social_retry_regressions.py`**  
   - **Status (2026-04-03):** Active ownership split **documented and closed enough** — see `TEST_CONSOLIDATION_PLAN.md` *Repair / retry cluster — Block 3* (contextual: branch, `debug_notes`, legality, anchors vs hard-line, payload guards; empty_social: retry metadata, `_final_emission_meta`, `/api/chat` repair). **Intentional overlap** when fixtures or asserted layers differ is OK.  
   - **Future:** Share fixtures/helpers only; optional thinning if a specific assertion duplicates the same **layer**.

2. **`test_turn_pipeline_shared.py` vs `test_directed_social_routing.py` vs `test_dialogue_routing_lock.py`**  
   - **Overlap:** Routing, dialogue lock, and social/adjudication boundaries appear in all three at different depths.  
   - **Canonical:** `test_turn_pipeline_shared.py` for **full `/api/chat` pipeline** locks; smaller files for **focused routing tables**.  
   - **Merge/weaken:** Prefer new routing cases in `test_directed_social_routing.py` unless they require full pipeline; avoid a third parallel file for the same lock.

3. **`test_output_sanitizer.py` vs `test_prompt_and_guard.py` (validator / guard / prose)**  
   - **Overlap:** Legality, validator voice, and sanitization strings.  
   - **Canonical:** `test_output_sanitizer.py` for **emit-time sanitizer**; `test_prompt_and_guard.py` for **prompt construction + guard contracts**.  
   - **Merge/weaken:** When a failure is “output shape after GM,” add sanitizer tests; when “messages to model,” add prompt/guard tests. Prefer trimming phrase-level bans in `test_prompt_and_guard.py` when the same phrase is already canonically locked (and more strongly covered) in `test_output_sanitizer.py`.

4. **`test_social.py` vs `test_social_exchange_emission.py` vs `test_social_escalation.py`**  
   - **Overlap:** Broad social behavior, escalation, and emission formatting share vocabulary.  
   - **Canonical:** `test_social_exchange_emission.py` for **strict social / emission**; `test_social_escalation.py` for **pressure/escalation state machine**; `test_social.py` as **misc integration** only if no better home.  
   - **Merge/weaken:** New strict-social assertions should default to `test_social_exchange_emission.py`.

5. **`test_exploration_resolution.py` (naming discipline)**  
   - **Overlap:** Thematic clusters (parse vs API vs engine schema) live in one module; keep **distinct** top-level `test_*` names so pytest collects every case (`tools/test_audit.py` flags duplicate names in-module).  
   - **Canonical:** One named test per behavior; prefer **parametrize** for variant matrices.  
   - **Merge/weaken:** No merge across files required for naming alone; extend here for exploration resolution.

---

## Full file index

`primary_bucket` = majority of tests in that file. **High-brittleness** = count of tests with heuristic `brittleness: high` in that file. Feature tags = top primary feature labels (first keyword hit per test, aggregated).

**Authoritative list:** Every `test_*.py` under `tests/` is one row in `tests/test_inventory.json` → `files`, including `pytest_collected`, `collected_nodeids`, `likely_architecture_layer`, `likely_ownership_theme`, `overlap_hints`, and `primary_feature_area_breakdown`. The old static markdown table was removed to avoid rot; use your editor’s JSON viewer, `jq`, or ad-hoc Python to slice `files[]`.

---

## Methodology & limitations

- **Ground truth for “what runs”:** pytest collection (see *Executive counts* / Block C1 snapshot; re-run `pytest --collect-only` after large edits). AST `def test_*` counts are per-file module-level defs; **duplicate names in the same file** are listed in `summary.files_with_shadowed_duplicate_test_defs` and echoed when running `tools/test_audit.py`.  
- **Buckets:** Test-level buckets use filename patterns (`transcript_gauntlet`, `regression`) then body signals (`TestClient`, `tmp_path`, length).  
- **Feature areas:** Substring rules on `nodeid`, merged with explicit `# feature:` / ownership `pytest.mark.*` when present; unannotated tests may still land on **general**.  
- **Architecture layer + ownership theme:** Filename, AST-parsed `game.*` imports, and source keywords feed `likely_architecture_layer` / `likely_ownership_theme` on each file (and duplicated on each test row for filtering). These are **heuristics** for triage, not runtime ownership law (the prose tables above remain governance).  
- **Assertion style / brittleness:** Regex on function source (long string `==`, `in "..."`, structural calls). Transcript/regression modules biased to **high** brittleness.  
- **Redundancy:** `possible_overlap` on a test row flags identical **base** names collected from multiple files (`cross_file_duplicate_test_names` aggregates them). Semantic duplicates are **not** auto-detected.  
- **Pytest markers:** `pytest.ini` defines `unit`, `integration`, `regression`, `transcript`, `slow`, `brittle`, plus optional ownership markers (`routing`, `retry`, `fallback`, `social`, `continuity`, `clues`, `leads`, `emission`, `legality`). `tools/test_audit.py` reads those ownership markers and `# feature:` comments when building `feature_areas`.

---

## Optional metadata comments

Use `# feature: routing, fallback` on the line before a test (or once per file before the first top-level `def test_`) so `test_inventory.json` picks up ownership without relying on `nodeid` keywords. Equivalent: `@pytest.mark.routing` (see `pytest.ini`). Large or previously-`general` modules are partially tagged; extend over time.
