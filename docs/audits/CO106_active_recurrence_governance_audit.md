# CO106 — Active Recurrence Governance Audit

**Date:** 2026-06-28  
**Scope:** Governance classification and graduation convergence analysis only. No taxonomy, scoring, propagation, or registry changes.

**Prior cycles:** CO104–CO105 validated retirement propagation; 2 keys retired, 5 active.

---

## Executive summary

Every remaining active protected recurrence key is **governance-classified** using existing audit documentation. **Zero keys** qualify as future retirement candidates under current evidence — the five active keys are **intentionally permanent** (design records, corpus duplicates, operational sentinel). No unresolved engineering work remains.

**Calibration ceiling:** With documented retirements complete, further calibration gains require **operational evidence accumulation** (live cycles, trajectory time, optional hygiene), not additional retirement propagation on existing keys.

**Verdict:** Governance intent is **resolved**. Graduation blockers are **operational**, not architectural or ambiguous.

---

## 1. Active key governance audit

### Classification legend (CO106)

| Category | Meaning |
|---|---|
| **Future retirement candidate** | Documented engineering fix exists; retirement registry could be created; propagation eligible when registry exists |
| **Intentional permanent design decision** | Observation reflects locked architecture; key should remain active as design record |
| **Duplicate historical observation** | Corpus or inflation row; preserved evidence without live defect signal |
| **Operational sentinel** | Instrumentation or pipeline-validation artifact; preserved for operational audit trail |
| **Unresolved engineering work** | Pending fix or unknown disposition |

---

### Key-by-key audit (5 active keys)

| # | Recurrence key (abbrev.) | Events | Scenarios | Governance category | Supporting documentation |
|---|---|---:|---|---|---|
| A | `speaker\|selected_speaker_id\|speaker_contract_enforcement.py` | 2 | `wrong_speaker_strict_social_emission`, `bx5_guard_ambiguous_multi_guard` | **Intentional permanent design decision** | [CO103 lifecycle inventory](CO103_outcome_lifecycle_inventory.md) — ambiguous multi-guard parity by design; [BX closeout](closeouts/BX_speaker_identity_end_to_end_parity_closeout.md) — locked `None`/resolved expectations |
| B | `speaker\|selected_speaker_source\|speaker_contract_enforcement.py` | 2 | `bx5_guard_ambiguous_multi_guard` | **Intentional permanent design decision** | CO103 — `selected_speaker_source=None` by design; BX closeout ambiguous guard contract |
| C | `fallback\|final_emitted_source\|final_emission_gate.py` | 1 | `directed_npc_question` | **Duplicate historical observation** | CO103 — corpus backfill row; scenario test passes; [BV8A registry](BV8A_retirement_registry.md) ACTIVE (emerging, monitor) |
| D | `sanitizer\|scaffold_leakage\|output_sanitizer.py` | 1 | `sanitizer_scaffold_leakage` | **Duplicate historical observation** | CO103 — corpus expansion row; scenario test passes; BV8A registry ACTIVE |
| E | `projection\|fallback_family\|golden_replay.py` | 1 | `wrong_speaker_strict_social_emission` | **Operational sentinel** | CO103 — rejected report; [CO102](CO102_live_recurrence_validation_report.md) — pipeline validation artifact, not production defect |

### Machine-readable history alignment

| Key | `lifecycle_stage` | `governance_status` | Consistent with audit? |
|---|---|---|---|
| A — speaker `selected_speaker_id` | recurring | investigate | **Yes** — live BX + corpus mix; recurring reflects 2 events |
| B — speaker `selected_speaker_source` | recurring | investigate | **Yes** |
| C — fallback `final_emitted_source` | emerging | watch | **Yes** — single corpus observation |
| D — sanitizer `scaffold_leakage` | emerging | watch | **Yes** |
| E — fallback `fallback_family` | emerging | watch | **Yes** — single CO102 validation event |

No internal inconsistencies between protected history analytics and documented governance intent.

---

## 2. Retirement eligibility matrix

**No propagation performed in CO106.** Readiness documented only.

| Key | Future retirement candidate? | Required engineering evidence | Required retirement registry | Required validation gate | Current blocking condition |
|---|---|---|---|---|---|
| A — speaker `selected_speaker_id` | **No** | N/A — design decision, not defect | N/A | N/A | **Permanent by design** — BX ambiguous guard contract |
| B — speaker `selected_speaker_source` | **No** | N/A | N/A | N/A | **Permanent by design** |
| C — fallback `final_emitted_source` | **No** (not without new registry) | None documented — duplicate only | Would require explicit duplicate-retirement registry entry | Scenario test pass gate | **No engineering disposition for retirement** — duplicate classification only |
| D — sanitizer `scaffold_leakage` | **No** (not without new registry) | None documented | Same | Scenario test pass gate | Same |
| E — fallback `fallback_family` | **No** | None — rejected false positive | N/A — retraction ≠ defect retirement | CO102 structural test pass | **Operational sentinel** — retraction is optional hygiene, not retirement |

### Summary

| Eligibility status | Count |
|---|---:|
| Future retirement candidates (documented, registry-ready) | **0** |
| Permanent operational records | **5** |
| Unresolved engineering work | **0** |

All eligible engineering retirements (BV8A projection, BX emission) were **already propagated** in CO104–CO105.

---

## 3. Permanent active-key inventory

Keys that **should remain excluded** from retirement propagation:

| Key | Permanent rationale | Exclude from propagation? |
|---|---|---|
| A — speaker `selected_speaker_id` | Documents BX ambiguous/resolved guard parity expectations locked in closeout; active status preserves design record for governance investigate tier | **Yes — permanent** |
| B — speaker `selected_speaker_source` | Documents ambiguous multi-guard `None` source contract | **Yes — permanent** |
| C — fallback `final_emitted_source` | Preserved corpus observation for controlled classification mapping audit trail; no live defect | **Yes — duplicate evidence** |
| D — sanitizer `scaffold_leakage` | Same — corpus baseline row preserved | **Yes — duplicate evidence** |
| E — fallback `fallback_family` | CO102 live pipeline validation sentinel; proves observation pipeline works; not a defect signal | **Yes — operational sentinel** |

**Governance maintenance note:** BV8A registry lists keys C and D as ACTIVE "monitor before retirement." CO106 audit **supersedes monitor intent** for these keys: CO103 duplicate disposition + passing scenario tests establish them as **preserved historical observations**, not pre-retirement watch items. No registry modification performed (audit classification only).

---

## 4. Calibration ceiling assessment

Analysis uses existing formulas only (`calculate_effectiveness_evidence_strength`, `calculate_confidence_calibration_score`). No methodology changes.

### Current state (post-CO105, snapshot #16)

| Metric | Value |
|---|---:|
| Total keys | 7 |
| Retired keys | 2 |
| Active keys | 5 |
| `validated_outcome_count` | 5 |
| `validated_closure_rate` | 0.2857 (2/7) |
| Outcome evidence strength | 0.60 |
| Calibration score | 66.3 |
| Largest calibration gap | 0.40 |
| `graduation_confidence_ready` | false |

### Outcome evidence strength formula (unchanged)

```
0.20 × trajectory_factor + 0.40 × (validated_outcome_count / total_keys)
  + 0.40 × max(validated_closure_rate, validated_reduction_rate, validated_remediation_rate)
```

With trajectory active (`trajectory_factor = 1.0`) and current validated signals:

```
0.20 + 0.40 × (5/7) + 0.40 × 0.2857 ≈ 0.60 ✓
```

### Theoretical ceilings

| Scenario | Retired keys | Closure rate | Approx. outcome strength | Notes |
|---|---:|---:|---:|---|
| **Current governance intent** (2 retired, 5 permanent active) | 2 | 0.286 | **~0.60** | **At ceiling** for documented retirements |
| Hygiene: retract CO102 sentinel (`deprecated`) | 3 | 0.429 | ~0.66 | Optional; modest gain; not defect retirement |
| Hypothetical: retire all 7 keys | 7 | 1.000 | ~1.00 | **Violates governance intent** — not actionable |
| New live cycle: add + retire 1 new key (8 total, 3 retired) | 3 | 0.375 | ~0.65+ | Requires future operational failure→fix→retire |

### Calibration score ceiling (under permanent 5-key inventory)

| Dimension | Reported confidence | Evidence strength | Gap | Status |
|---|---:|---:|---:|---|
| Forecast | 1.00 | ~1.00 | ~0.00 | calibrated |
| Governance | 1.00 | ~0.54 | ~0.46 | overconfident |
| Effectiveness | 1.00 | 0.60 | 0.40 | overconfident (largest gap) |

**Largest gap** is effectiveness-driven. With closure rate capped at 2/7 under permanent active keys, **calibration score cannot reach 70.0 and gap cannot reach ≤ 0.20** through additional retirement propagation on existing keys alone.

**Evidence that must come from future operations (not engineering on existing keys):**

1. **Live protected replay failure → fix → retire cycles** on **new** recurrence keys (expands validated outcome portfolio).
2. **Long-term trajectory stability** — governance health convergence via sustained operational history (currently 45.9 vs 80.0 target).
3. **Optional hygiene** — retract CO102 sentinel to reduce active-key noise (modest calibration lift, not graduation-sufficient alone).

---

## 5. Graduation artifact refresh

Regenerated via existing tooling (no propagation):

```bash
python tools/capture_recurrence_trajectory_activation.py --generated-at 2026-06-28T18:00:00Z
```

| Artifact | Regenerated | Key values |
|---|---|---|
| `BQ16_recurrence_graduation_audit.md` | Yes | Readiness 94.7; CO99 preamble preserved |
| `BQC4_final_graduation_decision.md` | Yes | Recommendation B; calibration 66.3; gap 0.40 |
| `BQC5_effectiveness_validation.md` | Yes | 2 retired keys; 5 validated outcomes; strength 0.60 |
| `bug_recurrence_history.json` | Yes | Internally consistent with event log |
| Trajectory snapshot | #16 appended | `trajectory_available: true` |

Governance classifications in this audit **align** with regenerated history — no contradictions detected.

---

## 6. Graduation convergence assessment

### Remaining retirement opportunities

| Opportunity | Actionable? | Rationale |
|---|---|---|
| Propagate retirements on 5 active keys | **No** | All classified permanent; no documented engineering retirements |
| Create new retirement registries for corpus keys | **No in CO106** | Would require new registry docs — outside audit scope; duplicate disposition does not establish engineering fix |
| BV8A/BX-class additional fixes | **None known** | CO103: zero unresolved investigations |

### Permanent active inventory

**5 keys** — see §3. These represent **resolved governance intent**, not graduation blockers.

### Remaining operational evidence requirements

| Requirement | Type | Target |
|---|---|---|
| Effectiveness evidence strength | Operational | ≥ ~0.80 (implicit for confidence ready) |
| Largest calibration gap | Operational | ≤ 0.20 |
| Calibration score | Operational | ≥ 70.0 |
| Governance health | Operational + time | ≥ 80.0 |
| Live failure→fix→retire cycles | Operational | ≥ 1 additional independent cycle recommended in CO105 |

### Estimated path to graduation

| Stage | Work type | Expected impact |
|---|---|---|
| **CO107** | Operational monitoring + optional CO102 sentinel hygiene | Modest calibration lift |
| **CO108+** | Live protected replay cycles with documented fix + retirement on **new** keys | Closure rate and outcome strength increase |
| **Sustained operations** | Trajectory snapshots over time | Governance health toward 80.0 |
| **Graduation evaluation** | Regenerate BQC4 when `graduation_confidence_ready` true | Potential B → A |

### Engineering-driven vs operational

| Category | Status |
|---|---|
| **Engineering-driven work remaining** | **None** for existing 7-key inventory |
| **Operational evidence accumulation** | **Primary graduation path** |
| **Governance maintenance** | Classifications locked in this audit; no recurring ambiguity |

---

## 7. Recommended CO107 target

**CO107 — Operational Evidence Accumulation & Graduation Convergence Monitoring**

Operational cycle to:

1. **Monitor** calibration metrics across ≥ 2 additional trajectory snapshots without modifying formulas or thresholds.
2. **Execute** one live protected replay failure→fix→retire cycle on a **new** recurrence key (independent of the 7-key inventory).
3. **Optionally retract** the CO102 `fallback_family` sentinel via existing propagation semantics (`deprecated` status) if hygiene is prioritized — document only if executed.
4. **Re-evaluate** BQC4 recommendation when `graduation_confidence_ready` transitions; expect graduation only when operational evidence closes the 0.40 effectiveness gap.

Distinguishes **completed governance classification** (CO106) from **ongoing operational evidence work** (CO107+).

---

## Cross-references

- CO105 multi-key validation: [`CO105_multi_key_retirement_validation_report.md`](CO105_multi_key_retirement_validation_report.md)
- CO103 lifecycle inventory: [`CO103_outcome_lifecycle_inventory.md`](CO103_outcome_lifecycle_inventory.md)
- CO103 correlation: [`CO103_observation_outcome_correlation.md`](CO103_observation_outcome_correlation.md)
- BX closeout: [`closeouts/BX_speaker_identity_end_to_end_parity_closeout.md`](closeouts/BX_speaker_identity_end_to_end_parity_closeout.md)
- BV8A registry: [`BV8A_retirement_registry.md`](BV8A_retirement_registry.md)
- Graduation audit: [`BQ16_recurrence_graduation_audit.md`](BQ16_recurrence_graduation_audit.md)
- Final decision: [`BQC4_final_graduation_decision.md`](BQC4_final_graduation_decision.md)
- Effectiveness validation: [`BQC5_effectiveness_validation.md`](BQC5_effectiveness_validation.md)
