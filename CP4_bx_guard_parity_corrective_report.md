# CP4 — BX Guard Speaker Identity Parity Corrective Report

Date: 2026-06-28  
Planning authority: `CP_corrective_locality_cohort_3_discovery.md`, `CP2_directed_route_corrective_report.md`, `CP3_vocative_override_corrective_report.md`, `CP5_fallback_projection_corrective_report.md`, `CP6_dialogue_lock_corrective_report.md`

## Executive Summary

Baseline BX speaker-identity suites and the `bx_speaker_parity` marker gate all passed (49 + 6 marker-selected tests). Exploratory probing continued across guard/gate_guard/guard_captain routing, multi-guard ambiguity, generic-role resolution, CP3 vocative variants, dual-guard rosters, and gate→replay lifecycle parity. **No reproducible parity drift defect was found.** No production changes were made.

## Defect Reproduced?

**No**

## Baseline Validation

### CP4 BX parity suite

```bash
python -m pytest \
  tests/test_bx_speaker_identity_end_to_end_parity.py \
  tests/test_bx_speaker_identity_golden_replay.py \
  tests/test_speaker_contract_enforcement.py \
  -q --tb=short
```

| Outcome | Count |
|---|---:|
| **Passed** | 49 |
| Failed | 0 |

Breakdown: BX end-to-end parity (7), BX5 protected golden replay (6), speaker contract enforcement (36).

### BX marker gate

```bash
python -m pytest -m bx_speaker_parity -q --tb=short
```

| Outcome | Count |
|---|---:|
| **Passed** | 6 |
| Failed | 0 |

### Manifest check

```bash
python tools/refresh_protected_replay_manifest.py --check
```

Result: **exit 0**

### Related protected replay (guard-adjacent)

```bash
python -m pytest \
  tests/test_golden_replay_structural_invariants.py::test_golden_replay_vocative_override_after_prior_continuity_structural_invariants \
  -q --tb=short
```

Result: **1 passed** — turn 2 `selected_speaker_id == "guard"` (gate_guard vocative scenario)

## Probe Scenarios Investigated

Ephemeral probes in `codex_pytest_tmp/` (not part of the test suite) extended BX Cases A–D.

### Case matrix (existing BX coverage — all pass)

| Case | Scenario | Expected speaker | Parity status |
|---|---|---|---|
| A | Role alias `"Guard, …"` → `guard_captain` | `guard_captain` | aligned |
| B | Canonical id `guard_captain` | `guard_captain` | aligned |
| C | Distinct `gate_guard` vocative | `gate_guard` | aligned; ≠ `guard_captain` |
| D | Ambiguous multi-guard (`"Tell me guard, …"`) | unresolved/ambiguous | `final_ambiguous`; risk S ≥ 20 |

### Extended routing probes

| Input | Roster | `npc_id` | Source | Notes |
|---|---|---|---|---|
| `Guard, who posted…` | frontier_gate default | `guard_captain` | `spoken_vocative` | Case A |
| `Hey guard - who posted…` | frontier_gate default | `guard_captain` | `spoken_vocative` | CP3 dash vocative integrates cleanly |
| `What does the guard know…` | frontier_gate default | `guard_captain` | `generic_role` | Generic role → canonical |
| `Gate Guard, what is your post?` | + gate_guard addressable | `gate_guard` | `spoken_vocative` | Case C |
| `Guard, …` with gate_guard + guard_captain | dual guard | `guard_captain` | `spoken_vocative` | Priority/tie-break; gate_guard wins only on full name vocative |
| `Tell me guard, …` | ambiguous (captain + sentry) | `null` | `none` | Case D phrase — stays ambiguous |
| `Guard, …` | ambiguous (captain + sentry) | `guard_captain` | `spoken_vocative` | Comma vocative resolves deterministically (not Case D phrase) |

### Lifecycle gate→replay probes

| Scenario | routed | final_resolved | replay_selected | fso_canonical | parity |
|---|---|---|---|---|---|
| GM line `"Guard says, …"` routes captain | `guard_captain` | `guard_captain` | `guard_captain` | `guard_captain` | aligned |
| GM line wrong label (`Gate Guard says…`) routes captain | `guard_captain` | `guard_captain` | `guard_captain` | `guard_captain` | aligned |
| CP3 dash vocative + captain GM line | `guard_captain` | `guard_captain` | `guard_captain` | `guard_captain` | aligned |
| Dual roster: Gate Guard vocative | `gate_guard` | `gate_guard` | `gate_guard` | `gate_guard` | aligned |

No instance of runtime/replay disagreement on `selected_speaker_id` or `selected_speaker_source` for resolved guard cases.

### Probed but ruled out

| Candidate | Outcome |
|---|---|
| `guard` role token stored as replay `selected_speaker_id` while runtime resolves `guard_captain` | **Not reproduced** in lifecycle probes |
| `gate_guard` collapsing into `guard_captain` on full-name vocative | **Not reproduced** |
| Ambiguous roster false parity (low-risk aligned) | **Blocked** by Case D assertions (`risk_S ≥ 20`, `final_ambiguous`) |
| `wrong_speaker_strict_social_emission` (runner/merchant) | **Out of scope** — different scenario; CO102 operational sentinel on `fallback_family`, not guard parity |
| Historical `guard` vs `guard_captain` projection drift in backfill corpus | **Synthetic classifier control** (`tests/test_backfill_bug_recurrence_history.py`); not a live BX matrix failure |

## Root Cause

N/A — no defect reproduced.

Observed behavior matches BX closed-out design (`docs/audits/closeouts/BX_speaker_identity_end_to_end_parity_closeout.md`):

- Scene-roster `address_roles` maps bare `guard` → `guard_captain` when unambiguous.
- `gate_guard` remains distinct when explicitly vocative-addressed or registered as separate addressable.
- Ambiguity is phrase-bound: `"Tell me guard, …"` with multiple guard-role addressables stays unresolved; comma vocatives resolve via deterministic roster priority.
- `final_speaker_observation` canonical stamp and replay `speaker_projection_parity` align for resolved cases (BX2/BX3/BX5).

## Production Files Modified

| File | Change |
|---|---|
| *(none)* | — |

## Tests Added or Updated

| File | Change |
|---|---|
| *(none)* | Ephemeral probes only in `codex_pytest_tmp/` |

## Validation Summary (post-probe)

All baseline and marker commands re-run green after probing. No regression introduced (no code changes).

## Locality Metrics (CP4 slice)

| Metric | Value |
|---|---:|
| Total files changed | 0 |
| Production files touched | 0 |
| Test files touched | 0 |
| Replay/helper files touched | 0 |
| Governance/docs files touched | 1 (this report) |

Within stop thresholds (≤5 production files, no identity redesign, no governance churn beyond report).

## Before/After Diagnostics

No fix applied. Representative resolved guard row (Case A):

| Field | Value |
|---|---|
| `selected_speaker_id` | `guard_captain` |
| `selected_speaker_source` | `resolution.social.npc_id` (replay projection) |
| `canonical speaker` (`final_speaker_observation.canonical_speaker_id`) | `guard_captain` |
| `parity status` | `aligned` |
| `replay impact` | none |
| `recurrence outcome` | no new failure |

Representative ambiguous row (Case D):

| Field | Value |
|---|---|
| `selected_speaker_id` | `None` |
| `selected_speaker_source` | `None` |
| `canonical speaker` | `None` |
| `parity status` | `final_ambiguous` |
| `risk_S` | ≥ 20 |

## Replay Impact

- BX5 protected scenarios (`bx5_guard_role_alias_guard_captain`, `bx5_guard_canonical_guard_captain`, `bx5_guard_gate_guard_distinct`, `bx5_guard_ambiguous_multi_guard`): **pass**, unchanged
- No golden expectation edits
- No manifest drift
- `vocative_override_after_prior_continuity` (gate_guard): **pass**

## Recurrence Evidence

- BX emission retirement evidence gate (`pytest -m bx_speaker_parity`) passes independently of BW short structural scenarios.
- Historical corpus row `guard` vs `guard_captain` projection mismatch exists as classifier/backfill documentation, not as a failing BX matrix case today.
- CO102 `wrong_speaker_strict_social_emission` sentinel remains operational/projection-classified — not a guard-parity production defect.
- No recurrence registry retirement performed.

## CP Cohort #3 Qualification

| Criterion | Met? |
|---|---|
| Reproduced real defect | **No** |
| Bounded production fix | **No** |
| Focused regression tests | **No** (probes only) |
| failure → fix → validation cycle | **No** |
| Locality within budget | **Yes** (zero production churn) |

**Verdict: does NOT qualify as an independent CP corrective-locality cohort #3 entry.** This slice confirms BX guard-matrix parity remains stable after CP2/CP3 routing/vocative fixes and CP5 projection fix. Same class as CP1 and CP6 (validation-only).

## Recommended Next Candidate

**CP9 — Upstream preflight/config self-invalidates**

Rationale:

1. CP4 found no actionable guard-parity defect; speaker-identity surfaces (CP3 vocative, CP4 BX matrix, CP5 projection) are currently stable.
2. CP9 was validation-only in CP1 but offers the lowest blast radius for a potential **production** corrective if a defect exists (preflight/config/import path).
3. Discovery execution order placed CP9 first as low-risk cohort proof; only CP2, CP3, and CP5 produced fixes so far — a small CP9 win would diversify cohort outcomes without another speaker slice.
4. Remaining discovery candidates (CP7, CP8) are higher risk or deferred.

**Alternative:** **CP7** or another discovery candidate if the cohort should skip another validation-only pass and pursue a different medium-blast-radius surface — but CP9 remains the lowest-risk path to a bounded production fix.
