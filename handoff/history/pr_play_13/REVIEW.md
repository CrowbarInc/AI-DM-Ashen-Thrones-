# Campaign

Campaign: PR-PLAY-13 — Engine-Owned Opening Narration
Identifier: `pr_play_13`
Date: 2026-11-01
Purpose: Opt-in opening renderer and deterministic validation

# Executive Summary

Campaign opening can now be delivered from an engine-owned public catalog when `ASHEN_OPENING_RENDERER=1`. The model selects catalog entries and reviewed variants. It does not write the player-facing facts. The flag is off by default, so the legacy opening path is unchanged.

Objective status: `B — Conditionally ready for controlled live validation`.

# Changes Made

## Production changes

- `game/opening_presentation_renderer.py` builds the public catalog, validates the plan, and renders the trace.
- `game/gm.py` uses that contract only for a scene opening when the flag is enabled or invalid.
- `game/api.py` restores the rendered opening text at publication and drops model update fields on that path.

## Validation changes

- `tests/test_pr_play_13_opening_renderer.py` covers R1–R36 with stubs.

## Tooling changes

- The playtest harness records the renderer mode and, only when the flag is enabled, returns a required-entry plan for the opening `success` fixture.
- Startup reads of `ready.json` retry a transient Windows sharing error. This is not a provider retry.

## Documentation changes

- Nine reports under `development/campaigns/product_realization/pr_play_13/`.
- `docs/NEXT_SESSION.md` points at this pass.

# What Was Tested

- **Focused tests:** 30 passed.
- **Legacy opening and claim authority:** passed with the flag unset.
- **Broader selection:** 871 passed, 19 failed, 2 errors. Fourteen failures are the preexisting baseline. Seven Windows file-race outcomes passed in isolation.
- **Five-turn deterministic run:** `20261101T144743Z-14b8c942e340`, renderer selected, opening accepted, 6 synthetic requests, 4 turns, zero live calls.

# Feature flag

Unset keeps the legacy opening. `ASHEN_OPENING_RENDERER=1` enables the renderer for campaign opening only. Any other value fails that opening before a provider call.

# Closeout

No live provider calls, connectivity tests, model changes, output-budget increases, automatic provider retries, semantic-validator relaxation, hidden-information relaxation, state-authority relaxation, ordinary gameplay changes, new persistent structures, PR-EG integration, ATGB edits, commit, or push.

# Next action

External review. Do not execute live validation from this package.
