# NPC lead continuity — practical testing

Compact checklist for re-validating **NPC lead continuity** after social or prompt-context changes. Architecture and prompt-contract intent live in code comments (Block C); this file is **procedural** only. Full pytest lanes and markers: `tests/README_TESTS.md`.

**Full manual smoke pass** (named scenarios, exact player prompt scripts, pass/fail criteria): [`docs/manual_gauntlets.md`](manual_gauntlets.md).

## Validation layers

**Unit/integration** — Storage, prompt export, behavior hints, and grounding invariants (targeted modules under `tests/`). **Synthetic transcript regression** — Deterministic multi-turn sessions that lock the exported continuity / repeat-suppression contract, not narration wording. **Manual gauntlets** — Spot-check conversational feel and obvious repetition or speaker bleed; use [`docs/manual_gauntlets.md`](manual_gauntlets.md) for the canonical scripted pass.

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

Run the **canonical** scripted scenarios (G1–G8), substitution guide, and rubric in [`docs/manual_gauntlets.md`](manual_gauntlets.md). Repeat in the live UI or your usual play harness after lead, prompt-context, narration, routing, or emission changes when you need a human spot-check beyond pytest.
