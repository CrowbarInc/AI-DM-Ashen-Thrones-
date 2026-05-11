# Failure Dashboard Operationalization - 2026-05-11

## Implemented

- Added opt-in latest dashboard artifact generation for replay failure classifications.
- Added `--write-failure-dashboard` pytest option.
- Added equivalent `ASHEN_WRITE_FAILURE_DASHBOARD=1` environment-variable path.
- Added session-level pytest recording/writing to `audits/failure_dashboard_latest.md`.
- Extended dashboard markdown with timestamp, command, scenario, turn, category, severity, owners, investigation target, replay tags, failed field path, expected/actual values, unavailable fields, final emitted source, fallback family, and post-gate mutation flag.
- Preserved normal test behavior: dashboard files are not written unless explicitly requested.

## Commands

Generate the latest artifact with:

```powershell
python -m pytest -m golden_replay -q --write-failure-dashboard
```

or:

```powershell
$env:ASHEN_WRITE_FAILURE_DASHBOARD='1'; python -m pytest -m golden_replay -q
```

## Tests Added

- Empty/no-failure dashboard state.
- One-failure dashboard row rendering.
- Owner, severity, and investigation target fields.
- Unavailable field preservation.
- Opt-in-only artifact generation.

## Remaining Gaps

- Late final-emission sublayer attribution is still coarse.
- Sanitizer run summaries are not always projected into replay rows.
- Projection-vs-runtime-missing ambiguity remains when raw runtime metadata is absent from replay views.
- The dashboard consumes existing replay/FEM/stage-diff signals only; it does not add live telemetry.
- Evaluator signals remain advisory and are not used as runtime policy.
