# Running tests

Markers are declared in `pytest.ini`. Only a subset of modules are tagged so far; unmarked tests still run under the full suite but are skipped by selective `-m` expressions.

## Common commands

| Goal | Command |
|------|---------|
| **Day-to-day core** (tagged unit + regression, skip transcript-heavy) | `pytest -m "(unit or regression) and not transcript"` |
| **All tagged unit + regression** (includes transcript-tagged regression modules) | `pytest -m "unit or regression"` |
| **Exclude transcript-heavy** | `pytest -m "not transcript"` |
| **Full suite** | `pytest tests/` |
| **Transcript / gauntlet only** | `pytest -m "transcript"` |
| **Slow slice** (for profiling or nightly) | `pytest -m "slow"` |

## Marker meanings

- **unit** — Small scope, mostly pure logic or tight helpers.
- **integration** — HTTP/API, storage, or multi-step pipeline through the app.
- **regression** — Locks for previously fixed bugs or fragile behavior.
- **transcript** — Multi-turn transcript harness or transcript gauntlet modules.
- **slow** — Longer runs (large gauntlets, many turns).
- **brittle** — Sensitive to prompt wording or prose shape.

Tagging is incremental: prefer `pytest tests/` or `pytest -m "not transcript"` when you need broad coverage until more files are marked.
