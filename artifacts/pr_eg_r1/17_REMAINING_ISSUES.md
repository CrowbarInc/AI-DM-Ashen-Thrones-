# 17 — Remaining Issues

## Conversational

- A request to say something "in plainer words" repeats the sentence. It does not produce a simpler restatement.
- Quote replies use the frame "I meant this:". It is accurate and sounds like a citation.
- The absent-NPC line is explicit about not speaking from the new place. It is longer than ordinary speech.
- "Who forged the lantern?" is a correct refusal of an unknown fact. It does not say what the maker's mark is, because that mark is an inspection result, not something Mara established in dialogue.

## Dialogue quality

- The stable preference is one sentence. It does not add the harmless color the mission used as an example ("the streets are quieter") because that color was not authorized as a world fact and the model was not relied on to invent it safely.

## Provider overhead

- The first social narration of a known street name is still about 26,000 input tokens. The preference narration is about 24,000. Neither retried. Reducing that prompt was out of scope.
- Follow-ups that quote a stored line are zero-call. That was the expensive failure mode.

## Regression debt

Nineteen inherited failures in the shared turn pipeline and exploration routing. Identities are unchanged.

## Architectural risk

The continuity directive is a focused layer in front of the existing decision path. It will miss a novel phrasing that matches none of the reference cues and does not overlap a supplied sentence. Those turns fall through to interpretation. That is preferable to capturing scene questions and conditional actions, which an earlier draft did and which the tests rejected.

Do not start PR-EH from these leftovers.
