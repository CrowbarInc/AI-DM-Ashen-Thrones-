# CO96 — Attribution Program Closeout & Governance Lock

Closeout date: 2026-06-27  
Scope: documentation and governance only. No production, projection, classifier, baseline, or metric calculation changes.

**Program status: Closed**

Policy authority: `tests/helpers/attribution_contract.py` (`ATTRIBUTION_GOVERNANCE_*` constants).

---

## Cycle Arc (CO83–CO95)

| Phase | Cycles | Outcome |
|---|---|---|
| Read-side convergence | CO83–CO90 | Inventory projection helpers consumed existing FEM/lineage evidence; resolved completeness rose from 5.36% (BS1) toward projection plateau |
| Plateau audit | CO91 | Declared read-side projection plateau at 69.64%; identified remaining gaps as production-intentional |
| Production stamps | CO92–CO93 | Response-type owner bucket (+6 resolved); sealed passive-scene `producer_repair_kind` (+4 resolved) |
| Lineage contract | CO94 | Locked `gate_outcome` as mutation-free; 8 intentional `mutation_classification` gaps accepted |
| Strict policy | CO95 | Strict completeness frozen at 0%; no legitimate strict-direct production targets without duplicating replay semantics |

---

## Final Metrics (BS5 closeout)

| Metric | Value | Role |
|---|---:|---|
| Resolved completeness | **48/56 (85.71%)** | **Primary production KPI** |
| Strict completeness | **0/56 (0.0%)** | Architectural diagnostic only |
| Contract compliance | 100% | Taxonomy validation |
| Taxonomy consistency | 100% | Union alignment |

Field missing totals (resolved layer): `repair_kind` 0, `owner_bucket` 0, `source_family` 0, `recurrence_key` 0, `mutation_classification` 8.

---

## Remaining Intentional Gaps (Architectural Constraints)

These are **not unfinished work**:

| Gap | Records | Constraint |
|---|---:|---|
| `gate_outcome` `mutation_classification` | 8 | Routing events omit `mutation_kind` by lineage contract (CO94); sibling `mutation` events carry classification |
| Strict completeness | 0/56 | Every resolved record includes replay-derived or projection-only fields by design (CO95) |

---

## Production vs Replay Ownership

| Layer | Owns | Does not own |
|---|---|---|
| **Production (FEM write time)** | Producer repair kinds, owner buckets, replacement-applied flags | `source_family`, lineage `recurrence_key`, lineage `mutation_kind` on non-mutation events |
| **Replay projection** | Lineage events, recurrence keys, mutation classification on `mutation` events, fallback_kind → source_family maps | Attribution completeness scoring, strict-direct origin labels |
| **Attribution inventory (read-side)** | Record construction, origin labeling, resolved/strict scoring | Taxonomy authority, production stamps |

**Philosophy:** Production stamps producer decisions. Replay derives observability from finalized FEM. Read-side projection fills gaps only from bounded production evidence — never to inflate metrics.

---

## Why Strict Completeness Remains 0%

Strict completeness requires all five fields with `attribution_origin == direct`. On the baseline corpus:

- **`source_family`** has no FEM stamp surface — always projected except classifier rows.
- **`recurrence_key`** and **`mutation_classification`** are lineage-scoped — FEM-metadata records read them from projected lineage bundles.
- **Classifier-inferred** fields are permanently non-strict regardless of production stamps.

No resolved record has a single-field strict blocker; multi-field replay derivation is the norm. Stamping replay-derived values on FEM solely to raise strict % would violate production/replay separation (CO95 policy).

---

## Governance Rules (Normative)

1. **Resolved completeness is the primary production KPI.**
2. **Strict completeness is an architectural diagnostic only** — not a graduation gate or production-stamp target.
3. **Replay-derived fields are not production-stamp candidates** (`recurrence_key`, lineage `mutation_kind`, `source_family` from fallback maps).
4. **Production stamps must never duplicate replay semantics solely to improve metrics.**
5. **Read-side projection remains bounded by existing production evidence** — no semantic invention (CO91 plateau).

---

## Validation

```text
python -m pytest tests/test_attribution_contract.py -q               PASS
python -m pytest tests/test_attribution_completeness_metric.py -q    PASS
python -m pytest tests/test_replacement_attribution_inventory.py -q  PASS
```

Live corpus reconciles with `BS5_MATURITY_SNAPSHOT` and `BS5_BASELINE_COMPLETENESS`.

---

## Files Modified

| File | Change |
|---|---|
| `docs/audits/CO96_attribution_program_closeout.md` | Added — this closeout document |
| `tests/helpers/attribution_contract.py` | Added CO96 governance policy constants |
| `tests/helpers/attribution_completeness_metric.py` | Governance footnote in BR1 report render |
| `tests/test_attribution_contract.py` | CO96 governance lock tests |

---

## Recommended CO97 Target

**CO97 — CG attribution registry governance sync** — **Completed**

- Registry synchronized: [`CG_attribution_contract_registry.md`](CG_attribution_contract_registry.md)
- CO96 established as governing authority in CG-5 header and governance section

---

## Recommended CO98 Target

**CO98 — Failure classification program handoff review**

- Target: `docs/audits/CG_failure_classification_authority_registry.md`, `docs/audits/BQC4_final_graduation_decision.md`
- Goal: confirm failure-classification graduation status is documented independently of the closed attribution maturity program
- Expected impact: documentation alignment only
