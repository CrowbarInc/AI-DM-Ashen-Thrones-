# Cycle AA — Gate Authority Extraction Recon

Date: 2026-05-31

## Executive Summary

Cycle AA is **feasible** and should proceed as **small, behavior-preserving module-boundary extractions**, not another file-size shuffle. `game/final_emission_gate.py` remains the canonical **orchestration** owner (~10,391 lines, 242 `def`/`class` symbols) but still holds substantial **decision authority**: strict-social routing, terminal fallback selection wiring, upstream fast-fallback containment, duplicated `final_emitted_source` inference, visibility/referent hard-replace orchestration, and six in-module policy layers (tone, narrative authority, anti-railroading, context separation, narration purity, answer-shape primacy) that both **decide** and **repair**.

Prior cycles already extracted meaningful boundaries (Cycle J opening adapter, visibility fallback module, sealed-fallback assembly/branch selection, validators/repairs/meta, read-side replay projection). **Replay projection is already out of the gate** in `game/final_emission_replay_projection.py`; AA should not re-move it unless gate-side FEM stamping drifts.

**Safest first implementation block (AA1):** extract **Block I upstream fast-fallback provenance containment** (`_upstream_fallback_canonical_provenance`, `_apply_upstream_fallback_pregate_containment`, `_finalize_upstream_fallback_overwrite_containment`) into `game/fallback_provenance_debug.py` (or a thin `game/final_emission_provenance_containment.py` shim that re-exports for tests). This removes gate **text-restore decisions** while keeping orchestration call sites in `apply_final_emission_gate` / `_finalize_emission_output`. Replay risk is **low** if fingerprints and containment kinds are unchanged.

**Second block (AA2):** consolidate duplicated **`final_emitted_source` / accept-path terminal projection** (strict-social accept ~9199–9255 and generic accept ~9973–10033) into `game/final_emission_meta.py` beside existing `apply_opening_fallback_projection_fields`. Same precedence order must be preserved; golden replay and failure classifier observe these fields.

Larger authority moves (non-strict sealed **provider** closures, full visibility orchestration, in-gate policy layers) are valid AA3+ targets but carry **medium–high** replay/behavior risk and should follow AA1–AA2.

---

## Current Gate Responsibility Map

| Area | Function / line range | Current responsibility | Classification | Extraction candidate? | Notes |
|------|----------------------|------------------------|----------------|----------------------|-------|
| Module header | L1–50 docstring | Documents orchestration vs delegated owners | orchestration only | no | Replace comment-only boundaries with imports/calls as blocks land |
| Imports / wiring | L51–290 | Pull validators, repairs, meta, social, provenance, sealed/opening/visibility adapters | orchestration only | partial | Historical re-exports for tests; do not rename public symbols without audit |
| Sealed fallback providers | `_NonStrictSealedFallbackProviders`, `_build_non_strict_sealed_fallback_providers` L296–470 | Builds callable providers that **select prose** from opening/social/passive/global owners | decision-making + orchestration | **yes (AA3)** | Branch **policy** already in `assemble_non_strict_sealed_fallback_selection`; gate still owns provider wiring and upstream tuple calls |
| Sealed fallback adapter | `_select_non_strict_*` L473–556 | Delegates to `game.final_emission_sealed_fallback` | orchestration only | thin | Keep compatibility tuple wrapper until tests migrate |
| Dialogue plan / strict-social shells | L602–821 | Dialogue-plan invariant enforcement on strict-social text | decision-making | later | Tied to `game.dialogue_social_plan` + `social_exchange_emission` |
| Narration constraint debug | L823–1154 | FEM/debug projection for narration constraints | projection/formatting | **yes (AA4)** | Read-side packaging; low player-text risk |
| Tone escalation layer | L1158–1604 | Contract resolve, skip, narrow repair, apply | decision-making | later | Full policy cluster still in gate |
| Narrative authority layer | L1608–2035 | Contract resolve, skip, sentence-span repairs, apply | decision-making | later | C2 boundary: narrow repairs still wired |
| Anti-railroading layer | L2039–2506 | Contract resolve/fallback build, repair passes, apply | decision-making | later | `_fallback_build_anti_railroading_contract` is gate-local contract synthesis |
| Context separation layer | L2511–2832 | Contract resolve, repair, apply | decision-making | later | |
| Player-facing narration purity | L2884–3118 | Contract resolve, repair, apply | decision-making | later | |
| Answer-shape primacy | L3120–3480 | Validate/repair/apply ASP | decision-making | later | |
| Scene state anchor | L3482–3818 | SSA contract resolve, opening repairs, apply | decision-making | later | Overlaps opening helpers L3828+ |
| Opening helpers (in-gate) | L3820–4046, `validate_opening_output` L4000 | Opening mode/anchor validation, `_opening_scene_safe_fallback_tuple` wrapper | decision-making + legacy shim | partial | Cycle J adapter owns selection; gate wrapper injects first-mention composition |
| Response type enforcement | `_enforce_response_type_contract` L4048–4402 | Large RT contract accept/repair/replace routing | decision-making | **no first** | High fan-out; tests in `test_final_emission_gate.py` |
| Fragment/participial helpers | L4403–4686 | Semantic finalize helpers (mostly disabled at boundary) | test-only / legacy shim | no | C2 Block C disabled at finalize |
| Fast-path eligibility | `_final_emission_fast_path_eligible` L4688–4748 | Skip heavy layers when safe | decision-making | later | Affects performance path, not prose family |
| Fallback provenance containment | L4751–4844 | Block I: restore upstream selector text on drift | provenance ownership + decision-making | **yes (AA1)** | Should live with `fallback_provenance_debug` |
| Finalize packaging | `_strip_appended_route_illegal_*` L4846–4895, `_finalize_emission_output` L4898–4998 | Strip-only packaging, channel projection, containment re-seal | orchestration + fallback/guard | partial | Containment call moves; strip stays at boundary |
| Scene/fast-fallback composition | L5079–5276+ | Passive pressure candidates, fast-fallback neutral composition | decision-making | AA5+ | Knows scene pressure and diegetic templates |
| Visibility / referent enforcement | `_apply_*_enforcement` L6884–7670, `_apply_visibility_enforcement` L7505 | Hard-replace routing after failed visibility validation | decision-making + orchestration | later | Delegates payloads to `final_emission_visibility_fallback` but gate routes |
| Interaction continuity | L7704–8315 | IC validate/repair/bridge before finalize | decision-making | medium | Heavily tested in `test_final_emission_gate.py` |
| N4 / NMO assessment | L8347–8570, `_apply_acceptance_quality_n4_floor_seam` L8479–8570 | N4 floor + C4 NMO policy (replace vs accept) | decision-making | partial | Sealed line **selection** injected; replace policy in gate |
| Scene-opening debug reassert | L8658–8714 | Reseal accepted opening candidate into output | replay behavior + guard | partial | Protects opening replay invariants |
| **Main entry** | `apply_final_emission_gate` L8748–10391 | Full layer ordering, strict vs generic branches, FEM assembly, logging | orchestration + decision-making | partial | Shrinks as sub-owners absorb decisions |
| Opening projection call | `apply_opening_fallback_projection_fields` L10209, L10272 | Copies opening FEM fields into RT debug | projection/formatting | **done in meta** | Gate should only call; no new logic |
| Realization family stamp | `attach_realization_fallback_family` (multiple) | Classify terminal replace families | source-family projection | **yes (AA2b)** | Some stamping already in `final_emission_sealed_fallback` |

---

## Authority / Decision Map

| Function | Line range | Decision made | Inputs | Output/effect | Proposed owner | Replay risk | Behavior risk |
|----------|------------|---------------|--------|---------------|----------------|-------------|---------------|
| `apply_final_emission_gate` (entry) | ~8767–8776 | Whether to merge upstream prepared emission / attach opening payload | `out`, resolution, session, world, scene_id | Mutates `out` before gate layers | `game.upstream_response_repairs` (already) | medium | low |
| `apply_final_emission_gate` | ~8806–8838 | Suppress strict-social coercion for non-native narration beat | resolution, session, world, coercion_reason, merged prompt | Flips `strict_social_turn`, re-sanitizes text | `game.social_exchange_emission` | medium | medium |
| `_apply_upstream_fallback_pregate_containment` | 4759–4781 | Restore upstream selector snapshot when gate-entry fingerprint mismatches | `metadata.fallback_provenance`, current text | Rewrites `player_facing_text` pre-gate | `game.fallback_provenance_debug` | medium | medium |
| `_finalize_upstream_fallback_overwrite_containment` | 4784–4844 | Revert to selector after in-gate mutation hints | provenance mismatch flags, mutation_hint | Finalize-time text restore + FEM patch | `game.fallback_provenance_debug` | medium | medium |
| `assemble_non_strict_sealed_fallback_selection` (called) | sealed_fallback module | Which sealed branch (opening / social / passive / neutral / anti-reset / global) | mode, opening flag, interlocutor, passive list | `SealedFallbackSelection` | **`game.final_emission_sealed_fallback`** (already) | high | high |
| `_build_non_strict_sealed_fallback_providers` | 353–470 | Which **prose tuple** each branch supplies | scene, session, world, resolution, interlocutor | Provider callables | `game.final_emission_sealed_fallback` + injected builders | high | high |
| `_enforce_response_type_contract` | 4048–4402 | Accept/repair/replace per response_type contract | text, gm_output, resolution, strict_social flags | text + `response_type_debug` | split: validators vs gate orchestration | high | high |
| Strict-social branch | 8904–8972 | Emergency fallback when RT fails or dialogue-plan blocked | `details`, `eff_resolution`, RT debug | `final_emitted_source`, fallback_kind, text | `social_exchange_emission` + meta projection | high | high |
| `build_final_strict_social_response` (called) | social module | Strict-social terminal text selection | pre_gate_text, resolution, tags | text, details | `game.social_exchange_emission` | high | high |
| `_final_emission_fast_path_eligible` | 4688–4748 | Skip heavy post-layers | FEM repair flags, tags, IC validation | bool fast_path | `game.final_emission_meta` or small policy module | low | low–medium |
| `_apply_acceptance_quality_n4_floor_seam` | 8479–8567 | Pass vs hard-replace on N4 floor failure | AQ validation, strict_social_path | text replace + FEM route | `game.acceptance_quality` + sealed meta helpers | medium | medium |
| `_narrative_mode_output_legality_assessment` | 8573–8655 | NMO skip vs enforce vs strict-social emergency | shipped contract, text | trace + gate reasons | `game.narrative_mode_contract` + gate orchestration | medium | medium |
| `_apply_visibility_enforcement` | 7505–7670 | Visibility hard-replace vs pass | visibility validation, scene context | text + FEM visibility fields | `game.final_emission_visibility_fallback` + thin gate router | high | high |
| `final_emitted_source` inference (strict accept) | 9199–9255 | Which layer “wins” attribution on accept path | layer metas, details, response_type_debug | FEM `final_emitted_source` | **`game.final_emission_meta`** (new projector) | medium | low |
| `final_emitted_source` inference (generic accept) | 9973–10033 | Same precedence for non–strict-social accept | layer metas, tags | FEM `final_emitted_source` | **`game.final_emission_meta`** | medium | low |
| Non-strict replace terminus | 10178–10260 | Sealed selection + opening projection + route meta | `sealed_selection`, composition_meta | `final_route=replaced`, FEM | `final_emission_sealed_fallback.prepare_sealed_replacement_route_meta` | high | high |
| `realign_fallback_provenance_selector_to_current_text` (calls) | ~9141, ~9869 | Refresh Block I snapshot after in-gate repair | text, reason | metadata provenance | `game.fallback_provenance_debug` | medium | low |
| `attach_realization_fallback_family` (gate calls) | 4228, 4330, 8475, etc. | Map terminal replace to realization family | strict_social vs generic | FEM family fields | `game.final_emission_sealed_fallback` / `realization_provenance` | medium | low |
| `_enforce_dialogue_plan_invariant_on_strict_social` | 716–821 | Block vs allow strict-social emission | dialogue plan, text | trace, blocked flag | `game.dialogue_social_plan` | medium | medium |
| `_reassert_scene_opening_accepted_candidate` | 8693–8711 | Force emitted text back to accepted opening | accepted_scene_opening_text | text + debug | opening policy module or meta | medium | medium |

---

## Candidate Extraction Seams

### AA1 — Upstream fast-fallback provenance containment (recommended first)

- **Objective:** Move Block I containment **decisions** (when to restore selector text, which containment kind) off the gate into provenance module; gate retains a single orchestration call.
- **Files likely touched:** `game/final_emission_gate.py`, `game/fallback_provenance_debug.py` (or new `game/final_emission_provenance_containment.py`), possibly `tests/test_final_emission_gate.py` (import path only).
- **Tests likely touched:** `tests/test_final_emission_gate.py` (provenance / overwrite cases), `tests/test_fallback_shipped_contract_propagation.py` if imports change.
- **Validation command:**
  ```text
  .\.venv\Scripts\python.exe -m pytest tests/test_final_emission_gate.py tests/test_fallback_shipped_contract_propagation.py tests/test_golden_replay.py -q --tb=short
  ```
- **Risk level:** low–medium
- **Why first:** Narrow surface, explicit tests, removes gate **authority** without touching sealed branch ordering or `final_emitted_source` precedence.

### AA2 — Terminal `final_emitted_source` projection consolidation

- **Objective:** Single function in `final_emission_meta` (e.g. `infer_final_emitted_source_from_layer_metas`) used by both strict-social and generic accept paths; eliminate duplicated if-ladder (~9199–9255 vs 9973–10033).
- **Files likely touched:** `game/final_emission_gate.py`, `game/final_emission_meta.py`, `tests/test_final_emission_meta.py`, `tests/test_failure_classification_contract.py`.
- **Tests likely touched:** Gate ordering tests, golden observed-turn projection, failure classifier source_family rows.
- **Validation command:**
  ```text
  .\.venv\Scripts\python.exe -m pytest tests/test_final_emission_gate.py tests/test_final_emission_meta.py tests/test_golden_replay.py tests/test_failure_classification_contract.py -q --tb=short
  ```
- **Risk level:** medium
- **Why second:** Pure metadata projection if precedence is copied exactly; improves Failure Locality and Maintenance Drag.

### AA3 — Non-strict sealed fallback provider ownership

- **Objective:** Move `_build_non_strict_sealed_fallback_providers` next to `assemble_non_strict_sealed_fallback_selection`; gate passes explicit builder callbacks for opening/global tuples only.
- **Files likely touched:** `game/final_emission_gate.py`, `game/final_emission_sealed_fallback.py`, `tests/test_final_emission_opening_fallback.py`, gate sealed-path tests.
- **Validation command:**
  ```text
  .\.venv\Scripts\python.exe -m pytest tests/test_final_emission_gate.py tests/test_final_emission_opening_fallback.py tests/test_opening_fallback_owner_bucket.py tests/test_golden_replay.py -q --tb=short
  ```
- **Risk level:** medium–high
- **Why not first:** Provider closures embed gate knowledge of passive pressure, anti-reset, and scene-integrity tuples; ordering must match `select_non_strict_replace_path_terminal_sealed_fallback_branch`.

### AA4 — Narration-constraint / opening FEM projection-only helpers

- **Objective:** Move `_build_narration_constraint_debug` cluster and opening observability merge helpers into `final_emission_meta` or `tests/helpers` read adapters.
- **Files likely touched:** `game/final_emission_gate.py`, `game/final_emission_meta.py`.
- **Tests:** `tests/test_final_emission_meta.py`, gate debug attachment tests.
- **Validation:** `pytest tests/test_final_emission_meta.py tests/test_final_emission_gate.py -q`
- **Risk level:** low
- **Why later:** Reduces gate size but not core route/fallback **authority**.

### AA5+ — In-gate policy layers (tone, NA, AR, CS, purity, ASP)

- **Objective:** Each cluster becomes `game.final_emission_<layer>.py` owning resolve/skip/repair/apply; gate sequences calls only.
- **Risk level:** high per layer
- **Why deferred:** Large duplicated contract-coercion patterns; replay-sensitive repair modes.

**Replay projection note:** `game/final_emission_replay_projection.build_fem_runtime_lineage_events` is already read-side and gate-free. AA should only ensure FEM fields required by projection remain stable when moving AA1–AA3.

**Source-family note:** `stamp_sealed_fallback_realization_family` and `attach_realization_fallback_family` should converge so the gate does not choose families on social emergency paths—delegate to sealed/social owners.

---

## Existing Ownership Modules

| File path | Apparent responsibility | Relevant symbols | Good destination? |
|-----------|-------------------------|------------------|-------------------|
| `game/final_emission_validators.py` | Deterministic RT/AC/RD validators | `validate_answer_completeness`, `validate_response_delta`, RT helpers | Reference; already delegated |
| `game/final_emission_repairs.py` | Layer wiring for AC/RD/SRS/NA/FB | `_apply_*_layer`, meta merges | Reference; gate still sequences |
| `game/final_emission_meta.py` | FEM shapes, opening/sealed owner buckets, lineage packaging | `apply_opening_fallback_projection_fields`, `build_fem_runtime_lineage_events`, owner bucket constants | **Yes** for projection & AA2 |
| `game/final_emission_replay_projection.py` | Read-side FEM → runtime lineage events | `build_fem_runtime_lineage_events`, opening/strict-social owner constants | **Yes** for replay projection (done) |
| `game/final_emission_sealed_fallback.py` | Sealed branch selection, route meta stamping | `assemble_non_strict_sealed_fallback_selection`, `stamp_sealed_fallback_realization_family` | **Yes** for AA3/source-family |
| `game/final_emission_opening_fallback.py` | Opening prepared vs fail-closed selection | `_opening_scene_safe_fallback_tuple` adapter | **Yes** (Cycle J) |
| `game/final_emission_visibility_fallback.py` | Visibility replacement payloads | `route_visibility_enforcement_after_failed_validation` | Partial; gate still orchestrates |
| `game/fallback_provenance_debug.py` | Fast-fallback fingerprint + gate entry/exit traces | `record_final_emission_gate_entry`, `realign_fallback_provenance_selector_to_current_text` | **Yes** for AA1 |
| `game/realization_provenance.py` | `realization_fallback_family` vocabulary | `attach_realization_fallback_family`, `FALLBACK_FAMILIES` | **Yes** for source-family stamping |
| `game/upstream_response_repairs.py` | Upstream prepared emission/opening payloads | `merge_upstream_prepared_emission_into_gm_output` | Reference |
| `game/social_exchange_emission.py` | Strict-social build, logging, terminal pools | `build_final_strict_social_response`, `minimal_social_emergency_fallback_line` | **Yes** for strict-social decisions |
| `game/response_policy_contracts.py` | Response policy bundle materialization | `materialize_response_policy_bundle` | Reference |
| `game/final_emission_boundary_contract.py` | Mutation allow-list | `assert_final_emission_mutation_allowed` | Reference (guard, not policy) |
| `game/runtime_lineage_telemetry.py` | Lineage event vocabulary | `make_runtime_lineage_event` | Read-side only |
| `game/state_channels.py` | Public/debug/author payload projection | `project_public_payload` | Finalize orchestration |
| `tests/helpers/golden_replay_projection.py` | Golden observed-turn field projection | opening/fallback family fields | Test read adapter |
| `tests/helpers/final_emission_gate_fixtures.py` | Gate test fixtures | shared payloads | Test-only |
| `tools/final_emission_ownership_audit.py` | Advisory boundary drift scan | regex heuristics | CI/advisory only |

---

## Test Coverage Inventory

| Path | What it protects | Recommended command |
|------|------------------|---------------------|
| `tests/test_final_emission_gate.py` (234 tests) | Layer order, strict-social, N4/NMO, IC, provenance, sealed replace, FEM shape | `pytest tests/test_final_emission_gate.py -q` |
| `tests/test_final_emission_meta.py` (36) | FEM packaging, `build_fem_runtime_lineage_events`, opening projection | `pytest tests/test_final_emission_meta.py -q` |
| `tests/test_final_emission_opening_fallback.py` (6) | Opening adapter selection/fail-closed | `pytest tests/test_final_emission_opening_fallback.py -q` |
| `tests/test_opening_fallback_owner_bucket.py` (10) | Opening owner bucket taxonomy | `pytest tests/test_opening_fallback_owner_bucket.py -q` |
| `tests/test_final_emission_visibility_fallback.py` (50) | Visibility fallback payloads/buckets | `pytest tests/test_final_emission_visibility_fallback.py -q` |
| `tests/test_final_emission_boundary_convergence.py` (21) | No semantic repair at boundary | `pytest tests/test_final_emission_boundary_convergence.py -q` |
| `tests/test_final_emission_boundary_contract.py` (91) | Mutation allow-list | `pytest tests/test_final_emission_boundary_contract.py -q` |
| `tests/test_golden_replay.py` (55) | Protected replay invariants, projection adapter, rerun compare | `pytest -m golden_replay -q` or `pytest tests/test_golden_replay.py -q` |
| `tests/test_runtime_lineage_telemetry.py` (6) | Lineage event vocabulary | `pytest tests/test_runtime_lineage_telemetry.py -q` |
| `tests/test_failure_classification_contract.py` | Owner buckets, source_family locks | `pytest tests/test_failure_classification_contract.py -q` |
| `tests/test_fallback_shipped_contract_propagation.py` (6) | Fallback contract propagation | `pytest tests/test_fallback_shipped_contract_propagation.py -q` |
| `docs/testing/protected_replay_manifest.md` | Governance for protected scenarios | manual review |

**Combined recon validation (executed 2026-05-31):**

```text
.\.venv\Scripts\python.exe -m pytest tests/test_final_emission_gate.py tests/test_final_emission_meta.py tests/test_final_emission_opening_fallback.py tests/test_opening_fallback_owner_bucket.py tests/test_runtime_lineage_telemetry.py tests/test_final_emission_boundary_convergence.py tests/test_final_emission_visibility_fallback.py tests/test_golden_replay.py tests/test_final_emission_boundary_contract.py tests/test_fallback_shipped_contract_propagation.py -q --tb=line
```

- **Result:** pass (515 tests collected in this bundle)
- **Notable failures:** none in this pass
- **Pre-existing failures:** not assessed (full suite not run)
- **Replay determinism warnings:** none observed; no snapshot/golden updates performed

---

## Recommended Implementation Order

| Block | Scope | Independently testable |
|-------|--------|------------------------|
| **AA1** | Provenance containment → `fallback_provenance_debug` | yes |
| **AA2** | `final_emitted_source` projector → `final_emission_meta` | yes |
| **AA2b** | Route strict-social `attach_realization_fallback_family` calls through sealed/social owners | yes |
| **AA3** | Sealed provider builders → `final_emission_sealed_fallback` | yes (high care) |
| **AA4** | Narration-constraint / debug projection helpers → meta | yes |
| **AA5+** | One policy layer per block (tone, NA, AR, …) | yes but high risk |

Do **not** rename public gate exports or delete compatibility shims until `tests/test_final_emission_debt_retirement.py` and import audits agree.

---

## Files to Pass Back to ChatGPT

Minimum set for AA1 block generation:

1. `docs/cycles/cycle_aa_gate_authority_extraction_recon_2026-05-31.md` (this report)
2. `game/final_emission_gate.py` — focus L4751–4844, L8748–8872, L9850–9900, L10178–10280
3. `game/fallback_provenance_debug.py`
4. `game/final_emission_meta.py` — projection patterns L260–336
5. `tests/test_final_emission_gate.py` — provenance / overwrite / containment tests
6. `tests/test_golden_replay.py` — if AA1 might affect fallback provenance traces

For AA2 add:

7. `game/final_emission_gate.py` — L9199–9255 and L9973–10070
8. `tests/test_final_emission_meta.py`, `tests/test_failure_classification_contract.py`
9. `tests/helpers/golden_replay_projection.py`

Reference only (do not move replay logic again):

10. `game/final_emission_replay_projection.py`
11. `game/final_emission_sealed_fallback.py`

Validation output to attach if a block fails: full pytest stderr for the block’s validation command above.

---

## Uncertainties (documented, not guessed)

- Whether `_enforce_response_type_contract` should ever leave the gate or split into validator + router modules needs a dedicated audit (L4048–4402, ~350 lines).
- Passive scene pressure fallback ordering inside `_passive_scene_pressure_fallback_candidates` may duplicate `diegetic_fallback_narration` policy; not traced in this pass.
- Full-suite CI status unknown; recon used targeted 515-test bundle only.
- `apply_final_emission_gate` strict-social vs generic branches still duplicate layer sequencing; AA2 does not collapse branches—only shared projection.
