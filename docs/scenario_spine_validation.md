# Scenario-spine / long-session validation

This document describes the **game-level** scenario-spine lane: JSON-defined spines (`game/scenario_spine.py`), deterministic session health (`game/scenario_spine_eval.py`), and the API harness `tools/run_scenario_spine_validation.py`.

It is **not** the N1 synthetic harness documented in [`docs/n1_scenario_spine_validation.md`](n1_scenario_spine_validation.md) (`tests/helpers/`, `tools/run_n1_scenario_spine_validation.py`). N1 stays test-only and separate; this lane drives **`POST /api/chat`** (in-process `TestClient` or `--base-url`) and records GM-facing text for the same evaluator the runner calls after the scripted turns complete.

## What this validation proves

Multi-turn, spine-shaped evidence that the stack can sustain:

- **Sustained continuity** — Scene pressure, cast, and location threads stay recognizable across many turns; hard reset language in GM text is flagged after early turns.
- **Referent persistence** — Named clues, officers, notices, and similar anchors are not contradicted after they appear in prior GM text (pattern-banked “unknown/denied” phrases).
- **World / project progression** — Progression anchors tied to checkpoints show keyword-level evidence in checkpoint windows; gross contradictions after positive signals surface as warnings.
- **Narrative grounding** — Player-facing GM text should not leak debug/system markers or raw JSON diagnostic lines; long runs flag excessive generic filler as warnings.
- **Branch coherence** — GM narration should not echo long distinctive substrings from **other** branches’ scripted player prompts (cross-branch bleed).

## What it does not prove

- **Fun** or engagement — No enjoyment metric; scripted prompts only.
- **Complete campaign readiness** — One fixture and a small branch set cannot cover a full product release.
- **Total rules correctness** — PF1e or engine mechanics are out of scope for this evaluator.
- **All possible player behavior** — Only the scripted `player_prompt` lines in the spine JSON are exercised.

## How this differs from per-turn playability validation

| Aspect | Playability (`docs/playability_validation.md`) | Scenario-spine (this doc) |
|--------|-----------------------------------------------|---------------------------|
| Evaluator | `evaluate_playability` per turn | `evaluate_scenario_spine_session` once per branch run |
| Session summary | Derived from the **final** turn’s playability output | Native **`session_health`** object in evaluator output |
| Primary signal | Turn-scoped behavioral axes | Cross-turn continuity, anchors, checkpoints, branch isolation |
| Typical use | Short scenarios, axis exemplars | Long scripted branches, branch comparison from shared fixture |

Both runners record transcripts and attach evaluator output; neither runner re-scores or overrides the evaluator.

## Deterministic evaluation (no LLM in the health lane)

Session health, **`degradation_over_time`** (early / middle / late windows, progressive signal codes), and **`evaluate_scenario_spine_branch_divergence`** (token overlap, consequence lexicon tags, scripted-player bleed checks) are **fixed heuristics** over recorded GM text and prompts. They do not call an external model for scoring.

The **CLI runner** still needs something to produce `gm_text` for each turn: in-process `TestClient` hits the real app stack (which may call a configured model), or `--base-url` posts to a live server. That is separate from evaluator determinism.

## Spine model: `fixed_start_state`, branches, anchors, checkpoints

Definitions live in `game/scenario_spine.py` and JSON fixtures under `data/validation/scenario_spines/`.

- **`fixed_start_state`** — JSON object describing the intended starting diegetic pressure (tone, scene, arrival, opening problem). It is **authoring context** for humans and tools; the harness still applies `apply_new_campaign_hard_reset()` before each branch unless `--no-reset`. It does not inject state by itself.
- **`branches`** — Ordered lists of `ScenarioTurn` (`turn_id`, `player_prompt`). Each branch is one scripted path. Canonical fixture `frontier_gate_long_session.json` defines three branches (see below).
- **`continuity_anchors`** — What should remain recognizable (location, active problem, NPC cast, scene objective). Used for checkpoint windows and late-window weak/absent checks.
- **`referent_anchors`** — Stable entities (notice, captain, clue, faction subtext). Used for establishment vs denial patterns and late-window referent presence.
- **`progression_anchors`** — Expected world/project movement (patrol investigation deepens, watch tightens). Keywords are derived for checkpoint windows and contradiction heuristics.
- **`checkpoints`** — Ordered gates that reference anchor ids. The evaluator splits the transcript into windows and tests referenced anchors per checkpoint; results appear in `checkpoint_results` (`passed`, `issues` with codes such as `continuity_weak`, `referent_weak`, `progression_missing`).

Schema validation (`validate_scenario_spine_definition`) requires at least one branch with **≥ 20 turns** unless `smoke_only` is true on the spine.

## Runner and evaluator: health authority

`tools/run_scenario_spine_validation.py`:

1. Loads and validates the spine JSON.
2. For each selected branch, optionally resets the campaign, then posts each scripted `player_prompt` to `/api/chat`.
3. Builds per-turn rows (`gm_text`, `api_ok`, etc.) and calls **`evaluate_scenario_spine_session(spine, branch_id, turns)`** once.
4. Writes **`session_health_summary.json`** as the **full** evaluator return value (no pass/fail rewriting).

**Branch-level authority:** `session_health_summary.json` under each `…/<branch_id>/` is the single health report for that branch. `compact_operator_summary.md` is a human-oriented view of the same data (tables, top failures/warnings, suggested debug focus). `transcript.json` and `run_debug.json` are evidence trails.

**Cross-branch authority (`--all-branches` only):** `aggregate_session_health_summary.json` rolls up per-branch metrics, copies **`degradation_over_time`** from each branch into **`degradation_over_time_by_branch`**, and sets **`branch_divergence`** from **`evaluate_scenario_spine_branch_divergence(spine, transcripts)`** using the recorded turn rows (same starting state when the runner resets between branches). **`aggregate_operator_summary.md`** is the operator-facing markdown rollup (branch table, coverage note, divergence block, per-branch degradation lines, top blocking hint).

Single-branch runs (default branch, explicit `--branch`, or `--list`) do **not** write the aggregate files.

## Canonical fixture and branch roles

**File:** `data/validation/scenario_spines/frontier_gate_long_session.json`  
**Spine id:** `frontier_gate_long_session`

| Branch id | Scripted turns | Role |
|-----------|----------------|------|
| `branch_social_inquiry` | **25** | Primary **long / full-session** path: default when `--branch` is omitted; meets schema “≥ 20 turns” for serious continuity capture. |
| `branch_direct_intrusion` | **25** | Second **long** alternate — forced access, roster pressure, cordon, and watch backlash (same `fixed_start_state`, divergent player beats from social inquiry). |
| `branch_cautious_observe` | **10** | **Short** alternate — cautious observation beats; divergence + wiring vs long branches, not a ≥20-turn path. |

**Long-session / coverage intent:** Operator “Scenario-Spine Expansion” targets **40–60 executed turns summed across every branch whose spine definition has ≥ 20 scripted turns**, when each of those branches is run **full length** (no `--smoke`, no partial `--max-turns`), and compares divergent outcomes from the **same** `fixed_start_state` after per-branch reset. See **`coverage_band_met`** below.

**Fixture status (Scenario-Spine Expansion):** **`branch_social_inquiry`** (25) and **`branch_direct_intrusion`** (25) each have ≥ 20 scripted turns; the long-branch scripted total is **50**, inside the **40–60** band, so a canonical full **`--all-branches`** run (no smoke, every long branch executed to full length) can report **`coverage_band_met: true`** subject to the aggregate conditions in the next section. **`branch_cautious_observe`** remains short (10 turns) for contrast and harness checks.

### CLI branch aliases (optional)

The runner and evaluator resolve these aliases to canonical ids; **prefer canonical ids in docs and scripts:**

| Alias | Canonical id |
|-------|----------------|
| `social_investigation` | `branch_social_inquiry` |
| `direct_intrusion` | `branch_direct_intrusion` |
| `cautious_observation` | `branch_cautious_observe` |

## Defaults

- **Spine:** `data/validation/scenario_spines/frontier_gate_long_session.json` (or pass `--spine PATH_OR_ID`; bare id resolves under `data/validation/scenario_spines/<id>.json`).
- **Branch** when neither `--branch` nor `--all-branches`: **`branch_social_inquiry`**.
- **Artifact root:** `artifacts/scenario_spine_validation/` (override with `--artifact-dir`).

## Artifact layout

Each run uses a UTC timestamp folder, then spine id, then **resolved** branch id:

```text
artifacts/scenario_spine_validation/<UTC>/<spine_id>/<branch_id>/
```

Example:

```text
artifacts/scenario_spine_validation/20260423T120000Z/frontier_gate_long_session/branch_social_inquiry/
```

### All-branches aggregate (spine level)

When you pass **`--all-branches`**, the runner also writes spine-level summaries next to the branch folders (same `<UTC>/<spine_id>/` directory, not inside each `branch_id`):

| File | Role |
|------|------|
| `aggregate_session_health_summary.json` | Cross-branch JSON: `schema_version`, `spine_id`, `run_timestamp`, `branches_run`, `branch_turn_counts`, `total_executed_turns`, `long_branch_count`, **`coverage_band_met`**, **`all_full_length_branches_passed`**, per-branch `branch_classifications` / `branch_failures` / `branch_warnings`, **`degradation_over_time_by_branch`**, **`branch_divergence`**, and **`aggregate_meta`** (`smoke`, `max_turns`, `coverage_turn_total_long_scripted_branches`, `long_scripted_branch_ids`, `long_targets_complete`, `long_targets_all_passed`). |
| `aggregate_operator_summary.md` | Operator markdown: branch table (scripted vs executed turns, classification, score, progressive degradation flag), coverage line reflecting `coverage_band_met`, divergence block, per-branch degradation summary, top blocking branch/axis hint. |

Per-branch **`session_health_summary.json`** includes evaluator fields such as **`schema_version`**, **`degradation_over_time`** (windowed signals, **`progressive_degradation_detected`**, **`reason_codes`**), and **`session_health`** flags including **`full_length_branch`**, **`scripted_turn_count`**, **`long_session_band`**, and **`degradation_detected`**.

### `coverage_band_met` (aggregate)

`build_aggregate_session_health_summary` in `tools/run_scenario_spine_validation.py` sets **`coverage_band_met`** to **true** only when **all** of the following hold:

- The run is **not** `--smoke`.
- There is **at least one** branch whose **`scripted_turn_count` ≥ 20** (a “long scripted” branch).
- **Every** such long-scripted branch completed as **`full_length_branch`** in its session health (executed turns ≥ scripted count for that branch).
- The **sum** of **`turn_count`** over those long-scripted branches is **between 40 and 60 inclusive**.

With the **current** fixture, **`branch_social_inquiry`** and **`branch_direct_intrusion`** qualify as long-scripted (**25** turns each); the long-branch scripted sum is **50**, so **`coverage_band_met` can be true** for a canonical full `--all-branches` run when the run is not `--smoke`, every long branch completes at full length (`full_length_branch`), and the executed turn counts on those branches fall in the **40–60** band (see implementation in `build_aggregate_session_health_summary`).

Files in each `branch_id` directory:

| File | Role |
|------|------|
| `transcript.json` | Schema version, spine/branch ids, `turns[]` with `player_prompt`, `gm_text`, `api_ok`, `resolution_kind`, etc. (suitable for sharing without full `chat_response`). |
| `session_health_summary.json` | **Full** return value of `evaluate_scenario_spine_session` — `session_health`, **`degradation_over_time`**, `axes`, `detected_failures`, `warnings`, `checkpoint_results`. |
| `run_debug.json` | Per-turn debug: includes `debug_traces` when present and **full** `chat_response` per turn — large; use for deep API debugging. |
| `compact_operator_summary.md` | Markdown summary: classification, score, axis table, top failures/warnings, first failing checkpoint, suggested debug focus. |

## Smoke vs full branch validation

- **`--smoke`** — Caps executed turns to **5**, or fewer if `--max-turns` is set lower. Same evaluator and artifacts; scope is short for wiring checks. Aggregate **`coverage_band_met`** stays **false**.
- **Full branch** — Omit `--smoke` (and optionally omit `--max-turns`) to run all scripted turns in the branch up to the branch length.

Without `--base-url`, the runner uses FastAPI `TestClient` against the in-process app (full HTTP stack; model usage depends on project configuration). With `--base-url`, it POSTs to `{base}/api/chat`.

## Commands

From repo root:

```bash
python tools/run_scenario_spine_validation.py --list
python tools/run_scenario_spine_validation.py --branch branch_social_inquiry --smoke
python tools/run_scenario_spine_validation.py --branch branch_social_inquiry
python tools/run_scenario_spine_validation.py --all-branches
python tools/run_scenario_spine_validation.py --base-url http://127.0.0.1:8000 --branch branch_social_inquiry
```

Omitting `--branch` runs the default branch (`branch_social_inquiry`) with full turns (unless `--smoke` / `--max-turns`).

### Windows

If `python` is not on `PATH`:

```powershell
py -3 tools/run_scenario_spine_validation.py --list
py -3 tools/run_scenario_spine_validation.py --branch branch_social_inquiry --smoke
```

Other useful flags: `--no-reset`, `--artifact-dir PATH`, `--http-timeout SEC` (with `--base-url`), `--max-turns N`.

## Interpreting artifacts

### `transcript.json`

- Confirms which prompts ran and order (`turn_index`, `turn_id`).
- `gm_text` is what the evaluator saw (`gm_output.player_facing_text` when present).
- `api_ok` / `api_error` show transport or API-level failures — majority `api_ok=false` becomes a **session**-level failure in the evaluator.

### `session_health_summary.json`

- **`session_health`:** `overall_passed`, `score`, `classification` (`clean`, `warning`, `degraded`, `failed` — see evaluator `_classify` in `game/scenario_spine_eval.py`). `overall_passed` is true for **`clean`** and **`warning`**. Also **`full_length_branch`**, **`scripted_turn_count`**, **`long_session_band`**, **`degradation_detected`** (any degradation signal presence).
- **`degradation_over_time`:** Early / middle / late window **`signals`**, **`progressive_degradation_detected`**, and **`reason_codes`** — use for “session got worse over time” triage without subjective scoring.
- **`axes`:** Per-axis `passed`, `failure_codes`, `warning_codes` for: `state_continuity`, `referent_persistence`, `world_project_progression`, `narrative_grounding`, `branch_coherence`.
- **`detected_failures` / `warnings`:** List of `{axis, code, detail, ...}` entries — primary list for triage.
- **`checkpoint_results`:** Per-checkpoint `passed`, `window_end_turn_index`, `issues` with structured codes.

### `aggregate_session_health_summary.json`

- **`branch_divergence`:** `distinct_outcomes_detected`, `divergence_score`, `shared_prompt_bleed_detected`, `reason_codes`, `branches_compared` — all from deterministic comparison of the transcripts written in the same run.
- **`degradation_over_time_by_branch`:** Map of branch id → the same structure as per-branch **`degradation_over_time`**.

### `run_debug.json`

- Same turn list as the transcript path plus **full** API payloads and `debug_traces` — use when you need headers, nested JSON, or non-player-facing fields. Not required for routine pass/fail reading.

### `compact_operator_summary.md` / `aggregate_operator_summary.md`

- Quick operator pass: classification, axis table (per branch), truncated failures/warnings, first failing checkpoint id, suggested next debugging area (single-branch file); aggregate adds coverage and cross-branch divergence/degradation sections.

## Debugging by evaluator axis

Use `session_health_summary.json` (`axes[*].failure_codes` / `warning_codes` and `detected_failures`) together with `transcript.json` GM text windows.

### `state_continuity`

- **Failures:** e.g. `continuity_reset_language` — GM text matches reset/amnesia phrases after early turns.
- **Warnings:** `continuity_anchor_weak_by_checkpoint`, `continuity_anchor_absent_late_window` — continuity anchor tokens sparse in a checkpoint window or early-established location thread weak in the final third.

### `referent_persistence`

- **Failures:** codes such as unknown/denial patterns for Thoran, notice, or clues after establishment (`_REFERENT_UNKNOWN_PATTERNS` in `scenario_spine_eval.py`).
- **Warnings:** `referent_absent_late_window` — required referents from checkpoints missing in the late GM window.

### `world_project_progression`

- **Failures:** `progression_missing_by_checkpoint` — progression anchor keywords missing in the checkpoint’s GM window.
- **Warnings:** `progression_contradicted` — progression keywords present but later contradicted by progression-contradiction regexes.

### `narrative_grounding`

- **Failures:** `debug_or_system_leak`, `json_diagnostic_dump` — forbidden markers or JSON-shaped diagnostic lines in GM text.
- **Warnings:** `repeated_generic_filler` — many turns and high density of generic filler phrases.

### `branch_coherence`

- **Failures:** `foreign_branch_prompt_echo` — GM text appears to echo a long distinctive substring from another branch’s scripted player line.

## Regression guidance (CI vs manual runner)

**Focused pytest** for spine contracts, evaluator, and runner wiring uses **stubs or subprocess** for the tool tests — **no OpenAI or live HTTP is required** for:

```bash
python -m pytest tests/test_scenario_spine_contracts.py tests/test_scenario_spine_eval.py tests/test_run_scenario_spine_validation.py
```

**Manual or integration runs** of `python tools/run_scenario_spine_validation.py` without replacing the chat path exercise whatever backend the app uses for `/api/chat` (which may include a configured model). Those runs are **not** implied by the pytest command above.

Related lanes (optional, if present in the tree):

```bash
python -m pytest tests/test_playability_eval.py tests/test_behavioral_gauntlet_smoke.py
```

Do not add Makefile-only conventions unless the repo already uses them for the same purpose.

## Definition of Done — operator thresholds

### Smoke (`--smoke`)

- Executes at most **5** turns per branch (or fewer if `--max-turns` is lower).
- **No crashes** — process completes and writes artifacts.
- **`session_health_summary.json`** present (evaluator always runs on recorded turns).
- **`transcript.json`**, **`run_debug.json`**, **`compact_operator_summary.md`** present — use smoke to verify wiring after pipeline changes.

### Full branch (long-session intent)

- **Minimum:** **20+** executed turns on a branch intended as “full-length” (the canonical fixture enforces ≥ 20 turns on at least one branch via schema).
- **Preferred band:** **25–50** scripted turns for a serious long-session regression capture on the primary branch.
- **“Clean” (strict operator reading):** `classification == "clean"` — no axis failures, no evaluator warnings, healthy API majority. (The evaluator also sets `overall_passed` true for `classification == "warning"`; treat **`warning`** as pass-with-tech-debt only if each warning is **understood and accepted** as non-blocking for your release bar.)
- **Failed axes:** Any axis with `passed: false` or `classification` in `degraded` / `failed` should block a “clean” release claim until addressed or waived with written rationale.

### Current canonical full validation bar

- Run **`branch_social_inquiry`** to completion **without** `--smoke`.
- Expect **`session_health_summary.json`** with **`classification: "clean"`** (or your explicitly documented warning tolerance) and **no failed axes** (`axes[*].passed` all true).

### Distinct outcomes across branches

- **`branch_direct_intrusion`** and **`branch_cautious_observe`** should produce **different** transcript shapes from **`branch_social_inquiry`** for deterministic checks (`branch_divergence`, `branch_coherence`). **`branch_direct_intrusion`** is now a second **20+**-turn long path from the same start, so aggregate **`coverage_band_met`** and long-run divergence both exercise paired long branches; **`branch_cautious_observe`** remains the short contrast branch.

---

## Definition of Done — Scenario-Spine Expansion

Treat the lane **complete** when **all** of the following are true:

1. **Fixture depth:** At least **two** branches in the canonical spine have **≥ 20** scripted turns each.
2. **Coverage band:** With **`--all-branches`**, no **`--smoke`**, and full execution of every long-scripted branch, **`aggregate_session_health_summary.json`** reports **`coverage_band_met: true`** (sum of executed turns on those branches in **40–60**, every long branch **`full_length_branch: true`** — see implementation in `build_aggregate_session_health_summary`).
3. **Clean long runs:** On those full-length long-branch runs, **no failed health axes** (`axes[*].passed` all true) for the release bar you document (typically **`classification: "clean"`**).
4. **Degradation reporting:** **`degradation_over_time`** is either absent of progressive signals (`progressive_degradation_detected: false` and acceptable window signals) or any issue is **explicitly visible** in **`reason_codes`** / **`session_health.degradation_detected`** (no silent “feel” scoring).
5. **Branch divergence:** **`branch_divergence`** in the aggregate is computed from the **same** spine and **recorded transcripts** after per-branch reset (deterministic **`evaluate_scenario_spine_branch_divergence`**).
6. **Aggregate artifacts:** **`--all-branches`** writes **`aggregate_session_health_summary.json`** and **`aggregate_operator_summary.md`** beside per-branch dirs.
7. **Test hygiene:** `python tools/test_audit.py` reports **no duplicate top-level `test_*` names** across the repo test suite.

**Current status:** Fixture depth and coverage-band targets for the canonical JSON are **met** (`branch_social_inquiry` 25 + `branch_direct_intrusion` 25 → long-branch sum **50**). Release-level “Scenario-Spine Expansion complete” still depends on **clean long-branch runs**, aggregate artifacts, and test hygiene per items 3–7 in this list—validate on your stack after full `--all-branches` runs against the real `/api/chat` path when claiming a release bar.

---

**Modules:** `game/scenario_spine.py`, `game/scenario_spine_eval.py`, `tools/run_scenario_spine_validation.py`  
**Canonical JSON:** `data/validation/scenario_spines/frontier_gate_long_session.json`
