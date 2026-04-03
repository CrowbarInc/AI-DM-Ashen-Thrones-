# Test suite audit (Block 15A)

Diagnostic inventory of `tests/` only: no runtime code or assertions were changed for this pass. **How to run tests (fast/full lanes, collect-only, Windows):** `tests/README_TESTS.md`.

**Regenerate artifacts:** from repo root run `py -3 tools/test_audit.py` (or `python tools/test_audit.py`). That refreshes `tests/test_inventory.json` using `pytest --collect-only` plus static heuristics. The script prints a one-line summary of **module-level duplicate `test_*` names** (shadowed defs); details are in JSON under `summary.files_with_shadowed_duplicate_test_defs`. It also prints a short **overlap spread** line (themes by distinct file count; heuristic, not semantic duplicate detection).

**Counts in this markdown** were reconciled with `tests/test_inventory.json` on 2026-04-03. For live numbers after adding tests, re-run the audit and read `summary` / `files` in that JSON (the full per-file table is not duplicated here).

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

### Repair / retry consolidation — applied ownership (Block 3 doc, 2026-04-03)

Cluster **closed enough** for this pass: enforced split and intentional overlap are recorded in `tests/TEST_CONSOLIDATION_PLAN.md` → *Repair / retry cluster — Block 3*. **Next batch:** prompt/sanitizer → social/emission → lead/clue (same plan → *Next consolidation order*).

### Canonical owners by theme

| Theme | Primary owner(s) | Integration smoke only (examples) |
| --- | --- | --- |
| **Routing / turn pipeline** | `test_turn_pipeline_shared.py` — full **`/api/chat`** and **`/api/action`** stack, dialogue-lock HTTP, turn-trace-adjacent flow, end-to-end resolution; `test_dialogue_routing_lock.py` — pure `choose_interaction_route` / dialogue-lock **table** (no `TestClient`); `test_directed_social_routing.py` — directed-social precedence, vocative overrides, segmentation, narrow directed `/api/chat`, emergent-actor targeting; `test_intent_parser.py` / `test_intent_and_runtime.py` — parse/runtime intent. | `test_mixed_state_recovery_regressions.py`, `test_exploration_resolution.py`, `test_social.py` — keep **narrative or scenario-specific** routing checks, not a second copy of table locks. |
| **Social escalation / emission / quality** | `test_social_exchange_emission.py` — strict exchange shape / emission; `test_social_escalation.py` — pressure / escalation state machine; `test_social_answer_retry_prioritization.py` — retry vs stall prioritization; `test_social_target_authority_regressions.py` — authority regressions. | `test_social_emission_quality.py` — multi-turn / quality harness (align module-level `transcript` policy in Block 2); `test_dialogue_interaction_establishment.py` — establishment flows; `test_social.py` — **misc** only until migrated. |
| **Lead lifecycle / clue / pending / registry** | `test_clue_knowledge.py`, `test_clue_idempotence.py` — clue idempotency / gateway; `test_world_updates_and_clue_normalization.py` — normalization; `test_clue_lead_registry_integration.py` — clue↔lead registry wiring; `test_lead_engine_upsert.py` — engine upsert; `test_follow_lead_commitment_wiring.py` — follow/commitment wiring; focused `test_lead_*.py` modules — obsolescence, payoff, NPC authority, resolution endings, etc.; `test_lead_lifecycle_block3_transcript_regression.py` — **multi-turn** lifecycle story. | `test_social_lead_landing.py`, `test_turn_pipeline_shared.py`, `test_prompt_and_guard.py`, `test_social_exchange_emission.py` — **smoke** or cross-cutting hooks, not a second registry spec. |
| **Transcript / gauntlet vs smaller tests** | `test_transcript_regression.py` — general play-loop / sequencing; `test_transcript_gauntlet_*.py` — slice-specific harness contracts; `test_transcript_runner_smoke.py` — runner wiring; `test_gauntlet_regressions.py` — API-style gauntlet regressions (name ≠ transcript harness). | `test_lead_lifecycle_block3_transcript_regression.py`, `test_mixed_state_recovery_regressions.py` — own their **story**; avoid duplicating single-turn gates covered elsewhere. |
| **Repair / fallback / legality / sanitizer** | **`test_contextual_minimal_repair_regressions.py`** — branch-specific repair behavior, `debug_notes` detail, repair-line legality, scene-anchor vs hard-line (nonsocial), payload-shape guards (no unwanted `clues` / `scene_update` / discoverables). **`test_empty_social_retry_regressions.py`** — retry/fallback wiring, `accepted_via`, `targeted_retry_terminal`, `retry_exhausted`, `fallback_kind` / `final_route`, `_final_emission_meta` continuity, `/api/chat` repair integration; nonsocial empty metadata in `test_ensure_minimal_nonsocial_resolution_fills_empty_text`. **`test_output_sanitizer.py`** — emit-time sanitizer; **`test_prompt_and_guard.py`** — prompt + guard; **`test_debug_payload_spoiler_safety.py`** — spoiler/debug safety. | Same helper may appear in **both** repair regression files when **fixtures differ**; phrase checks may split by **branch/layer** — see consolidation plan *Repair / retry cluster — Block 3*. Pipeline/mixed-state **smoke** only, not parallel legality suites. |

### Overlap hotspots (short list)

Heuristic tags (`test_inventory.json` → `feature_areas_by_distinct_files`) show **many files** touching the same themes; the hotspots below are the highest-risk *semantic* overlap areas for double-locking:

1. **Lead extraction + clue system** — **26** / **24** files respectively; many `test_lead_*.py` modules plus `test_social_lead_landing.py`, `test_clue_lead_registry_integration.py`, pipeline, and prompt/guard.
2. **Resolution / emission** — **21** files; `test_social_exchange_emission.py`, `test_turn_pipeline_shared.py`, `test_social_emission_quality.py`, `test_social.py`, and several lead payoff modules.
3. **Routing** — **15** files; pipeline vs `test_directed_social_routing.py` vs exploration/social misc.
4. **Legality / sanitizer + fallback** — **16** files each; repair regressions overlap with sanitizer, prompt/guard, and pipeline.
5. **Social continuity** — **15** files; `test_social.py`, `test_directed_social_routing.py`, `test_mixed_state_recovery_regressions.py`, `test_turn_pipeline_shared.py`, emission quality.

### Block 2 — concrete files to touch next

Prioritize **marker normalization + overlap trimming** (not mass deletion). **Routing** and **repair/retry** consolidation passes are **closed enough** for their doc blocks (`TEST_CONSOLIDATION_PLAN.md`). **Suggested batch order** now: **prompt/sanitizer** → **social/emission** → **lead/clue** — see *Next consolidation order* in that plan.

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

**Per-test rows:** `tests/test_inventory.json` — each collected pytest item includes `nodeid`, heuristic `primary_bucket`, `feature_areas`, `historically_motivated`, `assertion_style`, `brittleness`, and `redundancy_flag` (cross-file name collisions are rare; see limitations below).

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
   - Path matches `tests/test_transcript_gauntlet_*.py`.  
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

- **Module-level `pytestmark` today:** 18 files set lane-related markers (`unit` / `integration` / `regression` / `transcript` / `slow` / `brittle`). The other **60** `test_*.py` files have **no** module-level lane markers yet.
- **Per-test markers:** `test_turn_pipeline_shared.py` adds `unit`+`regression` on one test while the module is `integration`. `test_social_emission_quality.py` marks `transcript` on a subset of tests only — normalize in Block 2.
- **`test_prompt_and_guard.py`:** module is `brittle` only — add `integration` (or `unit`) alongside `brittle` so scope is explicit for inventory and optional filters.

**Optional narrow filter:** `pytest -m "(unit or regression) and not transcript"` is **not** the fast lane — it collected **69** tests in **10** files when last checked (2026-04-02) because most modules are not tagged `unit`/`regression` at module level. **Primary fast lane** remains `pytest -m "not transcript and not slow"` (documented in `tests/README_TESTS.md`).

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

Verified from repo root with `pytest` / `pytest --collect-only` (2026-04-03):

| Command | Result |
| --- | --- |
| `pytest --collect-only -q` | **887** tests collected |
| `pytest --collect-only -m "not transcript and not slow" -q` | **853** collected, **34** deselected |

The **34** deselected items match the **`transcript` or `slow`** slice (`pytest --collect-only -m "transcript or slow"` → 34 collected), so the fast lane is the complement of that slice.

---

## Executive counts

| Metric | Value |
| --- | ---: |
| Test files (`tests/test_*.py`) | 78 |
| Pytest collected items | 887 |
| Module-level `def test_*` lines (AST, summed per file) | 862 |
| Unique top-level `test_*` names per file (AST; matches def count when no shadowing) | 862 |
| Parametrized expansion (collected − AST def lines, suite-wide) | 25 |
| Items flagged `historically_motivated` (heuristic) | 68 |
| Assertion style (heuristic, per collected item) | structural 239, behavioral 599, mixed 38, prose-sensitive 11 |
| Brittleness (heuristic) | low 704, medium 148, high 35 |
| Redundancy flag `possible_overlap` from identical test names across files | 0 |

### Counts by test-level primary bucket

Derived per collected item (filename hint + body heuristics): **integration** 481, **unit** 358, **regression** 41, **transcript_gauntlet** 7.

### Counts by file-level primary bucket

`primary_bucket` on each file record is the **majority** bucket among that file’s collected tests: **integration** 46 files, **unit** 24, **transcript_gauntlet** 2, **regression** 6. The JSON field `filename_bucket` records path-pattern hints only (`transcript_gauntlet`, `regression`, or `mixed/unclear`).

---

## Module-level duplicate `test_*` names (guardrail)

If the same top-level `def test_foo` appears twice in one module, Python keeps only the last definition; pytest then collects **one** item for that name and earlier bodies never run. **`tools/test_audit.py` detects this** (AST duplicate names per file) and reports it on stdout and in `tests/test_inventory.json` → `summary.files_with_shadowed_duplicate_test_defs`.

`tests/test_exploration_resolution.py` currently has **38** unique top-level `test_*` names, **38** AST def lines (no shadowing), and **42** collected items (one parametrized test adds 4 extra cases). An older version of this audit text incorrectly claimed mass shadowing here; that was **stale documentation** — the live source of truth is `pytest --collect-only` plus the audit JSON.

---

## Top files by count of high-brittleness tests (heuristic)

Snapshot from `test_inventory.json` → `top_high_brittleness_files` (2026-04-03):  
`test_mixed_state_recovery_regressions.py` — 6; `test_transcript_regression.py` — 5; `test_empty_social_retry_regressions.py`, `test_social_emission_quality.py`, `test_transcript_gauntlet_actor_addressing.py` — 4 each; then several files at 3 or 1. Re-run the audit for an updated ordered list.

---

## Top 10 “likely overlap” **areas** (by spread across files)

These are **feature tags** (keyword heuristics), not proof of duplicate tests. High file counts mean trims/consolidation require reading tests, not deleting by tag.

| Rank | Feature tag (heuristic) | Distinct files touching tag (any position) |
| --- | --- | ---: |
| 1 | lead extraction | 26 |
| 2 | clue system | 24 |
| 3 | resolution/emission | 21 |
| 4 | general | 20 |
| 5 | legality/sanitizer | 16 |
| 6 | fallback | 16 |
| 7 | routing | 15 |
| 8 | social continuity | 15 |
| 9 | world/state | 11 |
| 10 | retry | 11 |

The **general** bucket still indicates tagging debt where modules do not match keyword rules; refine rules or add explicit `# feature:` / markers over time. Re-run the audit to refresh this table.

---

## Candidate canonical suites by feature area

Use as starting points when deciding where new coverage should live first.

| Area | Strong candidate files |
| --- | --- |
| End-to-end / session transcript flows | `test_transcript_regression.py`, `test_gauntlet_regressions.py` |
| Transcript gauntlet (LTC slice / harness) | `test_transcript_gauntlet_*.py`, `test_transcript_runner_smoke.py` |
| Mixed-state & social continuity | `test_mixed_state_recovery_regressions.py`, `test_dialogue_interaction_establishment.py` |
| Retry / empty social / terminal fallback | `test_empty_social_retry_regressions.py`, `test_social_answer_retry_prioritization.py` |
| Contextual minimal repair | `test_contextual_minimal_repair_regressions.py` |
| Shared chat/action pipeline | `test_turn_pipeline_shared.py` |
| Social emission / strict social | `test_social_exchange_emission.py`, `test_social_answer_candidate.py` |
| Directed routing & dialogue lock | `test_directed_social_routing.py`, `test_dialogue_routing_lock.py` |
| Clue knowledge & inference | `test_clue_knowledge.py`, `test_world_updates_and_clue_normalization.py` |
| Output / legality | `test_output_sanitizer.py`, `test_prompt_and_guard.py`, `test_debug_payload_spoiler_safety.py` |
| Exploration resolution | `test_exploration_resolution.py`, `test_exploration_skill_checks.py` |

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
| Final emission gate (invalid blob replacement) | `tests/test_turn_pipeline_shared.py::test_final_emission_gate_replaces_invalid_social_exchange_blob_before_emit` |
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
   - **Merge/weaken:** When a failure is “output shape after GM,” add sanitizer tests; when “messages to model,” add prompt/guard tests.

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

`primary_bucket` = majority of tests in that file. `High-brittleness` = count of tests with heuristic `brittleness: high` in that file. Feature tags = top primary feature labels (first keyword hit per test, aggregated).

**Authoritative list:** All `tests/test_*.py` rows (78 files) live in `tests/test_inventory.json` → `files`. The table below is a partial snapshot; rows for newer modules may be missing until this section is expanded.

| File | Collected | Primary bucket (majority of tests) | High-brittleness tests | Top primary feature tags |
| --- | ---: | --- | ---: | --- |
| test_activate_scene_validation_and_get_persistence.py | 6 | integration | 0 | general |
| test_affordance_generation.py | 12 | integration | 0 | general |
| test_agenda_simulation.py | 9 | unit | 1 | general |
| test_campaign_reset.py | 5 | integration | 0 | world/state |
| test_campaign_state_factory.py | 3 | unit | 0 | world/state |
| test_clocks_projects_logging_lint.py | 5 | integration | 0 | general, clue system |
| test_clue_discovery.py | 4 | integration | 1 | clue system |
| test_clue_knowledge.py | 10 | integration | 0 | clue system |
| test_combat_resolution.py | 6 | integration | 0 | resolution/emission |
| test_conditional_affordances.py | 14 | unit | 0 | general, clue system |
| test_contextual_minimal_repair_regressions.py | 6 | regression | 0 | fallback |
| test_debug_payload_spoiler_safety.py | 3 | integration | 0 | legality/sanitizer |
| test_dialogue_interaction_establishment.py | 10 | integration | 0 | social continuity |
| test_dialogue_routing_lock.py | 5 | unit | 0 | routing |
| test_directed_social_routing.py | 21 | integration | 0 | routing, social continuity |
| test_discovery_memory.py | 8 | integration | 0 | clue system |
| test_emergent_scene_actors.py | 6 | unit | 1 | general |
| test_empty_social_retry_regressions.py | 8 | regression | 4 | retry |
| test_exploration_resolution.py | 42 | unit | 0 | resolution/emission, routing, clue system |
| test_exploration_skill_checks.py | 5 | integration | 0 | combat/skill |
| test_gauntlet_regressions.py | 5 | regression | 1 | transcript regression |
| test_intent_and_runtime.py | 2 | unit | 0 | routing |
| test_intent_parser.py | 18 | unit | 0 | routing, fallback |
| test_interaction_context_owner.py | 8 | unit | 0 | general, social continuity |
| test_mixed_state_recovery_regressions.py | 6 | regression | 6 | mixed-state recovery |
| test_narration_state_consistency.py | 9 | unit | 0 | general, fallback, clue system |
| test_output_sanitizer.py | 41 | unit | 0 | legality/sanitizer, fallback, routing, transcript regression |
| test_project_schema.py | 4 | integration | 0 | general |
| test_prompt_and_guard.py | 67 | integration | 3 | legality/sanitizer, fallback, lead extraction, clue system |
| test_prompt_compression.py | 17 | integration | 0 | general, world/state, fallback |
| test_save_load.py | 5 | integration | 0 | world/state, clue system |
| test_scene_advancement_signals.py | 3 | integration | 0 | general, world/state |
| test_scene_entity_lock.py | 4 | integration | 0 | social continuity, general |
| test_scene_graph.py | 6 | integration | 0 | world/state, routing |
| test_scene_layers.py | 2 | integration | 0 | clue system, general |
| test_scene_transition_authority.py | 3 | integration | 0 | general |
| test_scene_validation.py | 17 | unit | 0 | general, clue system |
| test_skill_checks.py | 9 | unit | 0 | combat/skill, fallback |
| test_snapshots.py | 5 | integration | 0 | general, world/state |
| test_social.py | 23 | integration | 0 | general, clue system, social continuity, legality/sanitizer |
| test_social_answer_candidate.py | 7 | unit | 0 | general, fallback |
| test_social_answer_retry_prioritization.py | 4 | integration | 0 | retry |
| test_social_escalation.py | 16 | unit | 0 | general |
| test_social_exchange_emission.py | 43 | unit | 0 | resolution/emission, fallback, retry, clue system |
| test_social_interaction_authority.py | 7 | integration | 0 | general, fallback, resolution/emission |
| test_social_lead_landing.py | 17 | integration | 0 | lead extraction, clue system |
| test_social_probe_determinism.py | 6 | integration | 0 | general, legality/sanitizer, lead extraction |
| test_social_target_authority_regressions.py | 10 | regression | 0 | social continuity |
| test_startup_and_timestamps.py | 4 | unit | 0 | general |
| test_transcript_gauntlet_actor_addressing.py | 4 | transcript_gauntlet | 4 | transcript regression |
| test_transcript_gauntlet_campaign_cleanliness.py | 3 | transcript_gauntlet | 3 | transcript regression |
| test_transcript_regression.py | 5 | regression | 5 | transcript regression |
| test_transcript_runner_smoke.py | 1 | integration | 0 | transcript regression |
| test_turn_pipeline_shared.py | 46 | integration | 0 | general, routing, retry, combat/skill |
| test_validation_journal_affordances.py | 10 | unit | 0 | general, clue system |
| test_world_engine_updates.py | 9 | unit | 0 | resolution/emission |
| test_world_state.py | 8 | unit | 0 | world/state |
| test_world_updates_and_clue_normalization.py | 7 | integration | 0 | clue system |

---

## Methodology & limitations

- **Ground truth for “what runs”:** pytest collection (`887` items as of 2026-04-03). AST `def test_*` counts are per-file module-level defs; **duplicate names in the same file** are listed in `summary.files_with_shadowed_duplicate_test_defs` and echoed when running `tools/test_audit.py`.  
- **Buckets:** Test-level buckets use filename patterns (`transcript_gauntlet`, `regression`) then body signals (`TestClient`, `tmp_path`, length).  
- **Feature areas:** Substring rules on `nodeid`, merged with explicit `# feature:` / ownership `pytest.mark.*` when present; unannotated tests may still land on **general**.  
- **Assertion style / brittleness:** Regex on function source (long string `==`, `in "..."`, structural calls). Transcript/regression modules biased to **high** brittleness.  
- **Redundancy:** `possible_overlap` only triggers on identical **base** test names in different files (none found). Semantic duplicates are **not** auto-detected.  
- **Pytest markers:** `pytest.ini` defines `unit`, `integration`, `regression`, `transcript`, `slow`, `brittle`, plus optional ownership markers (`routing`, `retry`, `fallback`, `social`, `continuity`, `clues`, `leads`, `emission`, `legality`). `tools/test_audit.py` reads those ownership markers and `# feature:` comments when building `feature_areas`.

---

## Optional metadata comments

Use `# feature: routing, fallback` on the line before a test (or once per file before the first top-level `def test_`) so `test_inventory.json` picks up ownership without relying on `nodeid` keywords. Equivalent: `@pytest.mark.routing` (see `pytest.ini`). Large or previously-`general` modules are partially tagged; extend over time.
