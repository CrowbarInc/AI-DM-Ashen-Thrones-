# Planner convergence (CTIR → narrative plan → GPT → gate)

This document describes the **manual-play narration** convergence seam and the **static audit** that keeps it from regressing quietly. Runtime contracts live in `game/planner_convergence.py`; enforcement in `game/api.py`; prompt shipping in `game/prompt_context.py` and `game/narration_plan_bundle.py`.

## Pipeline (normal path)

1. **CTIR** — Turn-scoped bounded meaning snapshot on `session` (`game.ctir_runtime`).
2. **Narrative plan** — Deterministic structural bridge from CTIR, built only via `game.narrative_planning.build_narrative_plan` at approved upstream seams (see below), attached in the narration plan bundle on `session`.
3. **Prompt** — `game.prompt_context.build_narration_context` **renders** the bundle; it does not rebuild planner semantics for the same stamp.
4. **GPT** — `game.gm.build_messages` / `call_gpt` run only when convergence is satisfied and `gm` is still unset (no pre-seam exit).
5. **Gate** — `game.final_emission_gate.apply_final_emission_gate` is the canonical orchestration owner for last-mile player-facing text.

### Normal path labels (annotate_narration_path_kind)

When narration completes without planner or upstream repair exits, the primary resolved-turn label is **`resolved_turn_ctir_bundle`**: CTIR-backed, bundle required, plan-driven. Related normal/telemetry labels are defined alongside the narration path matrix in `game/narration_seam_guards.py`.

## Emergency labels

Registered emergency fallback labels (runtime contract) include:

- `upstream_api_fast_fallback`
- `manual_play_gpt_budget_exceeded`
- `deterministic_terminal_repair`
- `non_gpt_error_response`

Non-plan player-facing output on a narrative-classified path must pair **`emergency_nonplan_allowed`** semantics with one of these labels where the runtime contract requires it. API-level fallbacks that synthesize text should call **`record_emergency_nonplan_output`** (or an equivalent registration already wired through the same seam) so telemetry and audits stay honest.

## Planner convergence seam (Block B path unchanged)

When pre-prompt or post-prompt convergence fails, `game.api._build_gpt_narration_from_authoritative_state`:

1. Builds a **terminal GM dict** via `_gm_planner_convergence_seam_terminal` (deterministic repair; **no** real `build_messages` / GPT on that branch — `gm` is set so the GPT block is skipped).
2. Annotates the path as **`resolved_turn_ctir_planner_convergence_seam`** (`annotate_narration_path_kind`).
3. Calls **`record_emergency_nonplan_output`** with reason `planner_convergence_seam_failure` and emergency label `deterministic_terminal_repair`.

Convergence **reports** are attached under `gm["metadata"]["planner_convergence_report"]` when a report dict is available. Debug traces append planner convergence snapshots (`prompt_debug` / session traces) at pre- and post-prompt stages where configured.

## prompt_context: plan-consumer-only rule

For CTIR-backed turns, `build_narration_context` must **not** call `build_narrative_plan`. The bundled `narrative_plan` is the sole structural source; the model-facing top-level `payload["narrative_plan"]` must be exactly the output of **`public_narrative_plan_projection_for_prompt`** (or `None`), never the full planner blob or an ad-hoc dict assembled from raw engine state.

### Public `narrative_plan` projection keys (top-level prompt)

Only these keys may appear at the top level of the shipped plan (mirror of `public_narrative_plan_projection_for_prompt` in `game/narration_plan_bundle.py`):

- `version`
- `narrative_mode`
- `role_allocation`
- `scene_anchors`
- `active_pressures`
- `required_new_information`
- `allowable_entity_references`
- `narrative_roles`
- `narrative_mode_contract`
- `scene_opening` (C1-A structural opener projection; prose-free; see `docs/narrative_integrity_architecture.md`)

`prompt_debug` may carry a compact **`_narrative_plan_prompt_debug_anchor`** mirror; that is not the authoritative top-level plan field.

## C1-A — Scene opening convergence (static audit)

The same audit flags **plan-bypass opener** patterns: imports/calls of `opening_scene_realization` outside `prompt_context`, duplicate `infer_scene_opening_reason` / `validate_scene_opening` imports, references to `_derive_opening_reason` outside `narrative_planning`, **visible_facts** clustered with **player_facing_text** on one line in API/GM/storage/gate modules, **fallback/neutral/cinematic** clustering with **scene_opening / opening_scene / opener / is_opening_scene** tokens, and banned long opener-prose dict keys inside `build_narration_context`. Legitimate Block A/B wiring (`resume_entry`, `patch_opening_export_with_plan_scene_opening`, seam guard, plan-owned `scene_opening`) is structured vocabulary and should not trip the heuristic when unchanged.

### Presentation-only raw reads

If a line inside `build_narration_context` must touch `world` / `session` / `scene` / `combat` on the same line as `narrative_plan` for **formatting or packaging only**, mark it:

```python
x = session.get("turn_counter")  # planner_convergence_presentation_only
```

The static audit (`tools/planner_convergence_audit.py`) uses this tag to avoid false positives on intentional presentation reads.

## Approved `build_narrative_plan` owners

Only these modules may **call** `build_narrative_plan`:

- `game/narrative_planning.py` (definition + internal helpers)
- `game/narrative_plan_upstream.py` (bundle head → plan)
- `game/narration_plan_bundle.py` (if a direct call is added; today the bundle uses upstream)

## Prohibited future patterns

- A **second planner** in `prompt_context`, `api`, `gm`, or scene helpers (any `build_narrative_plan` call outside the owners above).
- **Raw state → prompt** semantic shortcuts: deriving narration structure from unconstrained `world` / `session` / `scene` / `combat` reads instead of CTIR + bundle + contracts.
- **Full bundled plan** as top-level `payload["narrative_plan"]` (bypasses projection and stamp hygiene).
- **Unregistered** non-plan player-facing fallbacks (no `record_emergency_nonplan_output` where required).
- **Bypassing** pre/post `build_planner_convergence_report` / `planner_convergence_ok` around the manual-play `build_messages` / GPT path documented in `game/api.py`.

## Adding a new narration path safely

1. Classify the path in `game.planner_convergence` (`ALLOWED_NARRATIVE_PATH_LABELS`, emergency labels, or non-narrative debug labels as appropriate).
2. Register `path_kind` in the narration path matrix / `REGISTERED_NARRATION_PATH_KINDS` in `game/narration_seam_guards.py` when emitting operator-facing narration.
3. Keep **one** planner build chain: CTIR → bundle → `public_narrative_plan_projection_for_prompt` → prompt.
4. If the path can emit **non-plan** player-facing text, call **`record_emergency_nonplan_output`** with a stable reason string and owner module.
5. Run the **static audit** and the **focused pytest slice** below (or `make planner-convergence-check` on systems with GNU Make).

## Developer workflow

### Static audit (exact command)

From the repository root:

```bash
python tools/planner_convergence_audit.py
```

On Unix/mac with **Make** installed, the same entrypoint is wired as:

```bash
make planner-convergence-audit
```

Exit code **0** prints `planner_convergence_audit: OK`; **1** lists one issue per line. **CI:** GitHub Actions runs this step in `.github/workflows/content-lint.yml` after dependencies install.

### Focused pytest slice (exact command)

These files cover Planner Convergence contracts, manual-play pipeline structure, plan-only prompt context, and the static audit harness. They do **not** start a heavyweight full-suite run.

**Windows / portable** (if `pytest` is not on `PATH`, use `py -3 -m pytest` — see `tests/README_TESTS.md`):

```bash
py -3 -m pytest tests/test_planner_convergence_contract.py tests/test_planner_convergence_live_pipeline.py tests/test_prompt_context_plan_only_convergence.py tests/test_planner_convergence_static_audit.py
```

**Single-file** quick loop while editing audit rules or prompt shipment:

```bash
py -3 -m pytest tests/test_planner_convergence_static_audit.py
```

### Aggregate command (audit + focused tests)

**Make** (runs audit, then the same four-file pytest list):

```bash
make planner-convergence-check
```

**Without Make:** run the static audit command, then the focused `py -3 -m pytest ...` command above in sequence.

### When to run

- Before merging anything that touches **`game/api.py`**, **`game/prompt_context.py`**, **`game/narration_plan_bundle.py`**, **`game/narrative_plan_upstream.py`**, **`game/narrative_planning.py`**, opening-scene helpers (`game/opening*.py`), or **`tools/planner_convergence_audit.py`**.
- After adding or reclassifying a narration **`path_kind`**, changing **`public_narrative_plan_projection_for_prompt`**, or moving **`build_narrative_plan`** call sites.
- After refactors that might reintroduce a **second planner**, raw-state → plan shortcuts, or unregistered emergency player-facing text.

### What failures usually mean

| Message shape | Likely cause |
| --- | --- |
| `build_narrative_plan(...) call outside approved owners` | A new call site was added outside `game/narrative_planning.py`, `game/narrative_plan_upstream.py`, or `game/narration_plan_bundle.py`. Route through the bundle/upstream seam instead. |
| `payload['narrative_plan'] must ship only public_narrative_plan_projection_for_prompt` | Model payload is assembling the full plan or a hand-built dict. Use the bundle projection (or `None`) only. |
| `local dict resembles narrative_plan assembly` | Inline plan-shaped dict inside `build_narration_context`; consolidate on bundle + projection. |
| `possible raw-state -> narrative_plan semantic shortcut` | Same line mixes `world`/`session`/`scene`/`combat` access with `narrative_plan` without a presentation marker. |
| `public_narrative_plan_projection_for_prompt emits unknown keys` / `missing keys` | Projection drift vs audit contract; align **`APPROVED_PROMPT_NARRATIVE_PLAN_TOP_KEYS`** in `tools/planner_convergence_audit.py` with the implementation and this doc’s key list. |
| `game/api.py`: missing … `build_planner_convergence_report` / `planner_convergence_ok` / seam markers | Manual-play GPT path structure diverged from the convergence seam (do not “fix” by skipping the seam). |
| `assigns player_facing_text without record_emergency_nonplan_output` | Synthetic-module rule: emergency text must register in-function. |

### Allowlist and exceptions (do safely)

1. **`# planner_convergence_presentation_only`** — For a **single line** in `build_narration_context` that legitimately reads `world` / `session` / `scene` / `combat` alongside `narrative_plan` for formatting or packaging only. Keep the tag on that line; do not use it to hide real planner semantics.
2. **`APPROVED_BUILD_NARRATIVE_PLAN_OWNER_PATHS`** — Only if a **new canonical owner module** must call `build_narrative_plan` (rare). Add the repo-relative POSIX path in `tools/planner_convergence_audit.py`, update **Approved `build_narrative_plan` owners** in this doc, and justify in the PR.
3. **`APPROVED_PROMPT_NARRATIVE_PLAN_TOP_KEYS`** — When **`public_narrative_plan_projection_for_prompt`** gains or drops a **top-level** model-facing key. Update the frozenset, the bullet list under **Public `narrative_plan` projection keys**, and any contract tests that lock the set.

Never “fix” the audit by weakening rules for one-off hacks; extend contracts and owners explicitly so runtime and docs stay aligned.

## Static audit tool

- **Tool:** `tools/planner_convergence_audit.py`
- **Tests:** `tests/test_planner_convergence_static_audit.py` (focused slice above includes related convergence tests)

The audit scans the primary modules listed in the tool (plus `game/opening*.py`) and fails the process with a non-zero exit code when a rule trips.
