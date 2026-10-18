# PR-DL Routing Error Analysis

These classes compare the stored live interpretation with the deterministic result. They are outcome classes. The preserved PR-DK routing labels stay in the evidence correction.

## False negatives

Selective routing left the deterministic result in place, and the stored interpretation would have improved it.

- `var_compound_subtle`: independent checks missed "drift over ... then try to pull it free." The model separated the approach and the pull. Deterministic gameplay is FAIL. Live gameplay is PASS.
- `var_quote_control`: the deterministic resolver is `travel` for a quoted joke. The routing label says assistance is not justified. The model treated the line as speech, with the explanation that it is not a literal action. Live gameplay is PASS.

## False positives

Selective routing invoked the model where the deterministic result was already PASS.

- `var_social_control`: ordinary rain question. The model also returned a correct ask. The call was unnecessary and harmless.
- `var_hypothetical_control`: hypothetical notice question. The model also returned a correct ask. The call was unnecessary and harmless.

## Harmful invocations

The stored interpretation is worse than a correct deterministic result.

- `control_combat`: deterministic combat handling is PASS. The model named the goblin and the attack, then invented the entity id `quarterstaff`. The adapter rejected the payload. Universal consumption replaces a usable attack interpretation with a rejection.

## Beneficial invocations

The stored interpretation ranks above the deterministic result.

C1, compound, ambiguous, var_compound_subtle, var_ambiguous_subtle, var_conseq_social, var_unsupported_mechanic, var_quote_control

`var_unsupported_mechanic` is a partial benefit: the model separated advantage, the spy, and the patrol, and it did not grant them, but it asked for entity ids instead of recognizing the requests as unsupported.

`declared_canon` and `mechanical_dump` are triggered by selective routing and are not beneficial. The canon output proposes a world update. The mechanical output proposes setting the goblin's hit points to zero and is rejected by the adapter.

## Count

- False negatives: 2
- False positives: 2
- Harmful invocations: 1
- Beneficial invocations: 8
