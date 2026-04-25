# Test consolidation plan (Block 15C, post-AER Block C1 boundary)

**Status:** Plan + recorded ownership; routing consolidation **pass closed**; **repair/retry cluster closed enough** (Block 3 doc — see *Repair / retry cluster — Block 3*). **Behavioral Gauntlet**, **Playability Validation**, and **AER** are **complete** as validation tracks—this document now governs **post-feature consolidation** only (no gameplay expansion in consolidation-only PRs).

### Test Ownership & Coverage Consolidation (Blocks A–D — complete)

Documentation and tooling only; **no runtime game behavior** changes in this track.

**Block A — inventory audit**

- **`tools/test_audit.py` enhanced** — richer inventory, overlap hints, and JSON fields aligned with triage (see `tests/TEST_AUDIT.md` → *Methodology & limitations*).
- **`tests/test_inventory.json`** — regenerated from collection + heuristics; **live** ground truth for counts and per-file metadata (`py -3 tools/test_audit.py` from repo root).
- **`tests/TEST_AUDIT.md`** — static rotting tables removed in favor of JSON-backed methodology and prose governance tables; counts and brittleness leaders are **regenerate**, not hand-maintained.

**Block B — ownership registry governance**

- **`tests/test_ownership_registry.py` added** — declares required **responsibility** groups with a single **direct_owner** path each (plus optional **neighbor** suites), checks inventory presence and layer alignment, and rejects **live legality** groups whose direct owner is classified as transcript/gauntlet/playability/evaluator-only.
- **Neighbor categories (exactly one slot per listed path within a group):** `smoke_suites`, `transcript_suites`, `gauntlet_suites`, `evaluator_suites`, `downstream_consumer_suites`, `compatibility_residue_suites`. Use **downstream_consumer** for integration suites that consume the owner boundary without being thin smoke; use **compatibility_residue** for documented legacy or read-side harnesses. The audit mirrors these lists under `ownership_registry_index.groups` and `files_roles` in `tests/test_inventory.json`.
- **Direct-owner governance checks** — registry + pytest prevent silent drift of “who owns this seam” and accidental double-claim of the same `direct_owner` path across groups. Inventory `likely_architecture_layer` heuristics treat **`general` as permissive for neighbors only**; a **direct owner** with a non-null `declared_architecture_layer` must not resolve to `general`, and must align with declared layer (with the same soft adjacency rules as before).
- **Duplicate base names** — cross-file identical `test_*` base names remain **heuristic triage** (`tests/test_inventory.json`, `block_b_overlap_clusters`); a small **allowlist** documents intentional collisions with **non-empty reasons**.

**Block C — smoke / transcript consolidation (examples)**

- **`tests/test_c4_narrative_mode_live_pipeline.py`** — thinned toward **C4 narrative-mode wiring / orchestration smoke**; not a second full NMO legality matrix.
- **`tests/test_narration_transcript_regressions.py`** — thinned away from **duplicate direct-legality** coverage already owned in focused suites; preserves transcript value for **multi-turn narration** behavior.
- **Canonical owners preserved** (extend these first for new rules): **prompt context** (`test_prompt_context.py`); **NMO legality** and narrative-mode contracts per existing governance docs; **`test_final_emission_gate.py`**; **`test_final_emission_validators.py`**; **`test_final_emission_repairs.py`**; **fallback** and downstream repair consumers as documented (not parallel derivation owners); **social emission** (`test_social_exchange_emission.py` and related strict-social paths per `TEST_AUDIT.md`).
- **Strict-social vs prompt stack (closeout):** exact duplicate **direct** validation for strict-social `question_resolution_rule_check` / first-sentence legality was moved to **`tests/test_social_exchange_emission.py`**. **`tests/test_prompt_and_guard.py`** keeps **smoke** near the prompt stack for that boundary, **`build_retry_prompt_for_failure`** text for unresolved-question / social-contract failures, and **`enforce_question_resolution_rule` prepend** behavior. **`downstream_consumer_suites`** and **`compatibility_residue_suites`** stayed **empty** (no Block D case justified populating them).

**Block D — inventory schema v2 + drift resistance**

- **`summary.inventory_schema_version` = 2** with **`summary.declared_pytest_markers`**, per-file **`likely_architecture_layer`**, **`marker_set`**, **`ownership_registry_positions`**, top-level **`ownership_registry_index`**, **`block_b_overlap_clusters`**, and **`import_hub_modules`** — all emitted by `tools/test_audit.py` and asserted by governance tests.
- **Neighbor-only overlap typing** — any path listed under a responsibility group must appear in exactly one neighbor field (or as `direct_owner`); heuristic inventory clusters remain **triage hints** and do not fail CI.
- **Intentional cross-file duplicate base names** (allowlisted): `test_deterministic_json_stable`, `test_version_constant`, `test_maybe_attach_respects_env` — see `tests/test_ownership_registry.py` → `_CROSS_FILE_DUPLICATE_ALLOWLIST`.

**Maintainer loop:** `tests/README_TESTS.md` → *Test ownership rules* and *Command cheat sheet*.

**Runtime map:** `docs/narrative_integrity_architecture.md` documents `game/` ownership (routing, continuity breaks, targeting, emission validators/repairs, **`final_emission_gate` orchestration**) and **explicit deferrals**. **Post-AER Consolidation Rules** and the **Consolidation Targets** table live there and in `docs/current_focus.md`.

**Validation layer seam (Objective #11):** Phase ownership (engine / planner / GPT / gate / evaluator) is governed by `docs/validation_layer_separation.md` and `game/validation_layer_contracts.py`. Block B residue and import/wording drift are optionally checked with `tools/validation_layer_audit.py` (see `docs/validation_layer_audit.md`); multiple files may implement one canonical layer without implying duplicate ownership.

**Terminology:** use **canonical owner**, **smoke overlap**, **deferred**, **orchestration**, and **deterministic / contract-driven** consistently with `tests/TEST_AUDIT.md`.

**Source:** Derived from `tests/TEST_AUDIT.md`, `tests/test_inventory.json` (regenerate via `py -3 tools/test_audit.py`), and spot review of transcript vs pipeline modules.

**Goal:** A concrete, low-risk roadmap so cleanup can run in small batches with full-suite checks between steps—prioritizing **final emission metadata packaging**, **telemetry/meta normalization**, and **test ownership** trimming aligned with runtime **orchestration** boundaries.

**Consolidation Block 1 (ownership):** The suite-wide **canonical ownership map** and **deferrals** live in `tests/TEST_AUDIT.md` → section *Consolidation Block 1 — Canonical ownership map & overlap hotspots*. **Prompt/sanitizer boundary** (this cluster) is recorded below so Block 2 can trim without re-deriving it.

### Prompt / sanitizer cluster — Block 1 (boundary confirmation; 2026-04-03)

**Confirmed ownership**

| File | Owns |
| --- | --- |
| `tests/test_prompt_and_guard.py` | **Pre-generation / pipeline guards:** `build_messages` payload and instructions, `SYSTEM_PROMPT` shape hooks, discoverable-clue justification (`allow_discoverable_clues` / intent), **retry** classification and **`build_retry_prompt_for_failure`** (including **retry prompt text** for unresolved-question / social-contract failures), **`guard_gm_output`** (spoiler / unjustified discoverables), **`enforce_npc_response_contract`**, **`enforce_question_resolution_rule` prepend** behavior, **`detect_retry_failures`**, uncertainty **classification + render** (`classify_uncertainty`, `render_uncertainty_response`, `choose_contextual_lead`, `resolve_known_fact_before_uncertainty`), **`apply_response_policy_enforcement`** ordering (incl. strict-social bypass), **`detect_validator_voice` / `enforce_no_validator_voice`** as **GM-side** enforcement + tags, scene momentum / generic phrase **detection** wired to policy. **Strict-social** `question_resolution_rule_check` / first-sentence **legality matrices** → `tests/test_social_exchange_emission.py` (this file keeps **smoke** only for that boundary). |
| `tests/test_output_sanitizer.py` | **Post-GM emit path:** `sanitize_player_facing_output`, `final_validation_pass`, `final_coherence_pass`, `rewrite_analytical_sentence`, extraction of leaked JSON payloads, **final** removal/rewrite of instructional strings, router/planner/validator **scaffold** leaks, duplicate collapse, **post-final strict-social clamp** / `gate_sealed_text` (boundary-only; thin vs repair cluster). |

**Overlap hotspots for Block 2 (1–2 only)**

1. **Procedural / instructional legality (“no answer presents itself…”, no “state exactly what you do”, no “scene offers no clear answer yet”).** Both files assert overlapping **player-visible** phrase bans / preferred fallbacks: e.g. `test_uncertainty_source_modes_render_distinct_voice_and_shape` (procedural branch in `test_prompt_and_guard.py`) vs `test_sanitizer_rewrites_procedural_engine_text`, `test_sanitizer_uses_procedural_insufficiency_fallback_for_adjudication_context`, and related sanitizer cases. **Invariant owner:** **`test_output_sanitizer.py`** (canonical for strings after sanitization). **`test_prompt_and_guard.py`** should **narrow** to **source/category** (e.g. `procedural_insufficiency`, shape/voice class) and at most **one** smoke phrase—or integration smoke—unless the assertion is strictly about **render helper** contract *before* sanitizer (document which layer if kept).

2. **Validator / analyst tone in player-facing text.** `enforce_no_validator_voice` + `_assert_bounded_uncertainty` in `test_prompt_and_guard.py` overlaps sanitizer tests that strip **role prefixes** and **validator/router/planner** scaffold terms (`test_sanitizer_strips_internal_role_prefixes`, `test_sanitizer_blocks_router_planner_validator_scaffold_terms`, analytical rewrites). **Invariant owner:** split by **layer** — **`test_prompt_and_guard.py`** owns **policy enforcement** (tags, integration with GM dict, uncertainty routing). **`test_output_sanitizer.py`** owns **final emitted string** cleanliness. **Reduce duplicate substring families** in Block 2: keep **detailed** forbidden-phrase / rewrite coverage in **sanitizer**; in **prompt/guard**, prefer **tags + minimal** smoke that the rewriter ran, not a second full legality list.

**Block 2 files to touch:** `tests/test_prompt_and_guard.py` (primary: thin procedural/validator **output** assertions toward smoke or source-only checks), `tests/test_output_sanitizer.py` (keep canonical phrase-level locks; optional cross-link comment only if helpful). **Do not** move ownership of `build_messages` / retry prompts / `guard_gm_output` into the sanitizer file.

**Validation:** `pytest --collect-only -q` after doc edits.

**Block 2 applied (2026-04-09):** In `test_prompt_and_guard.py`, the procedural branch of `test_uncertainty_source_modes_render_distinct_voice_and_shape` asserts `source` / `category` plus a short render smoke (length + terminal punctuation) instead of re-locking procedural fallback phrases owned by `test_output_sanitizer.py`. Validator enforcement tests use `detect_validator_voice(...) == []` plus tags (and diegetic preservation where relevant) instead of duplicating substring legality with `_assert_bounded_uncertainty` / explicit “as an AI” checks. `test_social_exchange_uncertainty_stays_npc_grounded_on_repeated_questions` dropped the redundant ban on `"nothing in the scene points to a clear answer yet"` (canonical post-GM phrase ban lives in `test_output_sanitizer.py`). One clarifying comment added on the adjudication procedural sanitizer test.

**Block C3 applied (2026-04-12 — prompt / sanitizer test ownership):** `build_retry_prompt_for_failure` string contracts moved from `test_transcript_regression.py` into `test_prompt_and_guard.py` (`test_retry_prompt_warns_against_known_gate_failure_shapes`, `test_retry_prompt_multi_lead_and_urgency_language`). Transcript retry-exhaustion tests use `detect_validator_voice(...) == []` on final player-facing text instead of locking the exact trap phrase. `test_gauntlet_regressions.py` sanitizer-adjacent cases weakened to “pipeline transformed the mocked GPT line” smoke plus one distinctive splice token; detailed substring families remain in `test_output_sanitizer.py`.

**Block C4 applied (2026-04-12 — social / emission ownership + transcript thinning):** Module docstrings clarify **engine** (`test_social.py`) vs **strict emission** (`test_social_exchange_emission.py`) vs **quality harness** (`test_social_emission_quality.py`). Renamed mislabeled `test_transcript_*` cases in `test_social_emission_quality.py` to `test_emission_quality_*` so transcript modules are not implied owners. `test_transcript_regression.py` social-grounding helper trimmed to a shorter marker set with an explicit “smoke only” comment. `test_lead_lifecycle_block3_transcript_regression.py` dropped a duplicate procedural phrase lock in favor of length + NPC-voice absence checks (sanitizer owns exact fallback strings).

**SE2-R applied (2026-04-13 — practical strict-social emission owner convergence):** `tests/test_social_exchange_emission.py` now carries the narrow direct-owner checks for terminal dialogue **application** semantics, while `tests/test_strict_social_emergency_fallback_dialogue.py` is explicitly scoped to downstream retry-terminal wiring, first-mention gate integration, and legacy `repair_*` compatibility coverage. `tests/test_social_emission_quality.py` and `tests/test_dialogue_interaction_establishment.py` remain secondary downstream / harness evidence rather than semantic owners. Governance docs now describe this seam as `game/social_exchange_emission.py` -> `tests/test_social_exchange_emission.py` -> named secondary downstream / compatibility suites, reducing the remaining mixed-owner signal without changing runtime behavior.

**Prompt-contract governance note (post-PC2):** Treat `game/prompt_context.py` as the canonical runtime owner and `tests/test_prompt_context.py` as the practical primary direct-owner suite for prompt-contract semantics and exported helper/bundle ownership. `tests/test_prompt_compression.py` remains secondary integration coverage, while `tests/test_prompt_and_guard.py`, `tests/test_dialogue_interaction_establishment.py`, `tests/test_fallback_shipped_contract_propagation.py`, `tests/test_social_escalation.py`, `tests/test_social_interaction_authority.py`, `tests/test_social_speaker_grounding.py`, `tests/test_social_topic_anchor.py`, `tests/test_stale_interlocutor_invalidation_block3.py`, `tests/test_strict_social_answer_pressure_cashout.py`, `tests/test_synthetic_sessions.py`, `tests/test_answer_completeness_rules.py`, `tests/test_turn_pipeline_shared.py`, and relevant gate/emission/transcript suites such as `tests/test_final_emission_gate.py`, `tests/test_social_exchange_emission.py`, and `tests/test_narration_transcript_regressions.py` are downstream consumers or prompt-adjacent evidence rather than co-equal owners. Support-only extraction residue may remain in `game/prompt_context_leads.py`, and exported consumer paths may keep consuming prompt-owned bundles without becoming prompt owners.

**FG2-R applied (2026-04-15 — final-emission gate governance alignment):** `game/final_emission_gate.py` remains the canonical runtime owner and `tests/test_final_emission_gate.py` remains the practical primary direct-owner suite for direct orchestration-order and final-route semantics. `tests/test_social_exchange_emission.py`, `tests/test_turn_pipeline_shared.py`, `tests/test_stage_diff_telemetry.py`, `tests/test_social_emission_quality.py`, `tests/test_dead_turn_detection.py`, and transcript/regression suites now read consistently as downstream emission-consumer, pipeline/request-shipping, observability, packaged-snapshot, or regression coverage rather than orchestration co-owners. `game/final_emission_meta.py` remains metadata packaging/read-side support only, and retry/compatibility adjacency remains support residue rather than a second orchestration home.

**GC2-R applied (2026-04-15 — final continuity-adjacent gate owner-story alignment):** `tests/test_interaction_continuity_speaker_bridge.py`, `tests/test_interaction_continuity_validation.py`, and `tests/test_interaction_continuity_repair.py` are now framed consistently as downstream bridge / validation / repair consumer coverage around an already-owned gate seam rather than practical orchestration homes. `tests/test_final_emission_gate.py` remains the place for direct continuity-adjacent gate-step semantics, including gate-private attachment/order assertions. The remaining residue to watch is narrow: `tests/test_interaction_continuity_repair.py` still touches `_apply_interaction_continuity_emission_step(...)`, which should stay support/compatibility residue unless a later pass can remove it cleanly.

**TD2-R applied (2026-04-15 — stage-diff telemetry governance alignment):** `game/stage_diff_telemetry.py` remains the canonical runtime owner for telemetry semantics, while `game/turn_packet.py` remains the packet-boundary owner. `tests/test_stage_diff_telemetry.py` is now the practical primary direct-owner suite for direct snapshot/diff/helper semantics and telemetry-owned observability fields. `tests/test_turn_packet_stage_diff_integration.py` remains downstream turn-packet + gate/retry consumer coverage, and `tests/test_narrative_authenticity_aer4.py` remains downstream narrative-authenticity regression / evaluator-consumer coverage. `game.stage_diff_telemetry.resolve_gate_turn_packet(...)` remains compatibility residue only, and packet/gate/retry adjacency remains support/consumption residue rather than telemetry co-ownership.

**RT7-R applied (2026-04-20 — Objective #7 referent seam: docs + regressions):** Runtime ownership and compact-vs-full boundaries are recorded in `docs/narrative_integrity_architecture.md` (*Objective #7*) and `tests/TEST_AUDIT.md` (*RT7-R*). Focused regressions extend `tests/test_final_emission_validators.py`, `tests/test_final_emission_gate.py`, and `tests/test_prompt_context.py`, with optional `tests/helpers/objective7_referent_fixtures.py` for JSON-safe stubs. Keep `validate_player_facing_referential_clarity` (`narration_visibility`) narratively separate from the prompt-artifact referent pack.

**Adjacent low-risk overlap trims (2026-04-09):**

- `tests/test_social.py`: generic-addressing “smoke” now avoids locking the exact `source` / `target_source` enum when the **canonical target id** is correct (vocative vs generic-role precedence is owned by `tests/test_social_target_authority_regressions.py`).
- `tests/test_scene_entity_lock.py`: offscene-npc chat smoke no longer hard-locks the global visibility fallback sentence (canonical phrase contract lives in emission-focused suites); it still asserts **no GPT call** (via monkeypatch), offscene targeting flags, and non-refusal narrator output.
- `tests/test_mixed_state_recovery_regressions.py`: removed the duplicate `targeted_retry_terminal` expectation from an emergent-actor continuity regression; retry terminal metadata is owned by the retry/repair regression cluster.

**Completed — routing / turn-pipeline cluster:** Restored `test_dialogue_routing_lock.py` as the home for the pure `choose_interaction_route` / dialogue-lock table (`test_choose_interaction_route_dialogue_lock_pure_contract`); removed that duplicate from `test_turn_pipeline_shared.py` and trimmed redundant `kind != adjudication_query` / GM substring checks where stronger assertions already held. `test_directed_social_routing.py` chat smoke cases dropped the redundant adjudication negation when `kind == "question"` already applied.

### Block 3 — Routing ownership (consolidation pass closed)

The following **routing ownership pattern** is now the explicit contract for new tests and overlap review. It reflects what the consolidation pass proved: three modules, three layers — not one mega-file.

| Module | Owns |
| --- | --- |
| `tests/test_turn_pipeline_shared.py` | Full-stack **`/api/chat`** and **`/api/action`** routing behavior; dialogue-lock **HTTP** regressions; **turn-trace-adjacent** flow; **end-to-end resolution** behavior. |
| `tests/test_dialogue_routing_lock.py` | The **pure routing-table / dialogue-lock contract** (e.g. `choose_interaction_route`) **without** `TestClient`. |
| `tests/test_directed_social_routing.py` | **Directed-social precedence**, **vocative overrides**, **segmentation**, **narrow directed `/api/chat` scenarios**, and **emergent-actor targeting** behavior. |

**Intentional duplication:** Some phrases or scenarios appear in **both** pure-routing / table coverage (`test_dialogue_routing_lock.py`, aspects of `test_directed_social_routing.py`) **and** full-pipeline coverage (`test_turn_pipeline_shared.py`) because they assert **different layers** (unit/table vs HTTP/stack vs resolution). That overlap is expected unless a later pass maps a specific case to a single layer with a replacement strategy.

### Next consolidation order (after routing; Block C1 canonical)

Work the clusters in this order unless a release forces a narrow fix:

1. ~~**Repair / retry cluster**~~ — **Closed enough for now**: applied ownership recorded in *Repair / retry cluster — Block 3*; further edits are optional thinning only.
2. **Runtime alignment (parallel doc-driven)** — **Final emission metadata packaging** and **narrative authenticity telemetry shape / reuse** under `apply_final_emission_gate` **orchestration** (see `docs/narrative_integrity_architecture.md` → **Consolidation Targets**). Tests should follow, not lead, ambiguous emit-path moves.
3. **Prompt / sanitizer cluster** — `test_prompt_and_guard.py`, `test_output_sanitizer.py`, symptom-based split (messages-to-model vs post-GM output); reduce duplicate phrase locks in favor of one **canonical owner** per string family plus **smoke overlap** where layers differ (**Block 2** partial application already recorded above).
4. **Social / emission** — `test_social_exchange_emission.py`, `test_social_escalation.py`, `test_social.py` migration, emission-quality harness alignment; clarify social vs strict-social **orchestration** test homes.
5. **Transcript duplicate assertion thinning** — `test_transcript_regression.py`, gauntlet modules, and related harnesses: keep **deterministic** sequencing/state checks; **deferred** heavy deletes until each case has a replacement **contract-driven** owner.
6. **Lead / clue** — **Deferred** until steps **3–4** complete — includes `test_social_destination_redirect_leads.py` (destination-redirect / pending-lead contract); overlap reduction is normal consolidation, not a blocker for earlier clusters.

### Repair / retry cluster — Block 1–2 (history)

**Block 1:** Ownership confirmation (2026-04-03). **Block 2:** Thin pass on `test_contextual_minimal_repair_regressions.py` / `test_empty_social_retry_regressions.py` — trimmed duplicate `targeted_retry_terminal` / prose where wiring smoke suffices; kept fixture-specific phrase coverage where contexts differ.

### Repair / retry cluster — Block 3 (applied ownership; cluster closed enough)

**Status:** **Complete enough for now** (documentation only; no further refactors in this cluster pass). This is the **enforced** split after Block 2; intentional overlap below is acceptable when layers differ.

| File | Owns (applied) |
| --- | --- |
| `tests/test_contextual_minimal_repair_regressions.py` | Branch-specific **repair behavior**; **`debug_notes` detail**; **repair-line legality**; **scene-anchor vs hard-line** distinctions (nonsocial); **payload-shape guards** (no unwanted `clues` / `scene_update` / discoverables). |
| `tests/test_empty_social_retry_regressions.py` | **Retry/fallback wiring**; **`accepted_via`**; **`targeted_retry_terminal`**; **`retry_exhausted`**; **`fallback_kind` / `final_route`**; **`_final_emission_meta` continuity**; **`/api/chat` repair integration** behavior. |

**Intentional overlap (OK):**

- The **same helper surface** may still appear in **both** files when **fixture/runtime context** differs — each file asserts what that harness is for.
- **Phrase/prose checks** may live in one file while the other covers a **different branch** — acceptable when they assert **different layers** (e.g. deep repair contract vs retry metadata + smoke).

**Block 2 outcomes recorded (examples):**

- Contextual file **no longer owns** `targeted_retry_terminal` — that belongs with retry/wiring in `test_empty_social_retry_regressions.py`.
- Empty-social file **no longer re-locks** contextual prose/detail where **wiring/smoke** is sufficient.
- **“They answer cautiously”** remains **intentionally** in the exhausted-helper **minimal social** path (`test_empty_social_retry_regressions.py` — fixture distinct from tavern contextual repair cases).
- **Nonsocial empty metadata** remains owned by **`test_ensure_minimal_nonsocial_resolution_fills_empty_text`** in `test_empty_social_retry_regressions.py` (integration/metadata), while scene-anchor vs hard-line and legality stay with the contextual file.

**Pipeline re-locks (adjacent; not primary repair owners):**

- `tests/test_output_sanitizer.py` — e.g. post-final gate / `strict_social_terminal_clamp` with empty output returning `gate_sealed_text`: **sanitizer-boundary** contract; keep **thin** relative to `ensure_minimal_*` / `force_terminal_*` in the repair cluster.
- `tests/test_prompt_and_guard.py` — e.g. `detect_retry_failures`, `build_retry_prompt_for_failure`, validator-voice enforcement: **retry classification and prompt/guard** contracts; **do not** treat as the home for minimal repair line content (symptom split: messages-to-model vs post-GM output stays as in §3 R3).

**Repair cluster files:** **Canonical owners** are the two regression modules above; further thinning is **optional** and **not** part of this closed cluster. **Optional later:** targeted thinning in `tests/test_output_sanitizer.py` or `tests/test_prompt_and_guard.py` only where a specific assertion **duplicates** a repair lock; broader work is the **prompt/sanitizer** batch (*Next consolidation order* step **3**).

**Validation:** `pytest --collect-only -q` — green after documentation-only passes.

---


## 1. Short summary

### Over-tested (redundant *surface area*, not necessarily redundant *value*)

- **Clue + legality + routing themes** appear across many files (audit: clue system in ~19 files; legality/sanitizer ~14; routing ~11). Multiple modules can assert similar high-level outcomes with different harness depth.
- **Large integration files** concentrate many scenarios in one place: `test_turn_pipeline_shared.py` (~53 items), `test_prompt_and_guard.py` (~67), `test_social_exchange_emission.py` (~43), `test_output_sanitizer.py` (~41). New cases have historically landed in “kitchen sink” files instead of extending a single canonical home. (Approximate counts — re-run `pytest --collect-only` for live totals.)
- **Social behavior** is spread across `test_social.py`, `test_social_exchange_emission.py`, `test_social_escalation.py`, `test_directed_social_routing.py`, and others — overlap is *thematic*, not name-collision (audit: 0 identical cross-file test names).

### Fragile (high churn / prose-sensitive / expensive)

- **Transcript and regression modules** dominate high-brittleness counts (audit): `test_transcript_regression.py`, `test_lead_lifecycle_block3_transcript_regression.py`, `test_mixed_state_recovery_regressions.py`, `test_transcript_gauntlet_actor_addressing.py`, `test_empty_social_retry_regressions.py`, `test_transcript_gauntlet_campaign_cleanliness.py`, plus scattered cases in `test_prompt_and_guard.py` and others.
- **Prose-sensitive assertions** are few in count (audit: ~7 prose-sensitive items) but disproportionately painful when prompts or copy change.
- **Scope marker debt:** `unit` / `integration` / `regression` adoption is still uneven at module level; audit heuristics do not mirror those tags. **Fast vs full lanes** still use `pytest -m "not transcript and not slow"` (see `tests/README_TESTS.md`) regardless — that is selection/composition, not “all green.”

### Under-protected

- **`test_exploration_resolution.py`:** Module-level `test_*` names are unique and collected count matches intent (see `tests/TEST_AUDIT.md` and `pytest --collect-only`). Keep using distinct names or parametrization so `tools/test_audit.py` never reports in-file shadowing.
- **Tagging / “general” bucket:** Many tests fall through to `general` in audit feature tags, which obscures true gaps vs redundancy.

---

## 2. Classification

### A. Keep as canonical (extend here first)

| Area | Canonical files / examples |
| --- | --- |
| Full `/api/chat` + `/api/action` stack, dialogue-lock HTTP regressions, turn-trace-adjacent flow, end-to-end resolution | `test_turn_pipeline_shared.py` |
| Pure dialogue-lock / routing table (no `TestClient`) | `test_dialogue_routing_lock.py` |
| Directed-social precedence, vocative overrides, segmentation, narrow directed `/api/chat`, emergent-actor targeting | `test_directed_social_routing.py` |
| Emit-time sanitizer | `test_output_sanitizer.py` |
| Prompt construction + guard contracts | `test_prompt_and_guard.py` |
| Strict social / emission shape | `test_social_exchange_emission.py` |
| Escalation / pressure state machine | `test_social_escalation.py` |
| Retry prioritization | `test_social_answer_retry_prioritization.py` |
| Clue idempotency / gateway | `test_clue_knowledge.py`, `test_world_updates_and_clue_normalization.py` |
| Mixed-state & social continuity | `test_mixed_state_recovery_regressions.py`, `test_dialogue_interaction_establishment.py` |
| Empty social + terminal retry + API repair | `test_empty_social_retry_regressions.py` |
| Repair payload / legality invariants | `test_contextual_minimal_repair_regressions.py` |
| End-to-end transcript sequencing | `test_transcript_regression.py` |
| Gauntlet / harness slice | `test_transcript_gauntlet_*.py`, `test_transcript_runner_smoke.py` |
| Exploration resolution | `test_exploration_resolution.py` + `test_exploration_skill_checks.py` |

### B. Merge / reduce (planned actions — execute later in batches)

See **§3** for per-item detail. High-level targets:

- Share helpers/fixtures between repair-focused regression files without merging scenarios blindly.
- Route new social strict assertions to `test_social_exchange_emission.py`; shrink `test_social.py` to true misc only or fold cases into canonical files.
- Reduce transcript vs integration **double-locking** where a smaller test already pins the same invariant.
- In `test_exploration_resolution.py`, prefer **parametrize or distinct names** for variants so module-level duplicate `def test_*` names never reappear (audit script surfaces those).

### C. Leave alone for now

- **`test_inventory.json` / `tools/test_audit.py`:** Inventory tooling; keep until consolidation stabilizes.
- **Files with single high-brittleness tests** (`test_agenda_simulation.py`, `test_clue_discovery.py`, `test_emergent_scene_actors.py`, `test_gauntlet_regressions.py`): not priority targets until broader batches complete.
- **World/state, snapshots, save/load, schema, clocks/lint:** Lower overlap in audit; avoid drive-by merges.
- **Broad scope-marker refactors:** Defer mass `unit` / `integration` / `regression` cleanup until done in small batches; optional `brittle` / extra `slow` tuning can follow the same pilot pattern (§5).
- **Consolidation Block 1 explicit deferrals:** No broad merge of `test_prompt_and_guard.py` or `test_turn_pipeline_shared.py`; no regression/transcript deletion without nodeid replacement map.

### D. Block 2 — clusters (routing done; remaining batches)

Routing three-module split is **complete** (Block 3 above). Repair/retry pair is **closed enough** (*Repair / retry cluster — Block 3*). Overlap reduction and marker cleanup elsewhere — **not** wholesale rewrites:

1. ~~`test_turn_pipeline_shared.py`, `test_directed_social_routing.py`, `test_dialogue_routing_lock.py`~~ — **routing pass closed**; only thinning with a replacement strategy if needed later.
2. ~~`test_contextual_minimal_repair_regressions.py`, `test_empty_social_retry_regressions.py`~~ — **repair/retry cluster closed enough** (applied ownership in Block 3 doc).
3. **Emit-path / telemetry alignment (doc-first)** — keep tests aligned with `final_emission_gate` **orchestration** and metadata packaging decisions (`docs/narrative_integrity_architecture.md` **Consolidation Targets**).
4. **Next (tests):** `test_prompt_and_guard.py`, `test_output_sanitizer.py` (prompt/sanitizer batch; **canonical owner** per layer, **smoke overlap** only).
5. **Then:** `test_social.py`, `test_social_exchange_emission.py`, `test_social_escalation.py` (social/emission migration).
6. **Transcript thinning:** `test_transcript_regression.py`, `test_lead_lifecycle_block3_transcript_regression.py`, `test_gauntlet_regressions.py`, `test_social_emission_quality.py` (module-level transcript policy) — prefer **deterministic** structural checks over duplicate prose locks.
7. **Lead / clue cluster** — **`deferred`** until **4–5** complete: `test_social_lead_landing.py`, `test_clue_lead_registry_integration.py`, `test_social_destination_redirect_leads.py` (see *Next consolidation order* above).

---

## 3. Proposed consolidation items (detail)

Each row is a **future** change candidate. **Do not** execute without a replacement strategy for regression locks.

| ID | Tests / files involved | Overlap reason | Proposed action | Risk |
| --- | --- | --- | --- | --- |
| R1 | `test_contextual_minimal_repair_regressions.py` ↔ `test_empty_social_retry_regressions.py` | Both touch contextual/minimal repair and social empties; shared helper behavior | **Merge:** extract shared fixtures/helpers to `tests/conftest.py` or a new helper module under `tests/helpers/`; **do not** merge scenario lists until ownership split is clear (retry/API vs payload/legality). Optionally **weaken** duplicated prose checks if one file keeps the strict version. | Low (helpers only); Medium if merging test bodies |
| R2 | `test_turn_pipeline_shared.py` ↔ `test_directed_social_routing.py` ↔ `test_dialogue_routing_lock.py` | Dialogue lock, routing, and social boundaries recur at different depths | **Ownership settled** (Block 3). **Future thinning only:** add new routing cases to `test_directed_social_routing.py` unless full pipeline required; **avoid** a fourth parallel routing file. **Weaken** only duplicate assertions already structurally locked in the smaller file. | Medium |
| R3 | `test_output_sanitizer.py` ↔ `test_prompt_and_guard.py` | Legality strings, validator voice, sanitization | **No file merge.** **Move** new cases by symptom: post-GM output → sanitizer; messages-to-model → prompt/guard. **Weaken** cross-file duplicate string equality if one side keeps canonical assertion. | Low |
| R4 | `test_social.py` ↔ `test_social_exchange_emission.py` ↔ `test_social_escalation.py` | Broad “social” vocabulary | **Reduce:** migrate strict emission tests into `test_social_exchange_emission.py`; keep escalation in `test_social_escalation.py`. **Delete** from `test_social.py` only after migration (replacement required). | Medium |
| R5 | `test_transcript_regression.py` ↔ `test_turn_pipeline_shared.py` / other integration tests | Multi-step flows may re-assert the same gate (e.g. routing, emission) already covered in pipeline tests | **Reduce overlap:** drop or **weaken** transcript assertions that duplicate a named integration/regression test; keep transcript steps that prove **ordering** or **cross-turn state**. **Move** heavy cases to `@pytest.mark.slow` + `@pytest.mark.transcript` consistently. | Medium–High |
| R6 | `test_transcript_gauntlet_*.py` ↔ `test_gauntlet_regressions.py` ↔ `test_transcript_regression.py` | All exercise long / harness-style flows; gauntlet files are LTC-slice focused | **Merge/reduce:** consolidate **shared harness fixtures** only; keep slice-specific files until one module owns “gauntlet runner” smoke. **Marker-only:** ensure gauntlet + transcript regression share `transcript` + `slow` (and `brittle` where prose-bound). | Medium |
| R7 | `test_exploration_resolution.py` (internal) | Risk of reintroducing duplicate top-level `test_*` names (Python shadowing) | **Prevent:** rename or **parametrize** variants; run `tools/test_audit.py` after large edits. | Low |
| R8 | Multiple clue-tagged files (`test_clue_knowledge.py`, `test_clue_discovery.py`, `test_discovery_memory.py`, …) | Thematic spread; not automatic duplicates | **Leave** canonical clue tests; **merge** only after side-by-side read. Prefer **weaken** redundant prose in peripheral files after `test_clue_knowledge.py` owns idempotency/gateway. | Medium |

---

## 4. Transcript tests: value vs duplication

### 4.1 Valuable — should remain (possibly slimmed, not removed without replacement)

- **`test_transcript_regression.py` (module):** Protects **multi-step sequencing** and play-loop state transitions; explicitly deterministic, no live GPT. Keep as the **canonical end-to-end transcript** suite unless each scenario’s ordering guarantees exist elsewhere.
- **`test_transcript_runner_smoke.py`:** Validates the transcript runner / harness wiring; cheap sanity check for the gauntlet toolchain.
- **`test_lead_lifecycle_block3_transcript_regression.py`:** Multi-turn lead lifecycle story on the transcript harness; own **cross-turn lifecycle ordering**, not single-turn routing tables duplicated elsewhere.
- **`test_transcript_gauntlet_actor_addressing.py`:** Address stability under validation (audit cites explicit-address test as canonical example).
- **`test_transcript_gauntlet_campaign_cleanliness.py`:** Campaign/scene cleanliness invariants for the gauntlet slice.

### 4.2 Likely duplicate of smaller integration / regression tests

- Any **transcript** case whose failure mode is already a **single-turn** assertion in `test_turn_pipeline_shared.py`, `test_directed_social_routing.py`, `test_dialogue_routing_lock.py`, or focused regression files (e.g. empty social repair, dialogue lock → social lane). **Strategy:** keep the **smaller** test as structural truth; in transcript, **weaken** to milestone checks (state keys, routes) or remove redundant substring locks.
- **`test_gauntlet_regressions.py`** vs **`test_transcript_regression.py`:** Overlap risk on “session transcript” outcomes — reconcile by **scenario ownership** (one file = harness gate stories, the other = general play-loop regressions) before deleting either.

### 4.3 Regression tests — do not remove without a replacement

These encode historical bug locks or narrow invariants; removal requires **either** merged equivalent assertion **or** explicit product decision:

| File | Rationale |
| --- | --- |
| `test_mixed_state_recovery_regressions.py` | Mixed narration / social continuity; audit lists canonical examples here |
| `test_empty_social_retry_regressions.py` | Terminal retry, API repair, emission continuity |
| `test_contextual_minimal_repair_regressions.py` | Repair must not inject clue/resolution payloads; legality of repair lines |
| `test_social_target_authority_regressions.py` | Social target authority regressions |
| `test_gauntlet_regressions.py` | Gauntlet-specific regression locks |
| `test_transcript_regression.py` | End-to-end transcript regressions |
| `test_transcript_gauntlet_*.py` | Slice-specific gauntlet regressions |

**Replacement rule:** Before delete, require a **nodeid mapping** (old test → new owning test or parametrized case) in the PR that performs the merge.

---

## 5. Recommended order of operations

Execute **one bullet per PR** (or smaller), then **full test suite** (`pytest` from repo root). Use `py -3 tools/test_audit.py` after structural changes to refresh inventory.

1. **Keep exploration tests collectible:** When adding cases in `test_exploration_resolution.py`, use unique top-level names or parametrization; re-run `pytest --collect-only` and `tools/test_audit.py` after bulk edits. *Risk: none if naming discipline holds.*
2. **Weaken brittle prose assertions (pilot):** Pick one high-brittleness file (e.g. a single `test_transcript_gauntlet_*.py` or one `test_transcript_regression.py` case). Replace fragile substring locks with structural checks where a canonical integration test already covers wording. Mark remaining prose-bound tests `@pytest.mark.brittle`. *Validates marker workflow.*
3. **Tighten transcript/slow/brittle tagging:** Keep `test_transcript_gauntlet_*.py`, `test_transcript_regression.py`, and long harness tests aligned with `transcript` + `slow` where appropriate; add `brittle` where prose remains. **Fast vs full commands** are already documented in `tests/README_TESTS.md`.
4. **Extract shared helpers (R1, R6):** Move duplicate `_patch_storage` / seed helpers into shared test utilities **without** deleting tests. *Low risk.*
5. **Merge duplicate regression scenarios (R2, R4, R5):** After helper dedup, merge **only** pairs that have been read side-by-side; keep mapping table of removed nodeids → replacements.
6. **Reduce transcript overlap (R5, R6):** Remove or slim transcript steps only when covered by smaller tests; prefer **weaken** before **delete**.
7. **Periodic audit:** After each batch, regenerate `test_inventory.json` and spot-check high-brittleness counts in `TEST_AUDIT.md` methodology section.

---

## Acceptance criteria (this document)

| Criterion | Met by |
| --- | --- |
| Concrete roadmap, no blind deletions | §3 table: every item lists action, files, and risk; §4.3 replacement rule |
| Small safe batches | §5 ordered steps with “one PR + full suite” between |
| Canonical vs merge vs defer | §2A / §2B / §2C |
| Transcript and regression explicitly classified | §4.1–§4.3 |

---

## References

- `tests/README_TESTS.md` — full lane, fast lane, stricter fast, collect-only, Windows `py -3 -m pytest`.
- `tests/TEST_AUDIT.md` — counts, brittleness leaders, canonical examples, duplicate-name guardrail notes.
- `tests/test_inventory.json` — per-item `nodeid`, buckets, heuristics.
- `pytest.ini` — markers: `unit`, `integration`, `regression`, `transcript`, `slow`, `brittle`.
