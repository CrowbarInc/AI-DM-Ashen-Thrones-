# BV14 — Symbol Concentration Analysis

**Date:** 2026-06-21
**Method:** Per-symbol AST importer scan (`artifacts/bv14_social_exchange_emission_analysis.json`)

---

## Executive answer

Module FI **52** is **multi-symbol** — unlike BV13's 90% `_normalize_text` choke. Top three symbols (`minimal_social_emergency_fallback_line`, `strict_social_emission_will_apply`, `build_final_strict_social_response`) account for **~29 BU FI** combined. The module bundles **composition**, **fallback**, **eligibility policy**, **telemetry**, and **private-helper leaks**.

## Symbol fan-in (ranked, BU baseline)

| Rank | Symbol | BU FI | AST FI | Category | Authority class |
| --- | --- | --- | --- | --- | --- |
| 1 | `minimal_social_emergency_fallback_line` | **10** | 12 | fallback | fallback-authority |
| 2 | `strict_social_emission_will_apply` | **9** | 10 | policy | policy-vocabulary |
| 3 | `build_final_strict_social_response` | **8** | 8 | composition | canonical-composition-authority |
| 4 | `effective_strict_social_resolution_for_emission` | **7** | 8 | composition | composition-helper |
| 5 | `merged_player_prompt_for_gate` | **7** | 7 | projection | realization-projection |
| 6 | `social_exchange_emission` | **6** | 6 | other | accidental-bridge |
| 7 | `strict_social_ownership_terminal_fallback` | **5** | 5 | fallback | fallback-projection |
| 8 | `is_route_illegal_global_or_sanitizer_fallback_text` | **4** | 5 | validator | validator-projection |
| 9 | `_npc_display_name_for_emission` | **4** | 4 | other | accidental-bridge |
| 10 | `reconcile_strict_social_resolution_speaker` | **4** | 4 | composition | composition-helper |
| 11 | `apply_social_exchange_retry_fallback_gm` | **3** | 4 | composition | composition-helper |
| 12 | `log_final_emission_decision` | **3** | 3 | projection | telemetry-projection |
| 13 | `log_final_emission_trace` | **3** | 3 | projection | telemetry-projection |
| 14 | `apply_strict_social_terminal_dialogue_fallback_if_needed` | **2** | 3 | fallback | fallback-projection |
| 15 | `strict_social_terminal_dialogue_fallback_valid` | **2** | 3 | validator | validator-projection |
| 16 | `_has_explicit_interruption_shape` | **2** | 2 | other | accidental-bridge |
| 17 | `build_open_social_solicitation_recovery` | **2** | 2 | composition | composition-helper |
| 18 | `player_line_triggers_strict_social_emission` | **2** | 2 | policy | eligibility-projection |
| 19 | `project_strict_social_replace_realization_family` | **2** | 2 | projection | realization-projection |
| 20 | `select_strict_social_emergency_fallback_line` | **2** | 2 | fallback | fallback-projection |
| 21 | `should_apply_strict_social_exchange_emission` | **2** | 2 | policy | policy-vocabulary |
| 22 | `stamp_strict_social_deterministic_fallback_family` | **2** | 2 | projection | realization-projection |
| 23 | `strict_social_deterministic_fallback_family_token` | **2** | 2 | projection | realization-projection |
| 24 | `interruption_cue_present_in_text` | **1** | 2 | policy | eligibility-projection |
| 25 | `lawful_strict_social_dialogue_emergency_fallback_line` | **1** | 2 | fallback | fallback-projection |

## Classification buckets

| Category | Symbols (public) | Top symbol FI | Role |
| --- | --- | --- | --- |
| **Composition exports** | 13 | `build_final_strict_social_response` **8** | Strict-social terminal response assembly + ownership filters |
| **Projection exports** | 6 | `merged_player_prompt_for_gate` **7** | FEM/realization family stamping + gate prompt merge + telemetry |
| **Validator exports** | 4 | `is_route_illegal_global_or_sanitizer_fallback_text` **4** | Route legality + sanitizer/global fallback rejection |
| **Fallback exports** | 8 | `minimal_social_emergency_fallback_line` **10** | Emergency/deterministic social fallback line selection |
| **Policy exports** | 7 | `strict_social_emission_will_apply` **9** | Strict-social eligibility / will-apply predicates |

## Private symbol leaks (accidental export surface)

**10** private helpers imported by external modules — violates encapsulation and inflates perceived hub authority:

- `_npc_display_name_for_emission` — AST FI **4** (`game/final_emission_referential_clarity.py`, `game/final_emission_visibility_fallback.py`, `game/speaker_contract_enforcement.py`, `game/upstream_response_repairs.py`)
- `_has_explicit_interruption_shape` — AST FI **2** (`game/emitted_speaker_signature.py`, `game/speaker_contract_enforcement.py`)
- `_text_is_strict_social_minimal_emergency_fallback` — AST FI **1** (`game/dialogue_social_plan.py`)
- `_active_interlocutor_matches_resolution_social_npc` — AST FI **1** (`game/final_emission_referential_clarity.py`)
- `_speaker_label` — AST FI **1** (`game/final_emission_referential_clarity.py`)
- `_merge_open_social_recovery_emission_debug` — AST FI **1** (`game/gm_retry.py`)
- `_open_social_recovery_passes_anti_stall` — AST FI **1** (`tests/test_broad_address_social_bid.py`)
- `_sse` — AST FI **1** (`tests/test_narration_transcript_regressions.py`)
- `_apply_interruption_repeat_guard` — AST FI **1** (`tests/test_social_exchange_emission.py`)
- `_social_integrity_fallback_line_candidates` — AST FI **1** (`tests/test_social_exchange_emission.py`)

## Highest fan-in exports (maintenance risk)

| Rank | Symbol | BU FI | Risk |
| --- | --- | --- | --- |
| 1 | `minimal_social_emergency_fallback_line` | 10 | **High** — cross-cuts terminal pipeline, sanitizer, gm, visibility |
| 2 | `strict_social_emission_will_apply` | 9 | **High** — API entry, preflight, sanitizer, policy enforcement |
| 3 | `build_final_strict_social_response` | 8 | **Medium** — canonical composition; mostly stack + tests |
| 4 | `effective_strict_social_resolution_for_emission` | 7 | **Medium** — resolution projection for gate/sanitizer |
| 5 | `merged_player_prompt_for_gate` | 7 | **Medium** — gate preflight prompt merge (6 production) |
