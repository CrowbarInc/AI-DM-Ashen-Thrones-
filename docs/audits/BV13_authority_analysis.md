# BV13 — Authority vs Utility Analysis

**Date:** 2026-06-21

---

## Module self-description vs reality

Docstring claims: *"Shared text utilities … No policy orchestration."*

Actual contents span **formatting**, **validator policy constants**, **fallback content wrapper**, and **legacy semantic repair** (test-only). Only the formatting subset matches the stated role.

## Export classification

| Export | Class | Verdict |
| --- | --- | --- |
| `_normalize_text` | formatting-helper | **Canonical primitive** — should live in dedicated formatting module |
| `_normalize_text_preserve_paragraphs` | formatting-helper | Canonical primitive (strict-social / NA paragraph seams) |
| `_sanitize_output_text` | formatting-helper | Canonical primitive (finalize + provenance debug) |
| `_normalize_terminal_punctuation`, `_capitalize_sentence_fragment`, `_has_terminal_punctuation` | formatting-helper | Formatting sub-primitives |
| `_RESPONSE_TYPE_VALUES` | policy-constant | **Misplaced authority** — belongs with `response_policy_contracts` or validator policy module |
| `_ANSWER_*`, `_ACTION_*`, `_AGENCY_*` pattern tuples | policy-constant | **Misplaced authority** — validator vocabulary; currently split across `final_emission_validators` consumers |
| `_global_narrative_fallback_stock_line` | convenience-wrapper | Accidental bridge to `diegetic_fallback_narration` — content authority is diegetic, not text utils |
| `_decompress_overpacked_sentences`, `_repair_fragmentary_participial_splits` (+ helpers) | accidental-bridge | **Retired production path** — C2 packaging-only boundary explicitly excludes these; test-only retention |

## Canonical authority determination

| Question | Answer |
| --- | --- |
| Is `final_emission_text` a legitimate authority module? | **No** — it is a **mixed utility hub** with no write ownership or orchestration role |
| What is actually authoritative here? | Nothing. All exports are pure functions/constants consumed by gate, validators, and finalize layers |
| Closest legitimate owners | Formatting → new `final_emission_text_formatting`; policy tuples → `final_emission_validators` or `response_policy_contracts`; stock line → `diegetic_fallback_narration` facade |

## Projection helpers vs accidental bridges

| Pattern | Examples | Assessment |
| --- | --- | --- |
| Projection helpers | `_normalize_text` used for comparison/hashing in tests | Legitimate **if** owned by formatting module |
| Convenience wrappers | `_global_narrative_fallback_stock_line` | Thin delegate — creates cross-domain fallback coupling |
| Accidental bridges | Legacy participial repair suite in same module as normalize | Violates C2 boundary; increases perceived hub authority |

## BU1 alignment

BU1 stack contract marked `final_emission_text` as **"Keep (shared primitive)"** for normalize only. BV13 confirms that verdict for **`_normalize_text`** but rejects keeping policy + legacy repair in the same module.
