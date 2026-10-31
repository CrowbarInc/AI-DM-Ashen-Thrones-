# 03 — Implementation Diff

## Production files

- `game/interaction_completion.py` — added `speech_participant_head` and applied it inside `addressed_person_nominal`. About 62 lines changed.
- `game/ordinary_semantic_ownership.py` — extended the contextual pronoun set and the function docstring. About 16 lines changed.

Combined diff stat: 2 files, 73 insertions, 5 deletions. Full diff: `artifacts/atgb/atgb_r2_02/source.diff`.

## What changed

Extraction no longer returns continuation words as part of a person name. Grounding recognizes `you`/`your` and `i`/`me`/`my`/`we`/`us` as speech roles and routes them through the existing established-interlocutor, unique-visible, and conflict branches.

## Tests

`tests/test_atgb_r2_02_speech_participant_grounding.py` is new. It replays the captured S03.3 and S05.3 records, checks grammatical variants, and checks ambiguity, absence, third-party reference, bridge rejection, and resolver disclosure. Frozen holdout strings were not edited.

## Paths not changed

No edits to orchestration, the interpretation bridge, API pre-tick gate, prompts, schemas, provider configuration, social disclosure, pending-action storage, combat, factions, or the frozen ATGB baseline. Those callers consume the same grounding result they already consumed. `explicit_discourse_binding` was left as it was.
