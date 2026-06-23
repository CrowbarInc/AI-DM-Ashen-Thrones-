# CB Feature Boundary Guardrail Catalog

Standardized guardrails referenced by `docs/audits/CB_feature_boundary_registry.json`. Each guardrail defines a trigger, required evidence, required tests, and approval criteria.

**Source:** [`CB_feature_boundary_readiness_discovery.md`](CB_feature_boundary_readiness_discovery.md)  
**Registry:** [`CB_feature_boundary_registry.json`](CB_feature_boundary_registry.json)

---

## SAFE Guardrails

### SAFE_G1 — Focused domain tests

| Field | Requirement |
|---|---|
| **Trigger condition** | Any additive or behavioral change in a **safe** domain. |
| **Required evidence** | PR description names the domain, lists touched paths, and states that runtime emission / replay / policy surfaces were not modified. |
| **Required tests** | At least one focused pytest module from the domain's `required_tests` list in the registry; new behavior must add or extend assertions in that suite (not only downstream integration). |
| **Approval criteria** | Domain owner suite passes locally; no new imports from prohibited domains; reviewer confirms change stays within safe boundary notes. |

### SAFE_G2 — Author-time / advisory boundary

| Field | Requirement |
|---|---|
| **Trigger condition** | Safe-domain work that could be promoted into runtime gates, final emission, sanitizer, response policy, or protected replay assertions. |
| **Required evidence** | Explicit statement that outputs remain author-time, advisory, or presentation-only; diff shows no new runtime consumers of lint/evaluator/UI-mode artifacts on the emit path. |
| **Required tests** | SAFE_G1 tests plus a negative check: no new `game/final_emission*`, `game/fallback*`, `game/response_policy*`, or `tests/helpers/golden_replay*` imports from changed safe modules. |
| **Approval criteria** | No wiring into gate orchestration, fallback lanes, or policy enforcement; configuration-only routing changes do not alter fallback-trigger semantics without escalating to caution review. |

---

## CAUTION Guardrails

### CAUTION_G1 — Narrow, data-backed scope

| Field | Requirement |
|---|---|
| **Trigger condition** | Any feature or refactor in a **caution** domain. |
| **Required evidence** | Scoped change description (what state/contract fields move), data or fixture references (`data/scenes/*`, `data/*.json`, session snapshots), and ownership framing per `docs/architecture_ownership_ledger.md` when touching a governed seam. |
| **Required tests** | Domain direct-owner suite(s) from registry `required_tests`; rollback or save/load tests when persistence semantics change. |
| **Approval criteria** | Change is narrow (no broad schema/default churn); fan-in hubs (`api`, `storage`, `interaction_context`) are not refactored without explicit plan; state-authority guards respected when mutating authoritative domains. |

### CAUTION_G2 — Replay-smoke probe

| Field | Requirement |
|---|---|
| **Trigger condition** | Caution-domain change that can alter player-visible choices, resolved-turn meaning, route/speaker fields, prompt context, or protected long-session fixture observations. |
| **Required evidence** | Replay-smoke decision note: which observation families could move and why; if none, document the negative case. |
| **Required tests** | CAUTION_G1 tests plus at least one of: targeted replay smoke (`tests/test_replay_*`, transcript slice, or domain-specific protected fixture probe); CTIR/prompt contract tests when turn meaning changes; social route/speaker tests when interaction routing changes. |
| **Approval criteria** | Replay-smoke failures are triaged before merge; no silent semantic rewrite at prompt/final-emission boundary; API orchestration changes prefer leaf-module behavior with downstream integration tests. |

### CAUTION_G3 — High-coupling seam contract

| Field | Requirement |
|---|---|
| **Trigger condition** | Caution-domain edits on seams with fan-in ≥ 100 or ledger **governed drift-watch** status (world progression, CTIR/prompt adapter, social emission, telemetry tied to trend windows). |
| **Required evidence** | Contract test map listing affected modules and ledger runtime owner; for telemetry/audit tooling, append-only and schema-stability impact note. |
| **Required tests** | CAUTION_G1 tests plus boundary/contract modules (e.g. `tests/test_ctir_*_boundary.py`, `tests/test_prompt_context_ctir_boundary.py`, `tests/test_state_authority.py`, attribution/report contract tests for metric schema changes). |
| **Approval criteria** | No new co-equal ownership homes; metric history and trend-window artifacts preserve append-only semantics unless CB5/CB4 audit approves schema change. |

---

## PROHIBITED Guardrails

### PROHIBITED_G1 — Named audit approval

| Field | Requirement |
|---|---|
| **Trigger condition** | Any change under a **prohibited** domain path (normal feature work blocked by default). |
| **Required evidence** | Named audit block approval (CB4 gate when established; until then: explicit audit issue/block id, stabilization purpose, and metric-impact note for Feature Readiness / maintenance economics). |
| **Required tests** | N/A until approval granted; approval packet must name required test bundles (see PROHIBITED_G2/G3). |
| **Approval criteria** | Change is stabilization, additive reporting, or manifest-governed replay work—not net-new player-facing feature behavior; approval author is recorded in PR and audit closeout. |

### PROHIBITED_G2 — Protected replay evidence

| Field | Requirement |
|---|---|
| **Trigger condition** | Approved prohibited-domain change that can affect protected observation fields (41 fields per `docs/testing/protected_replay_manifest.md`), trend windows, or recurrence measurements. |
| **Required evidence** | Before/after protected replay command output; manifest diff when observation schema changes; BZ/BW trend-window impact note when applicable. |
| **Required tests** | `python -m pytest -m golden_replay -q` (or scoped equivalent named in approval); domain direct-owner suites (`tests/test_final_emission*`, `tests/test_fallback_*`, `tests/test_speaker_contract_*`, `tests/test_response_policy_*`, `tests/test_protected_replay_registry.py`); incidence or parity reports when fallback/speaker fields move (BV1/BX/BY lineage). |
| **Approval criteria** | Protected replay passes or failures are explicitly accepted with manifest/trend-window update; no undocumented observation drift. |

### PROHIBITED_G3 — Ownership review

| Field | Requirement |
|---|---|
| **Trigger condition** | Approved prohibited-domain change touching runtime owner modules in `docs/architecture_ownership_ledger.md`. |
| **Required evidence** | Ownership review checklist: runtime owner unchanged or ledger updated; direct-owner suite identified; no BA-7 test-magnet regression on gate suites; fan-in/fan-out delta when hubs move. |
| **Required tests** | `tests/test_ownership_registry.py`; practical primary direct-owner suite for each touched seam; `tools/final_emission_ownership_audit.py` (advisory) for final-emission boundary edits. |
| **Approval criteria** | Singular runtime owner preserved; downstream suites remain consumers not alternate semantic homes; incomplete owner buckets (BV1) are not worsened without follow-up block. |

---

## Guardrail selection matrix

| Classification | Default guardrails | Replay smoke | Audit approval |
|---|---|---|---|
| **safe** | SAFE_G1, SAFE_G2 | Not required | Not required |
| **caution** | CAUTION_G1 + CAUTION_G3 | CAUTION_G2 when player-visible / replay-adjacent | Not required (escalate to prohibited if emit path entered) |
| **prohibited** | PROHIBITED_G1, PROHIBITED_G2, PROHIBITED_G3 | Required via PROHIBITED_G2 | Required via PROHIBITED_G1 |
