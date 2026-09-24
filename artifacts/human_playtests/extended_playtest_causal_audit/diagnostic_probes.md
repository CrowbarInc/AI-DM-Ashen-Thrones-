# Diagnostic probes

Specifications for the root owners. Not run against the preserved session. Not implemented as tests in this audit, because no production repair was made.

Use a disposable scene with one world NPC, one addressable who has no topics, two visible facts, and one interactable that reveals a single clue. Do not use Cinderwatch nouns as the assertion.

## 1. Environmental query with no interactable

Ask about visible scenery that is only in an opening sentence, not an interactable.
Expect: no match, or a non-answer. Do not expect `visible_facts[0]` to be presented as what the look found.

## 2. Current-state query with no clock

Ask what time of day it is in a fixture whose session date is static and whose world clocks are empty.
Expect: failure or an explicit absence. Do not expect a visible-fact sentence and do not expect an invented hour.

## 3. Interactable inspection

Ask what an authored interactable says, using its label, in a sentence that also steps toward it.
Expect: the authored clue or inspectable text. Do not expect a statute the fixture does not contain.

## 4. Broad solicitation with no resolved NPC

Ask anyone nearby a question that matches no id.
Expect: the existing no-target hint. Do not expect a catalog line whose speaker exists only because `npc_id` is empty.

## 5. Bare follow-up after no speaker was stored

After probe 4, ask "Do you know…?" with no name.
Expect: still unresolved, or a real continuity target if one was stored. Do not expect the sole world NPC solely because the route reason was `no_addressable_target`.

## 6. NPC knowledge boundary

Ask the world NPC about the other addressable's willingness to meet.
Expect: refusal or the NPC's authored topic only. `topic_revealed` stays null. The reply is not a new fact.

## 7. Contaminated-context probe

In an isolated fixture, write an unsupported sentence into `topic_pressure.last_answer` for the current topic and speaker, with no `topic_revealed` and no clue.
Ask a follow-up the selector would treat as the same thread.
Expect: that sentence is not returned as `structured_fact` / `topic_pressure:last_answer`. An authored clue on the same NPC still can be.

Probe 7 is the one that decides the immediate slice. Probes 1–6 keep the other clusters from being "fixed" by a last-answer change.
