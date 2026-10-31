# Product Realization Validation

This document is the narrow durable home for Product Realization
**validation** rules. It does not replace architecture, state authority,
gameplay rules, or `docs/DEVELOPMENT_CONSTITUTION.md`.

The Constitution remains repository-wide process only. Campaign reports remain
evidence. This file states the validation principle those campaigns must use
when they claim a **systemic** engine repair.

## Content may be specific. Systems must be general.

Scenario-specific content may satisfy content requirements.

Engine behavior intended to be systemic must demonstrate generality
independently of the calibration scenario whenever practical.

Cinderwatch / `frontier_gate` / `old_milestone` remain valid real-world
reproducers. They are not sufficient proof of a systemic engine contract.

When a Product Realization campaign claims a general owner:

- calibration-specific nouns belong in canonical content and calibration tests;
- generic engine code must not grow special-case knowledge of those nouns;
- scenario-independent fixtures with unrelated vocabulary are a hard acceptance
  gate for systemic claims.

A systemic claim is also a generalization claim under
`docs/DEVELOPMENT_CONSTITUTION.md`. Keep the original reproduction, related
variations, independent generalization, and the unrelated regression result
separate. Passing the original calibration scenario does not satisfy the
scenario-independent fixture gate in this document. That gate remains the
acceptance rule for a claimed general owner.

Fixtures authored alongside the implementation, including
scenario-independent fixtures, are not independent held-out evidence.
Independent generalization requires previously unseen or genuinely held-out
scenarios. A limited repair that does not claim a general owner may be
accepted without related variations or independent generalization. This
paragraph does not relax the fixture gate when a general owner is claimed.

This is a validation rule, not a new runtime owner.
