# Running tests

## Test ownership rules (Blocks A–D)

These rules keep the suite maintainable without turning CI into a heavy transcript or harness gate.

- **Direct-owner tests** — Each governed seam has a **practical primary direct-owner** module (see `tests/TEST_AUDIT.md` and `tests/TEST_CONSOLIDATION_PLAN.md`). Those files own **detailed invariants** (schemas, layer order, legality families, helper semantics). Extend the owner first; avoid parallel “second homes” for the same contract.
- **Smoke tests** — Cross-layer and pipeline modules should assert **wiring and orchestration** only (routes, sequencing, presence of keys, thin post-transform smoke). They must not grow into duplicate full **legality matrices** already owned elsewhere.
- **Transcript tests** — Transcript- and harness-backed modules preserve **multi-turn story, ordering, and playability** behavior. Prefer structural or milestone checks over re-locking strings that a direct owner already pins.
- **Gauntlets and playability validation** — Behavioral gauntlets, manual gauntlets, and playability suites remain **end-to-end or slice harnesses** for behavior in motion; they complement—not replace—focused pytest owners.
- **Evaluators** — Offline evaluators (for example behavioral gauntlet and playability helpers) **score** deterministic slices; they must **not** become live **legality enforcement** or gate substitutes.
- **Downstream consumer suites** — Verify that a consumer **observes or ships** behavior through an owner boundary; they are **not** alternate homes for canonical invariants.
- **Compatibility residue suites** — Intentionally preserved historical coverage; **not** canonical ownership.
- **`general` in inventory** — `likely_architecture_layer: general` is a **weak heuristic bucket**, not a validation layer. Direct owners with a declared validation layer must not rest on `general` in the inventory (enforced by `tests/test_ownership_registry.py`).
- **New validation rules** — Before adding **broad** coverage across many files, add or extend **one canonical owner** for the new rule, then optional smoke elsewhere. `tests/test_ownership_registry.py` locks the responsibility registry (exactly one **direct_owner** path per governed slice, inventory presence, layer alignment, and **no transcript/gauntlet/playability/evaluator** module as direct owner for **live legality** groups). Cross-file duplicate `test_*` **base names** stay **heuristic** triage in `tests/test_inventory.json` (allowlisted pairs require reasons); see `tests/TEST_AUDIT.md`.

**Quick maintenance loop (local, low noise):** `py -3 tools/test_audit.py` → `py -3 -m pytest tests/test_ownership_registry.py -q` → `py -3 -m pytest --collect-only -q` → day-to-day `py -3 -m pytest -m "not transcript and not slow" -q`. Details: *Command cheat sheet* below and `tests/TEST_AUDIT.md`.

**Block C prompt / strict-social split (final):** strict-social **first-sentence** and **question-resolution** legality matrices live in `tests/test_social_exchange_emission.py`. `tests/test_prompt_and_guard.py` keeps **retry prompt text** for unresolved-question / social-contract failures, **`enforce_question_resolution_rule` prepend** behavior, **validator-voice detect/rewrite** at the GM layer, and thin smoke near the prompt stack for that boundary. **`apply_final_emission_gate` orchestration** remains owned by `tests/test_final_emission_gate.py`.

## Objective #12 — validation coverage (contributor workflow)

Objective #12 is **governance and tooling only**: it does **not** add a runtime layer, a policy engine, or a new scoring path.

- **`tests/validation_coverage_registry.py`** is the **canonical declaration layer** — one row per feature/domain, with `required_surfaces` and typed pointers (transcript modules, behavioral axes, manual gauntlet IDs, playability smoke node IDs, unit/integration paths). Human intent and machine checks both anchor here; update this file when coverage ownership changes.
- **`tools/validation_coverage_audit.py`** is the **canonical inspection layer** — reads the committed registry, runs `validate_entries`, prints summaries, per-feature views, surface filters, and declarative “likely commands”. It does **not** import `game/` or run evaluators.
- **Existing evaluators and harnesses** (for example `evaluate_playability`, `evaluate_behavioral_gauntlet`, transcript runners, manual rubrics) remain the **only scoring authorities**. The registry maps *what to run*; it does not rescore turns.
- **`optional_smoke_overlap`** is **secondary** to canonical ownership: use it for extra smoke pointers without pretending they own the feature’s defense.

**Repeatable loop:** validation-sensitive change → declare/update `tests/validation_coverage_registry.py` → `py -3 -m pytest tests/test_validation_coverage_registry.py -q` → `python tools/validation_coverage_audit.py --feature <feature_id>` → run the emitted tests/tools/scenarios → manual gauntlets when feel, prose, or player-facing behavior changed materially. Contract detail: [`docs/objective12_validation_contract.md`](../docs/objective12_validation_contract.md).

## Planner convergence — static audit (Block D)

Author-time only; **no runtime behavior**. Full maintainer notes: [`docs/planner_convergence.md`](../docs/planner_convergence.md).

**Audit:**

```bash
python tools/planner_convergence_audit.py
```

**Focused pytest** (contracts + manual-play convergence structure + plan-only prompt + static audit tests):

```bash
py -3 -m pytest tests/test_planner_convergence_contract.py tests/test_planner_convergence_live_pipeline.py tests/test_prompt_context_plan_only_convergence.py tests/test_planner_convergence_static_audit.py
```

**Optional Make** (same audit + same four tests): `make planner-convergence-check` from repo root.

CI runs the audit in `.github/workflows/content-lint.yml` (step **Planner convergence static audit**).

**Copy/paste — registry pytest and audit CLI** (repo root; if `pytest` is not on `PATH`, use `py -3 -m pytest`):

```bash
py -3 -m pytest tests/test_validation_coverage_registry.py -q

python tools/validation_coverage_audit.py
python tools/validation_coverage_audit.py --strict

python tools/validation_coverage_audit.py --feature <feature_id>

python tools/validation_coverage_audit.py --missing transcript
python tools/validation_coverage_audit.py --missing behavioral_gauntlet

python tools/validation_coverage_audit.py --surface playability
```

`--surface` / `--missing` accept the same surface ids as the registry: `transcript`, `behavioral_gauntlet`, `manual_gauntlet`, `playability`, `unit_contract`, `integration_smoke` (the CLI also accepts hyphenated forms, e.g. `behavioral-gauntlet`). **`--strict`:** exit code **2** if `validate_entries` finds issues. For **`--feature`**, **`--surface`**, and **`--missing`**, when `--strict` is set and there are errors, the tool writes errors to **stderr** and exits **2** before printing the requested feature/surface list; the default **summary** (no mode flags) prints the full summary first, then reports validation OK/FAIL.

**Full lane** runs the whole suite. **Fast lane** excludes items marked `transcript` or `slow`. **Stricter fast** also excludes `brittle`. Marker definitions live in `pytest.ini`; scope and ownership notes are in `tests/TEST_AUDIT.md`. Routing and **repair/retry regression** ownership are settled (see `tests/TEST_CONSOLIDATION_PLAN.md` → *Block 3 — Routing* and *Repair / retry cluster — Block 3*).

**Post-AER Block C1:** Behavioral Gauntlet, Playability Validation, and AER are **complete** as validation tracks. Consolidation PRs target **orchestration** clarity, **telemetry/meta** normalization, and **test ownership** (**canonical owner** per module, **smoke overlap** only where layers differ)—see `docs/current_focus.md` and `docs/narrative_integrity_architecture.md` (**Post-AER Consolidation Rules**).

**Windows:** If `pytest` is not on your `PATH`, use `py -3 -m pytest` instead of `pytest` for every command below (for example `py -3 -m pytest -m "not transcript and not slow"`).

## Manual gauntlets (outside pytest)

Manual gauntlets are **not** part of pytest selection. Use them after changes that can **feel wrong in play** (lead follow-up, narration voice, speaker grounding, scene transitions) even when automated tests pass. Named scenarios, exact player prompt sequences, and pass/fail criteria live in [`docs/manual_gauntlets.md`](../docs/manual_gauntlets.md); the CLI surface is [`tools/run_manual_gauntlet.py`](../tools/run_manual_gauntlet.py).

## Behavioral gauntlet coverage (complete)

This repo has a **deterministic**, **contract-driven behavioral gauntlet stack** for compact narration-behavior checks (validation track — **complete**). The main pieces are:

- Evaluator helper: `tests/helpers/behavioral_gauntlet_eval.py`
- Behavioral smoke tests: `tests/test_behavioral_gauntlet_smoke.py`
- Manual gauntlet source of truth: `docs/manual_gauntlets.md`
- Manual gauntlet runner: `tools/run_manual_gauntlet.py`

The evaluator covers four explicit axes:

- `neutrality`
- `escalation_correctness`
- `reengagement_quality`
- `dialogue_coherence`

### Automated smoke lane

`tests/test_behavioral_gauntlet_smoke.py` is marked `integration` and `regression`.

- **Layer A** uses direct simplified transcript rows.
- **Layer B** uses gauntlet-style payload compatibility slices.
- The lane is deterministic.
- It makes **no GPT calls**.
- It has **no transcript-runner dependency**.

The helper contract lives in `evaluate_behavioral_gauntlet(turns, *, expected_axis=None) -> dict` and is locked directly by `tests/test_behavioral_gauntlet_eval.py`.

### Manual gauntlet integration

Behavioral gauntlets `G9` through `G12` are available in the manual gauntlet registry.

`summary.json` may include:

- `axis_tags`
- advisory `behavioral_eval`
- `behavioral_eval_warning`

Behavioral evaluation in manual reports is **advisory only**. It helps reviewers spot narration-behavior seams, but it does **not** determine manual pass/fail by itself.

- For `G9` through `G12`, `behavioral_eval` is filtered to the gauntlet's tagged axis or axes.
- For gauntlets without `axis_tags`, `behavioral_eval` includes the full axis set.

### Transcript shaping behavior

Manual report attachment prefers simplified behavioral rows derived from snapshot-shaped records. If that shaping path fails for a row, the fallback path preserves the raw dict row instead. Evaluator failures are turned into compact warnings in `behavioral_eval_warning` and do **not** fail the gauntlet run.

### What this is / is not

**What this is:**

- deterministic behavior-in-motion smoke coverage
- advisory behavioral scoring for manual gauntlet reports
- compact transcript-slice evaluation
- regression support for narration-behavior seams

**What this is not:**

- not a live-model evaluation lane
- not a full transcript-runner lane
- not a replacement for human feel checks
- not a full playability certification
- not a new runtime architecture layer

### Recommended validation order

After narration / behavior changes:

1. Run the behavioral evaluator and smoke tests.
2. Run gauntlet regressions and manual report tests.
3. Run manual gauntlet spot-checks if prose feel materially changed.

Copy/paste commands:

```bash
py -3 -m pytest tests/test_behavioral_gauntlet_eval.py tests/test_behavioral_gauntlet_smoke.py -q
py -3 -m pytest tests/test_manual_gauntlet_report.py tests/test_manual_gauntlet_aggregation.py -q
py -3 tools/run_manual_gauntlet.py --list
```

## Playability tests (complete)

### Playability Tests

**Location:** `tests/test_playability_smoke.py`

**Status:** **Complete** as a validation layer—the suite remains the **canonical owner** for turn-scoped playability checks.

**Characteristics:**

- integration-level
- evaluator-driven
- non-brittle assertions

These tests:

- validate behavioral quality
- do **not** enforce exact phrasing
- rely entirely on `evaluate_playability(...)`

### Important Notes

- The escalation test includes a **scoped** emission-gate bypass (`apply_final_emission_gate`), required to observe meaningful variation across pressured turns
- Other tests use the full pipeline unmodified

### Commands

```bash
pytest tests/test_playability_smoke.py -q
```

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

Exact suite counts change over time; use the collect-only output and `tests/test_inventory.json` → `summary.pytest_collected_items` (regenerate via `py -3 tools/test_audit.py`) as the source of truth after large suite changes. See `tests/TEST_AUDIT.md` → *Block 3 — Fast/full workflow verification*.

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

Exact counts drift as modules are added; prefer the live collect-only output over hard-coded numbers.

## Optional stricter fast lane (`brittle`)

When prompt- or prose-sensitive tests are too noisy locally:

```bash
pytest -m "not transcript and not slow and not brittle"
```

## Synthetic-player harness (`synthetic`)

The synthetic-player helpers under `tests/helpers/` are **test/tooling infrastructure only** (no `game/` coupling in the scaffold). They are meant to drive or evaluate automated “synthetic players” alongside `tests/helpers/transcript_runner.py`, not to add gameplay modes.

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

When recording **which scenarios defend which feature** (Objective #12), update `tests/validation_coverage_registry.py` per [`docs/objective12_validation_contract.md`](../docs/objective12_validation_contract.md).

See `tests/TEST_AUDIT.md` → *Consolidation Block 1 — Canonical ownership map & overlap hotspots* for **canonical owner** themes and **smoke overlap** guidance. **Test ownership & audit (Blocks A–D)** are **complete** for the consolidation pass: **inventory schema v2** (`summary.inventory_schema_version`, `declared_pytest_markers`, per-file `likely_architecture_layer`, `marker_set`, `ownership_registry_positions`, top-level `ownership_registry_index`, `block_b_overlap_clusters`, `import_hub_modules`) plus governance pytest and doc pointers; see *Test ownership rules* above and `tests/TEST_CONSOLIDATION_PLAN.md` → *Test Ownership & Coverage Consolidation*. **Next consolidation order (Block C1):** emit-path **orchestration** / metadata + **telemetry** alignment (doc-driven) → prompt/sanitizer → social/emission → transcript duplicate assertion thinning → **lead/clue `deferred`** last (repair/retry cluster documented and closed enough — see `tests/TEST_CONSOLIDATION_PLAN.md` → *Next consolidation order* and *Repair / retry cluster — Block 3*).

## Command cheat sheet

| Goal | Command |
|------|---------|
| **Test audit (regenerate inventory)** | `py -3 tools/test_audit.py` |
| **Ownership registry governance** | `py -3 -m pytest tests/test_ownership_registry.py -q` |
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
