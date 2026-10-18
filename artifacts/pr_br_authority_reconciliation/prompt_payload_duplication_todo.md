# Token-cost TODO

Do not implement these reductions in the preservation / premise / inference slice. Correctness first. Preserve the finding for the next product-performance campaign.

## Measured duplication

Discovery, two live turns, four generation attempts:

| Call | Input tokens |
| --- | --- |
| A1 initial | ~24,750 |
| A1 retry | ~26,010 |
| A2 initial | ~29,221 |
| A2 retry | ~30,917 |

Confirmed repeated material:

- `gm_resolution_decision` appears more than once in the base prompt.
- `realization_claims` are carried inside the decision and repeated beside it.
- The full `resolution_contract` is repeated.
- Response policy is represented in more than one block.
- A retry resends the full base payload and then adds the contract and decision again inside the feedback context.

The premise-link field added one schema key and one instruction sentence. That is a small increase and was required so a later model call can name premises. It is not a reduction.

## Likely safe future reductions

- Send the compact decision once. Do not paste `realization_claims` a second time when they are already inside `gm_resolution_decision`.
- On retry, send the rejection reasons, the rejected declaration ids, and the premise-ceiling rule. Do not resend the entire base payload plus a second full contract and decision.
- Drop duplicate `player_facing_text` when the structured narration field is the same string.

## Risky reductions

- Dropping narration constraints, temporal provenance buckets, or authored facts from the retry payload. Those are what keep a retry from re-authorizing a rejected hypothesis.
- Compressing premise instructions into a shorter slogan. The model has to see that uncertainty does not establish the premise.
- Removing response policy entirely from one of the blocks without checking which block the generator actually follows.

## Explicit non-goal

This note does not authorize a prompt diet, a second envelope shape, or another authority-hardening cycle.
