# CB3 Caution Domain Readiness

**Block:** CB3 — Caution Domain Guardrail Template  
**Guardrail template:** [`CB3_caution_domain_guardrails.md`](CB3_caution_domain_guardrails.md)  
**Registry:** [`CB_feature_boundary_registry.json`](CB_feature_boundary_registry.json)  
**Generated:** 2026-06-23

---

## Domain Inventory

Six caution domains from CB1 registry. Fan-in/fan-out from CB discovery AST scan.

| Registry ID | Domain | FI / FO | Primary owners | Primary tests | Replay deps | Protected fields | Speaker | Fallback |
|---|---|---:|---|---|---|---|---|
| `world_scenes_affordances` | World, scenes, affordances, clues, leads | 179 / 43 | `game/world.py`, `game/affordances.py`, `game/exploration.py` | `tests/test_world_*`, `tests/test_affordance_*`, `tests/test_exploration_resolution.py` | Long-session fixture source data; prompt context from scene state | Indirect: `resolution_kind` | Moderate (interaction context) | Moderate (visible-fact selection) |
| `state_storage_persistence` | State, storage, persistence, reset | 284 / 16 | `game/state_authority.py`, `game/storage.py`, `game/session.py` | `tests/test_state_authority.py`, `tests/test_save_load.py`, `tests/test_runtime_persistence_regression_suite_obj14.py` | Replay harness storage/reset semantics | Indirect via persisted turn state | Low–moderate | Low–moderate |
| `prompt_ctir_planning` | Prompt, CTIR, planning, turn packet | 184 / 73 | `game/prompt_context.py`, `game/ctir.py`, `game/ctir_runtime.py`, `game/turn_packet.py` | `tests/test_prompt_context.py`, `tests/test_ctir_pipeline_integration.py`, `tests/test_prompt_context_ctir_boundary.py` | Replay output + trend windows | `final_text`, `resolution_kind`, `response_type_*`, mutation lineage | Moderate | Moderate |
| `social_interaction_routing` | Social, interaction, dialogue | 260 / 75 | `game/social_exchange_emission.py`, `game/interaction_context.py` | `tests/test_social_exchange_emission.py`, `tests/test_directed_social_routing.py` | Six+ protected golden scenarios (speaker/route) | `selected_speaker_id`, `route_kind`, `trace.social_contract_trace.*`, `trace.canonical_entry.*` | **High** | **High** (`sanitizer_strict_social_*`) |
| `api_turn_orchestration` | API, GM, turn pipeline | 156 / 101 | `game/api.py`, `game/gm.py` | `tests/test_turn_pipeline_shared.py`, `tests/test_api_*` | Full E2E replay path | Most protected families (orchestration hub) | **High** | **High** |
| `telemetry_diagnostics_audit` | Telemetry, diagnostics, audit tooling | 86 / 152 | `game/stage_diff_telemetry.py`, `tools/test_audit.py` | `tests/test_stage_diff_telemetry.py`, `tests/test_attribution_*` | BW/BZ trend windows; recurrence history | Low (additive); high if projection tooling touched | Moderate (attribution reads) | Moderate (incidence reads) |

---

## Guardrail Matrix

Full matrix with required tests, replay-smoke rules, protected-field review, escalation triggers, and approval paths:

→ **[`CB3_caution_domain_guardrails.md` — Guardrail matrix](CB3_caution_domain_guardrails.md#guardrail-matrix)**

Per-domain minimum validation bundles (unit / integration / replay smoke / ownership):

→ **[`CB3_caution_domain_guardrails.md` — Per-domain bundles](CB3_caution_domain_guardrails.md#per-domain-minimum-validation-bundles)**

---

## Escalation Rules

Caution workflow **stops** and **PROHIBITED_G1–G3** applies when:

1. **Final emission** — any `game/final_emission*` edit (E1)
2. **Fallback / sanitizer / repair** — fallback behavior, sanitizer, upstream repairs (E2, E7)
3. **Speaker identity** — speaker contract, signature, post-emission adoption (E3)
4. **Response policy** — contracts, enforcement, post-GPT mutation (E4, E8)
5. **Replay governance** — golden replay helpers, protected registry, manifest tools (E5)
6. **Protected fields** — changes affecting 41 manifest paths without audit path (E6)

Import tripwire list and constant-only exception documented in guardrails doc.

→ **[Escalation rules detail](CB3_caution_domain_guardrails.md#escalation-rules-caution--prohibited)**

---

## Replay Smoke Standard

| Element | Standard |
|---|---|
| **When required** | Player-visible, CTIR/prompt, social route/speaker, API orchestration, or persistence harness changes |
| **Qualifying suites** | R1 targeted structural → R6 full `golden_replay` (lowest tier that covers risk) |
| **Pass** | Exit 0 on selected suite; no drift in targeted protected fields |
| **Fail** | Fix, triage with documented out-of-scope, or escalate to prohibited |
| **Evidence** | PR section: domain, tier, command, observation families, result, output excerpt |

→ **[Full replay smoke standard](CB3_caution_domain_guardrails.md#replay-smoke-standard)**

---

## Highest-Risk Caution Domains

Ranked by **coupling × replay adjacency × protected-field exposure**:

| Rank | Domain | Score rationale |
|---|---|---|
| 1 | `api_turn_orchestration` | Hub for storage, prompt, CTIR, retry, fallback, finalization; E2E replay flows through `api`/`gm`; highest emit-path adjacency without being prohibited |
| 2 | `social_interaction_routing` | FI 260; direct protected fields (`selected_speaker_id`, `route_kind`, social trace); six protected golden scenarios; speaker/fallback prohibited domains adjacent |
| 3 | `prompt_ctir_planning` | FI 184/FO 73; shifts `final_text` and `resolution_kind` downstream; ledger drift-watch on CTIR/prompt adapter |
| 4 | `state_storage_persistence` | FI 284; replay harness depends on reset/storage; `defaults` FI 105 churn risk |
| 5 | `world_scenes_affordances` | FI 179; fixture and prompt context adjacency; moderate protected exposure |
| 6 | `telemetry_diagnostics_audit` | Lowest direct protected-field risk for **additive** work; rises to rank 3–4 when trend/recurrence schema changes |

---

## Recommended Pilot Domain

### Primary recommendation: `telemetry_diagnostics_audit` (additive scope)

**Why safest caution pilot:**

- CB registry notes: "Safe for additive reports"
- Default guardrails: CAUTION_G1 + CAUTION_G3 only (CAUTION_G2 conditional)
- No mandatory replay smoke for read-only report extensions
- Clear escalation tripwire: touching `golden_replay*` or trend tools → prohibited

**Suggested pilot feature:** Add one additive column or summary field to an existing audit report (mirror CB2 safe pilot pattern) in `tools/test_audit.py` output or a `tests/test_*report*.py` contract — no metric history schema change.

### Secondary recommendation: `world_scenes_affordances` (data-only scope)

**When:** Feature is confined to `data/scenes/**` or `data/world.json` with no `game/world*.py` logic change.

**Why:** Author-time data changes with existing scene/world test suites; replay smoke only if protected fixture source changes.

**Avoid for first caution pilot:** `social_interaction_routing`, `api_turn_orchestration` — mandatory replay smoke and high protected-field exposure.

---

## Validation

| Check | Result |
|---|---|
| Every caution domain from CB registry represented | **PASS** — 6/6 domains |
| Every domain has validation requirements | **PASS** — per-domain bundles in guardrails doc |
| Every domain has escalation criteria | **PASS** — matrix + E1–E8 rules |
| Replay-smoke standard documented | **PASS** — when/tiers/criteria/evidence format |
| No runtime code modified | **PASS** — documentation only |
| No prohibited paths modified | **PASS** |

---

## Readiness status

**CB3 template status: COMPLETE**

Caution-domain feature work can proceed under CAUTION_G1–G3 with documented bundles. Next block: **CB4** (prohibited approval gate) or caution pilot on `telemetry_diagnostics_audit`.

---

## Cursor Feedback

| Item | Finding |
|---|---|
| **Safest caution domain** | `telemetry_diagnostics_audit` for additive reports (no trend-window schema change) |
| **Riskiest caution domain** | `api_turn_orchestration` — routes through all emit-path layers; mandatory replay smoke for orchestration edits |
| **Replay-smoke requirements** | Conditional for world/state/prompt/telemetry; **mandatory** for social route/speaker and API orchestration changes; six-tier suite ladder (R1–R6) |
| **Escalation triggers discovered** | Eight explicit triggers (E1–E8); import tripwire list; protected-field path changes; CB2 constant-only import exception carries forward |
| **CB4 dependency** | Prohibited approval gate should reference this doc's escalation table and replay R6 tier |
| **CB5 dependency** | Metric stability inventory should narrow `telemetry_diagnostics_audit` trend-sensitive tool subset |
