# PR-DD Affordability Benchmark

No live calls are part of this design. The optional live method is specified so a later cycle can run it without inventing a new procedure.

## Purpose

Record, for each successful player turn, how many tokens were required, whether the first provider attempt was accepted, and whether the accepted text stayed inside authority and stayed useful.

## Required metrics

1. Input tokens per successful turn.
2. Total tokens per successful turn, input plus output, summed across attempts that belonged to that turn.
3. First-attempt acceptance rate. Accepted means immutable finalization kept the first generation.
4. Retry overhead. Tokens of later attempts, plus the first attempt when the turn ends in fallback rather than an accepted generation.
5. Useful player-facing answer rate. A deterministic rubric: the reply names the authorized fact, the authorized limit, or the authorized outcome, and it is not a restatement of the player line alone.
6. Authority violation rate. Existing validators: hidden fact disclosure, unsupported certainty, wrong speaker, state mutation, invented roll.
7. Conversation continuity. On scripted multi-turn fixtures: interlocutor, allowed speaker, active interaction target, and reply-plan kind.
8. Cost per 100 successful turns, using the formula in `PR-DD_cost_model.md` and a price file supplied at runtime. If the price file is absent, store tokens and leave cost blank.
9. Prompt size by interaction class. Serialized bytes, `ceil(chars/4)`, and live input tokens when a live run exists.
10. Context growth across multiple turns. Bytes and estimated tokens at turns 1, 2, 3, and at a scripted eight-entry history.

## Fixture selection

Use the fixtures already measured in this audit. Do not invent world facts.

| Id | Player line | Expected class |
|---|---|---|
| S1 | Guard Captain preference line from `tests/test_pr_db_speaker_grounding.py` | Harmless social, reduced context |
| S2 | "Does the rain make it harder to keep watch?" after S1 | Experiential follow-up |
| S3 | "Does it get any easier after a while?" after S1 and S2 | Multi-turn continuation |
| F1 | "Captain, what do you know about the missing patrol?" | Authored factual, full context |
| N1 | "I examine the notice board for anything unusual." | Notice board, `discover_clue` |
| O1 | "I look around." | Ordinary observation |
| M1 | "I walk closer to the notice board." | Unresolved local movement, recorded as a limitation until a destination binds |
| C1 | "Does rain make it easier to assassinate the captain?" | Consequential social |
| H1 | "Where is the secret tunnel?" | Hidden-information question, `genuine_refusal` |
| T1 | "Enter Cinderwatch" | Scene transition to `market_quarter` |
| K1 | Synthetic skill scene from `tests/test_exploration_skill_checks.py` | Skill-check shape only, labeled synthetic |
| B1 | Synthetic goblin from `tests/test_combat_resolution.py` with `roll_die` fixed at 10 | Combat shape only, labeled synthetic |

S1 and C1 have byte-identical hashes in this audit and are the reproducibility anchors.

## Deterministic measurement method

1. Build each fixture through the current resolvers and `build_messages`. Do not call `call_gpt`.
2. Record serialized bytes, character count, `ceil(chars/4)`, message count, system bytes, policy bytes, history bytes, envelope, projection mode, and sha256.
3. Section bytes use an independent JSON serialization of each top-level key and are labeled as non-additive.
4. Replay S1, S2, S3 on one in-memory session and record continuity fields.
5. Run the existing authority validators against canned narration fixtures. The benchmark stores pass or fail. It does not generate narration.
6. Write `artifacts/affordability/baseline/<cycle>.json` and a CSV with the columns above. Do not write `data/session.json` or other production saves.

## Optional live measurement method

Disabled by default. A later cycle may enable it only with an explicit flag.

1. Use an isolated data directory. Do not open the production save.
2. Send only S1, S2, and C1, one session, model `gpt-4.1-mini` unless the cycle names another model.
3. Record provider-reported input, output, cached input, attempt index, acceptance, and the `build_messages` hash for that attempt.
4. Stop after three turns or after two failed attempts on one turn, matching the PR-CY budget lesson.
5. Store live usage beside the deterministic hash. Do not replace the deterministic baseline with the live token count. Report both.

## Baseline storage

The first baseline is this audit:

- S1 sha256 `d8d6737d1bfa4f6d0928719c7e1d454b83ba46b1868434c5be71b13053c26e4f`, 98,773 bytes
- C1 sha256 `40e5408dc2cac4524faf2cc5a17182d92b67614e4a5d50822ed20591a8260f60`, 108,362 bytes
- S2 and S3 byte counts 98,123 and 98,061, hashes not stable against PR-DC and therefore stored as PR-DD hashes in `PR-DD_context_inventory.csv`

A cycle updates the baseline only when its report includes the previous hash, the new hash, and the byte delta.

## Regression thresholds

Deterministic, on a cycle that claims no payload change:

- S1 and C1 hashes must match the baseline.
- Continuity fields on S1–S3 must match.
- Authority validator fixture pass count must not drop.

Deterministic, on a cycle that claims a context reduction:

- Serialized bytes for S1 must fall.
- S1 projection must remain selected.
- C1, F1, and H1 projection must remain unselected.
- No required authority field listed in the cycle's contract may disappear.
- Estimated tokens may fall. A rise of more than 2% on a class the cycle did not intend to touch is a failure.

Live, only when the optional method is enabled:

- First-attempt acceptance on S1 must remain true.
- Input tokens for an accepted S1 must be less than or equal to the previous live S1, or the report must explain a payload change with the deterministic hash.
- Authority violation count must stay zero on the scored canned checks. A live authority violation fails the cycle even if tokens fell.

There is no threshold that requires every class to hit the same token number.

## Comparison methodology

Compare a cycle to the immediately previous baseline, not to PR-CY's live tokens, unless the cycle is a live run of the same three lines. State which of the four buckets the number belongs to: historical live usage, reconstructed `ceil(chars/4)` estimate, hypothetical savings, or unverified assumption.

Report cost per 100 turns only with a supplied price. Otherwise report tokens per 100 successful turns using the measured input and output of accepted turns, and set cost to blank.
