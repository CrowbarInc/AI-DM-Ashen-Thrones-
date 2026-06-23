# BO — Next Cycle Candidates

**Date:** 2026-06-17  
**Basis:** Measured data only from BO audit (`artifacts/bo_maintenance_audit.json`)  
**Constraint:** Opportunities only — no implementation plans

Candidates ranked by expected maintenance-economics ROI given post-BJ/BK/BL/BN/BM plateau.

---

## 1. BK-H1 — Owner-Bucket Consolidation (`final_emission_meta` read-side registry)

| Field | Value |
|-------|-------|
| **Target** | Collapse opening/visibility/sealed bucket classifiers into unified `final_emission_meta` read-side registry |
| **Expected maintenance benefit** | **High** — reduces BK-measured 7–11 FTPF on owner-bucket changes to estimated 3–5; addresses fan-in 57 hub growth (+8 since BK recon) |
| **Expected risk** | **Medium** — FEM meta is replay/dashboard-sensitive; protected projection tests (`test_final_emission_meta`, `test_golden_replay_projection`) must hold |
| **Estimated repository impact** | 4–6 runtime modules + 3 direct-owner test suites (`opening`, `visibility`, `sealed` fallback tests = 3,893 LOC combined) |
| **Rationale** | BK recon identified this as the **largest ownership seam**. BO confirms `final_emission_meta` fan-in grew to 57 — hub is active, not shrinking. Highest measured cross-projection drag remaining in FE domain. |

---

## 2. BK-H2 — Sealed Consumes Visibility Outcomes

| Field | Value |
|-------|-------|
| **Target** | Stop `final_emission_sealed_fallback` from re-assembling provider graph owned by `standard_visibility_safe_fallback` |
| **Expected maintenance benefit** | **High** — attacks BK **largest touch cascade** (6–9 FTPF visibility family); `final_emission_visibility_fallback` measured 18 fan-in / 18 fan-out |
| **Expected risk** | **Medium** — selection order changes are behavior-sensitive; `test_final_emission_sealed_fallback` (516 LOC) + visibility suites co-move |
| **Estimated repository impact** | 2–3 runtime modules + 2–3 test suites (~2,500 LOC cluster) |
| **Rationale** | BO confirms visibility fallback is a **bidirectional routing hub** — only FE module with symmetric 18/18 fan metrics. BK git co-occurrence (7 shared commits between opening/visibility test suites) still valid. |

---

## 3. BP-1 — Golden Replay Helper Decomposition

| Field | Value |
|-------|-------|
| **Target** | Split `tests/helpers/golden_replay.py` (1,995 LOC, fan-out 13, 15 external callers) into scenario-runner / assertion / manifest sub-helpers |
| **Expected maintenance benefit** | **High** — reduces replay change blast radius; addresses #18 largest file in repo |
| **Expected risk** | **Low–Medium** — BM already decomposed test owners; helper split is import-path work similar to BD-4 pattern |
| **Estimated repository impact** | 1 helper → 3–4 helpers; ~15 external caller import updates |
| **Rationale** | Replay maintenance **not fully localized** per BO §C — two helper hubs (`golden_replay.py` + `golden_replay_projection.py`) = 3,580 LOC. BM decomposed tests but not helpers (BM completion doc "Shared Helper Pressure" follow-up). |

---

## 4. BP-2 — Golden Replay Projection Facade Thinning

| Field | Value |
|-------|-------|
| **Target** | Reduce `tests/helpers/golden_replay_projection.py` (1,585 LOC) surface area |
| **Expected maintenance benefit** | **Medium–High** — BD-4 already routed consumers; remaining density is internal helper complexity + `test_golden_replay_projection.py` (747 LOC, 25 tests) |
| **Expected risk** | **Medium** — protected observation path; 3 allowlisted direct import sites for runtime projection |
| **Estimated repository impact** | 1 helper + 1 test owner (~2,330 LOC) |
| **Rationale** | Second replay hub by LOC. External callers down to 6 (BD success) but internal LOC unchanged — next gain is **within-facade** compression, not routing. |

---

## 5. BT-1 — Visibility Fallback Test Suite Thinning

| Field | Value |
|-------|-------|
| **Target** | `tests/test_final_emission_visibility_fallback.py` (1,927 LOC, 59 tests) — assertion economy / structural lock thinning |
| **Expected maintenance benefit** | **Medium–High** — largest single FE test file; pairs with 1,976 LOC runtime module (3,903 combined) |
| **Expected risk** | **Medium** — direct owner suite; over-thinning loses legality coverage BE6 protects |
| **Estimated repository impact** | 1 test file; potential helper extraction to shared visibility harness |
| **Rationale** | BO test maintenance analysis: #1 remaining FE test hotspot by LOC. BM addressed gate tests but not visibility fallback owner suite. |

---

## 6. BT-2 — BJ Delegator Regression Suite Economy

| Field | Value |
|-------|-------|
| **Target** | `tests/test_final_emission_gate_delegator_regression.py` (1,370 LOC, 123 tests, fan-out 42) |
| **Expected maintenance benefit** | **Medium** — reduces static `inspect.getsource` tax on every gate submodule edit |
| **Expected risk** | **Medium–High** — BJ locks exist to prevent delegator regression; over-thinning loses refactor safety net |
| **Estimated repository impact** | 1 test file; possible migration to registry-driven delegator manifest |
| **Rationale** | Highest fan-out **test module** (42). BM intentionally isolated BJ locks here — BO confirms it remains edit-tax hotspot post-decomposition. |

---

## 7. BG-1 — Governance Registry Domain Split

| Field | Value |
|-------|-------|
| **Target** | `tests/test_ownership_registry.py` (4,518 LOC, fan-out 56) — split BN/BD/BM/BA guard domains |
| **Expected maintenance benefit** | **Medium** — reduces governance edit coupling; #4 largest file in repo |
| **Expected risk** | **Low** — test-only; guards are additive; split preserves enforcement if index preserved |
| **Estimated repository impact** | 1 file → 3–4 guard domain files + shared index |
| **Rationale** | Highest fan-out module in entire repo (56). BN added 11 guard blocks here — contraction cycles **concentrated** guards into a megamodule. |

---

## 8. BR-1 — Replay Drift Taxonomy Consolidation

| Field | Value |
|-------|-------|
| **Target** | `tests/helpers/replay_drift_taxonomy.py` (1,253 LOC) + drift test suite (115 tests across 6 files, 1,977 LOC) |
| **Expected maintenance benefit** | **Medium** — taxonomy hub feeds 115 drift/governance tests; consolidation reduces parallel classification surfaces |
| **Expected risk** | **Low–Medium** — advisory/reporting only per AR cycle; no runtime behavior |
| **Estimated repository impact** | 1 helper + 6 test files (~3,230 LOC island) |
| **Rationale** | Drift suite is coherent but **taxonomy helper is #26 largest file** and single classification authority for hotspots, risk, trends, longitudinal modules. |

---

## 9. BR-2 — Runtime Megamodule Boundary Recon (`interaction_context`)

| Field | Value |
|-------|-------|
| **Target** | `game/interaction_context.py` (6,004 LOC, fan-in 74) — ownership boundary recon only |
| **Expected maintenance benefit** | **High** (if followed by scoped extraction) — #1 LOC file; 74 importers = widest runtime blast radius |
| **Expected risk** | **High** — core runtime state; not addressed by BJ/BN/BM scope |
| **Estimated repository impact** | Recon: 1 module; potential future: 3–5 extraction targets |
| **Rationale** | Contraction cycles did not touch this module. BO confirms it **replaced gate monolith as top hotspot**. Recon-only cycle aligns with BO "measure first" mandate. |

---

## 10. BA-1 — API Router Fan-Out Reduction Recon

| Field | Value |
|-------|-------|
| **Target** | `game/api.py` (5,534 LOC, fan-in 61, fan-out 48) — routing layer recon |
| **Expected maintenance benefit** | **High** (if followed by extraction) — dual hub (#2 LOC, highest runtime fan-out) |
| **Expected risk** | **High** — HTTP entry point; all integration tests depend on API surface |
| **Estimated repository impact** | Recon: 1 module; potential future: turn-support / UI-mode / upstream splits (partial work exists in `api_turn_support`) |
| **Rationale** | BO routing layer analysis: `game.api` is the **primary runtime router** with symmetric hub metrics. Contraction improved FE entry but API spine unchanged. |

---

## Candidate Priority Matrix

| Priority | Candidate | Benefit | Risk | Domain |
|:--------:|-----------|---------|------|--------|
| 1 | BK-H1 Owner-bucket consolidation | High | Medium | Final emission |
| 2 | BK-H2 Sealed/visibility dedup | High | Medium | Final emission |
| 3 | BP-1 Golden replay helper split | High | Low–Med | Replay |
| 4 | BP-2 Projection facade thinning | Med–High | Medium | Replay |
| 5 | BT-1 Visibility fallback test thinning | Med–High | Medium | Tests |
| 6 | BT-2 BJ delegator economy | Medium | Med–High | Tests |
| 7 | BG-1 Governance registry split | Medium | Low | Governance |
| 8 | BR-1 Drift taxonomy consolidation | Medium | Low–Med | Replay |
| 9 | BR-2 Interaction context recon | High* | High | Runtime |
| 10 | BA-1 API router recon | High* | High | Runtime |

\* High potential benefit contingent on follow-up extraction cycle — recon itself is low-risk.

---

## Explicitly Deprioritized (Measured Reasons)

| Former Target | Deprioritize Because |
|---------------|---------------------|
| Further `final_emission_gate.py` contraction | 324 LOC — BN/BM already reached diminishing returns; BN11 allowlist guarded |
| `test_golden_replay.py` / `test_final_emission_gate.py` monolith split | BM complete — stubs + 11 focused owner files exist |
| BD-style import facade expansion | BD-6 at 0 violations — facades holding; new facades should target **LOC hubs**, not import count |
| Gate context preflight extraction | BN3–BN11 complete — 8 modules, 436 LOC, guarded |

---

## Sequencing Recommendation (Economics Only)

1. **FE fallback cluster** (BK-H1 + BK-H2) — highest measured cross-file drag remaining in contraction scope adjacency
2. **Replay helper hubs** (BP-1 + BP-2) — second-largest concentrated LOC island (3,580 LOC in 2 files)
3. **Test economy** (BT-1, BT-2, BG-1) — reduce edit tax without runtime behavior risk
4. **Runtime recon** (BR-2, BA-1) — largest LOC/fan-in but highest behavior risk; recon before any extraction

No implementation plans included — candidates derived strictly from BO measured evidence.
