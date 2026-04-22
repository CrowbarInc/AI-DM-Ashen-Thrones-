# N1 — Scenario-Spine / Long-Session Validation (Test Tooling)

## Purpose

N1 provides a **separate** validation lane for **long-session continuity and branching** under the synthetic / transcript harness. It produces a **session-health artifact** that is intentionally **not** playability scoring, not a substitute for the behavioral gauntlet, and not a manual GM gauntlet replacement.

Use N1 when you need:

- Explicit **scenario spine** definitions (anchors, progression markers, revisit expectations).
- **Branch comparisons** after a **shared prefix** of player lines (same starting history, divergent suffixes).
- Deterministic, replayable **fingerprints** and **reason codes** for regression tooling.

## Boundaries

- **Test and tooling only**: modules live under `tests/helpers/` (`n1_scenario_spine_contract.py`, `n1_scenario_spine_harness.py`). Do not import these from `game/`.
- **Does not change playability authority**: N1 never calls `game.playability_eval.evaluate_playability` and does not reinterpret playability outputs. The contract in `docs/playability_validation.md` stands: playability is turn-scoped; session summaries for playability remain **final-turn-derived** only.
- **No runtime behavior changes**: observations are derived from existing harness snapshots (`SyntheticRunResult.turn_views` and related shapes). There are no test-specific hooks inside production code paths.
- **Deterministic**: `run_id`, JSON emission, and reason-code ordering avoid wall-clock inputs. `extra_scene_ids` in the deterministic fingerprint are **sorted** so tuple order does not perturb hashes.

## Non-goals

- Replacing or extending **P3 playability** artifacts or thresholds.
- Proving fun, tone quality, or model safety (see existing evaluators and gauntlets).
- Defining a second “score” for GM quality; N1 emits **flags**, **verdicts for session health**, and **machine-readable reason codes** only.

## Primary entrypoints

| Function | Role |
|----------|------|
| `build_n1_scenario_spine_definition` / `load_n1_scenario_spine_from_json` | Construct or load a spine definition. |
| `execute_n1_spine_branch_with_shared_prefix` | Wraps `run_synthetic_session` with `prefix + suffix` player lines. |
| `collect_n1_per_turn_continuity_observations` | Read-only extraction from `SyntheticRunResult`. |
| `compute_n1_session_health_summary` | Aggregates drift, anchors, progression, revisit, and scene-gap heuristics. |
| `emit_n1_session_health_artifact_dict` | Stable JSON-shaped dict for disk or CI logs. |
| `compare_n1_branch_session_health_summaries` | Cross-branch comparison (requires caller-supplied full player lines per branch). |
| `analyze_n1_longitudinal_continuity` | Longitudinal report for one `N1SessionHealthSummary` (issues, merged reason codes, counters). |
| `analyze_n1_branch_longitudinal_continuity` | Branch-only checks: shared-anchor preservation vs `forgotten_anchor_flags`, optional informational divergence from `N1BranchComparisonSummary`. |
| `tools/run_n1_scenario_spine_validation.py` | Deterministic operator CLI: list/run registered scenarios from `n1_registered_scenarios()`, emit `session_health.json` + `continuity_report.json` (+ optional `branch_comparison.json`). |

## Artifact: `n1_session_health`

Serialized via `emit_n1_session_health_artifact_dict` (keys recursively sorted for stable dumps). Core fields:

- **Identity**: `artifact_kind` (`n1_session_health`), `artifact_version`, `run_id`, `scenario_spine_id`, `branch_id`.
- **Deterministic config**: `deterministic_config` (seed, `use_fake_gm`, `max_turns`, `profile_id`, scene knobs, stall threshold).
- **Turn data**: `turn_count`, `per_turn_observations` (fingerprints and boolean hit maps; no raw GM/player text in the artifact by default).
- **Continuity**: `continuity_verdict_ok`, `continuity_verdict_notes` (scene-gap strings when present).
- **Drift flags**: `drift_flags` (`gm_text_empty_turns`, `player_text_empty_turns`).
- **Anchor / progression / revisit**: `forgotten_anchor_flags`, `progression_chain_integrity_ok` + `progression_chain_integrity_flags`, `revisit_consistency_ok` + `revisit_consistency_flags`.
- **Roll-ups**: `aggregate_issue_counts`, `final_session_verdict` (`pass` / `warn` / `fail` / `not_evaluated`), sorted `reason_codes`.

Reason codes use stable prefixes such as `N1_CONTINUITY_OK`, `N1_PROGRESSION_CHAIN_BROKEN`, `N1_FORGOTTEN_ANCHOR:<id>`, `N1_REVISIT_OK:<node>`, `N1_BRANCH_DIVERGENT_FINAL_SCENE_ID` (branch comparison), plus analyzer extensions listed under **Analyzer Semantics** below.

## Spine JSON shape (authoring)

Minimal example:

```json
{
  "metadata": {},
  "narrative_anchor_ids": ["ledger"],
  "progression_chain_step_ids": ["step_a", "step_b"],
  "revisit_expectations": [
    {
      "consistency_token": "seal",
      "revisit_node_id": "postern_gate",
      "trigger_player_substrings": ["return to the postern gate"]
    }
  ],
  "scenario_spine_id": "example_spine"
}
```

## Relationship to existing harnesses

- **Synthetic runner**: `execute_n1_spine_branch_with_shared_prefix` delegates to `tests.helpers.synthetic_runner.run_synthetic_session`.
- **Transcript runner**: Real-GM / transcript-backed runs still flow through the same runner when `use_fake_gm=False` and tmp/monkeypatch are supplied; N1 observation collection remains snapshot-driven.
- **Playability CLI / artifacts**: Unrelated output tree; do not merge N1 artifacts into `artifacts/playability_validation/` summaries.

## Analyzer Semantics (`tests/helpers/n1_continuity_analysis.py`)

The longitudinal analyzer **does not replace** `compute_n1_session_health_summary`. It consumes an existing `N1SessionHealthSummary` (and optional branch comparison) and emits a separate, JSON-serializable **`N1LongitudinalContinuityReport`** via `continuity_report_to_jsonable` / `deterministic_continuity_report_json`. Session-health **artifact** shape (`emit_n1_session_health_artifact_dict`) is unchanged.

**Inputs (structured only):** per-turn `anchor_hits`, `progression_hits`, `scene_id`, text **fingerprints** (including empty-text detection), revisit definitions, and harness booleans already on the summary. There is no prose-quality scoring, no wall-clock entropy, and no production hooks.

**Severity buckets** on each `N1ContinuityIssue`:

- **hard**: progression break, forgotten anchor (harness-aligned), revisit token mismatch, branch shared-fact loss (`N1_BRANCH_SHARED_FACT_VIOLATION:<anchor>` when an anchor appears in the shared-prefix observations of **every** compared branch but `forgotten_anchor_flags` is true on a branch).
- **soft**: GM/player empty turns, scene-gap notes, referent gap heuristic (`N1_REFERENT_INCONSISTENT:<anchor>` — anchor absent for two consecutive turns then present again **while `scene_id` stays identical**), revisit scene instability across triggers (`N1_REVISIT_SCENE_UNSTABLE:<node>`), long-session grounding degradation (`N1_NARRATIVE_GROUNDING_DEGRADED` — **heuristic** drop in any-anchor hit rate between first and second halves of the session).
- **info**: branch outcome divergence only (`N1_BRANCH_DIVERGENT_FINAL_SCENE_ID` when final `scene_id` differs across branches); this is **allowed** divergence, not a failure.

**Ordering:** `merged_reason_codes` and JSON payloads use **lexical** sorting for stable diffs. Per-issue rows are sorted by `(severity, category, reason_code, first_seen_turn, last_seen_turn)`.

**Heuristic vs strict:** Strict alignment with the harness for drift, forgotten anchors, progression integrity, and revisit token checks. Additional dimensions (referent gap, revisit scene jump, grounding slope, branch shared-fact cross-check) are **deterministic but interpretive** — documented here so CI consumers treat them as structured signals, not narrative truth.

## Regression strategy (session-health vs analyzer)

N1 regression coverage uses **two layers** that must not be conflated:

1. **`compute_n1_session_health_summary` + `emit_n1_session_health_artifact_dict`** — the **session-health** lane. It answers “did the harness flags and spine checks pass for this run?” with sorted `reason_codes`, drift tallies, and verdict fields. It is the stable **artifact** contract for long-session bookkeeping.
2. **`analyze_n1_longitudinal_continuity` / `analyze_n1_branch_longitudinal_continuity`** — the **analyzer** lane. It consumes the same structured observations (and optional branch comparison) and emits a **separate** `N1LongitudinalContinuityReport` (JSON via `deterministic_continuity_report_json`). It adds severity-bucketed **issues**, **merged_reason_codes**, and cross-branch checks without changing the session-health artifact shape.

**Why the analyzer is the primary regression signal:** Session-health summaries compress multiple dimensions into a single verdict; the analyzer exposes **per-dimension** machine codes (`N1_REFERENT_INCONSISTENT:<anchor>`, `N1_REVISIT_SCENE_UNSTABLE:<node>`, `N1_NARRATIVE_GROUNDING_DEGRADED`, branch `N1_BRANCH_SHARED_FACT_VIOLATION:<anchor>`, informational `N1_BRANCH_DIVERGENT_FINAL_SCENE_ID`) with **stable ordering** and counters. CI and tests should assert on **reason-code prefixes**, **issue categories**, **severity counts**, and **structural invariants** (sorted `merged_reason_codes`, lexically sorted JSON, issue sort key `(severity, category, reason_code, first_seen_turn, last_seen_turn)`), not on GM prose or raw player text.

**Example expectations (fixtures under `tests/helpers/n1_scenarios.py`):**

| Fixture role | Expect (merged / issues) | Branch analyzer (when applicable) |
|--------------|--------------------------|-----------------------------------|
| Anchor persistence | No `N1_REFERENT_INCONSISTENT:`; no `N1_NARRATIVE_GROUNDING_DEGRADED`; no `N1_FORGOTTEN_ANCHOR:` | — |
| Revisit / investigation | No `N1_REVISIT_SCENE_UNSTABLE:`; harness revisit flags clean | — |
| Progression chain | No `N1_PROGRESSION_CHAIN_BROKEN` | — |
| Branching (shared prefix) | Per-branch longitudinal clean of branch-violation codes | No `N1_BRANCH_SHARED_FACT_VIOLATION:`; **include** informational `N1_BRANCH_DIVERGENT_FINAL_SCENE_ID` when final `scene_id` differs by design |

**Synthetic runner note:** Deterministic fake-GM snapshots may attach `scene_id` from the fake responder payload when present (test-only), so branch divergence checks can observe distinct finals without touching `game/` or the N1 harness collection rules.

## CLI (`tools/run_n1_scenario_spine_validation.py`)

Deterministic operator entrypoint (adds repo root to `sys.path`, imports `tests.helpers.n1_scenarios` only — no duplicated fixture/analyzer logic).

**Exit codes:** `0` success (no branch verdict `fail`); `1` at least one `fail` verdict in a `run`; `2` operator/config error (stderr lines prefixed with `error:`).

### Commands

- **List** registered scenarios (stable `scenario_id` order, stable `branches` sub-order):

```bash
python tools/run_n1_scenario_spine_validation.py list
python tools/run_n1_scenario_spine_validation.py list --json
```

- **Run** requires **exactly one** of `--scenario <id>` or `--all` (mutually exclusive). Artifacts default under `artifacts/n1_scenario_spine_validation/` (override with `--artifact-dir`, which is created if missing).

```bash
python tools/run_n1_scenario_spine_validation.py run --scenario n1_progression_chain
python tools/run_n1_scenario_spine_validation.py run --scenario n1_branch_divergence --branch n1_branch_left
python tools/run_n1_scenario_spine_validation.py run --scenario n1_branch_divergence --compare-branches
python tools/run_n1_scenario_spine_validation.py run --all
```

Optional knobs: `--seed <int>`, `--max-turns <int>` (must be a **positive** integer **≥** the scenario’s scripted player-line minimum; the synthetic runner still executes exactly the scripted prefix+suffix lines — this field remains part of the deterministic fingerprint).

### Common operator mistakes

| Mistake | What the CLI expects |
|---------|----------------------|
| Unknown `scenario_id` | Use `list` / `list --json`; ids are the `scenario_id` field from `tests/helpers/n1_scenarios.py`. |
| `--branch` on a linear fixture with a fork-only id | Linear scenarios expose a single branch id (`n1_main` today); fork ids such as `n1_branch_left` are only valid for `n1_branch_divergence`. |
| `--compare-branches` on a linear scenario | Only `n1_branch_divergence` supports compare; omit the flag for linear fixtures. |
| Multi-branch scenario without `--branch` or `--compare-branches` | For `n1_branch_divergence` alone, pass `--branch n1_branch_left` or `n1_branch_right`, or `--compare-branches`. |
| `--max-turns` too low | Must be ≥ scripted line count for that scenario (error names the minimum). Non-integers / values `< 1` are rejected before the run. |

Stdout is **one line per executed branch**, plus **one aggregate line** after `--compare-branches`, using stable `key=value` fields (`scenario_id`, `branch_id`, `run_id`, `final_session_verdict`, `severity_counters`, `merged_reason_codes_top`, `session_health`, `continuity_report`, `branch_comparison`). Compare-only summaries use sentinel placeholders (`*compare*`, `*multi*`) where a single branch does not apply; per-branch paths use `-` where not applicable. Full transcripts are never printed.

### Artifact layout

Under `<artifact-dir>/<scenario_id>/`:

- **Per branch directory** `<branch_id>/`:
  - `session_health.json` — **harness artifact** only (`emit_n1_session_health_artifact_dict`); canonical bookkeeping for spine checks, drift tallies, and sorted harness `reason_codes`. This file is **not** the enriched longitudinal report.
  - `continuity_report.json` — **primary interpreted N1 signal** from `deterministic_continuity_report_json` / `analyze_n1_longitudinal_continuity` (severity-bucketed issues, merged codes, counters). It is **never** embedded inside `session_health.json`.

- **Linear / single-branch runs:** only the per-branch directory above — **no** `branch_comparison.json`.

- **Branching compare runs** (`--compare-branches` on `n1_branch_divergence`, or the branching leg of `run --all`): additionally

  - `branch_comparison.json` — harness `compare_n1_branch_session_health_summaries` plus `analyze_n1_branch_longitudinal_continuity` issues, emitted **once** beside branch subfolders (not merged into per-branch session health). Not emitted for linear scenarios or for single-branch runs of a branching scenario.

### Canonical scenario source

Registered scenario ids, spines, branch points, and scripted player lines remain **code-defined** in `tests/helpers/n1_scenarios.py` (`N1RegisteredScenario` / `n1_registered_scenarios()`). The CLI does not ship parallel JSON scenario corpora; coverage is intentionally limited to those **four** deterministic fixtures today.

### Governance

`tests/validation_coverage_registry.py` records this lane under **integration smoke** as longitudinal continuity / scenario-spine validation tooling — explicitly **not** a playability substitute or runtime gameplay evaluator.
