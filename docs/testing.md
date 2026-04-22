# NPC lead continuity — practical testing

Compact checklist for re-validating **NPC lead continuity** after social or prompt-context changes. Architecture and prompt-contract intent live in code comments (Block C); this file is **procedural** only. Full pytest lanes and markers: `tests/README_TESTS.md`.

**Objective #12** (registry + audit CLI, governance/tooling only): [`docs/objective12_validation_contract.md`](objective12_validation_contract.md), `tests/validation_coverage_registry.py`, `tools/validation_coverage_audit.py`. Step-by-step contributor workflow is in the **Objective #12 — contributor workflow** section below.

**Full manual smoke pass** (named scenarios, exact player prompt scripts, pass/fail criteria): [`docs/manual_gauntlets.md`](manual_gauntlets.md).

**Post-AER consolidation:** Behavioral gauntlet, playability validation, and AER are **functionally complete** validation tracks. Ongoing work targets **orchestration** boundaries, **telemetry** normalization, and **test ownership** trimming (each test module should have one **canonical owner** domain; cross-suite checks stay **smoke overlap** unless layers truly differ)—see `docs/current_focus.md` and `docs/narrative_integrity_architecture.md`.

## Objective #12 — contributor workflow

Use this when your change touches a **validation-sensitive** feature or domain (anything that would change which scenarios should defend it, or that needs new defense in depth).

1. **Declare or update coverage** in [`tests/validation_coverage_registry.py`](../tests/validation_coverage_registry.py): `required_surfaces`, typed pointers, and notes. Follow the contract in [`docs/objective12_validation_contract.md`](objective12_validation_contract.md).
2. **Run registry validation** (pytest locks schema, allowlists, and active-entry rules — this is not an evaluator run):

   `py -3 -m pytest tests/test_validation_coverage_registry.py -q`

3. **Inspect the feature** (summary of one row + declarative “likely commands” from pointers only):

   `python tools/validation_coverage_audit.py --feature <feature_id>`

4. **Run** the referenced pytest modules, `tools/` entrypoints, and playability/manual paths printed under *Likely commands* (plus any team-standard lanes you already use).
5. **Manual gauntlets** when **feel**, **prose**, or **player-facing** behavior changed in a way automated lanes will not catch — scripted scenarios and rubric: [`docs/manual_gauntlets.md`](manual_gauntlets.md).

The registry answers **where coverage is declared**; the audit CLI answers **how to inspect it** and suggests **what to run**. Objective #12 does **not** add runtime behavior: evaluators and existing tests remain the only authorities that **score** behavior.

### Copy/paste — audit CLI (matches `tools/validation_coverage_audit.py`)

From repo root. On Windows, if `pytest` is not on `PATH`, keep using `py -3 -m pytest` as in [`tests/README_TESTS.md`](../tests/README_TESTS.md).

```bash
# 1) Registry validation (pytest)
py -3 -m pytest tests/test_validation_coverage_registry.py -q

# 2) Audit summary — totals, per-surface “active features missing this surface”, registry OK/FAIL
python tools/validation_coverage_audit.py

# 3) Strict — exit 2 if validate_entries reports any issue (CI-style gate)
python tools/validation_coverage_audit.py --strict

# 4) One feature — full row + likely pytest / manual / playability commands (hints only)
python tools/validation_coverage_audit.py --feature <feature_id>

# 5) Missing-surface — active features that do NOT list this surface in required_surfaces
python tools/validation_coverage_audit.py --missing transcript
python tools/validation_coverage_audit.py --missing manual_gauntlet

# 6) Surface filter — all rows that require this surface
python tools/validation_coverage_audit.py --surface integration_smoke
```

**`--strict` behavior:** if validation fails, exit code is **2**. With **`--feature`**, **`--surface`**, or **`--missing`**, validation errors are printed to **stderr** and the process exits **2** **before** the requested feature/surface output. The default summary (no `--feature` / `--surface` / `--missing`) prints the full summary first, then reports validation OK/FAIL.

**Mutually exclusive modes:** only one of `--feature`, `--surface`, or `--missing` may be used per invocation (argparse mutual exclusion). Surface ids: `transcript`, `behavioral_gauntlet`, `manual_gauntlet`, `playability`, `unit_contract`, `integration_smoke` (hyphenated spellings are accepted, e.g. `unit-contract`).

### How to think about validation ownership (practical)

| Surface / idea | What it is for | Typical trigger |
|----------------|----------------|-----------------|
| **Transcript regression** | Deterministic multi-turn or harness modules that lock **contracts** (routing, exports, invariants) — not narration wording. | You changed pipeline seams covered by transcript-tagged tests. |
| **Behavioral gauntlet** | Deterministic **axis-scored** narration-behavior smoke (`tests/test_behavioral_gauntlet_smoke.py`); axes listed in registry. | You changed compact narration-behavior seams the gauntlet encodes. |
| **Manual gauntlet** | Scripted **human** pass/fail in [`docs/manual_gauntlets.md`](manual_gauntlets.md); CLI `tools/run_manual_gauntlet.py`. | Lead follow-up, voice, grounding, transitions — **feel** the automation does not own. |
| **Playability** | Turn-scored **`evaluate_playability`** via `tests/test_playability_smoke.py` and/or `tools/run_playability_validation.py`. | Player-facing turn quality under API-shaped pressure. |
| **`unit_contract` / `integration_smoke`** | **Structural support**: fast module-level contracts, wiring, smoke scripts — pointers in registry, not a replacement for the four behavioral layers above. | Schema, export shape, “does this module still run” guardrails tied to the feature. |

Declare **`required_surfaces`** for what **must** be true for an **active** feature; use **`optional_smoke_overlap`** only for helpful extra pointers that do not redefine ownership.

### Quick Q&A

- **I changed narration behavior (voice, grounding, feel); what do I owe?** Update the owning feature row if validation ownership shifts; keep or add **manual_gauntlet** (and **behavioral_gauntlet** if axis-level smoke applies). Run registry pytest, `python tools/validation_coverage_audit.py --feature <id>`, then manual gauntlets from the hints plus [`docs/manual_gauntlets.md`](manual_gauntlets.md).

- **I changed a transcript-protected domain; what do I update?** Point **transcript** modules in the registry row, run `py -3 -m pytest tests/test_validation_coverage_registry.py -q`, then run the transcript pytest paths the audit prints (and full/transcript lanes as your team expects).

- **I added a new feature; where do I register required coverage?** Add a **`CoverageEntry`** in `tests/validation_coverage_registry.py` with **`feature_id`**, **`required_surfaces`**, and the typed pointer fields the contract requires for each declared surface; validate with pytest and inspect with `--feature`.

- **When do I add manual gauntlets vs playability?** **Manual** when rubric-based human judgment and scripted **feel** are the signal. **Playability** when **`evaluate_playability`** over `/api/chat` (or the smoke harness) is the right automated authority. You can require both surfaces on one feature if both apply.

## Validation layers

**Unit/integration** — Storage, prompt export, behavior hints, and grounding invariants (targeted modules under `tests/`). **Synthetic transcript regression** — **Deterministic** multi-turn sessions that lock the exported continuity / repeat-suppression **contract**, not narration wording. **Manual gauntlets** — Spot-check conversational feel and obvious repetition or speaker bleed; use [`docs/manual_gauntlets.md`](manual_gauntlets.md) for the **canonical** scripted pass.

### Objective #7 (referent artifact + post-GM clarity)

Regression coverage for the **derivative** referent seam (not player-visibility `validate_player_facing_referential_clarity`, which remains `narration_visibility`-owned):

- **`tests/test_referent_tracking.py`** — deterministic `build_referent_tracking_artifact` / schema invariants.
- **`tests/test_prompt_context.py`** — prompt bundle includes full `referent_tracking`; `turn_packet["referent_tracking_compact"]` stays the **four-field** mirror only (no drift toward duplicating the full artifact).
- **`tests/test_final_emission_validators.py`** — `validate_referent_clarity` prefers the full artifact; compact-only observability + repair abstention; at-most-one pronoun repair; forbidden-name / category abstention rules.
- **`tests/test_final_emission_gate.py`** — `_apply_referent_clarity_pre_finalize` merges `_final_emission_meta` and keeps `final_text_preview` / `post_gate_mutation_detected` coherent after repair.

Shared JSON-safe stubs (optional): `tests/helpers/objective7_referent_fixtures.py`.

## Playability validation (complete)

### Playability Validation

**Purpose:** validate end-to-end narrative behavior at the player-facing level.

**Status:** **Complete** as a validation layer (not a pending feature track). It remains the **canonical owner** for turn-scoped playability scoring in CI-style runs.

**Tools:**

1. **Integration tests** — `pytest tests/test_playability_smoke.py`
   - Drives real `POST /api/chat`
   - Uses `evaluate_playability(...)` as the **only** scoring authority
   - Asserts axis-level behavioral success

2. **CLI validation runner** — `python tools/run_playability_validation.py --scenario <id>`
   - Executes multi-turn scenarios
   - Emits transcript and evaluator artifacts
   - Summary is derived from the **final turn** evaluation

### Key Design Rules

**Evaluator authority**

- `evaluate_playability(...)` is the only source of truth
- Tests and CLI **must not**:
  - rescore behavior
  - reinterpret thresholds
  - duplicate heuristics

**Turn-based evaluation**

- Each turn is evaluated independently
- Session summaries use the final turn as the representative output

### Known Testing Constraints

**Escalation vs emission gate**

- Strict-social emission repair can collapse repeated pressure turns
- That can suppress observable escalation signals

**Resolution:** the escalation test bypasses `apply_final_emission_gate` **only** within that test, so the evaluator can assess real pipeline variation.

**Important:** this is a **test harness** adjustment, not a runtime change and not a system defect.

### Validation Layers (final form)

| Layer | Purpose | Status |
|------|--------|--------|
| Contracts | Structural correctness | Ongoing (baseline regression) |
| Behavioral Gauntlet | **Deterministic** pipeline / narration-behavior smoke | **Complete** |
| Playability | Human-DM behavioral validation via live `/api/chat` | **Complete** |
| AER (Anti-Echo & Rumor Realism) | Narrative authenticity operator + repairs + telemetry | **Complete** (functionally) |

## Behavioral gauntlet (complete)

The **Behavioral Gauntlet** is **complete** as a compact, **deterministic** adjunct to broader gauntlet and transcript inventory:

- `tests/helpers/behavioral_gauntlet_eval.py` — evaluator helper (`evaluate_behavioral_gauntlet(turns, *, expected_axis=None)`).
- `tests/test_behavioral_gauntlet_smoke.py` — automated smoke lane (`integration` + `regression`).
- `tests/test_behavioral_gauntlet_eval.py` — locks the evaluator **contract**.
- `docs/manual_gauntlets.md` — manual source of truth including behavioral gauntlets `G9` through `G12`.
- `tools/run_manual_gauntlet.py` — optional advisory `behavioral_eval` attachment to `summary.json`.

Manual `behavioral_eval` output is advisory only: it does not replace operator judgment or determine manual pass/fail by itself.

## Commands

From repo root (on Windows, use `py -m pytest` if `pytest` is not on your `PATH`; see `tests/README_TESTS.md`).

| Lane | Command |
|------|---------|
| Default full run | `py -m pytest -q` |
| Synthetic-focused | `py -m pytest tests/test_synthetic_sessions.py -q` |
| Prompt-context | `py -m pytest tests/test_prompt_context.py -q` |
| Fast lane | `pytest -m "not transcript and not slow"` |

- **Default** `py -m pytest -q` includes synthetic-player tests (`pytest.ini` only adds `-q`; no marker filter).
- **Fast lane** skips slow smoke (e.g. `tests/test_synthetic_smoke.py`) but still runs the lighter synthetic modules (`tests/README_TESTS.md` → Synthetic-player harness).

**Synthetic and manual:** Continuity can stay correct even when a later same-NPC follow-up does not create a fresh discussion write (for example, no new `mention_count` increment), because prompt/export continuity can still come from existing discussion rows.

## Manual continuity gauntlets

Run the **canonical** scripted scenarios (G1–G12), substitution guide, and rubric in [`docs/manual_gauntlets.md`](manual_gauntlets.md). Behavioral slices `G9` through `G12` may include advisory `behavioral_eval` data and warnings in `summary.json`, but manual judgment still owns pass/fail. Repeat in the live UI or your usual play harness after lead, prompt-context, narration, routing, or emission changes when you need a human spot-check beyond pytest.
