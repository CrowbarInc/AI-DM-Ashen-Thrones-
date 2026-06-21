# BV9 — Recurrence Review

**Date:** 2026-06-21  
**Source:** BV8A deduplicated recurrence view (`artifacts/bv8a_recurrence_history.json`)  
**Raw event log:** Unmodified

---

## Executive answer

Speaker projection recurrence is **retired** in the BV8A view. Three **emerging** families remain active with single observations each. No recurring keys remain after deduplication.

## Active recurrence families

| Family | Recurrence key |
| --- | --- |
| speaker|selected_speaker_id|game/speaker_contract_enforcement.py | `recurrence:v1:speaker_drift|speaker|selected_speaker_id|game/speaker_contract_enforcement.py` |
| fallback|final_emitted_source|game/final_emission_gate.py | `recurrence:v1:fallback_drift|fallback|final_emitted_source|game/final_emission_gate.py` |
| sanitizer|scaffold_leakage|game/output_sanitizer.py | `recurrence:v1:semantic_drift|sanitizer|scaffold_leakage|game/output_sanitizer.py` |

## Retired families

| Family | Recurrence key |
| --- | --- |
| projection|selected_speaker_id|tests/helpers/golden_replay.py | `recurrence:v1:speaker_drift|projection|selected_speaker_id|tests/helpers/golden_replay.py` |

## Historical families (evidence retained)

| Family | Recurrence key |
| --- | --- |
| projection|selected_speaker_id|tests/helpers/golden_replay.py | `recurrence:v1:speaker_drift|projection|selected_speaker_id|tests/helpers/golden_replay.py` |

## Emerging families

Same as active — each key has `occurrence_count = 1` and trend class `emerging`.

## Metric delta (BV8A)

| Metric | Before | After |
| --- | --- | --- |
| Dominant share | 0.7273 | 0.25 |
| Recurring keys | 1 | 0 |
| Validated outcomes | 0 | 1 |

