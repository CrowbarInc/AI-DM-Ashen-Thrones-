# 01 — Baseline and Architecture

PR-PLAY-13 · 2026-11-01. Opt-in opening renderer. No live provider calls.

Repository revision at entry: `d40f1ed198236c604085f1c842ead267a8104ce2`.
Tracked production files were clean. Unrelated untracked storage-cleanup notes were left in place.

## Source map

| Boundary | Owner | This pass |
| --- | --- | --- |
| Authoritative opening facts | Existing scene documents, `gm_resolution_decision.realization_claims`, curated opening facts | Read only. No new world database |
| Public catalog | `game/opening_presentation_renderer.py` | New. Engine-built, ephemeral |
| Model plan | Same module, parsed inside `game/gm.py` `call_gpt` | Selections only |
| Final narration | Renderer, then `enforce_rendered_publication` in the opening commit tail | Player text comes from the trace |
| Legacy opening | Existing narration envelope and lexical audit | Unchanged when the flag is off |
| Ordinary turns | Existing envelope | Flag is ignored |
| Playtest harness | `tools/playtest/worker.py`, `tools/playtest/runner.py` | Opt-in plan fixture and observable mode |

## Prototype differences

`artifacts/pr_play_12/prototypes.py` stayed an experiment. It was not imported by production.

The production catalog is built from the opening prompt's public claims and curated facts. It is not the prototype's three hardcoded claim ids. Required facts are the curated public matches when any exist, otherwise the public `MUST_STATE` claims. Hidden and unrecognized disclosure states are omitted. Duplicate selections are rejected. There is no rain texture, because that sentence would be a new fact. One reviewed concise variant exists for one exact authored notice sentence. The plan cannot carry narration or state updates.

## Implementation boundary

The flag `ASHEN_OPENING_RENDERER` defaults off. Enabled mode replaces only the scene-opening provider contract with a selection plan, renders catalog text, and still uses the existing opening commit, rollback, and one-request budget. Invalid flag values fail the opening before a provider call.
