# 06 — Corpus Design

Frozen hash: `871f124e7ddb452303a1a24d3fea76e5c62c9791e84c5718f64bf2f8bf8bc221`

164 turns, 12 families. Labels were authored in `experiments/pr_eg_r6_r5/corpus.py` before provider execution. The runner aborts if the hash changes after `freeze.json` exists.

## Quotas

| Tag | Required | Actual |
|---|---:|---:|
| direct public | 20 | 50 |
| multi-role | 15 | 25 |
| correction | 20 | 25 |
| follow-up | 20 | 35 |
| partial | 15 | 15 |
| genuine unknown | 15 | 32 |
| genuine ambiguity | 15 | 15 |
| restricted | 15 | 22 |

Tags overlap. Classes: DIRECT 62, PARTIAL 15, RELATED_NONANSWER 3, UNKNOWN 47, CLARIFICATION_REQUIRED 15, RESTRICTED 22.

## Families

Each family is one location, its NPCs, and a multi-turn conversation. Situations differ by fact, role, and dialogue state. They are not lexical copies.

| Id | Partition | Scene | NPCs |
|---|---|---|---|
| c01 | development | Ferry office | Nara, Oren |
| c02 | development | Mill archive | Quill |
| c03 | development | Gate watch | Ilse, Pico |
| c04 | development | Shrine court | Maud, Lior |
| c05 | validation | Lamp market | Sela, Joss |
| c06 | validation | Night archive | Vesper, Brin |
| c07 | validation | Stable yard | Wren, Cala |
| c08 | validation | Infirmary | Doss, Nia |
| c09 | holdout | Watch house | Rhee, Tamsin |
| c10 | holdout | Quay tavern | Pell, Bram |
| c11 | holdout | Chapel bench | Edda |
| c12 | holdout | Three-person yard | Ansel, Brea, Cole |

## Distinct situation types inside the families

- Direct public facts (names, times, places, duties).
- Multi-role questions (who told whom, who keeps what).
- Corrections that change the requested argument or the prior question.
- Follow-ups after an answer, after uncertainty, and after a correction.
- Partial answers where one qualifier is known and another is not.
- Genuine unknowns with no eligible source.
- Ambiguous addressees or ambiguous referents.
- Restricted topics the addressed NPC holds but must not disclose.
- Rumors and beliefs that may be said only with the host hedge.
- A related non-answer that shares an argument and does not answer the question.
- Topic changes and a second NPC in the same conversation.

The builder rejects a turn whose player utterance contains a restricted fixture phrase that also appears in a secret topic. Evidence spans must be literal substrings of the player line or the source line.

## What was not done

The corpus was not enlarged with wording variants of the same fact. Holdout labels are not copied into provider prompts. The full document, including restricted fixture text, stays in `frozen_corpus.json` for local replay. Review copies redact those strings.
