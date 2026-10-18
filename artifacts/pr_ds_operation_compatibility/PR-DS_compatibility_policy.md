# PR-DS Compatibility Policy

The policy is one gate on one operation. It lives in `experiments/pr_dq/surface_compat.py` and is applied by the existing PR-DR connector and the existing PR-DQ gameplay adapter.

## Eligibility, before the resolver runs

All of the following must hold:

1. The model operation class is INSPECT.
2. The target id is in the active scene's visible catalog.
3. The catalog kind is `perceive_target`.
4. The player utterance is non-empty. A bare id, with no utterance, is left incompatible.
5. The interactable has no `reveals_clue`.
6. Its description is non-empty and is already one of the scene's `visible_facts`.
7. `classify_referenced_surface`, called with that utterance and that target id, returns either:
   - an authored visible feature whose visible fact equals the description, or
   - an authored interactable whose id is the target and whose inspectable text equals the description.
8. The classification is visible and contains no hidden fact.

When those hold, the connector offers the existing investigate action and sets `visible_surface_inspection`. The operation class on the action stays INSPECT. The target id stays the model's target id.

## Acceptance, after the one resolver call

The gameplay adapter accepts the investigate result only when the resolver confirms the same limits:

- kind is `investigate` and success is true
- no discovered clues, clue id, world updates, skill check, dice, or transition
- state changes are empty
- a bound interactable id, if present, is the requested target
- metadata authority is the authored visible feature or the authored interactable
- the text in that metadata equals the interactable description
- that description is still one of the scene's visible facts
- no hidden fact is marked revealed

The deterministic response is that description. The GM hint is not returned. The interactable is not marked resolved. The clock is not advanced.

If the resolver returns `discover_clue`, a hidden authority, an unsupported authority, or any other text, the attempt is rejected and the pre-call session is restored.

## What the policy does not do

There is no synonym table. PERCEIVE is not rewritten to INSPECT, and INSPECT is not rewritten to PERCEIVE. A target id is not replaced. A clue, a hidden fact, an unsupported object, an exit, and an NPC do not become eligible through this gate. Requested outcomes are not copied into the action. The model record is not edited.

The notice board remains an ordinary INSPECT. It has `reveals_clue`, so this gate does not apply. Setting `visible_surface_inspection` on the notice anyway is rejected, and the clue text is not returned.
