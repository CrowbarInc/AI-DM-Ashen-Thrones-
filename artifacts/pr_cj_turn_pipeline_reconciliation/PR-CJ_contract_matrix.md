# PR-CJ Contract Matrix

Live provider calls: 0.

For each failing group, three layers are distinguished. They disagree. The newer implementation is not treated as the contract, and the older test is not treated as the contract.

## Shared turn execution

| Layer | Statement |
| --- | --- |
| A. Architectural contract | `game/ordinary_semantic_ownership.py` says one Resolution Contract selects a resolver and does not replace social, travel, exploration, or combat internals. `generation` is narration when no specialized resolver applies. `unresolved` and `clarify` select generation. |
| B. Implementation | `chat()` builds a contract before parsers. `stage_permitted` runs only the selected resolver's stages. `_operation` ends in `OP_ASK` for unmatched text. Leftover asks receive subject `social`. `select_ordinary_resolver` then returns `social`. |
| C. Test expectation | Action and chat share engine outcomes when the utterance is an investigation, a wait, or a narration retry. Unparsed chat exposes `resolution is None`. |

## Action versus chat routing

| Layer | Statement |
| --- | --- |
| A. Architectural contract | `/api/action` receives an already classified action. `/api/chat` classifies, then uses the same resolved-turn pipeline. |
| B. Implementation | Action exploration still resolves `kind=discover_clue` for an explicit investigate payload. Chat will not call `parse_exploration_intent` unless the contract permits the exploration stage. |
| C. Test expectation | Stubbing `parse_exploration_intent` on chat is enough for "I investigate the desk." to discover the desk clue. |

## Social interaction resolution

| Layer | Statement |
| --- | --- |
| A. Architectural contract | `social_interaction_frame` is an addressed social ask. Inherited scene focus is not an addressee. A direct question with no address keeps its topical subject. |
| B. Implementation | Any leftover `ask` becomes subject `social`, including "I investigate the desk.", "I wait.", "Describe the gate.", "hello there", and "Where are we?". `investigate` is absent from `_INSPECT_RE`. |
| C. Test expectation | Those utterances stay on exploration, passive pressure, or narration retry. Addressed questions stay on the social exchange. |

## Narration-only generation and structured realization

| Layer | Statement |
| --- | --- |
| A. Architectural contract | Narration-only and structured envelopes are selected before sealing. Hard validation may reject consequential facts the decision did not authorize. |
| B. Implementation | `regeneration_feedback` names `unauthorized_resolution_decision_fact` ahead of the older `validator_voice` retry target. Meta voice ("based on what's established" / "we can determine") is also tagged `malformed_or_truncated`. |
| C. Test expectation | The second provider call contains `Retry target: validator_voice.` |

## Retry handling

| Layer | Statement |
| --- | --- |
| A. Architectural contract | Targeted retry is per failure class: validator voice, unresolved question, scene stall. `apply_deterministic_retry_fallback` is marked removed from the critical path in the immutable mutator inventory. |
| B. Implementation | Place-location asks never reach the provider. Social-selected waits and location questions make one provider call and do not arm `unresolved_question` or `scene_stall`. |
| C. Test expectation | Those chats make two provider calls and record `retry_strategy:selected=...`. |

## Final response validation and immutable sealing

| Layer | Statement |
| --- | --- |
| A. Architectural contract | A hard-valid candidate is sealed. A rejected candidate may be replaced by an authorized observation or by safe nonresolution. Sealing happens after that choice. |
| B. Implementation | Passive and wrong-speaker candidates are replaced by `No one here can answer that from what is settled here.` |
| C. Test expectation | A hard-valid atmosphere line is kept. A wrong speaker is rewritten to Tavern Runner rather than replaced by the generic line. |

## State mutation and provenance

| Layer | Statement |
| --- | --- |
| A. Architectural contract | Authoritative clue discovery is an engine mutation, applied before narration, and only for an accepted investigation resolution. |
| B. Implementation | Chat investigation never builds that resolution, so `discovered_clues` stays empty. No provider sentence is written into clue state. |
| C. Test expectation | Chat investigation records "A map indicates patrol locations." before the provider request. |

## Embedded adjudication

| Layer | Statement |
| --- | --- |
| A. Architectural contract | The full utterance owns the contract. A trailing parenthetical is not a second semantic owner. |
| B. Implementation | When the contract is owned, `embedded_adjudication` is not attached. |
| C. Test expectation | The main lane stays `question` and `metadata.embedded_adjudication.category` is `roll_requirement_query`. |
