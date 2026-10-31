# Validation Evidence: ATGB-R2-01

> **No important player-facing PASS without inspectable behavioral evidence.**

What was tested: Offline historical reconstruction and prioritization; no fresh gameplay
Runtime path: Historical production API; this pass reads saved JSON/source only
GM boundary: Raw interpretation, adapted projection, host grounding/routing, final delivered reply
Player inputs: Authored frozen ATGB scenarios
Runs / turns: 6 / 19
Automated conclusion: No new automated semantic judgment; A prioritization verdict is agent analysis
Result counts: `{"{'review_id': 'S01.4/trial-1', 'interpretation': 'fail', 'response': 'fail', 'authority': 'pass', 'failure_severity': 'major', 'clarification': 'none', 'continuity': 'preserved', 'reviewer_explanation': 'Conversational acknowledgment/withdrawal incorrectly treated as an unestablished rules question.'}": 1, "{'review_id': 'S02.1/trial-1', 'interpretation': 'pass', 'response': 'fail', 'authority': 'pass', 'failure_severity': 'major', 'clarification': 'none', 'continuity': 'not_applicable', 'reviewer_explanation': 'Reading notices produces only category list, not the available posted warning; notice-route clue remains undiscovered.'}": 1, "{'review_id': 'S02.2/trial-1', 'interpretation': 'pass', 'response': 'fail', 'authority': 'pass', 'failure_severity': 'major', 'clarification': 'none', 'continuity': 'preserved', 'reviewer_explanation': 'Curfew time not authored; should explicitly say exact hour is unknown, not repeat board categories.'}": 1, "{'review_id': 'S02.3/trial-1', 'interpretation': 'fail', 'response': 'fail', 'authority': 'pass', 'failure_severity': 'major', 'clarification': 'none', 'continuity': 'lost', 'reviewer_explanation': 'Player corrects time question; identical generic notice text fails to acknowledge correction.'}": 1, "{'review_id': 'S02.4/trial-1', 'interpretation': 'pass', 'response': 'fail', 'authority': 'pass', 'failure_severity': 'major', 'clarification': 'none', 'continuity': 'lost', 'reviewer_explanation': 'Asks warning location, but response repeats notice headings and fails to deliver route detail or acknowledge unavailable text.'}": 1, "{'review_id': 'S03.1/trial-1', 'interpretation': 'pass', 'response': 'pass', 'authority': 'pass', 'failure_severity': 'minor', 'clarification': 'none', 'continuity': 'not_applicable', 'reviewer_explanation': 'Grounded runner hearsay supplied; slightly awkward third-person quotation is stylistic only.'}": 1, "{'review_id': 'S03.2/trial-1', 'interpretation': 'pass', 'response': 'pass', 'authority': 'pass', 'failure_severity': '', 'clarification': 'none', 'continuity': 'preserved', 'reviewer_explanation': 'Runner admits source is unknown without inventing informant.'}": 1, "{'review_id': 'S03.3/trial-1', 'interpretation': 'fail', 'response': 'fail', 'authority': 'pass', 'failure_severity': 'major', 'clarification': 'unnecessary_fail', 'continuity': 'lost', 'reviewer_explanation': 'Active runner interlocutor is established; commitment question is misread as unresolved NPC addressee.'}": 1, "{'review_id': 'S03.4/trial-1', 'interpretation': 'fail', 'response': 'fail', 'authority': 'uncertain', 'failure_severity': 'major', 'clarification': 'none', 'continuity': 'lost', 'reviewer_explanation': 'Repeats runner rumor without comparing accounts; posted route detail was never delivered. Three faction agenda flags advance on this turn; authorization cannot be resolved from bounded state alone.'}": 1, "{'review_id': 'S03.5/trial-1', 'interpretation': 'pass', 'response': 'fail', 'authority': 'pass', 'failure_severity': 'major', 'clarification': 'none', 'continuity': 'lost', 'reviewer_explanation': 'Correction recognized at topic level but output lists unrelated facts instead of saying whether accounts match; notice detail not actually disclosed.'}": 1, "{'review_id': 'S05.1/trial-1', 'interpretation': 'pass', 'response': 'pass', 'authority': 'pass', 'failure_severity': 'minor', 'clarification': 'none', 'continuity': 'not_applicable', 'reviewer_explanation': 'Correct runner rumor, with stiff third-person hearsay phrasing.'}": 1, "{'review_id': 'S05.2/trial-1', 'interpretation': 'pass', 'response': 'fail', 'authority': 'pass', 'failure_severity': 'major', 'clarification': 'none', 'continuity': 'lost', 'reviewer_explanation': 'Board question answered with validation error, not public notice content or qualified uncertainty.'}": 1, "{'review_id': 'S05.3/trial-1', 'interpretation': 'fail', 'response': 'fail', 'authority': 'pass', 'failure_severity': 'major', 'clarification': 'unnecessary_fail', 'continuity': 'lost', 'reviewer_explanation': 'Referent may be ambiguous between runner and board, but asks which person instead of which account; prior addressee remains runner.'}": 1, "{'review_id': 'S05.4/trial-1', 'interpretation': 'fail', 'response': 'fail', 'authority': 'uncertain', 'failure_severity': 'major', 'clarification': 'none', 'continuity': 'lost', 'reviewer_explanation': 'Player resolves referent to runner version; answer gives no elaboration. Faction agenda flags advance; authorization cannot be established from this packet.'}": 1, "{'review_id': 'S07.1/trial-1', 'interpretation': 'uncertain', 'response': 'uncertain', 'authority': 'pass', 'failure_severity': '', 'clarification': 'none', 'continuity': 'not_applicable', 'reviewer_explanation': 'Opening not delivered. Player rain/queue remark is clear, but scene summary may be initial scene presentation; cannot confidently grade expected naturalness without delivered opening.'}": 1, "{'review_id': 'S07.2/trial-1', 'interpretation': 'fail', 'response': 'fail', 'authority': 'pass', 'failure_severity': 'major', 'clarification': 'none', 'continuity': 'preserved', 'reviewer_explanation': 'Regardless of missing banner opening, explicit observation is not a request for a rules ruling; mechanical fallback is nonresponsive. Opening-dependent continuity not judged.'}": 1, "{'review_id': 'S08.1/trial-1', 'interpretation': 'pass', 'response': 'pass', 'authority': 'pass', 'failure_severity': '', 'clarification': 'none', 'continuity': 'not_applicable', 'reviewer_explanation': 'Public scene description answers broad observation question.'}": 1, "{'review_id': 'S08.2/trial-1', 'interpretation': 'fail', 'response': 'fail', 'authority': 'pass', 'failure_severity': 'major', 'clarification': 'none', 'continuity': 'preserved', 'reviewer_explanation': 'Correction to people is routed to pending-intention revision rather than refining scene description.'}": 1, "{'review_id': 'S08.3/trial-1', 'interpretation': 'pass', 'response': 'pass', 'authority': 'pass', 'failure_severity': '', 'clarification': 'none', 'continuity': 'preserved', 'reviewer_explanation': 'Correctly identifies visible serjeant as crowd handler.'}": 1}`

## Selected Evidence

### Representative Success

Selection: first automated PASS labeled representative_player_behavior and not HUMAN_REJECTED/HUMAN_AMBIGUOUS

No example observed in this campaign.

### Boundary Success

Selection: first automated PASS or HUMAN_ACCEPTED example labeled boundary_case

No example observed in this campaign.

### Representative Failure

Selection: first failure labeled representative_player_behavior

No example observed in this campaign.

### Severe / Worst Failure

Selection: maximum INVALID_RUN, mandatory-gate failure count, then lowest diagnostic score; source order breaks ties

No example observed in this campaign.

### Evaluator Disagreement

Selection: first example with explicit evaluator_disagreement.present=true

No example observed in this campaign.

### Unexpected / Unclassified Behavior

Selection: first HUMAN_AMBIGUOUS or unexpected_behavior example

No example observed in this campaign.

### Stress Probe

Selection: first example labeled stress_probe

No example observed in this campaign.

## All Evaluator Disagreements

No example observed in this campaign.

## Missing Concepts / Future Capabilities


## What This Does Not Prove

- Historical AI-assisted assessment is not human-attested. No post-repair performance measurement.
- Original request messages unavailable for these initial captures; evaluation world facts are not proof of prompt inclusion.
- No semantic_result is synthesized from provisional judgments. Automatic success/failure category selectors therefore have no scored examples; selected exact historical success/failure are described separately below.
- S05 topic uncertainty and S07 missing opening remain. No unseen generalization or new authority guarantee.

## Review Notes

Human review is recorded beside automated evaluation and never rewrites the historical result.
The manifest contains every exact exchange and full gate evidence; this summary exposes the deterministic selections.

## Agent-selected retrospective orientation (not human adjudication)

Selected in report 02 before packaging, in addition to unchanged automatic categories. Historical success: S03.1 explicitly addresses runner and receives authorized rumor. Historical failures: S03.3 selects runner in raw model JSON but host asks which person; S02.2 repeats category-only board text for curfew time. Exact selected exchanges and judgments are embedded in the manifest. Severe/worst: no new severity ordering beyond historical major failures. Evaluator disagreement: no newly adjudicated disagreement; original S03.4/S05.4 authority uncertainties remain. Unexpected/ambiguous: S05.3 topic after board refusal; S07 missing opening. No stress probe or boundary-success claim. All human review UNREVIEWED.
