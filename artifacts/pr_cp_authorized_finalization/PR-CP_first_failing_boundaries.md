# PR-CP first failing boundaries

Trace for all three targets:

authoritative resolver → decision-facing recipe → recorded provider narration → claim extraction → claim classification → decision-level validation → hard validation → retry (none in replay) → immutable response → final emission.

## A — preference

Earliest incorrect step: decision-level undeclared comparison, not extraction.

Narration validation classified the gesture as an existence observation and the preference as claim-only speech, and that layer was hard-valid. The envelope path then ran `_undeclared_consequential_violations` because `declared_claims` is an empty list. The existence row has authority `world_truth`. The empty declaration made "Guard Captain exists" an `undeclared_consequential_claim`. `validate_generated_response` appended `unauthorized_resolution_decision_fact` and replaced the reply with gate narration.

Classification of the preference itself was already non-consequential. The defect was the later comparison.

## B — patrol sentence

Two stacked boundaries. The earliest incorrect one is a missing authority reference.

The resolver selected "A patrol went missing near the old milestone." That text was not copied onto the decision, so the audit corpus did not contain it. Claim extraction kept the sentence. Classification then matched `patrol_route_or_geography` (patrol + milestone). That match was treated as an unauthorized discovery of the authored sentence.

A second, correct failure sat in the same reply: "That's all I can confirm for now" is `unauthorized_certainty_upgrade` and `unauthorized_evidential_relation`. Finalization discarded the authorized sentence with that clause. PR-CI preseal does not replace text once `_text_communicates_authored_fact` is already true, so the mixed reply stayed intact until hard validation rejected all of it. Bounded sentence preservation does not run on the narration-only envelope path.

## C — notice board

Earliest incorrect step: pattern classification of an authorized sentence.

`notice_roster_history` matches notice/board together with posted, listed, or names. The visible fact uses those words. `authorized_observation_line` refused to emit it. The provider paraphrase added edicts, urgent, and freshly posted, which also fail the one-extra-content-word cover. Hard validation replaced the reply with a denial that nothing further could be established.

## Origin

Not a single defective validator function. The shared incorrect step is H in the phase list only in the sense that three symptoms meet at one comparison: restatement of authorized material was classified as an undeclared consequential claim, and finalization then dropped the whole reply.

The implementation repairs that comparison and the projection that follows a mixed-reply failure. It does not rewrite extraction, the resolver, or retry policy.
