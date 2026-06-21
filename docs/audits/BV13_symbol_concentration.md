# BV13 — Symbol Concentration Analysis

**Date:** 2026-06-21
**Method:** Per-symbol AST importer scan (`artifacts/bv13_final_emission_text_analysis.json`)

---

## Executive answer

Module FI **52** is almost entirely **`_normalize_text` concentration (FI 47, 90%)**. The module bundles four unrelated concerns: whitespace normalization, HTML sanitize, validator regex policy, and retired semantic-repair helpers. This is **utility sprawl**, not a single authority surface.

## Symbol fan-in (ranked)

| Rank | Symbol | FI | Category | Authority class |
| --- | --- | --- | --- | --- |
| 1 | `_normalize_text` | **47** | formatting | formatting-helper |
| 2 | `_normalize_terminal_punctuation` | **4** | formatting | formatting-helper |
| 3 | `_ACTION_RESULT_PATTERNS` | **3** | policy | policy-constant |
| 4 | `_ANSWER_DIRECT_PATTERNS` | **3** | policy | policy-constant |
| 5 | `_normalize_text_preserve_paragraphs` | **3** | formatting | formatting-helper |
| 6 | `_global_narrative_fallback_stock_line` | **3** | orchestration | convenience-wrapper |
| 7 | `_sanitize_output_text` | **2** | formatting | formatting-helper |
| 8 | `_ANSWER_FILLER_PATTERNS` | **2** | policy | policy-constant |
| 9 | `_RESPONSE_TYPE_VALUES` | **2** | policy | policy-constant |
| 10 | `_ACTION_STOPWORDS` | **1** | policy | policy-constant |
| 11 | `_AGENCY_SUBSTITUTE_PATTERNS` | **1** | other | policy-constant |
| 12 | `_capitalize_sentence_fragment` | **1** | formatting | formatting-helper |
| 13 | `_decompress_overpacked_sentences` | **1** | legacy-repair | accidental-bridge |
| 14 | `_repair_fragmentary_participial_splits` | **1** | legacy-repair | accidental-bridge |
| 16 | `emission_text` | **1** | other | projection-helper |

## Classification buckets

| Category | Symbols | Combined FI | Role |
| --- | --- | --- | --- |
| **Formatting** | `_normalize_text`, `_normalize_text_preserve_paragraphs`, `_sanitize_output_text`, `_normalize_terminal_punctuation`, `_capitalize_sentence_fragment` | **56** (module-level; `_normalize_text` shared) | Whitespace/HTML/punctuation primitives |
| **Policy constants** | `_RESPONSE_TYPE_VALUES`, `_ANSWER_*`, `_ACTION_*`, `_AGENCY_*` | **13** (unique importers ~6) | Validator / contract regex vocabulary |
| **Orchestration wrapper** | `_global_narrative_fallback_stock_line` | **3** | Diegetic fallback delegate + stock line |
| **Legacy semantic repair** | `_decompress_overpacked_sentences`, `_repair_fragmentary_participial_splits` (+ 6 internal helpers, **0 production importers**) | **1** (tests only) | Retired C2 boundary repair — docstring says not invoked in production |

## Read-only vs mutating

| Export kind | Count | Notes |
| --- | --- | --- |
| Read-only pure functions | 14 | All formatting + legacy repair helpers |
| Read-only constants | 6 | Pattern tuples + `_RESPONSE_TYPE_VALUES` |
| Orchestration (calls diegetic) | 1 | `_global_narrative_fallback_stock_line` |

## Highest fan-in exports (maintenance risk)

| Rank | Symbol | FI | Risk |
| --- | --- | --- | --- |
| 1 | `_normalize_text` | 47 | **Critical** — cross-cuts gate, finalize, social, fallback |
| 2 | `_normalize_terminal_punctuation` | 4 | Low — repairs + authenticity only |
| 3 | `_ACTION_RESULT_PATTERNS` / `_ANSWER_DIRECT_PATTERNS` / `_normalize_text_preserve_paragraphs` / `_global_narrative_fallback_stock_line` | 3 each | Medium — policy/fallback coupling |
| 4 | `_sanitize_output_text` / `_ANSWER_FILLER_PATTERNS` / `_RESPONSE_TYPE_VALUES` | 2 each | Low-medium |
