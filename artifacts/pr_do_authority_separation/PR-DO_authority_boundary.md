# PR-DO Authority Boundary

Authority is structural. The eligibility function does not read `player_intent.summary`, premise text, outcome text, component descriptions, or clarification text. Its parameters are mode, status, operation classes, target ids, orders, unresolved references, permitted ids, the correction subject, and an optional engine channel.

Consequences:

- A player-asserted premise stays a claim. Repeating it in model text does not create canon.
- A requested outcome stays unadjudicated. It is not copied into `engine_submission`.
- A descriptive sentence that says to set HP, force a critical hit, execute an action, or update the world does not become a command. If the operation class is `ATTACK`, the submission contains `ATTACK` and the permitted target id. It does not contain that sentence.
- An unsupported operation class produces no submission, even when the status is `INTERPRETED` and the surrounding text sounds compliant.
- A payload that includes `authorized` or `execution_eligibility` is rejected.

`engine_submission` is built from a whitelist: disposition, the constant `execution_authorized=false`, allowlisted class tokens, permitted target ids, component orders, and three boolean flags that say model text, premises, and outcomes were not included. `authoritative_effects` is always empty. `executed` and `mutated_state` are always false.

`ELIGIBLE_FOR_VALIDATION` means the attempt may be shown to the existing engine later. This package does not show it to the engine. The engine would still own legal actions, targets, resources, mechanics, dice, NPC decisions, world facts, state transitions, and time.

The old PR-DM guard remains in place and was not patched with more phrases. Old-schema payloads are not submitted by this package. See the translation report.
