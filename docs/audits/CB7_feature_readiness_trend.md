# CB7 Feature Readiness Trend

**Block:** CB7 — Longitudinal Feature Readiness Trend  
**Primary metric:** Feature Readiness  
**Secondary metrics:** Ownership Drift, Coupling Drift, Governance Drift  
**Generated:** 2026-06-23

---

## Trend summary

| Phase | Date | Feature Readiness | Ownership | Coupling | Governance |
|---|---|---|---|---|---|
| **CB baseline** (discovery) | 2026-06-23 | Boundaries mapped; 5 safe / 6 caution / 5 prohibited | BV1 redistribution documented | AST spot-check baselines captured | Inventory freshness unknown |
| **CB2** (safe pilot) | 2026-06-23 | **↑** Safe domain validated (`content_lint_validation`) | No registry change | No emit-path coupling added | PASS |
| **CB3** (caution template) | 2026-06-23 | **↑** Guardrails machine-readable | Unchanged | Unchanged | PASS |
| **CB5** (caution pilot) | 2026-06-23 | **↑** Caution telemetry pilot validated | Unchanged | Unchanged | **↓** +19 drift surfaced (pre-existing) |
| **CB6** (frequency probe) | 2026-06-23 | **→** Prohibited domains affirmed with evidence | Unchanged | Unchanged | Drift noted, not fixed |
| **CB7** (drift watch) | 2026-06-23 | **→** Stable; safe throughput proven | **Drift detected** (hub shift) | **Drift detected** (replay/prompt↑) | **Drift confirmed** (+19) |

**Assessment:** Readiness is **improving for safe/caution process clarity**, **stable for prohibited risk posture**, and **not regressing** on architecture — but **governance inventory hygiene lags** feature velocity.

---

## CB baseline (discovery)

**Source:** [`CB_feature_boundary_readiness_discovery.md`](CB_feature_boundary_readiness_discovery.md)

| Classification | Count | Representative domains |
|---|---:|---|
| Safe | 5 | content lint, behavioral evaluators, UI mode, model config, combat/checks |
| Caution | 6 | world/scenes, state/storage, prompt/CTIR, social, API/GM, telemetry |
| Prohibited | 5 | replay, final emission, fallback/sanitizer, speaker, response policy |

**Gaps identified:** No committed full-repo fan-in table; governance JSON freshness unknown; BV1 missing runtime frequency evidence.

**Readiness score (qualitative):** **Low → Medium** — boundaries understood but not yet enforced by pilots.

---

## CB2 — Safe domain pilot

**Source:** [`CB2_safe_domain_pilot.md`](CB2_safe_domain_pilot.md)

| Metric | Result |
|---|---|
| Domain | `content_lint_validation` |
| Outcome | **PASS** — additive `code_family_counts` metric |
| Replay risk | None |
| Coupling impact | None on emit path |

**Readiness delta:** **+1** — proves safe-domain throughput with SAFE_G1/G2 only.

---

## CB3 — Caution guardrails

**Source:** [`CB3_caution_domain_readiness.md`](CB3_caution_domain_readiness.md), [`CB3_caution_domain_guardrails.md`](CB3_caution_domain_guardrails.md)

| Metric | Result |
|---|---|
| Caution domains instrumented | 6 |
| Escalation rules | E1–E8 defined |
| Replay-smoke standard | R1–R6 tiers |

**Readiness delta:** **+1** — caution domains have predictable review gates; no classification changes.

---

## CB5 — Caution domain pilot

**Source:** [`CB5_caution_domain_pilot.md`](CB5_caution_domain_pilot.md)

| Metric | Result |
|---|---|
| Domain | `telemetry_diagnostics_audit` |
| Feature | `architecture_layer_file_counts` (full diagnostic only) |
| Outcome | **PASS** |
| Governance drift | **+19 files** reported (pre-existing) |

**Readiness delta:** **+1** for caution pilot mechanics; **−0.5** for surfaced governance debt.

---

## CB6 — Speaker / fallback frequency

**Source:** [`CB6_speaker_fallback_runtime_frequency.md`](CB6_speaker_fallback_runtime_frequency.md)

| Signal | BV1 legacy | BV3D scoped | Implication |
|---|---:|---:|---|
| Fallback incidence | 69.16% (107 FEM) | 1.05% (95 FEM) | Scope-sensitive; prohibited status holds |
| Speaker repair events | N/A | 0% | Does not justify reclassification |
| Protected recurrence | 8 raw / 1 unique speaker defect | — | Acceptance risk dominates |

**Readiness delta:** **→** — evidence quality **improved**; **no domain reclassification**.

---

## CB7 — Ownership drift watch (this block)

**Source:** [`CB7_ownership_drift_watch.md`](CB7_ownership_drift_watch.md), [`artifacts/cb7_analysis.json`](../../artifacts/cb7_analysis.json)

### Coupling vs CB discovery (full-repo AST)

| Domain | CB FI | CB7 FI | Δ | Trend |
|---|---:|---:|---:|---|
| Final emission | 527 | 527 | 0 | **Stable** |
| Replay governance | 200 | 222 | +22 | **Drifting up** (test suites) |
| Prompt / CTIR | 184 | 236 | +52 | **Drifting up** |
| State / storage | 284 | 284 | 0 | **Stable** |
| API orchestration | 156 | 156 | 0 | **Stable** |
| Speaker | 29 | 29 | 0 | **Stable** |

### Coupling vs BV1 (ecosystem key modules)

| Signal | Direction | Interpretation |
|---|---|---|
| `final_emission_meta` FI 61 → 24 | **↓ Improved** | BV2/BV10 read-cluster routing |
| `emission_smoke_assertions` FI 70 → 15 | **↓ Improved** | BV7 smoke bridge extraction |
| `visibility_fallback` FI 17 → 32 | **↑ Watch** | Fallback hub pressure |
| `text_formatting` FI → 52 | **↑ Watch** | BV13 authority (governed) |
| `replay_fem_read_smoke` FI → 60 | **↑ Expected** | BV12 intentional facade |

### Governance

| Metric | CB5 | CB7 |
|---|---:|---:|
| Missing governance files | +19 | **+19** (unchanged) |
| Registry groups | 17 | **17** |

**Readiness delta:** **→** overall — process maturity up, inventory hygiene flat.

---

## Is readiness improving, stable, or regressing?

| Dimension | Verdict | Rationale |
|---|---|---|
| **Safe domain throughput** | **Improving** | CB2 PASS; registry + guardrails operational |
| **Caution domain predictability** | **Improving** | CB3/CB5 PASS; escalation rules exercised |
| **Prohibited domain stability** | **Stable** | CB6 + CB7 coupling do not justify downgrade |
| **Measurement confidence** | **Improving** | CB6 frequency + CB7 fan-in tables committed |
| **Governance hygiene** | **Regressing (mild)** | +19 unregistered files persist across CB5→CB7 |
| **Architecture concentration** | **Stable / shifted** | Hubs moved per BV program; no new monolith |

**Net:** **Stable with selective improvement** — not ready for blanket “resume all feature work.”

---

## Readiness recommendations

### Domains ready for normal feature work (safe)

| Domain ID | Evidence |
|---|---|
| `content_lint_validation` | CB2 PASS |
| `behavioral_playability_evaluators` | CB2 stretch candidate; offline lane |
| `ui_mode_frontend` | Low FI; Objective 15 isolation |
| `model_config_routing` | Config presentation; escalate if fallback triggers touched |
| `combat_checks_adjudication` | Localized engine modules; low replay adjacency |

### Domains requiring caution workflow

| Domain ID | Trigger |
|---|---|
| `world_scenes_affordances` | FI 179; replay fixture adjacency |
| `state_storage_persistence` | FI 284; harness dependence — **stable but high coupling** |
| `prompt_ctir_planning` | **FI +52 since BV1** — contract tests mandatory |
| `social_interaction_routing` | Protected speaker/route fields |
| `api_turn_orchestration` | FI 156 hub — leaf-module preference |
| `telemetry_diagnostics_audit` | CB5 pilot path; schema/history changes need CB3 replay-smoke decision |

### Domains requiring prohibited workflow

| Domain ID | CB7 affirmation |
|---|---|
| `replay_governance` | FI +22 vs CB; acceptance authority |
| `final_emission_core` | FI 527 stable; hub redistribution only |
| `fallback_sanitizer_repairs` | visibility_fallback FI +15 vs BV1 |
| `speaker_identity_adoption` | CB6: recurrence > runtime rate |
| `response_policy_contracts` | Ledger drift-watch; mutation snapshots required |

---

## Recommended next maintenance (post-CB7)

1. **Governance inventory refresh** — dedicated PR regenning `tests/test_inventory_governance.json` (+19 files).
2. **Longitudinal fallback tracking** — append scoped snapshots to `fallback_incidence_history.json` when ≥3 comparable rows exist (CB6 recommendation).
3. **Optional CB8** — speaker mismatch proxy from protected scenario pass/fail counts (still not live traffic).

---

## Program recommendation

| Question | Answer |
|---|---|
| Continue maintenance? | **Yes** — governance inventory + fallback longitudinal rows |
| Resume normal feature development? | **Yes, in safe domains only** — content lint pattern proven; use CB1 registry query before touching files |
| Expand to caution without guardrails? | **No** |
| Relax prohibited domains? | **No** — CB6/CB7 evidence does not support reclassification |

---

## Cursor Feedback

| Item | Value |
|---|---|
| Readiness trend | **Stable with selective improvement** |
| Safe domain status | **Ready** (5 domains) |
| Caution domain status | **Guarded** (6 domains; prompt FI watch) |
| Prohibited domain status | **Unchanged** (5 domains) |
| Blocking maintenance | Governance JSON +19 drift |
| Feature development | **Resume in safe domains; maintain elsewhere** |
