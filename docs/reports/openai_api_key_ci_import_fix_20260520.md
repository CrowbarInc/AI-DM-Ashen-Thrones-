# OPENAI_API_KEY CI Import Fix - 2026-05-20

## Files Changed

- `tests/helpers/transcript_snapshots.py`
- `tests/helpers/transcript_runner.py`
- `tests/test_dead_turn_evaluation_threading.py`
- `docs/reports/openai_api_key_ci_import_fix_20260520.md`

## Import-Boundary Fix Summary

Snapshot-only transcript helpers now live in `tests/helpers/transcript_snapshots.py`. This module owns:

- `snapshot_from_chat_payload`
- `_journal_summary`
- `_world_summary`
- `_compact_resolution`
- `compact_snapshot_summary`
- `latest_target_id`
- `latest_target_source`
- `format_turn_debug`

`tests/test_dead_turn_evaluation_threading.py` now imports `snapshot_from_chat_payload` from the snapshot-only helper instead of `tests.helpers.transcript_runner`.

`tests/helpers/transcript_runner.py` remains the transcript execution harness and still owns chat-turn execution helpers. It imports/re-exports snapshot formatting helpers from `tests.helpers.transcript_snapshots` for backward compatibility, while keeping `game.api.chat` scoped to the runner module.

A regression test was added:

```text
test_transcript_snapshot_helper_import_does_not_load_live_api_stack
```

It imports `tests.helpers.transcript_snapshots` in an isolated `sys.modules` window and asserts that `game.api`, `game.gm`, and `game.config` are not loaded by the snapshot helper import.

## Validation Commands and Results

Requested command, literal local shell:

```text
python -m pytest tests/test_dead_turn_evaluation_threading.py --collect-only -q
```

Result:

```text
python : The term 'python' is not recognized as the name of a cmdlet, function, script file, or operable program.
```

Equivalent local command using the available bundled Python plus `.venv` site-packages:

```text
$env:PYTHONPATH='.\\.venv\\Lib\\site-packages'
python.exe -m pytest tests\\test_dead_turn_evaluation_threading.py --collect-only -q
```

Result:

```text
tests/test_dead_turn_evaluation_threading.py: 9
```

Target test run:

```text
$env:PYTHONPATH='.\\.venv\\Lib\\site-packages'
python.exe -m pytest tests\\test_dead_turn_evaluation_threading.py -q
```

Result:

```text
.........                                                                [100%]
```

Evaluator boundary slice:

```text
$env:PYTHONPATH='.\\.venv\\Lib\\site-packages'
python.exe -m pytest tests\\test_dead_turn_evaluation_threading.py tests\\test_playability_eval.py tests\\test_behavioral_gauntlet_eval.py tests\\test_scenario_spine_eval.py tests\\test_final_emission_meta.py tests\\test_architecture_audit_tool.py tests\\test_validation_layer_audit_smoke.py -q
```

Result:

```text
........................................................................ [ 62%]
...........................................                              [100%]
```

Forbidden live-stack import/string check:

```text
rg -n "game\\.api|game\\.gm|game\\.config|OPENAI|OpenAI|api_key" tests\\helpers\\transcript_snapshots.py
```

Result: no matches.

CI-like missing-secret collection simulation:

```text
$env:PYTHONPATH='.\\.venv\\Lib\\site-packages'
$env:PYTHON_DOTENV_DISABLED='1'
Remove-Item Env:\\OPENAI_API_KEY -ErrorAction SilentlyContinue
python.exe -m pytest tests\\test_dead_turn_evaluation_threading.py --collect-only -q
```

Result:

```text
tests/test_dead_turn_evaluation_threading.py: 9
```

## OPENAI_API_KEY Requirement

`OPENAI_API_KEY` is no longer required for the `tests/test_dead_turn_evaluation_threading.py` evaluator collection path. With local dotenv loading disabled and no shell `OPENAI_API_KEY`, collection still succeeds.

This does not change production runtime behavior and does not loosen `game/config.py`.

## Remaining Follow-Up

The proper production follow-up remains lazy config loading: `game.config` should not require `OPENAI_API_KEY` at module import time. Required secrets should be validated only when upstream API/client code is invoked.
