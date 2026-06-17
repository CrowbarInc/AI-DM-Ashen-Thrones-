# BK — Fallback Touch Cascades

**Cycle:** BK — Discovery / Audit  
**Date:** 2026-06-16  

**Method:** `git log --since=2025-10-01` over fallback-named paths; co-occurrence analysis of files appearing in the same commit; cross-reference with cycles AP, AB, AM, AU, BJ, BL.

**FTPF (Files Touched Per Fix):** estimated typical file count when behavior in the cluster changes.

---

## Cluster 1 — Gate Visibility Family (opening + sealed + visibility)

**Files involved:**
- `game/final_emission_visibility_fallback.py`
- `game/final_emission_opening_fallback.py`
- `game/final_emission_sealed_fallback.py`
- `game/final_emission_opening_fallback.py` ↔ tests:
  - `tests/test_final_emission_opening_fallback.py`
  - `tests/test_final_emission_sealed_fallback.py`
  - `tests/test_final_emission_visibility_fallback.py`
- `tests/helpers/opening_fallback_evidence.py`
- `tests/test_opening_fallback_owner_bucket.py`

**Co-occurrence evidence:**  
- `test_final_emission_opening_fallback` + `test_final_emission_sealed_fallback`: **7** shared commits  
- `test_final_emission_opening_fallback` + `test_final_emission_visibility_fallback`: **7** shared commits  
- `test_final_emission_sealed_fallback` + `test_final_emission_visibility_fallback`: **5** shared commits  
- `game/final_emission_sealed_fallback` + `game/final_emission_visibility_fallback`: **4** shared commits  

**Reason they move together:**  
Visibility routing (`standard_visibility_safe_fallback`) delegates opening to `opening_scene_safe_fallback_selection` and sealed paths wrap `VisibilitySelectedFallback`. Selection order, owner buckets, and composition meta are **cross-asserted** across three direct-owner test suites. Cycle BJ ("Gate Responsibility Extraction") touched all three runtime modules in one commit.

**Estimated FTPF:** **6–9 files** (3 runtime + 3–4 tests + evidence helper)

---

## Cluster 2 — Opening Authorship & Metadata

**Files involved:**
- `game/opening_deterministic_fallback.py`
- `game/upstream_response_repairs.py`
- `game/final_emission_opening_fallback.py`
- `game/final_emission_meta.py`
- `game/final_emission_replay_projection.py`
- `tests/helpers/opening_fallback_evidence.py`
- `tests/test_opening_fallback_owner_bucket.py`
- `tests/test_golden_replay.py` / `tests/test_golden_replay_fallback_projection.py`

**Co-occurrence evidence:**  
Cycles AJ ("Opening Fallback Metadata Consolidation") and AP ("Fallback Authorship Resolution") touched `opening_fallback` + `replay_projection` + `opening_deterministic_fallback` together. `opening_fallback_evidence` + `test_opening_fallback_owner_bucket`: **5** shared commits.

**Reason they move together:**  
Authorship is stamped at **upstream packaging**, mirrored at **selection**, projected via **`apply_opening_fallback_projection_fields`**, bucket-mapped in **meta**, lineage-projected in **replay_projection**, and **golden-replay protected**. Field renames require manifest refresh (`tools/refresh_protected_replay_manifest.py`).

**Estimated FTPF:** **7–11 files**

---

## Cluster 3 — Fallback Behavior Policy (contract → repair → gate)

**Files involved:**
- `game/fallback_behavior.py`
- `game/final_emission_repairs.py`
- `game/final_emission_validators.py`
- `game/prompt_context.py`
- `tests/test_fallback_behavior_gate.py`
- `tests/test_fallback_behavior_repairs.py`
- `tests/test_fallback_behavior_validator.py`
- `tests/helpers/fallback_behavior_fixtures.py`

**Co-occurrence evidence:**  
`test_fallback_behavior_gate` + `test_fallback_behavior_repairs`: **8** shared commits. Cycle E ("Test Signal Ownership Thinning") touched gate + repairs + validator + overwrite containment together.

**Reason they move together:**  
Single policy contract (`fallback_behavior`) is **built for prompts**, **validated** at gate, and **repaired** in `repair_fallback_behavior`. Tests split by layer but assert the same contract shape.

**Estimated FTPF:** **4–6 files** (1 policy + 2 gate stack + 2–3 tests)

---

## Cluster 4 — Diegetic Content & Template Taxonomy

**Files involved:**
- `game/diegetic_fallback_narration.py`
- `game/final_emission_text.py`
- `tests/test_diegetic_fallback_narration.py`
- `tests/test_diegetic_fallback_block4.py`
- Often adjacent: `game/final_emission_visibility_fallback.py`

**Co-occurrence evidence:**  
`diegetic_fallback_narration.py` appears in cycles AB, D, and narrative hardening commits with `replay_projection` and `sealed_fallback`. `test_diegetic_fallback_narration`: **7** fallback-commit touches.

**Reason they move together:**  
`fallback_template_metadata` drives `fallback_family_used` on FEM; visibility and sealed selectors tag `fallback_kind` from diegetic IDs. Template additions require taxonomy tests + visibility/sealed meta assertions.

**Estimated FTPF:** **3–5 files**

---

## Cluster 5 — Golden Replay Projection & Protected Manifest

**Files involved:**
- `tests/helpers/golden_replay_projection.py`
- `tests/test_golden_replay_fallback_projection.py`
- `tests/test_golden_replay_projection.py`
- `tests/test_golden_replay.py`
- `tests/failure_classification_contract.py`
- `tools/refresh_protected_replay_manifest.py`

**Co-occurrence evidence:**  
Cycles AU, BB, BC, BD, BL all touched `golden_replay_projection.py`. BD also pulled `opening_fallback_evidence` and multiple fallback tests.

**Reason they move together:**  
`PROTECTED_OBSERVATION_FIELDS` is the CI authority; adding/changing observed fallback keys requires projection helper + golden tests + classifier allowlist + manifest refresh.

**Estimated FTPF:** **4–7 files**

---

## Cluster 6 — Upstream Fast Fallback & Provenance

**Files involved:**
- `game/api.py`
- `game/gm_retry.py`
- `game/fallback_provenance_debug.py`
- `game/final_emission_meta.py` (trace key)
- `tests/test_upstream_fast_fallback_block_l.py`
- `tests/test_fallback_overwrite_containment.py`

**Co-occurrence evidence:**  
`test_fallback_overwrite_containment` + `test_upstream_fast_fallback_block_l`: **4** shared commits. Cycle AP touched `fallback_provenance_debug` + `replay_projection` + fast-fallback tests.

**Reason they move together:**  
Fast fallback spans API selection, gm_retry content, provenance fingerprinting, and FEM trace packaging. Containment tests lock overwrite behavior across the path.

**Estimated FTPF:** **4–6 files**

---

## Cluster 7 — Runtime Lineage vs Acceptance (AO5 boundary)

**Files involved:**
- `game/final_emission_replay_projection.py`
- `tests/helpers/golden_replay_projection.py`
- `tests/test_final_emission_meta.py`
- `tests/test_runtime_lineage_telemetry.py`

**Co-occurrence evidence:**  
Cycles AO, AE, AB, AJ modified both projection modules in the same commits. Cycle BL ("Replay Projection Simplification") touched only `golden_replay_projection.py` — sign of **partial decoupling success**.

**Reason they move together:**  
Split-owner fields (`fallback_selection_owner`, `fallback_content_owner`) must align between runtime lineage events and acceptance observation docs. Golden replay **consumes** lineage builder but owns observed field precedence separately.

**Estimated FTPF:** **2–4 files** (improving post-BL)

---

## Cluster 8 — Strict Social Emergency Fallback

**Files involved:**
- `game/social_exchange_emission.py`
- `game/final_emission_terminal_pipeline.py`
- `game/output_sanitizer.py`
- `tests/test_strict_social_emergency_fallback_dialogue.py`
- `tests/test_social_fallback_leak_containment.py`

**Reason they move together:**  
Strict-social content owner is `social_exchange_emission`, but visibility routing and sanitizer also select `minimal_social_emergency_fallback_line`. Leak-containment tests observe repair-layer interactions.

**Estimated FTPF:** **3–5 files**

---

## Cluster 9 — Fallback Behavior Shipped Contract Propagation

**Files involved:**
- `game/fallback_behavior.py`
- `game/response_policy_contracts.py`
- `game/prompt_context.py`
- `tests/test_fallback_shipped_contract_propagation.py`
- `tests/test_prompt_context.py`

**Reason they move together:**  
Prompt bundle must ship the same contract shape validators/repairs consume downstream.

**Estimated FTPF:** **3–4 files**

---

## Largest touch cascade (summary)

| Rank | Cluster | Typical FTPF | Primary seam |
|------|---------|--------------|--------------|
| 1 | Opening authorship & metadata | 7–11 | Stamping + projection + replay protection |
| 2 | Gate visibility family | 6–9 | Triplicated selection tests + shared `VisibilitySelectedFallback` |
| 3 | Golden replay projection | 4–7 | Protected manifest |
| 4 | Fast fallback provenance | 4–6 | API/retry/provenance debug |
| 5 | Fallback behavior policy | 4–6 | Contract/repair/validator |

---

## Cascade heatmap (commit co-touch)

```
test_opening_fallback ──┬── test_sealed_fallback (7)
                        ├── test_visibility_fallback (7)
                        └── opening_fallback_evidence (4–5)

test_fallback_behavior_gate ──┬── test_fallback_behavior_repairs (8)
                              └── test_fallback_behavior_validator (4)

game_sealed_fallback ──────── game_visibility_fallback (4)
```

---

## Implications for BK compression

- **Highest FTPF reduction potential:** Clusters 1 and 2 (visibility/opening/sealed + authorship metadata).
- **Already improving:** Cluster 7 (BL decoupled golden projection from runtime lineage churn).
- **Low priority:** Cluster 3 (`fallback_behavior` policy) — already relatively tight at 4–6 files.
