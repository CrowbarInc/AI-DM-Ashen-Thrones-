# Running tests

Markers are declared in `pytest.ini`. Module-level `pytestmark` carries scope (`unit` / `integration` / `regression`) and lane markers (`transcript`, `slow`, `brittle`) per `tests/TEST_AUDIT.md`.

**Where to add new tests:** See `tests/TEST_AUDIT.md` → *Consolidation Block 1 — Canonical ownership map & overlap hotspots* for canonical owners by theme (routing, social, leads/clues, transcript vs focused, repair/legality). For **routing** specifically, the three-module split is recorded in `tests/TEST_CONSOLIDATION_PLAN.md` → *Block 3 — Routing ownership (consolidation pass closed)*. See the same file for the **next consolidation order** after routing.

## What “trustworthy” means for fast vs full

**Lane trustworthiness is about correct composition and selection** — which tests are included or excluded by markers — **not** about the whole suite being green. A failing test in the fast lane is still a real failure; it is simply **orthogonal** to whether the fast/full split matches intent (exclude transcript harness and slow modules from fast; run everything on full).

## Fast lane

**Purpose:** Day-to-day feedback: run most of the suite without transcript-harness modules and modules explicitly marked `slow`.

**Selection:** Everything **except** tests on items marked `transcript` or `slow` (module- or test-level marks both apply).

**Command** (from repo root):

```bash
pytest -m "not transcript and not slow"
```

**Sanity check (collection only):**

```bash
pytest --collect-only -m "not transcript and not slow" -q
```

Expect **853 tests collected** and **34 deselected** (suite size **887** total) — re-verify after adding tests; see `tests/TEST_AUDIT.md` (Block 3) for the last recorded numbers.

## Full lane (authoritative)

**Purpose:** Pre-merge, milestone, or CI confidence: **the full regression surface**, including transcript replay, gauntlets, and expensive flows. This is the authoritative “all tests” path.

**Command:**

```bash
pytest
```

Equivalent explicit path:

```bash
pytest tests/
```

**Sanity check (collection only):**

```bash
pytest --collect-only -q
```

Expect **887 tests collected** (no marker deselection).

## Optional stricter local run (brittle)

If prompt- or prose-sensitive tests are too noisy locally, narrow further:

```bash
pytest -m "not transcript and not slow and not brittle"
```

## Known baseline failures (outside lane work)

These failures **reproduce with the same three tests** whether you run the fast lane or the full suite. They are **pre-existing** relative to fast/full marker normalization and should be **fixed or quarantined in a separate task** — not interpreted as “the lanes are wrong.”

After the routing consolidation pass (Block 3), **fast-lane failures still come from** `tests/test_social_destination_redirect_leads.py` — not from routing test ownership or the routing-module split. Treat destination-redirect / pending-lead baseline work as orthogonal to routing consolidation.

| Module | Notes |
|--------|--------|
| `tests/test_social_destination_redirect_leads.py` | Three failing tests (destination redirect / pending lead behavior). Unrelated to transcript vs slow selection and unrelated to routing consolidation. |

## Common commands (reference)

| Goal | Command |
|------|---------|
| **Fast lane** | `pytest -m "not transcript and not slow"` |
| **Stricter fast** (optional) | `pytest -m "not transcript and not slow and not brittle"` |
| **Full suite** | `pytest` or `pytest tests/` |
| **Legacy / partial** (only `unit` or `regression`; narrower than fast lane) | `pytest -m "(unit or regression) and not transcript"` |
| **All tagged unit + regression** | `pytest -m "unit or regression"` |
| **Exclude transcript only** | `pytest -m "not transcript"` |
| **Transcript / gauntlet slice** | `pytest -m "transcript"` |
| **Slow slice** (profiling / nightly) | `pytest -m "slow"` |

## Marker meanings

- **unit** — Small scope, mostly pure logic or tight helpers.
- **integration** — HTTP/API, storage, or multi-step pipeline through the app.
- **regression** — Locks for previously fixed bugs or fragile behavior.
- **transcript** — Multi-turn transcript harness or transcript gauntlet modules (**fast lane excludes**).
- **slow** — Longer runs (large gauntlets, many turns; **fast lane excludes**).
- **brittle** — Sensitive to prompt wording or prose shape (**optional** fast-lane exclusion).

Ownership markers (`routing`, `retry`, `fallback`, …) are for feature ownership and inventory tooling — **not** for choosing fast vs full lanes. See `pytest.ini` for the full list.

The `(unit or regression)` filter is intentionally **narrower** than the fast lane: many integration-only modules are fast-eligible but would be omitted by that expression.
