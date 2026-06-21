# BV17 — Remaining Candidate Rankings

**Date:** 2026-06-21  
**Trigger:** Post-BV16C contraction reassessment  

---

## Top remaining opportunities (ranked by ROI)

### 1. BV18A — Visibility fallback test-coupling governance (optional)

- **Target:** `game.final_emission_visibility_fallback`
- **Projected FI reduction:** 8–14 (test seam migration; production FI stable)
- **Implementation effort:** medium
- **Replay risk:** medium-high
- **Maintenance impact:** Reduces #4 module FI (31) if test hooks mirror BV16 terminal pattern
- **Actionability:** marginal — authority is legitimate; only test inflation is addressable
- **Evidence:** FI 31/FO 20; grew +14 since BV11

### 2. BV18B — Strict/non-strict stack fan-out thinning (defer)

- **Target:** `game.final_emission_strict_social_stack + non_strict_stack`
- **Projected FI reduction:** 5–10 (orchestration import narrowing)
- **Implementation effort:** high
- **Replay risk:** high
- **Maintenance impact:** FO 24/19 routing hubs — BJ-created legitimate authorities
- **Actionability:** low — would invert acyclic gate→stack→terminal boundary
- **Evidence:** strict FI 22/FO 24

### 3. BV18C — Ownership registry fan-out split (defer)

- **Target:** `tests.test_ownership_registry`
- **Projected FI reduction:** 0 FI (FO 57 governance router)
- **Implementation effort:** high
- **Replay risk:** low
- **Maintenance impact:** Meta-governance hub — splitting risks guard fragmentation
- **Actionability:** low — intentional concentration with high operability return
- **Evidence:** FO 57 unchanged; collects BV12C–BV16C guards

### 4. BV18D — Smoke/text/social domain hub further split (not recommended)

- **Target:** `replay_fem + gate_orch + text_formatting`
- **Projected FI reduction:** 15–25 (would recreate accidental hubs)
- **Implementation effort:** high
- **Replay risk:** medium
- **Maintenance impact:** Negative ROI — BV12–BV14 just established governed domain hubs
- **Actionability:** none — regrowth blocked by import guards
- **Evidence:** Domain cluster FI 99+59

### 5. BV18E — Residual RC observe fallback elimination

- **Target:** `referential_clarity_hard_replacement (1 event / 1.05%)`
- **Projected FI reduction:** 1 incidence event (not FI)
- **Implementation effort:** medium
- **Replay risk:** medium
- **Maintenance impact:** Clears last measurable fallback; diminishing structural returns
- **Actionability:** marginal — not a hotspot driver
- **Evidence:** BV1B 1 event unchanged

## Priority ordering

| Rank | Cycle | Projected FI ↓ | Replay risk | Actionability | Rationale |
| --- | --- | --- | --- | --- | --- |
| 1 | BV18A | 8–14 | medium-high | marginal | Optional visibility test seam cleanup |
| 2 | BV18E | 1 event | medium | marginal | Last fallback event — not structural |
| 3 | BV18B | 5–10 | high | low | Stack FO thinning — defer |
| 4 | BV18C | 0 | low | low | Registry split — defer |
| 5 | BV18D | negative ROI | medium | none | Do not split governed domain hubs |

## Recommendation: **REPOSITORY_CONTRACTION_COMPLETE**

Post BV12–BV16C, the top-25 concentration is dominated by governed domain authorities (smoke 99 FI, text 59 FI, social 82 FI, gate/terminal 41 FI) and legitimate production authorities. Accidental compat shim FI totals 18 (text 4 + social 12 + smoke 2). No module exceeds 8% ecosystem fan-in share. Remaining optional work (visibility test seams, 1 fallback event) is marginal ROI.
