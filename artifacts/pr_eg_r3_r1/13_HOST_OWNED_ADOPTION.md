# 13 — Host-Owned Adoption

Generated speech is delivered only when validation returns adopt and the existing seal records host speech. Rejected candidates stay on the turn audit.

Integrity findings on the final transcript: [].

Prior-adoption reuses, which the raw scorer marked `rejected_candidate_delivered`: [{"conversation": "primary", "turn": 14, "candidate": "I prefer the evening because it feels calmer and more peaceful to me.", "delivered_generated": false, "adoption": "HOST_FALLBACK", "earlier_turn": 2}, {"conversation": "secondary", "turn": 10, "candidate": "I prefer the evening because it feels calmer and more peaceful to me.", "delivered_generated": false, "adoption": "HOST_FALLBACK", "earlier_turn": 6}].

Those two turns asked for the characterization again. The model repeated the sentence already adopted. Validation rejected the verbatim repeat. The host then reused the earlier adopted line. `delivered_generated` is false. The rejected candidate did not become a new authorization.

Primary turn 4 shows the other boundary. The north-street candidate is absent from the delivered line and from later recall. Recall quotes the original road sentence, not the rejected rename.
