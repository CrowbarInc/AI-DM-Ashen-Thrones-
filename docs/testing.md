# NPC lead continuity — practical testing

Compact checklist for re-validating **NPC lead continuity** after social or prompt-context changes. Architecture and prompt-contract intent live in code comments (Block C); this file is **procedural** only. Full pytest lanes and markers: `tests/README_TESTS.md`.

**Full manual smoke pass** (named scenarios, exact player prompt scripts, pass/fail criteria): [`docs/manual_gauntlets.md`](manual_gauntlets.md).

**Post-AER consolidation:** Behavioral gauntlet, playability validation, and AER are **functionally complete** validation tracks. Ongoing work targets **orchestration** boundaries, **telemetry** normalization, and **test ownership** trimming (each test module should have one **canonical owner** domain; cross-suite checks stay **smoke overlap** unless layers truly differ)—see `docs/current_focus.md` and `docs/narrative_integrity_architecture.md`.

## Validation layers

**Unit/integration** — Storage, prompt export, behavior hints, and grounding invariants (targeted modules under `tests/`). **Synthetic transcript regression** — **Deterministic** multi-turn sessions that lock the exported continuity / repeat-suppression **contract**, not narration wording. **Manual gauntlets** — Spot-check conversational feel and obvious repetition or speaker bleed; use [`docs/manual_gauntlets.md`](manual_gauntlets.md) for the **canonical** scripted pass.

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
