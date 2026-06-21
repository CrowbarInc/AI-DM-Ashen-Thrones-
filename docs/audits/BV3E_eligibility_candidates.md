# BV3E — Eligibility Expansion Candidates

**Date:** 2026-06-21  
**Method:** Live re-validation of frozen FEM shapes against `seed_frontier_gate_world` + BV3E eligibility predicates  
**Machine-readable:** `artifacts/bv3e_shape_simulation.json`

---

## Classification summary

| Risk | Candidates | BV3E action |
|---|---:|---|
| **Low** | 11 | **Implemented** |
| **Medium** | 4 | Documented only |
| **High** | 30+ | Rejected |

---

## Low risk — implemented

### EC-L01 — Multi-violation alias introducer (MV-01)

| Field | Value |
|---|---|
| **Current eligibility** | false (BV3A) |
| **Expanded eligibility** | true (BV3E) |
| **Expansion rule** | `_violations_eligible_for_bv3e_exact_alias_introducer_repair` |
| **Repair** | Replace role alias at violation offset when: (1) singular indefinite introducer precedes token, (2) multi-entity candidates disambiguate via exact-alias + title exclusion, (3) single token occurrence (or offset-targeted match), (4) post-repair re-validation passes |
| **Turns** | 11 gate-interruption observe turns |
| **Ownership impact** | None — no speaker/replay/ownership contract changes |

---

## Medium risk — not implemented

### EC-M01 — Isolated dialogue `he` + multi-person (archive shape)

| Field | Value |
|---|---|
| **Shape** | `"…," he says` without named antecedent, 4–5 visible persons |
| **Grounding** | None without interlocutor |
| **Why medium** | Expanding dialogue-attribution grounding without introducer risks wrong speaker selection |
| **Turns** | ~30 archive OBS-001 pattern |
| **Decision** | **Reject** — preserve hard replace |

### EC-M02 — Possessive narrative (`his` primary)

| Field | Value |
|---|---|
| **Shape** | Non-dialogue possessive in multi-clause narration |
| **Why medium** | Single-token substitution can distort narrative voice |
| **Decision** | **Reject** |

### EC-M03 — Bounded referent_drift (`they` dialogue)

| Field | Value |
|---|---|
| **Shape** | `referent_drift` with 2-entity candidate set |
| **Why medium** | Separate validator kind; drift semantics differ from alias introducer |
| **Decision** | **Defer** — not in low-risk set |

### EC-M04 — Multi-violation without introducer alias

| Field | Value |
|---|---|
| **Shape** | Multiple pronoun violations, no disambiguated role noun |
| **Decision** | **Reject** |

---

## High risk — rejected

| Candidate | Reason |
|---|---|
| Relax ownership multi-entity guard | Would guess between gate_guard / guard_captain without introducer signal |
| Repair `his`/`their` in isolation | No safe single-token anchor |
| Multi-sentence pronoun substitution without offset targeting | False positives inside `The`/`when`/`before` |
| Expand to strict-social route | Speaker contract boundary |

---

## Eligibility predicate changes (code)

| Function | Change |
|---|---|
| `_violations_eligible_for_non_strict_local_repair` | Superset of BV3A pronoun eligibility + BV3E alias introducer |
| `_try_bv3e_exact_alias_introducer_substitution_repair` | New repair path before pronoun substitution |
| `apply_observe_referential_clarity_upstream_repair` | Uses expanded eligibility + stamps `referential_clarity_bv3e_repair_mode` |

**Unchanged:** `_violations_eligible_for_non_strict_local_pronoun_repair` (BV3A contract preserved for strict-single-violation path).
