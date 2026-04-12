# NPC lead continuity — practical testing

Compact checklist for re-validating **NPC lead continuity** after social or prompt-context changes. Architecture and prompt-contract intent live in code comments (Block C); this file is **procedural** only. Full pytest lanes and markers: `tests/README_TESTS.md`.

**Full manual smoke pass** (named scenarios, exact player prompt scripts, pass/fail criteria): [`docs/manual_gauntlets.md`](manual_gauntlets.md).

## Validation layers

**Unit/integration** — Storage, prompt export, behavior hints, and grounding invariants (targeted modules under `tests/`). **Synthetic transcript regression** — Deterministic multi-turn sessions that lock the exported continuity / repeat-suppression contract, not narration wording. **Manual gauntlets** — Spot-check conversational feel and obvious repetition or speaker bleed; use [`docs/manual_gauntlets.md`](manual_gauntlets.md) for the canonical scripted pass.

## Playability validation

### Playability Validation

**Purpose:** validate end-to-end narrative behavior at the player-facing level.

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

### Validation Layers (Final Form)

| Layer | Purpose |
|------|--------|
| Contracts | structural correctness |
| Behavioral Gauntlet | pipeline stability |
| Playability | human-DM behavioral validation |

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

Run the **canonical** scripted scenarios (G1–G12), substitution guide, and rubric in [`docs/manual_gauntlets.md`](manual_gauntlets.md). That now includes behavioral slices `G9` through `G12`; their `summary.json` output may include advisory `behavioral_eval` data and warnings, but manual judgment still owns pass/fail. Repeat in the live UI or your usual play harness after lead, prompt-context, narration, routing, or emission changes when you need a human spot-check beyond pytest.
