# PR-CR Provenance Assessment

PR-CQ exposed a provenance ambiguity: the final text was an authorized deterministic projection, but the accepted response provenance was `safe_nonresolution`.

No existing provenance category represented deterministic authorized projection. Reusing `initial_generation` or `regeneration` would misrepresent the accepted text as provider-authored. Keeping `safe_nonresolution` would keep conflating an answer with a refusal/nonresolution.

PR-CR therefore adds a minimal accepted-response provenance value:

`authored_answer_projection`

Downstream distinction after PR-CR:

- accepted provider generation: `initial_generation`;
- accepted provider retry: `regeneration`;
- authorized deterministic projection: `authored_answer_projection`;
- genuine safe nonresolution: `safe_nonresolution`.

The acceptance reason remains `authored_answer_projection`.

