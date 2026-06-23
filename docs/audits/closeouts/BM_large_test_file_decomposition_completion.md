# BM Large Test File Decomposition — Completion

## Summary

BM decomposed two large integration test monoliths into focused owner files while preserving redirect stubs for navigation, registry anchors, and validation-command compatibility (BM9 collection-safe stub tests).

| Monolith (before) | Lines | Tests | After |
|---|---:|---:|---|
| `tests/test_golden_replay.py` | 803 | 13 | Redirect stub (26 lines, 1 stub test) + 5 focused owner files (13 tests) |
| `tests/test_final_emission_gate.py` | 2,917 | 159 | Redirect stub (19 lines, 1 stub test) + 5 focused owner files (159 tests) |

**Total monolith tests moved:** 172 (unchanged count; +2 collection-safe stub tests).

## Final file map

### Golden replay (BM4–BM8, BM9)

| File | Lines | Tests | Ownership cluster |
|---|---:|---:|---|
| `tests/test_golden_replay.py` | 26 | 1 | Redirect stub + BI-8 governance anchor |
| `tests/test_golden_replay_protected_bridge.py` | 42 | 1 | Protected assertion bridge diagnostics |
| `tests/test_golden_replay_structural_invariants.py` | 235 | 6 | Short full-replay structural invariant integration |
| `tests/test_golden_replay_long_session.py` | 353 | 3 | 25-turn stability/profile + resume persistence |
| `tests/test_golden_replay_direct_seam.py` | 105 | 2 | Direct-seam gate output observation |
| `tests/test_golden_replay_scenario_spine.py` | 126 | 1 | Scenario-spine smoke integration |

**Pre-existing golden replay neighbors (not part of BM monolith split):**

| File | Lines | Tests | Role |
|---|---:|---:|---|
| `tests/test_golden_replay_projection.py` | 747 | 25 | Protected observation projection contracts |
| `tests/test_golden_replay_fallback_projection.py` | 457 | 14 | Fallback owner-bucket projection locks |
| `tests/test_golden_replay_helper_contracts.py` | 179 | 8 | Helper/fixture contract smoke |

### Final emission gate (BM1–BM3, BM9)

| File | Lines | Tests | Ownership cluster |
|---|---:|---:|---|
| `tests/test_final_emission_gate.py` | 19 | 1 | Redirect stub |
| `tests/test_final_emission_gate_delegator_regression.py` | 1,370 | 123 | BJ delegator / re-export regression locks |
| `tests/test_final_emission_gate_selector_snapshots.py` | 437 | 11 | Selector snapshots + sealed-branch order + Block M4 |
| `tests/test_final_emission_gate_orchestration_order.py` | 805 | 18 | Behavioral layer order |
| `tests/test_final_emission_gate_n4.py` | 145 | 3 | N4 acceptance-quality gate placement |
| `tests/test_final_emission_gate_diagnostics.py` | 172 | 4 | FEM/debug diagnostics |

## Tests moved per cluster

### Golden replay monolith → focused files

| Test | Destination |
|---|---|
| `test_protected_golden_assertion_failure_records_canonical_report` | `test_golden_replay_protected_bridge.py` |
| `test_golden_replay_directed_npc_question_structural_invariants` | `test_golden_replay_structural_invariants.py` |
| `test_golden_replay_vocative_override_after_prior_continuity_structural_invariants` | `test_golden_replay_structural_invariants.py` |
| `test_golden_replay_wrong_speaker_strict_social_emission_structural_invariants` | `test_golden_replay_structural_invariants.py` |
| `test_golden_replay_thin_answer_action_outcome_final_emission_structural_invariants` | `test_golden_replay_structural_invariants.py` |
| `test_golden_replay_sanitizer_scaffold_leakage_structural_invariants` | `test_golden_replay_structural_invariants.py` |
| `test_golden_replay_lead_followup_with_dialogue_lock_structural_invariants` | `test_golden_replay_structural_invariants.py` |
| `test_golden_direct_seam_declared_alias_dialogue_plan_structural_invariants` | `test_golden_replay_direct_seam.py` |
| `test_golden_direct_seam_canonical_opening_fallback_path_has_no_compatibility_local_ownership` | `test_golden_replay_direct_seam.py` |
| `test_golden_replay_frontier_gate_social_inquiry_25_turn_structural_stability` | `test_golden_replay_long_session.py` |
| `test_golden_replay_frontier_gate_social_inquiry_25_turn_resume_persistence_supporting` | `test_golden_replay_long_session.py` |
| `test_golden_replay_frontier_gate_direct_intrusion_25_turn_diagnostic_stability` | `test_golden_replay_long_session.py` |
| `test_golden_replay_scenario_spine_three_branch_structural_smoke` | `test_golden_replay_scenario_spine.py` |

### Final emission gate monolith → focused files

All 159 behavioral/regression tests were extracted per discovery clusters BM1–BM3 into the five `test_final_emission_gate_*.py` owner files (123 BJ delegator tests + 36 non-BJ cluster tests).

## Validation commands

```bash
# Golden replay decomposition suite (includes redirect stub)
python -m pytest tests/test_golden_replay_protected_bridge.py \
  tests/test_golden_replay_structural_invariants.py \
  tests/test_golden_replay_long_session.py \
  tests/test_golden_replay_direct_seam.py \
  tests/test_golden_replay_scenario_spine.py \
  tests/test_golden_replay.py -q

# Final emission gate decomposition suite (includes redirect stub)
python -m pytest tests/test_final_emission_gate_delegator_regression.py \
  tests/test_final_emission_gate_selector_snapshots.py \
  tests/test_final_emission_gate_n4.py \
  tests/test_final_emission_gate_diagnostics.py \
  tests/test_final_emission_gate_orchestration_order.py \
  tests/test_final_emission_gate.py -q
```

Expected counts: **14 passed** (golden replay BM suite), **160 passed** (gate BM suite).

## Registry / documentation updates (BM10)

- `docs/architecture_ownership_ledger.md` — gate practical owner suite now documents redirect stub + focused owner files.
- `tests/test_ownership_registry.py` — BD-6 allowlist extended for decomposed gate owner files; gauntlet neighbor list extended for decomposed golden replay integration files; module docstring clarifies redirect stubs.
- `docs/refactor/BM_large_test_file_decomposition_discovery.md` — completion banner added (baseline preserved).

Redirect stub paths remain valid registry anchors (`direct_owner`, AL4 legality paths, magnet-guard exclusions).

## Remaining risks

| Risk | Mitigation |
|---|---|
| **Long-session runtime** (~15–25s for 3 tests) | Shard `test_golden_replay_long_session.py` separately in CI if needed |
| **Resume persistence storage hazard** | `try/finally` and `patch_transcript_storage` preserved exactly in long-session file |
| **Global protected-failure recording** | Protected-bridge test keeps `clear_recorded_protected_replay_failures` in `finally` |
| **BJ `inspect.getsource` fragility** | Isolated in `test_final_emission_gate_delegator_regression.py`; run after gate module edits |
| **Historical cycle docs** | Many audit/cycle notes still cite monolith paths for historical commands; left intact unless actively misleading |
| **BA-7 magnet guard scope** | Still keyed to registry `direct_owner` paths (stubs + other gate owners); decomposed gate files covered via BD-6 allowlist |

## Recommendation for next cycle

1. **CI shard tags** — add `pytest.mark.long_session` (or similar) to `test_golden_replay_long_session.py` for optional slow-path sharding.
2. **Discovery doc hygiene** — optional pass to add “post-BM path” footnotes in high-traffic cycle recon docs (`cycle_q`, `cycle_s`) without rewriting history.
3. **Architecture audit tool** — review `tests/test_architecture_audit_tool.py` expectations that still classify `test_final_emission_gate.py` as a full smoke/overlap owner.
4. **No further monolith splits required** — BM scope for these two files is complete; next compression work should target helper extraction (discovery “Shared Helper Pressure” table) rather than additional file moves.
