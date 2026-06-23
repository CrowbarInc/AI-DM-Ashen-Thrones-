# CB1 Feature Boundary Registry

**Block:** CB1 — Feature Boundary Registry  
**Source discovery:** [`CB_feature_boundary_readiness_discovery.md`](CB_feature_boundary_readiness_discovery.md)  
**Machine-readable registry:** [`CB_feature_boundary_registry.json`](CB_feature_boundary_registry.json)  
**Guardrail catalog:** [`CB_feature_boundary_guardrails.md`](CB_feature_boundary_guardrails.md)  
**Generated:** 2026-06-23

---

## Registry Summary

| Classification | Count |
|---|---|
| **Safe** | 5 |
| **Caution** | 6 |
| **Prohibited** | 5 |
| **Total domains** | 16 |

**Primary metric:** Feature Readiness — boundaries are now machine-queryable for audits and feature-planning gates (CB2–CB7).

---

## Domain Table

| Domain | Classification | Path Count | Guardrails | Required Evidence |
|---|---|---:|---|---|
| Content lint and validation tooling | safe | 4 | SAFE_G1, SAFE_G2 | Author-time scope; no emit-path wiring |
| Behavioral and playability evaluators | safe | 3 | SAFE_G1, SAFE_G2 | Advisory/offline outputs only |
| UI mode policy and frontend shell | safe | 4 | SAFE_G1, SAFE_G2 | API contracts preserved |
| Model, config, and upstream availability routing | safe | 5 | SAFE_G1, SAFE_G2 | Config scope; fallback-trigger escalation note |
| Combat, conditions, skill checks, and adjudication | safe | 5 | SAFE_G1, SAFE_G2 | Localized mechanics; CTIR impact when turn meaning shifts |
| World, scenes, affordances, clues, and leads | caution | 10 | CAUTION_G1, CAUTION_G2, CAUTION_G3 | Narrow scope; replay-smoke decision; ledger seam framing |
| State authority, storage, persistence, and session reset | caution | 9 (+ exclusions) | CAUTION_G1, CAUTION_G2, CAUTION_G3 | Rollback/replay-harness note; guard adoption |
| Prompt, CTIR, narrative planning, and turn packet | caution | 6 globs | CAUTION_G1, CAUTION_G2, CAUTION_G3 | Contract map; no silent prompt/emission rewrite |
| Social and interaction routing | caution | 3 globs | CAUTION_G1, CAUTION_G2, CAUTION_G3 | Route/speaker/fallback impact; protected replay plan |
| API and turn pipeline orchestration | caution | 5 | CAUTION_G1, CAUTION_G2, CAUTION_G3 | Leaf-module preference; integration test plan |
| Telemetry, diagnostics, attribution, and audit tooling | caution | 7 | CAUTION_G1, CAUTION_G3 | Additive vs schema change; append-only/trend-window note |
| Golden replay, protected replay, recurrence, and drift governance | prohibited | 9 | PROHIBITED_G1–G3 | Audit approval; protected replay output; ownership review |
| Final emission core, metadata, runtime projection, and terminal pipeline | prohibited | 1 glob (+ 4 exclusions) | PROHIBITED_G1–G3 | Stabilization approval; golden replay; BA-7 compliance |
| Fallback, sanitizer, and upstream repairs | prohibited | 9 | PROHIBITED_G1–G3 | Audit approval; BV1 incidence; protected replay |
| Speaker identity and post-emission adoption | prohibited | 3 | PROHIBITED_G1–G3 | BX/BT audit approval; parity/golden replay |
| Response policy contracts, enforcement, and policy mutation | prohibited | 3 | PROHIBITED_G1–G3 | Policy-block approval; mutation snapshots; golden replay |

*Path counts are registry entries (literal paths + glob patterns). Domains with `path_exclusions` document delegated ownership to avoid duplicate claims.*

---

## Highest-Risk Domains

### Replay governance (`replay_governance`)

**Classification:** prohibited  
**Why:** Acceptance authority for 41 protected observation fields. Measured 44 replay/governance modules (fan-in 200). Recent BW/BZ/BQ/BX/BY stabilization is active. Changes invalidate trend windows, recurrence measurements, and CI acceptance.

### Final emission core (`final_emission_core`)

**Classification:** prohibited  
**Why:** Core final-output-critical path (52 modules, fan-in 527). Owns gate ordering, validators, repairs orchestration, sanitizer invocation, metadata packaging, and runtime projection. Leaf unit tests are insufficient without replay and ownership proof.

### Fallback, sanitizer, and repairs (`fallback_sanitizer_repairs`)

**Classification:** prohibited  
**Why:** BV1 measured 69.16% fallback incidence on FEM artifacts with incomplete owner buckets. Fallback family, sanitizer, and opening/sealed/visibility fields are protected observations. Semantic mutation at this boundary drives player-visible meaning.

### Speaker identity and adoption (`speaker_identity_adoption`)

**Classification:** prohibited  
**Why:** Recent BX parity and BT divergence work; BV1 reports speaker projection drift on 8 protected rows. `selected_speaker_id` and social trace route/speaker fields are protected. Post-emission adoption can mutate player-visible speaker attribution.

### Response policy (`response_policy_contracts`)

**Classification:** prohibited  
**Why:** Ledger marks contracts and enforcement as governed drift-watch. Enforcement owns post-GPT mutation and strict-social bypass routing. Protected fields include response-type requirements, repairs, and mutation lineage.

---

## Feature Planning Guidance

### Can proceed immediately (safe domains)

| Example work | Domain |
|---|---|
| Add a new scene lint rule and CLI report field | content_lint_validation |
| Add an offline playability metric to the behavioral gauntlet | behavioral_playability_evaluators |
| New UI mode display toggle behind existing API contracts | ui_mode_frontend |
| Model alias table or upstream preflight messaging | model_config_routing |
| New condition effect or noncombat resolution branch | combat_checks_adjudication |

**Gate:** SAFE_G1 focused tests + SAFE_G2 boundary check (no emit-path wiring).

### Requires caution review

| Example work | Domain | Extra guardrails |
|---|---|---|
| New affordance type affecting player choices in scenes | world_scenes_affordances | CAUTION_G2 replay smoke |
| Campaign reset default change | state_storage_persistence | CAUTION_G2 + rollback tests |
| CTIR field added to resolved-turn shape | prompt_ctir_planning | CAUTION_G2 + boundary contract tests |
| Directed social routing for broadcast open calls | social_interaction_routing | CAUTION_G2 protected route/speaker probes |
| New API endpoint wiring through turn pipeline | api_turn_orchestration | CAUTION_G3 — prefer leaf module |
| Recurrence history schema change in trend tooling | telemetry_diagnostics_audit | CAUTION_G3 + CB5 alignment |

### Requires audit approval (prohibited domains)

| Example work | Domain | Approval packet |
|---|---|---|
| Add protected observation field to manifest | replay_governance | PROHIBITED_G1 + manifest diff + golden_replay |
| Reorder final-emission gate layers | final_emission_core | PROHIBITED_G1–G3 + ownership audit |
| Change sanitizer strip behavior | fallback_sanitizer_repairs | PROHIBITED_G1–G3 + BV1 incidence |
| Speaker signature algorithm change | speaker_identity_adoption | PROHIBITED_G1–G3 + BX parity suite |
| New post-GPT policy mutator | response_policy_contracts | PROHIBITED_G1–G3 + mutation snapshots |

---

## Consistency Validation

Validation run against `CB_feature_boundary_registry.json` on 2026-06-23.

| Check | Result |
|---|---|
| Every CB discovery domain present in registry | **PASS** — 16/16 domains mapped |
| Every domain has a classification | **PASS** — all `safe`, `caution`, or `prohibited` |
| Every caution domain has guardrails | **PASS** — all caution domains have ≥ CAUTION_G1 |
| Every prohibited domain has guardrails | **PASS** — all have PROHIBITED_G1, G2, G3 |
| No duplicate literal path ownership | **PASS** — no literal path appears in two domains |
| Glob overlap resolved via exclusions | **PASS** — see notes below |

### Glob overlap resolutions

| Overlap | Resolution |
|---|---|
| `game/final_emission*.py` vs fallback-named modules | `final_emission_core.path_exclusions` delegates 4 fallback modules to `fallback_sanitizer_repairs` |
| `data/*.json` vs `data/world.json` / `data/scenes/**` | `state_storage_persistence.path_exclusions` delegates world/scene data to `world_scenes_affordances` |
| `docs/audits/**` in telemetry domain | Intentional — audit artifacts are tooling output; CB registry files are meta-governance, not runtime ownership conflict |

### Discovery-to-registry ID map

| Discovery row | Registry `id` |
|---|---|
| Content lint and validation tooling | `content_lint_validation` |
| Behavioral and playability evaluators | `behavioral_playability_evaluators` |
| UI mode policy and frontend shell | `ui_mode_frontend` |
| Model/config/upstream availability routing | `model_config_routing` |
| Combat, conditions, skill checks, adjudication | `combat_checks_adjudication` |
| World, scenes, affordances, clues, leads | `world_scenes_affordances` |
| State authority, storage, persistence, campaign/session reset | `state_storage_persistence` |
| Prompt, CTIR, narrative planning, turn packet | `prompt_ctir_planning` |
| Social and interaction routing | `social_interaction_routing` |
| API and turn pipeline orchestration | `api_turn_orchestration` |
| Telemetry, diagnostics, attribution, audit tooling | `telemetry_diagnostics_audit` |
| Golden replay, protected replay, recurrence, drift governance | `replay_governance` |
| Final emission core, metadata, runtime projection, terminal pipeline | `final_emission_core` |
| Fallback, sanitizer, upstream repairs | `fallback_sanitizer_repairs` |
| Speaker identity and post-emission adoption | `speaker_identity_adoption` |
| Response policy contracts/enforcement and policy mutation | `response_policy_contracts` |

---

## Cursor Feedback

### Domain counts

- **5 safe** — throughput lanes for normal feature work with SAFE_G1/G2 only.
- **6 caution** — feature work allowed with CAUTION_G1–G3 and conditional replay smoke.
- **5 prohibited** — feature work blocked; stabilization requires PROHIBITED_G1–G3 audit packet.

### Missing ownership areas

| Gap | Impact | Suggested owner block |
|---|---|---|
| `game/narrative_*.py` / `game/planner_*.py` — no singular ledger seam | prompt_ctir_planning lists owners but planner/narrative submodules lack explicit runtime-owner rows | CB7 ownership refresh |
| `game/defaults.py` — high fan-in (FI 105) under state bucket | Persistence defaults churn risk | Tie to state_storage_persistence + CB3 rollback template |
| Behavioral evaluator subpackages — offline owner clear but no `tests/TEST_AUDIT.md` row refresh post-BZ | Test placement ambiguity | CB7 + test inventory refresh |
| `artifacts/**` — telemetry domain owns path but artifact schema owners are per-tool | Trend-window sensitivity undocumented per artifact | CB5 metric stability inventory |
| Combat/adjudication — no dedicated ledger seam (localized modules) | Lower risk; acceptable for safe pilot | Optional CB2 extension after content_lint pilot |

### Unresolved classification ambiguities

| Topic | Current classification | Ambiguity | Resolution path |
|---|---|---|---|
| Upstream routing fallback triggers | safe (`model_config_routing`) | Discovery notes moderate speaker/policy risk when upstream failures enter fast fallback | Escalate to caution if `upstream_dependent_run_gate*` changes fallback entry; document in PR |
| `game/narration_*.py` | caution (prompt bucket) | Overlaps visibility and emission-adjacent behavior | Keep caution; CB3 probe template should name narration visibility tests |
| Telemetry `tools/**` vs `game/*telemetry*` | caution | Broad glob includes unrelated tools | CB5 narrows trend-sensitive tool subset |
| `game/final_emission_speaker_observation.py` | prohibited (final_emission glob) | Speaker observation vs speaker_identity_adoption boundary | Remains prohibited; speaker contract changes need both domains in approval packet |

### Recommended CB2 scope

**CB2 — Safe Domain Pilot** (per discovery recommendation):

1. **Target:** `content_lint_validation` domain (`game/content_lint.py`, `tools/run_content_lint.py`).
2. **Pilot change:** One additive diagnostic rule or report field with no runtime consumer.
3. **Success:** SAFE_G1/G2 satisfied; no imports from prohibited paths; no replay/final-emission/speaker surface diff.
4. **Stretch:** If pilot passes, second pilot on `behavioral_playability_evaluators` (offline metric only).

**Follow-on priority:** CB3 (caution probe templates) and CB4 (prohibited approval gate) should reference this registry JSON as the query source.

---

## Related blocks

| Block | Purpose |
|---|---|
| CB2 | Safe domain pilot — validate throughput on `content_lint_validation` |
| CB3 | Caution guardrail template — minimal test bundles per caution domain |
| CB4 | Prohibited domain approval gate — formalize PROHIBITED_G1 criteria |
| CB5 | Metric stability inventory — trend-window-sensitive artifacts |
| CB6 | Speaker/fallback runtime frequency probe — close BV1 evidence gaps |
| CB7 | Ownership drift watch refresh — post-BZ fan-in comparison |
