# CP2 — Directed NPC Route Drift Corrective Report

Date: 2026-06-28  
Planning authority: `CP_corrective_locality_cohort_3_discovery.md`, `CP1_preflight_sanitizer_corrective_slice_report.md`

## Executive Summary

A genuine routing defect was reproduced and fixed with a **2-file, 1-production** change. Generic-role perception questions (e.g. `What does the guard see?`) were classified as dialogue by `choose_interaction_route` but failed canonical social entry binding, leaving `target_actor_id` unset and breaking social turn contract ownership. The fix extends generic-role address patterns in `interaction_context.py` so role-in-perception questions resolve to the sole matching roster NPC.

## Defect Reproduced?

**Yes**

## Reproduction Scenario

With two scene NPCs present (`runner`, `gate_guard` with `role: guard`), player input:

```text
What does the guard see?
```

### Before fix

| Signal | Value |
|---|---|
| `resolve_directed_social_entry.should_route_social` | `False` |
| `resolve_directed_social_entry.target_actor_id` | `None` |
| `resolve_directed_social_entry.reason` | `no_addressable_target` |
| `choose_interaction_route` | `dialogue` |
| `_build_dialogue_first_action.target_id` | `None` |
| `social_turn_contract.reply_owner_actor_id` | `None` |
| `social_turn_contract.continuity_status` | `broken` |

Contrast: full-name variant `What does Tavern Runner see?` correctly bound to `runner` via slug match; comma vocative `Guard, what do you see?` bound via spoken vocative. Only **mid-line generic role + perception verb** failed.

`test_local_observation_routing.py` already asserted `What does the guard see?` is **not** a local observation query, but no test required canonical social binding — leaving this gap unprotected.

## Root Cause

`_GENERIC_ADDRESS_PATTERNS` in `game/interaction_context.py` matched comma vocatives, `to the guard`, line-leading roles, etc., but **not** the pattern `what does the {role} {perception_verb}`.

As a result:

1. `match_generic_role_address` returned empty for `What does the guard see?`
2. `find_addressed_npc_id_for_turn` and `resolve_directed_social_entry` could not bind `gate_guard`
3. `is_directed_dialogue` still returned `True` via `asks_for_information && has_present_character`, producing **route/canonical-entry drift**: dialogue lane with no resolved addressee

This is a directed-NPC route drift class defect (social dialogue lane without social target), not a policy redesign issue.

## Production Files Changed

| File | Change |
|---|---|
| `game/interaction_context.py` | Added generic-role pattern for `what does/did the {role} see|know|notice|…` to `_GENERIC_ADDRESS_PATTERNS` |

No changes to `game/interaction_routing.py` or `game/dialogue_targeting.py` (fix correctly localized to authoritative target binding).

## Tests Added/Updated

| File | Change |
|---|---|
| `tests/test_local_observation_routing.py` | Added `test_resolve_directed_social_entry_generic_role_perception_binds_single_guard` |

## Validation Results

### Baseline + golden (post-fix)

```bash
python -m pytest tests/test_directed_social_routing.py tests/test_dialogue_routing_lock.py tests/test_local_observation_routing.py tests/test_golden_replay_structural_invariants.py -q --tb=short
```

| Outcome | Count |
|---|---:|
| **Passed** | 48 |
| Failed | 0 |

Breakdown: directed social (32), dialogue lock (1), local observation (9), golden structural (6).

### Protected scenario (directed NPC question)

```bash
python -m pytest tests/test_golden_replay_structural_invariants.py::test_golden_replay_directed_npc_question_structural_invariants -q --tb=short
```

Result: **1 passed** (unchanged; protected scenario uses comma vocative `Runner, who attacked the patrol?`).

### Manifest check

```bash
python tools/refresh_protected_replay_manifest.py --check
```

Result: **exit 0**

## Locality Metrics

| Metric | Value |
|---|---:|
| Total files changed | 2 |
| Production files touched | 1 |
| Test files touched | 1 |
| Governance/docs files touched | 0 |
| Replay/golden files touched | 0 |

Within CP2 expected surface (≤5 production files). No stop conditions triggered.

## Before/After Routing Diagnostics

Scenario: `What does the guard see?` with `runner` + `gate_guard` in scene.

| Field | Before | After |
|---|---|---|
| `should_route_social` | `False` | `True` |
| `target_actor_id` | `None` | `gate_guard` |
| `target_source` | `None` | `generic_role` |
| `reason` | `no_addressable_target` | `generic_role_address` |
| `route_kind` / `choose_interaction_route` | `dialogue` | `dialogue` |
| `selected_speaker_id` (downstream) | unset / broken contract | binds via `gate_guard` |
| Canonical routing decision | dialogue lane, no target | dialogue lane, guard bound |

Local observation control (`What does he see?`) unchanged: `should_route_social=False`, `reason=local_scene_observation_query`, route `undecided`.

## Replay Impact

- Protected `directed_npc_question` golden: **pass** (no golden rewrite)
- No protected manifest drift
- No replay artifact edits

## Recurrence Evidence

- Historical corpus row for `directed_npc_question` documents an older `final_emitted_source` mismatch (corpus observation); not this specific generic-role perception binding gap.
- This slice introduces **new prevention evidence**: focused unit test locks `What does the guard see?` → `gate_guard` via `generic_role`.
- No existing BV8A recurrence key was retired (no documented protected failure→fix key for this exact pattern); prevention is test-gated going forward.

## CP Cohort #3 Qualification

| Criterion | Met? |
|---|---|
| Reproduced real defect | **Yes** |
| Bounded production fix | **Yes** (1 file) |
| Focused test proves prevention | **Yes** |
| Independent failure → fix → validation | **Yes** |
| Locality within cohort budget | **Yes** (2 total files) |

**Verdict: qualifies as a CP corrective-locality cohort #3 entry** — first slice in this cohort with an actual failure→fix→validation cycle (following CP1 validation-only probe).

## Recommended Next Candidate

**CP3 — Vocative speaker override regression**

Rationale:

1. CP2 generic-role perception binding is closed with minimal surface area.
2. Discovery order places speaker parity (CP3/CP4) next; vocative override has a protected scenario (`vocative_override_after_prior_continuity`) and measurable `selected_speaker_id` outcomes.
3. CP5 (fallback projection) aligns with the unrelated CO102 operational sentinel; defer until runtime route/speaker surfaces are stable.
4. Run **only CP3 or CP4 first** to avoid over-concentrating on speaker work.
