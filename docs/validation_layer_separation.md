# Validation layer separation (canonical contract)

Maintainer-facing contract for **Objective #11**: strict separation of validation responsibilities across the live narration stack and offline tooling. This document **does not** add a parallel policy system, LLM-based validation, or new runtime enforcement. It aligns with `docs/narrative_integrity_architecture.md`, `docs/architecture_ownership_ledger.md`, and `docs/state_authority_model.md`.

**Executable registry (leaf module):** `game/validation_layer_contracts.py` — stable layer ids, governed responsibility domains, pure predicates, and a forward read matrix for collaboration audits.

---

## Five canonical layers

| Layer id | Role name | One-line charter |
|----------|-----------|------------------|
| `engine` | Truth | Authoritative simulation, resolution commits, and interaction/world/scene **truth** after deterministic rules. |
| `planner` | Structure | Contract assembly and **intent/state consumption** for prompting and routing; shapes what the model is asked to do. |
| `gpt` | Expression | Model-generated **surfaces** (prose, JSON-shaped drafts) **within** supplied contracts; never authoritative for truth or legality. |
| `gate` | Legality | Deterministic **validators**, **bounded repairs**, and **orchestration** that seals pass/fail legality on emitted output; not scoring. |
| `evaluator` | Scoring | **Offline** numeric or axis judgments on telemetry and artifacts; **read-only** to live legality. |

---

## What each layer owns

### Engine (`engine`)

- World/scene/session **persistence truth** and mechanics outcomes.
- Resolved-turn **meaning** (for example CTIR-class shapes) **after** authoritative mutation and hygiene — not prompt-side reinterpretation.
- Authoritative **interaction framing** and social-target precedence where the engine is already declared owner (`game.interaction_context`, orchestrated via `game.api` per existing docs).

### Planner (`planner`)

- **Prompt bundle** and guard-facing **structure** (`game.prompt_context` and adjacent assembly as documented).
- **Shipped policy shapes** the writer must satisfy (for example `game.response_policy_contracts` as the canonical **read-side / ship-side** contract owner — **structure**, not post-hoc legality verdict ownership).
- Coarse **routing** and planner-visible **intent packets** feeding narration.
- **Objective N5 (`clause_referent_plan` / `referent_clause_prompt_hints`):** Per-slot rows in **`clause_referent_plan`** are **derivative-only** metadata constructed solely in `game.referent_tracking`; `game.prompt_context` may ship **trimmed read-side** **`referent_clause_prompt_hints`** only. Not a second semantic authority, not prose parsing, not CTIR—see `docs/clause_level_referent_tracking.md` and `tests/test_n5_boundary_regressions.py`.

### GPT (`gpt`)

- **Player-facing text** and model JSON **drafts** as **expression** within contracts.
- Rhetorical choices that remain **non-authoritative** for engine domains (see `docs/state_authority_model.md`).

### Gate (`gate`)

- **Deterministic validators** and **inspectors** (`game.final_emission_validators` and peers).
- **Bounded deterministic repairs** (`game.final_emission_repairs` and peers).
- **N5 consumption:** Gate referent-clarity logic may **read** optional **`clause_referent_plan`** rows on the full referent artifact; it **does not** construct that field, does not own upstream truth, and stays on the existing **minimal** substitution repair path (`docs/clause_level_referent_tracking.md`, `tests/test_n5_boundary_regressions.py`).
- **Orchestration** that orders layers, integrates the sanitizer, and seals strict-social / emission paths (`game.final_emission_gate.apply_final_emission_gate` as orchestration owner per ledger).
- **Objective N4 (Acceptance Quality floor)** — `game.acceptance_quality` supplies a **data-shaped**
  contract and the canonical `validate_and_repair_acceptance_quality` loop; `apply_final_emission_gate`
  calls that seam (no duplicated orchestration), merges `acceptance_quality_*` / `acceptance_quality_trace`
  into FEM, and may swap to a deterministic sealed line if the floor still fails after bounded repair.
  It is **not** scoring, not an evaluator substitute, and not a second NA stack; unknown trailer
  pattern table versions are recorded as observational evidence, not silently “fixed” at the gate.
  See `docs/acceptance_quality_layer.md`.

**C2 shipped boundary (post Block B/D1/D2):** Resolved-turn **meaning** and contract-shaped **answer/action** fallback **prose** are decided **upstream** (`game.upstream_response_repairs` merged as `upstream_prepared_emission`; planner/CTIR context). The gate + default **strip-only** sanitizer path own **legality-preserving** cleanup, **visibility/route-illegal** stripping, serialized-field **packaging** recovery, and explicit **trace/meta** when prepared text is absent—not silent “finish the thought” narration. **Strict-social** terminal dialogue shaping stays the **`game.social_exchange_emission`** seam. **Evaluators** score offline; they do not perform live semantic repair at this boundary (see `docs/final_emission_ownership_convergence.md`).

### Evaluator (`evaluator`)

- **Offline** scoring axes, verdict summaries, and harness judgments (for example `game.narrative_authenticity_eval`, playability artifacts).
- Consumption of merged telemetry and **read-only** views of finalized outputs for regression and operator review.

---

## What each layer explicitly does **not** own

| Layer | Non-ownership (hard) |
|-------|----------------------|
| **Engine** | Post-generation **legality** orchestration; **expression** authoring for shipped GM text; **offline scoring**; prompt **shape** ownership beyond truth effects. |
| **Planner** | Engine **truth** mutation or reinterpretation of CTIR meaning as authority; **legality** verdicts; **bounded repairs**; **evaluator scores**. |
| **GPT** | Any authoritative **truth** write; **legality** pass/fail ownership; **scoring**; shipped **contract resolution** as a rival to engine/planner owners. |
| **Gate** | Engine **truth** commits; **scoring** or subjective quality as enforcement; **prompt assembly** as canonical owner; **model expression** choices. |
| **Evaluator** | Live **enforcement**, repairs, gate ordering, or any mutation of pipeline output based on scores. |

---

## Allowed read / write directions (validation collaboration)

**Forward pipeline (conceptual):** `engine → planner → gpt → gate → (optional offline) evaluator`

- **Reads:** downstream layers may consult upstream outputs in this order only. **No** feedback from evaluator scores into gate legality. **No** treating GPT text as a truth source for engine domains (see state authority model).
- **Writes:** each phase writes **only** its phase outputs. The gate may **repair emitted text** under bounded deterministic rules; it does **not** overwrite upstream engine truth stores with model prose.

The matrix helpers `layer_may_read_layer`, `allowed_reader_layers_for_writer`, and `assert_forward_read_path` in `game/validation_layer_contracts.py` encode the **validation-layer** read lattice (distinct from `game/state_authority.py` domain reads).

---

## Valid collaboration vs invalid overlap

### Valid (examples)

- **Planner reads engine truth** to assemble prompt slices and shipped contracts.
- **GPT reads planner contracts** to generate constrained prose/JSON.
- **Gate reads GPT candidate text** plus shipped contracts to run deterministic checks and bounded repairs.
- **Narrative authenticity (NA)** contributes deterministic checks and **NA-scoped** bounded repairs **under gate orchestration**. NA does **not** seal pass/fail for `response_delta`, does **not** author canonical `response_delta_*` legality metadata, and does **not** own primary delta repair—that remains the gate stack (`final_emission_repairs`). Where documented, NA may **shadow-read** the same delta predicate for diagnostics only (see `NA_SHADOW_RESPONSE_DELTA_FAILURE_REASON` in `game/validation_layer_contracts.py`).
- **Acceptance quality (N4)** contributes **floor** predicates (anti-collapse / grounding / trailer
  idiom tables) and **bounded subtractive** repairs **under gate orchestration** via the shipped
  `validate_and_repair_acceptance_quality` entrypoint; it does **not** attach numeric scores, does
  **not** call offline evaluators, and does **not** replace NA’s echo or filler ownership (see
  `docs/acceptance_quality_layer.md`).
- **Evaluator reads gate telemetry** and finalized meta for offline scores (artifacts only; no live enforcement).

### Invalid (anti-patterns)

- **Evaluator → gate feedback:** using evaluator scores to change pass/fail or repair decisions in the live pipeline.
- **GPT → truth:** treating model JSON or narration as authoritative for `world_state` / `scene_state` / `interaction_state` without engine validation.
- **Gate → scoring:** attaching numeric “quality” enforcement to the live gate beyond explicit deterministic reason codes.
- **Planner → truth overwrite:** rewriting CTIR or interaction authority outcomes from prompt assembly code.
- **NA → response_delta repair:** duplicating delta repair ownership; delta stays under the response-delta layer (`final_emission_repairs` / gate wiring).

---

## Specific anti-goals (do not regress)

1. **NA must not become `response_delta` repair owner** — Shadow validation signals are allowed where already documented; **primary** delta repair and `response_delta_*` meta stay with the response-delta layer.
2. **Evaluators remain read-only** — No enforcement hooks driven by evaluator output on live turns.
3. **Gate remains legality/orchestration, not scoring** — Pass/fail on explicit codes; numeric axes live in **evaluator** artifacts only.
4. **Planner structures intent/state consumption; it does not overwrite truth** — Prompt assembly consumes engine outputs; it is not a second semantic authority over resolved-turn meaning when CTIR is present (per CTIR adapter docs).
5. **GPT expresses within supplied contracts; it does not author legality or truth** — Model output is always non-authoritative for authoritative domains and non-owning for gate verdicts.

---

## Relationship to other registries

- **`game/state_authority.py`** — runtime **state domain** mutation guards (world/scene/interaction/hidden/player-visible). Complementary to this validation-layer contract; not a duplicate policy engine.
- **`docs/architecture_ownership_ledger.md`** — seam-level runtime module owners. This file names **phase responsibilities** that those modules must roll up into without blurring layers.
- **`docs/narrative_integrity_architecture.md`** — emit-path module map; use it for file-level placement, and use **this** document when deciding **which phase** may own a new concern.

---

## Fenced tolerated residue (compatibility)

Objective #11 allows **narrow, explicitly documented** shapes that look like “duplicate layers” but are **not** rival ownership claims:

- **Within-layer file splits** (for example several `final_emission_*` modules) are still **one** canonical `gate` layer; the audit treats them as benign splits, not drift.
- **NA shadow diagnostics** that re-invoke the delta predicate for tracing are **non-authoritative** for delta legality; canonical `response_delta_*` keys remain gate-written.
- **Offline evaluator naming** (`game.narrative_authenticity_eval`) stays off live import paths.

Inventory and “would become a violation if…” notes: `docs/validation_layer_separation_block_b_residue.md` (non-authoritative except as a compatibility checklist; the executable registry + this doc define ownership).

**Test ownership (Blocks B–D, pytest-only):** `tests/test_ownership_registry.py` maps each **live invariant responsibility** to exactly one **direct_owner** module under `tests/` plus optional **neighbor** modules. Neighbors are explicitly typed as **`smoke_suites`**, **`transcript_suites`**, **`gauntlet_suites`**, **`evaluator_suites`**, **`downstream_consumer_suites`**, or **`compatibility_residue_suites`** (see `tests/TEST_CONSOLIDATION_PLAN.md`). `tools/test_audit.py` embeds that map in `tests/test_inventory.json` (**schema v2**) for drift checks; it does not change runtime validation-layer behavior.

**How pytest roles line up with the five layers (maintenance vocabulary):**

- **Engine** — Tests aligned with engine concerns defend **state correctness** (truth, persistence, mechanics) after deterministic rules; they are not the home for post-generation **legality orchestration** or offline **scoring**.
- **Planner** — Tests defend **structure**: prompt-bundle / shipped-contract assembly and intent consumption for prompting; not authoritative **legality** verdicts or engine truth mutation.
- **Gate** — Tests defend **legality** and **final emission** (validators, bounded repairs, orchestration that seals output), not numeric quality scoring as enforcement.
- **Evaluator** — Tests defend **scoring / playability** and offline axes; they must **not** substitute for live gate enforcement.
- **Transcript** — Tests own **cross-turn sequencing** and multi-turn **regression stories**; they complement single-turn owners and must not be named **`direct_owner`** for **live legality** groups in the registry.
- **Gauntlet** — Tests own **harness / slice** behavior (including API-style gauntlet regressions where named); same **live legality** direct-owner restriction as transcript-style suites.
- **Smoke** — **Wiring only**: orchestration presence, routes, thin integration checks—not parallel full legality matrices for seams already directly owned.
- **Downstream consumer** (registry neighbor slot) — Verifies **consumer behavior** through an owner boundary; **not** a canonical invariant owner for the responsibility.
- **Compatibility residue** (registry neighbor slot) — **Intentionally preserved historical** coverage; **not** canonical ownership of new rules.
- **`general`** — Inventory field `likely_architecture_layer: general` means the static heuristic had **weak signal**; it is **not** a sixth validation layer. Declared **direct_owner** paths with a non-null `declared_architecture_layer` must not resolve to `general` in inventory (governance test).

**Block C closeout (strict-social vs prompt vs gate tests):** Strict-social **first-sentence** / **question-resolution** legality matrices → **`tests/test_social_exchange_emission.py`**. Retry **prompt text** for unresolved-question / social-contract failures, **`enforce_question_resolution_rule` prepend**, and **validator-voice** GM-layer enforcement → **`tests/test_prompt_and_guard.py`** (plus thin smoke at the prompt boundary). **`apply_final_emission_gate` orchestration** → **`tests/test_final_emission_gate.py`**.

---

## Change discipline

- Prefer extending **`game/validation_layer_contracts.py`** with new **domain ids** and tests when a concern is genuinely new, rather than introducing a second ownership vocabulary.
- **No** new smart enforcement layer, **no** LLM validation, **no** evaluator-driven live legality, **no** gate scoring, **no** gameplay expansion under this objective.

---

## Objective #11 — documented closeout (historical “Block D” label in Objective #11 work)

**Status:** Objective #11 is **satisfied with narrow fenced residue** (compatibility-shaped seams above). That residue is **not** a second source of truth: it is explicitly **non-authoritative** and must not override `game/validation_layer_contracts.py` or this document.

**Distinction:**

- **Acceptable compatibility residue** — Documented within-layer splits, NA shadow reads, planner structure surfaces, and offline evaluator artifacts that **do not** claim rival ownership of gate legality, engine truth, or `response_delta` repair/metadata.
- **Actual ownership violations** — Live paths where an offline evaluator or planner module imports gate repair/orchestration to enforce legality; NA importing gate orchestration or owning canonical `response_delta_*` meta; evaluator scores feeding gate pass/fail; or narrative text treated as engine truth without validation.

**Verification:** `tools/validation_layer_audit.py` (non-strict clean on `./game`; `--strict` for CI opt-in), plus regression tests under `tests/test_validation_layer_*`.
