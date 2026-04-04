# Running tests

**Full lane** runs the whole suite. **Fast lane** excludes items marked `transcript` or `slow`. **Stricter fast** also excludes `brittle`. Marker definitions live in `pytest.ini`; scope and ownership notes are in `tests/TEST_AUDIT.md`. Routing and **repair/retry regression** ownership are settled (see `tests/TEST_CONSOLIDATION_PLAN.md` → *Block 3 — Routing* and *Repair / retry cluster — Block 3*).

**Windows:** If `pytest` is not on your `PATH`, use `py -3 -m pytest` instead of `pytest` for every command below (for example `py -3 -m pytest -m "not transcript and not slow"`).

## Full lane

**When:** Pre-merge, milestones, or whenever you need the full regression surface (transcript harnesses, gauntlets, expensive flows).

From repo root:

```bash
pytest
```

Same thing with an explicit path:

```bash
pytest tests/
```

**Collect only:**

```bash
pytest --collect-only -q
```

Expect **889** tests collected (no marker deselection). Re-check after large suite changes; see `tests/TEST_AUDIT.md` → *Block 3 — Fast/full workflow verification*.

## Fast lane

**When:** Day-to-day feedback without transcript-harness modules and modules marked `slow`.

**Selection:** Everything except tests on classes/functions/modules marked `transcript` or `slow`.

```bash
pytest -m "not transcript and not slow"
```

**Collect only:**

```bash
pytest --collect-only -m "not transcript and not slow" -q
```

Expect **855** tests collected and **34** deselected (889 total). Re-verify after adding tests.

## Optional stricter fast lane (`brittle`)

When prompt- or prose-sensitive tests are too noisy locally:

```bash
pytest -m "not transcript and not slow and not brittle"
```

## Synthetic-player harness (`synthetic`)

The helpers under `tests/helpers/synthetic_*.py` are **test/tooling infrastructure only** (no `game/` coupling in the scaffold). They are meant to drive or evaluate automated “synthetic players” alongside patterns like `tests/helpers/transcript_runner.py`, not to add gameplay modes.

- **`py -m pytest -q` includes synthetic-player tests:** `pytest.ini` only adds `-q` (no marker filter). You get `tests/test_synthetic_sessions.py`, `tests/test_synthetic_policy.py`, and `tests/test_synthetic_smoke.py` (the last is `slow`). The fast lane `-m "not transcript and not slow"` skips `test_synthetic_smoke.py` but still runs the two lighter synthetic modules.
- The primary harness runner surface is `run_synthetic_session(...)`; `run_placeholder_session(...)` remains compatibility-only.
- Synthetic pytest smoke coverage is deterministic and fake-GM-backed by default.
- For manual exploratory runs, use `tools/run_synthetic_session.py` (defaults to fake-GM mode; real-GM mode is explicit opt-in via `--real-gm`).

### Manual CLI examples

```bash
# Default deterministic fake-GM run
python tools/run_synthetic_session.py

# Explicit real-GM exploratory run
python tools/run_synthetic_session.py --real-gm

# Use a non-default synthetic profile
python tools/run_synthetic_session.py --profile risk_taker

# Pin deterministic run parameters
python tools/run_synthetic_session.py --seed 1337 --max-turns 12
```

Fake-GM mode is for deterministic harness validation; real-GM mode is exploratory and may be less stable run-to-run.

### Recommended synthetic lanes

Use these marker slices to keep the synthetic workflow explicit without changing fast/full lane boundaries.

- **Fake-GM synthetic lane** (`synthetic and not transcript and not slow`)  
  Deterministic regression signal for day-to-day harness confidence.
- **Transcript-backed synthetic lane** (`synthetic and transcript`)  
  Lightweight real-path health checks (materially slower than fake-GM).
- **Full synthetic lane** (`synthetic`)  
  Everything tagged synthetic, across fake-GM and transcript-backed tests.
- **Manual CLI lane** (`tools/run_synthetic_session.py`)  
  Exploratory work outside pytest selection.

Quick run guidance:
- Run the **fake-GM synthetic lane** for routine local feedback and deterministic harness confidence.
- Run the **transcript-backed synthetic lane** when validating real-path wiring or bug/risk-sensitive social routing signals.
- Run the **full synthetic lane** before merge when harness, scenario presets, or policy behavior changes span both lanes.

Copy/paste commands:

```bash
# Deterministic synthetic non-transcript runs (recommended fake-GM lane)
pytest -m "synthetic and not transcript and not slow"

# Transcript-backed synthetic runs
pytest -m "synthetic and transcript"

# All synthetic runs
pytest -m "synthetic"

# One-file focused synthetic run
pytest tests/test_synthetic_smoke.py

# Runner / preset regression (fast synthetic; not transcript-backed)
pytest tests/test_synthetic_sessions.py
```

- **End-to-end** synthetic sessions (multi-turn, real `chat` / transcript loops) should usually be marked **`synthetic`** and **`slow`** so they stay out of the default fast lane (`not transcript and not slow`).
- **Unit tests** for the harness itself (imports, shapes, pure policy stubs) can stay **fast**: mark them `synthetic` and `unit` without `slow` if they do not run multi-turn sessions.

Optional stricter selection: add `and not synthetic` to a local fast-lane command if you want to skip all harness-tagged tests.

## What “trustworthy” means for fast vs full

**Lane trustworthiness is about composition and selection** — which tests the marker expression includes or excludes — **not** about the whole fast lane being green. A red test in the fast lane is still a real failure; it is **orthogonal** to whether the fast/full split matches intent (exclude transcript + slow from fast; run everything on full).

## Where to add new tests

See `tests/TEST_AUDIT.md` → *Consolidation Block 1 — Canonical ownership map & overlap hotspots* for owners by theme. **Next consolidation order:** prompt/sanitizer → social/emission → lead/clue (repair/retry cluster documented and closed enough — see `tests/TEST_CONSOLIDATION_PLAN.md` → *Next consolidation order* and *Repair / retry cluster — Block 3*).

## Command cheat sheet

| Goal | Command |
|------|---------|
| **Full lane** | `pytest` or `pytest tests/` |
| **Full lane, collect only** | `pytest --collect-only -q` |
| **Fast lane** | `pytest -m "not transcript and not slow"` |
| **Fast lane, collect only** | `pytest --collect-only -m "not transcript and not slow" -q` |
| **Stricter fast** (optional) | `pytest -m "not transcript and not slow and not brittle"` |
| **Transcript / slow slice** | `pytest -m "transcript or slow"` (complement of fast selection) |
| **Transcript only** | `pytest -m "transcript"` |
| **Slow only** | `pytest -m "slow"` |
| **Exclude transcript only** | `pytest -m "not transcript"` |
| **Synthetic fake-GM lane** | `pytest -m "synthetic and not transcript and not slow"` |
| **Synthetic transcript lane** | `pytest -m "synthetic and transcript"` |
| **All synthetic** | `pytest -m "synthetic"` |
| **Synthetic one-file focus** | `pytest tests/test_synthetic_smoke.py` |
| **All tagged unit + regression** | `pytest -m "unit or regression"` |
| **Narrow legacy filter** (not equivalent to fast lane) | `pytest -m "(unit or regression) and not transcript"` — omits many integration-only modules; see `tests/TEST_AUDIT.md` |

## Marker meanings (lane-relevant)

- **unit** / **integration** / **regression** — Scope and signal density; **not** the fast-lane gate. Use for inventory, filters like `pytest -m regression`, and documentation.
- **transcript** — Transcript harness / gauntlet-style modules (**fast lane excludes**).
- **synthetic** — Synthetic-player harness and automation-owned checks (tag for ownership; fast lane does **not** exclude unless you add `not synthetic`).
- **slow** — Longer or expensive runs (**fast lane excludes**).
- **brittle** — Prompt/prose-sensitive (**optional** extra exclusion for stricter fast).

Ownership markers (`routing`, `retry`, `fallback`, …) are for inventory and feature tagging only — **not** for choosing fast vs full. See `pytest.ini` for the full list.

The expression `(unit or regression) and not transcript` is **narrower** than the fast lane: many fast-eligible modules are integration-only and would be skipped.
