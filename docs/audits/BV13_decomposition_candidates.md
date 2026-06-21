# BV13 — Decomposition Candidates

**Date:** 2026-06-21

---

## Candidate modules

| Candidate | Extract | Est. FI | Consumers | Migration cost | Replay risk |
| --- | --- | --- | --- | --- | --- |
| **`final_emission_text_formatting`** | `_normalize_text`, `_normalize_text_preserve_paragraphs`, `_sanitize_output_text`, `_normalize_terminal_punctuation`, `_capitalize_sentence_fragment`, `_has_terminal_punctuation` | **~47–52** | 39 production + 12 test | **Medium** — mechanical import rewrite across gate trunk | **Low** — pure functions; golden hash stable if behavior preserved |
| **`final_emission_text_policy`** | `_RESPONSE_TYPE_VALUES`, `_ANSWER_*`, `_ACTION_*`, `_AGENCY_*` | **~6** | validators, referential_clarity, answer_shape_primacy, narrative_mode_contract, interaction_continuity, response_policy_contracts | **Low-medium** — 6 modules + validator owner coordination | **Low** — constants only |
| **`final_emission_text_projection`** | (optional) re-export barrel for tests comparing normalized text | **~5–8** | test helpers only | **Low** | **Low** |
| **Retire / isolate legacy repair** | `_decompress_*`, `_repair_*`, participial helpers | **1** | `test_final_emission_visibility` only | **Low** — move to test fixture or `legacy_semantic_repair_archive` | **None** — not on production path |
| **Fallback stock line** | `_global_narrative_fallback_stock_line` | **3** | fast_fallback_composition, scene_emit_integrity, diegetic test | **Low** — colocate with `diegetic_fallback_narration` or `final_emission_fast_fallback_composition` | **Medium** — touches shipped fallback text |

## Not recommended

| Candidate | Reason |
| --- | --- |
| `final_emission_text_views` | No view/projection exports exist — module is function/constants only |
| Full module deletion | Formatting primitive is genuinely shared; deletion would recreate hub elsewhere |

## Projected FI reduction (module-level)

| Stage | `final_emission_text` FI | New module FI |
| --- | --- | --- |
| Current | **52** | — |
| After formatting extract + compat re-export | **52** (unchanged short-term) | formatting **47** |
| After consumer migration (formatting) | **~5–8** | formatting **47** |
| After policy extract | **~2–3** (compat/legacy only) | policy **6**, formatting **47** |
| Steady state (compat retired) | **0–2** | formatting **47**, policy **6** |

**Net maintenance win:** FI **concentration** moves from ambiguous hub to **named primitive owner** (formatting FI ~47 is *legitimate* — same as stdlib `json` pattern for a true shared utility).
