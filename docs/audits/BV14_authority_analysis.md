# BV14 — Authority vs Utility Analysis

**Date:** 2026-06-21

---

## Module self-description vs reality

Docstring claims: *downstream emission consumer and application layer for strict-social turns; not the contract owner, not the repair owner.*

Actual contents span **canonical strict-social composition** (`build_final_strict_social_response`), **eligibility policy**, **fallback content authority**, **telemetry logging**, **route-legality validators**, and **102 private helpers** (many never imported externally). The composition subset matches a legitimate authority; fallback + policy + telemetry co-location creates BV13-style **mixed hub** pressure at FI 52.

## Export classification (public surface)

| Export | Class | Verdict |
| --- | --- | --- |
| `build_final_strict_social_response` | canonical-composition-authority | **Legitimate authority** — terminal strict-social assembly owner |
| `apply_strict_social_*_ownership_*`, `normalize_social_exchange_candidate`, `hard_reject_social_exchange_text` | composition-helper | Composition sub-primitives — belong with composition module |
| `strict_social_emission_will_apply`, `should_apply_strict_social_exchange_emission` | policy-vocabulary | **Policy authority** — eligibility predicates; consumers span API + gate |
| `merged_player_prompt_for_gate` | realization-projection | Gate prompt merge — policy/projection seam |
| `minimal_social_emergency_fallback_line`, `select_strict_social_emergency_fallback_line`, `strict_social_ownership_terminal_fallback` | fallback-authority | **Fallback content authority** — high FI sprawl (10+ importers) |
| `is_route_illegal_global_or_sanitizer_fallback_text`, `replacement_is_route_legal_social` | validator-projection | Validator vocabulary — belongs with validation module or `final_emission_validators` facade |
| `log_final_emission_decision`, `log_final_emission_trace` | telemetry-projection | Diagnostics — accidental co-location with composition |
| `project_strict_social_replace_realization_family`, `stamp_strict_social_deterministic_fallback_family` | realization-projection | FEM family projection — thin delegates to `realization_provenance` |
| `_npc_display_name_for_emission`, `_speaker_label`, `_has_explicit_interruption_shape` (private leaks) | accidental-bridge | **Encapsulation violation** — production imports private helpers |

## Canonical authority determination

| Question | Answer |
| --- | --- |
| Is `social_exchange_emission` a legitimate authority module? | **Partially** — strict-social **composition + fallback content** are genuine authorities |
| Is FI 52 justified by a single concern? | **No** — top symbol FI 10; five concern categories with overlapping consumers |
| What is actually authoritative here? | Terminal strict-social response assembly; emergency fallback line catalog; eligibility will-apply predicates |
| Closest legitimate owners after split | Composition → `social_exchange_composition`; Fallback → `social_exchange_fallback`; Policy → `social_exchange_policy`; Validators → `social_exchange_validation` |

## Projection helpers vs accidental bridges

| Pattern | Examples | Assessment |
| --- | --- | --- |
| Canonical composition | `build_final_strict_social_response` | Legitimate — should remain named authority (possibly renamed module) |
| Policy vocabulary | `strict_social_emission_will_apply` | Legitimate but **misplaced breadth** — API + gate + sanitizer share one predicate |
| Fallback authority | `minimal_social_emergency_fallback_line` | Legitimate content owner — **over-imported** across unrelated fallback layers |
| Telemetry | `log_final_emission_*` | Convenience — BJ-115 moved logging calls to direct import; should live in diagnostics module |
| Private helper leaks | `_npc_display_name_for_emission` (4 AST), `_has_explicit_interruption_shape` (2 AST) | **Accidental bridges** — force hub coupling for display/interruption scans |

## BU1 / BN8 alignment

BU ownership map marks module as **strict-social composition** (FI 52, 27 production). BN8 preflight strict-social boundary already treats this as a **coordination seam** with `final_emission_gate_preflight_strict_social`. BV14 confirms: keep **composition authority centralized**; decompose **fallback FI sprawl** and **private leaks** first (BV13 parallel).
