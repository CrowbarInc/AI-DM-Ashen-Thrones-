# BV13C — Hub Reclassification

**Date:** 2026-06-21  

---

## Does `final_emission_text` remain a maintenance hub?

**No.** Post-BV13C it is a **compat shim** (FI 4, cap ≤8) owning only `_global_narrative_fallback_stock_line` plus re-exports for delegate verification. It is not an edit choke for normalize or policy tuples.

## Is formatting concentration legitimate?

**Yes.** `final_emission_text_formatting` FI 51 reflects **intentional primitive ownership** after BV13B consumer migration. Single-category exports (normalize, sanitize, terminal punctuation) with no policy co-location.

## Is policy concentration controlled?

**Yes.** `final_emission_text_policy` FI 8 is bounded to validator vocabulary tuples and `_RESPONSE_TYPE_VALUES`. Importers are validators, contracts, and composition layers — not a regrown compat barrel.

| Module | FI | Hub type | Verdict |
| --- | --- | --- | --- |
| `final_emission_text` | 4 | Compat shim | Not a hub — capped residual |
| `final_emission_text_formatting` | 51 | Formatting primitive hub | Legitimate — production-core |
| `final_emission_text_policy` | 8 | Policy vocabulary hub | Controlled — narrow tuple surface |

## Accidental hub creation?

**No.** BV13A extracted three authorities; BV13B migrated ~47 consumer symbol imports; BV13C locks compat regrowth. Net module fan-in conserved across named surfaces, not re-concentrated on the compat barrel.

