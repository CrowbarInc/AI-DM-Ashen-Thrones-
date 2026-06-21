# BV4B — Concrete Beat Report

**Date:** 2026-06-21  
**Goal:** Satisfy `passive_scene_pressure_missing_concrete_beat` upstream before sealed PSP fallback.  
**Authority:** `artifacts/bv4b_concrete_beat_metrics.json`, post-refresh replay corpus.

---

## Implementation summary

| Task | ID | Status |
|---|---|---|
| Concrete beat contract | — | `docs/audits/BV4B_concrete_beat_contract.md` |
| Upstream validation / satisfier | EC-4A-01 | Gate + terminal hooks |
| Deterministic beat injection | EC-4A-02 | `_select_deterministic_upstream_concrete_beat` |
| FEM meta preservation | — | `run_generic_accept_exit` snapshot/restore |
| Visibility skip guards | — | PSP sealed replace bypass when contract satisfied |
| Instrumentation | — | Satisfier meta fields on observe FEM |

**Primary code paths:**

- `game/final_emission_passive_scene_pressure.py` — contract detection, injection, meta
- `game/final_emission_gate.py` — pre-stack satisfier
- `game/final_emission_terminal_pipeline.py` — post-RC satisfier
- `game/final_emission_generic_exit.py` — FEM meta preservation on accept
- `game/final_emission_visibility_fallback.py` — skip sealed replace when upstream satisfied

---

## Commands executed

```bash
python -m pytest tests/test_bv4b_concrete_beat_upstream_satisfier.py -q
python -m pytest tests/test_golden_replay_direct_seam.py tests/test_golden_replay_projection.py \
  tests/test_golden_replay_fallback_projection.py tests/test_speaker_contract_enforcement.py \
  tests/test_final_emission_visibility.py tests/test_final_emission_visibility_fallback.py \
  tests/test_final_emission_sealed_fallback.py tests/test_fallback_overwrite_containment.py \
  tests/test_bv3a_observe_referential_clarity_repair.py -q
python tools/bv3f_replay_corpus_refresh.py
python tools/bv4b_concrete_beat_metrics.py
```

All listed test suites passed after the visibility import fix.

---

## Comparison table

| Metric | BV3F Baseline | Current | Delta |
|---|---:|---:|---:|
| **PSP events** (`sealed_passive_scene_pressure_fallback`) | 10 | **0** | **−10** |
| **Observe route rate** | 47.83% | **4.35%** | **−43.48 pp** |
| **Fallback incidence** | 11.58% | **1.05%** | **−10.53 pp** |

Baseline source: `artifacts/bv3f_reduction_metrics.json`  
Current measurement: BV3D-filtered FEM scan post refresh (`artifacts/bv3f_replay_refresh/`)

---

## Satisfier instrumentation (observe route)

| Field | Count |
|---|---:|
| Observe turns | 23 |
| Satisfier attempted | 21 |
| Satisfier applied | 10 |
| Fallback avoided | 10 |
| Beat type: `generic_interruption` | 10 |

Applied count matches the pre-BV4B PSP cluster size (10/10). Remaining observe fallbacks (1 turn) are attributable to the residual RC hard-replacement family unchanged from BV3F.

---

## Verification outcomes

| Suite | Result |
|---|---|
| BV4B unit + gate integration | Pass (4/4) |
| Golden replay (direct seam, projection, fallback projection) | Pass |
| Speaker contract | Pass |
| Visibility + visibility fallback | Pass |
| Sealed fallback + overwrite containment | Pass |
| BV3A observe RC repair (no regression) | Pass |
| Replay corpus refresh | Pass — no divergence |

**Constraints held:**

- No replay divergence (golden replay suites green post refresh)
- No speaker-finalize regression (speaker contract suites green)
- No ownership relocation (PSP candidate pool unchanged; satisfier consumes same builders)

---

## Classification

### **EFFECTIVE_REDUCTION**

Criteria met:

- PSP count reduced by ≥8 with satisfier applied on ≥8 eligible turns (**−10 / 10 applied**)
- Reduction occurs through upstream contract satisfaction, not ownership relocation
- Sealed PSP fallback eliminated on refreshed replay corpus (10 → 0)

---

## Residual risk

| Risk | Mitigation |
|---|---|
| Injected beat triggers RC ambiguity (e.g. pronoun in dialogue) | Visibility/RC skip when `passive_scene_concrete_beat_satisfier_preserves_upstream` |
| FEM rebuild wipes satisfier meta | Snapshot/restore in `run_generic_accept_exit` |
| GM-provided concrete beat double-stamped | Satisfier skips injection when contract already satisfied |

---

## Related artifacts

| Path | Role |
|---|---|
| `artifacts/bv4b_concrete_beat_metrics.json` | Canonical BV4B metrics |
| `docs/audits/BV4B_concrete_beat_contract.md` | Beat contract specification |
| `docs/audits/BV4A_passive_scene_inventory.md` | Pre-change PSP inventory |
| `tests/test_bv4b_concrete_beat_upstream_satisfier.py` | Regression tests |
