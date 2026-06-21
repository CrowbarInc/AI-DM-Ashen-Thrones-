# BV14 — Decomposition Candidates

**Date:** 2026-06-21

---

## Candidate modules

| Candidate | Extract | Est. FI | Consumers | Migration cost | Replay risk |
| --- | --- | --- | --- | --- | --- |
| **`social_exchange_composition`** | `build_final_strict_social_response`, ownership filters, resolution coercion/reconcile, `hard_reject_social_exchange_text`, GM retry recovery | **~15–20** | strict_social_stack, gm_retry, test legality owner | **Medium** — stack owner coordination | **Medium** — transcript golden strict-social text |
| **`social_exchange_fallback`** | `minimal_social_emergency_fallback_line`, `select_*`, `strict_social_ownership_terminal_fallback`, deterministic/lawful dialogue fallbacks, sanitizer line | **~18–22** | terminal pipeline, visibility, sealed, response_type, gm, sanitizer, 8+ modules | **Medium-high** — widest production sprawl | **High** — shipped fallback phrase catalog |
| **`social_exchange_policy`** | `strict_social_emission_will_apply`, `should_apply_*`, `merged_player_prompt_for_gate`, player-line triggers, narration-beat suppression | **~12–15** | API, preflight, 6 gate policy modules, interaction_context | **Medium** — API + preflight first | **Low** — predicate-only |
| **`social_exchange_validation`** | `is_route_illegal_*`, `replacement_is_route_legal_social`, malformed echo checks | **~6–8** | validators, referential_clarity, gm, sanitizer tests | **Low-medium** | **Low** |
| **`social_exchange_projection`** | `log_final_emission_*`, FEM family stamp/project helpers | **~5–7** | generic_exit, strict_social_stack, visibility, fem_assembly | **Low** | **Low** — telemetry only |
| **Private helper encapsulation** | `_npc_display_name_for_emission`, `_speaker_label`, `_has_explicit_interruption_shape`, `_text_is_strict_social_minimal_emergency_fallback` | **~8–10** | referential_clarity, speaker_contract, dialogue_social_plan, emitted_speaker_signature | **Low** — promote to public on target module or inline at caller | **Low** |

## Not recommended

| Candidate | Reason |
| --- | --- |
| Full module deletion | Composition + fallback are genuine production authorities |
| Split composition per sentence-filter | Over-fragmentation — filters are internal to `build_final_strict_social_response` |
| Move eligibility to `response_policy_contracts` | Contracts are read-only; emission predicates need session/world resolution context |

## Projected FI reduction (module-level)

| Stage | `social_exchange_emission` FI | New module FI |
| --- | --- | --- |
| Current | **52** | — |
| After Phase 1 extract + compat re-export | **52** (unchanged short-term) | fallback **~20**, policy **~12**, composition **~15** |
| After Phase 2 consumer migration | **~6–10** | fallback **~20**, policy **~12**, composition **~15**, validation **~6** |
| Steady state (compat retired) | **0–4** | named authorities hold direct FI |

**Net maintenance win:** FI concentration moves from ambiguous 3881-LOC monolith to **named authorities**; fallback sprawl (FI ~20) becomes explicit maintenance surface rather than hidden in composition module.
