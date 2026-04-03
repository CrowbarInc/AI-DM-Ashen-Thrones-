# Test consolidation plan (Block 15C)

**Status:** Plan + recorded ownership; routing consolidation **pass closed** (Block 3 documentation only in the last routing block — no further routing refactors implied by this section).

**Source:** Derived from `tests/TEST_AUDIT.md`, `tests/test_inventory.json` (regenerate via `py -3 tools/test_audit.py`), and spot review of transcript vs pipeline modules.

**Goal:** A concrete, low-risk roadmap so cleanup can run in small batches with full-suite checks between steps.

**Consolidation Block 1 (ownership):** The authoritative **canonical ownership map**, **overlap hotspots**, **Block 2 file list**, and **deferrals** live in `tests/TEST_AUDIT.md` → section *Consolidation Block 1 — Canonical ownership map & overlap hotspots*. This plan stays aligned with that section.

**Completed — routing / turn-pipeline cluster:** Restored `test_dialogue_routing_lock.py` as the home for the pure `choose_interaction_route` / dialogue-lock table (`test_choose_interaction_route_dialogue_lock_pure_contract`); removed that duplicate from `test_turn_pipeline_shared.py` and trimmed redundant `kind != adjudication_query` / GM substring checks where stronger assertions already held. `test_directed_social_routing.py` chat smoke cases dropped the redundant adjudication negation when `kind == "question"` already applied.

### Block 3 — Routing ownership (consolidation pass closed)

The following **routing ownership pattern** is now the explicit contract for new tests and overlap review. It reflects what the consolidation pass proved: three modules, three layers — not one mega-file.

| Module | Owns |
| --- | --- |
| `tests/test_turn_pipeline_shared.py` | Full-stack **`/api/chat`** and **`/api/action`** routing behavior; dialogue-lock **HTTP** regressions; **turn-trace-adjacent** flow; **end-to-end resolution** behavior. |
| `tests/test_dialogue_routing_lock.py` | The **pure routing-table / dialogue-lock contract** (e.g. `choose_interaction_route`) **without** `TestClient`. |
| `tests/test_directed_social_routing.py` | **Directed-social precedence**, **vocative overrides**, **segmentation**, **narrow directed `/api/chat` scenarios**, and **emergent-actor targeting** behavior. |

**Intentional duplication:** Some phrases or scenarios appear in **both** pure-routing / table coverage (`test_dialogue_routing_lock.py`, aspects of `test_directed_social_routing.py`) **and** full-pipeline coverage (`test_turn_pipeline_shared.py`) because they assert **different layers** (unit/table vs HTTP/stack vs resolution). That overlap is expected unless a later pass maps a specific case to a single layer with a replacement strategy.

### Next consolidation order (after routing)

Work the clusters in this order unless a release forces a narrow fix:

1. **Repair / retry cluster** next — `test_contextual_minimal_repair_regressions.py`, `test_empty_social_retry_regressions.py`, and related repair/retry surfaces.
2. **Prompt / sanitizer cluster** after that — `test_prompt_and_guard.py`, `test_output_sanitizer.py`, symptom-based split (messages-to-model vs post-GM output).
3. **Social / emission** later — `test_social_exchange_emission.py`, `test_social_escalation.py`, `test_social.py` migration, emission-quality harness alignment.
4. **Lead / clue** only **after** the known **destination-redirect** baseline in `test_social_destination_redirect_leads.py` is handled in a **separate** fix/quarantine task (do not fold that baseline into consolidation scope).

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
- **Consolidation Block 1 explicit deferrals:** No broad merge of `test_prompt_and_guard.py` or `test_turn_pipeline_shared.py`; no regression/transcript deletion without nodeid replacement map; `test_social_destination_redirect_leads.py` failures are a separate bugfix track.

### D. Block 2 — clusters (routing done; remaining batches)

Routing three-module split is **complete** (Block 3 above). Overlap reduction and marker cleanup elsewhere — **not** wholesale rewrites:

1. ~~`test_turn_pipeline_shared.py`, `test_directed_social_routing.py`, `test_dialogue_routing_lock.py`~~ — **routing pass closed**; only thinning with a replacement strategy if needed later.
2. **Next:** `test_contextual_minimal_repair_regressions.py`, `test_empty_social_retry_regressions.py`
3. `test_social.py`, `test_social_exchange_emission.py`, `test_social_escalation.py`
4. `test_transcript_regression.py`, `test_lead_lifecycle_block3_transcript_regression.py`, `test_gauntlet_regressions.py`
5. `test_social_emission_quality.py` (module-level transcript policy)
6. `test_prompt_and_guard.py`, `test_output_sanitizer.py`
7. Lead/clue cluster: `test_social_lead_landing.py`, `test_clue_lead_registry_integration.py`, `test_social_destination_redirect_leads.py` — **last**, after **destination-redirect** baseline in that file is fixed or quarantined (`tests/README_TESTS.md`).

---

## 3. Proposed consolidation items (detail)

Each row is a **future** change candidate. **Do not** execute without a replacement strategy for regression locks.

| ID | Tests / files involved | Overlap reason | Proposed action | Risk |
| --- | --- | --- | --- | --- |
| R1 | `test_contextual_minimal_repair_regressions.py` ↔ `test_empty_social_retry_regressions.py` | Both touch contextual/minimal repair and social empties; shared helper behavior | **Merge:** extract shared fixtures/helpers to `tests/conftest.py` or a `tests/repair_helpers.py`; **do not** merge scenario lists until ownership split is clear (retry/API vs payload/legality). Optionally **weaken** duplicated prose checks if one file keeps the strict version. | Low (helpers only); Medium if merging test bodies |
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

- `tests/README_TESTS.md` — full lane, fast lane, stricter fast, collect-only, Windows `py -3 -m pytest`, known baseline failures.
- `tests/TEST_AUDIT.md` — counts, brittleness leaders, canonical examples, duplicate-name guardrail notes.
- `tests/test_inventory.json` — per-item `nodeid`, buckets, heuristics.
- `pytest.ini` — markers: `unit`, `integration`, `regression`, `transcript`, `slow`, `brittle`.
