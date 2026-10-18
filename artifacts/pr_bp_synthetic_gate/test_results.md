# PR-BP Test Results

Date: 2026-09-27
Base HEAD: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`

## Focused Real-Path Integration

Command:

```text
python -m pytest tests/test_pr_bp_live_resolution_routing.py -q --tb=short --basetemp=codex_pytest_tmp_prbp2
```

Result:

```text
4 passed
```

## Adjacent Regression Band

Command:

```text
python -m pytest tests/test_bounded_improvisation_authority.py tests/test_gm_retry.py tests/test_playability_eval.py tests/test_directed_social_routing.py tests/test_turn_pipeline_shared.py -q --tb=short --basetemp=codex_pytest_tmp_prbp5
```

Result:

```text
failed: 6 failures in tests/test_turn_pipeline_shared.py
```

Failures:

- `test_action_and_chat_investigate_both_mark_runtime_discovery_memory`
- `test_direct_npc_question_keeps_dialogue_contract_and_question_relevant_unknown_fallback`
- `test_chat_single_wait_in_tense_scene_forces_interaction_pressure`
- `test_chat_repeated_passive_actions_do_not_stall_into_atmosphere`
- `test_chat_passive_scene_prefers_already_introduced_suspicious_figure`
- `test_chat_passive_wait_with_recent_suspicious_figure_replaces_weak_atmosphere`

## Synthetic Gate

Command:

```text
python tools/run_pr_bp_synthetic_gate.py --turns 10 --artifact-dir artifacts/pr_bp_synthetic_gate
```

Artifact:

```text
artifacts/pr_bp_synthetic_gate/20260927T202617Z
```

Result:

```text
3 sessions, 30 turns, 16 semantic failures.
Synthetic gate FAILED.
Human playtest NOT recommended.
```

