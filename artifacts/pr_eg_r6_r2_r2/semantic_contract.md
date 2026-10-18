# Proposed operation contract

The provider classifies intent, proposes a referent ID, and supplies a witnessed delta. The host validates the schema, conversation ownership, target selection evidence, entities, role changes and preserved fields before constructing a candidate. Candidate construction is read-only. Source correspondence and disclosure authorization precede immutable speech adoption; referent/history persistence follows adoption.

Acts: information_question, correction, follow_up, clarification_response, reference_to_prior_speech, other. A missing answer does not imply missing intent. Other is a noncommitting safe disposition within the existing gated question route; the campaign does not redesign movement or combat routing.

Propositions retain predicate, binary compatibility fields, literal qualifiers, negation and prior reference. New proposals additionally carry up to eight uniquely named roles, each with value, optional existing entity ID and literal evidence, plus requested_role. No role ontology is enumerated. Empty roles do not establish a missing identity. Existing saves are not enriched with invented roles.

Transformations: existing binary operations remain compatible; replace_role_value changes one named argument, reassign_roles changes witnessed role assignments, replace_requested_argument changes the missing role, replace_relationship changes predicate, replace_qualifier changes qualifiers. Reject_interpretation preserves focus rather than accepting arbitrary replacement. Unlisted fields inherit. Unlisted nonempty changes are rejected.

Followups: source_attribution, explanation, evidence, temporal_modification, alternative_argument, speech_clarification. The target proposition ID survives; attribution cannot turn its topic into its source. Unknown epistemic status remains unknown. Partial answers retain the underlying requested proposition and answer status.

Malformed proposals receive a structured failure reason and safe uncertainty without committing a referent. Ambiguous targets or arguments may receive targeted clarification. Recovery is bounded to host identity completion and schema-equivalent normalization, with no extra provider validation calls. Protected source text never enters the proposal context. The default-off feature gate, provenance classes and final-delivery authority remain unchanged.
