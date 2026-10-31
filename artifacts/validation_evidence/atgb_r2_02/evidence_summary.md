# Validation Evidence: ATGB-R2-02

What was tested: host addressee grounding for the captured S03.3 and S05.3 interpretations, plus related speech-role and ambiguity fixtures.

Runtime path: offline calls to `addressed_person_nominal`, `assess_addressee_grounding`, `decision_from_interpretation_record`, and `resolve_social_action`. No API server and no provider.

GM boundary: the decision layer returns an empty player-facing string and an EXECUTE handoff. The resolver hint is the existing uncertainty line. No narration model ran.

Player-input mode: historical corpus lines replayed from saved interpretations, plus synthetic related variations.

Run/turn counts: 2 historical turns replayed before and after the repair. 46 focused tests. Regression slice 353 tests.

Automated conclusions: both historical host decisions no longer return unresolved-addressee. The runner stays the grounded recipient. S05.3 does not emit a rumor answer.

Representative success: S03.3 grounding keeps the runner. See the manifest.

Boundary success: two visible people and no established addressee still clarify.

Representative failure: No example observed in this campaign.

Severe / worst failure: No example observed in this campaign.

Evaluator disagreement: No example observed in this campaign.

Unexpected / unclassified behavior: No example observed in this campaign.

Stress probe: No example observed in this campaign.

What remains unproven: live model wording, a focused which-account question for S05.3, independent held-out play, and the full pytest suite. This packet is not a gameplay-benchmark score. Human review of the new host decisions is UNREVIEWED.
