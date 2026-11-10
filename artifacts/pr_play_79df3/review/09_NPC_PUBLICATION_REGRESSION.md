# NPC Publication Regression

PR-PLAY-79D-F2 behavior was rechecked with deterministic fixtures. No live provider call was used to repeat the already verified accepted path.

## Accepted dialogue

`test_accepted_dialogue_record_is_still_gameplay` keeps the accepted speech as a gameplay publication. The prior publication file, 36 tests, passed again in the 63-test run. Accepted speech stays visible, the speaker identity stays on the publication record, and the pointer advances for a completed sentence. No redundant primary narration is introduced by this classification change.

## Grounded fallback

`test_grounded_fallback_record_is_still_gameplay` and `test_http_fallback_is_not_an_operational_refusal` reject an ungrounded claim (“king paid”), publish the fallback, set `dialogue_accepted` false, and advance the pointer. The fallback is a completed gameplay publication. The rejected expression is not labeled accepted. The claim is not promoted to an authoritative fact.

Holdout cases H13 and H14 cover the same split. Both passed on the single scored run.
