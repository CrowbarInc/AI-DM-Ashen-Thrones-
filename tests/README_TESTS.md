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

Expect **887** tests collected (no marker deselection). Re-check after large suite changes; see `tests/TEST_AUDIT.md` → *Block 3 — Fast/full workflow verification*.

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

Expect **853** tests collected and **34** deselected (887 total). Re-verify after adding tests.

## Optional stricter fast lane (`brittle`)

When prompt- or prose-sensitive tests are too noisy locally:

```bash
pytest -m "not transcript and not slow and not brittle"
```

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
| **All tagged unit + regression** | `pytest -m "unit or regression"` |
| **Narrow legacy filter** (not equivalent to fast lane) | `pytest -m "(unit or regression) and not transcript"` — omits many integration-only modules; see `tests/TEST_AUDIT.md` |

## Marker meanings (lane-relevant)

- **unit** / **integration** / **regression** — Scope and signal density; **not** the fast-lane gate. Use for inventory, filters like `pytest -m regression`, and documentation.
- **transcript** — Transcript harness / gauntlet-style modules (**fast lane excludes**).
- **slow** — Longer or expensive runs (**fast lane excludes**).
- **brittle** — Prompt/prose-sensitive (**optional** extra exclusion for stricter fast).

Ownership markers (`routing`, `retry`, `fallback`, …) are for inventory and feature tagging only — **not** for choosing fast vs full. See `pytest.ini` for the full list.

The expression `(unit or regression) and not transcript` is **narrower** than the fast lane: many fast-eligible modules are integration-only and would be skipped.
