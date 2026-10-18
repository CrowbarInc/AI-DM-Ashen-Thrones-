# 12 — Frozen Dialogue Holdouts

Frozen 2026-10-16 in `tests/fixtures/pr_eg_dialogue_holdouts.json` before the authority implementation. The file was not rewritten after results. The note in the fixture says not to rewrite a failed holdout to match a result. None failed.

Scorer: `score_case` in `tests/test_pr_eg_dialogue_quality.py`. Dimensions are separate booleans. A run of that file with `tests/test_pr_dc_subjective_followups.py` passed 73 tests, including every holdout dimension.

The scorer classifies the resolver and the authority record. It does not call the provider. Live behavior is artifact 13 and is not folded into these booleans.

| Id | Request | Expected posture | Improvisation | Narration determined | Deterministic result |
| --- | --- | --- | --- | --- | --- |
| established_road_name | general | established | no | no | All nine dimensions pass. Line may contain the north road. |
| watched_not_identity | surveillance | unestablished | no | yes | Road-name topic is not sufficient. Not an authoritative plan. |
| watched_reworded | surveillance | unestablished | no | yes | Same, different wording. |
| partial_patrol_fact | surveillance | partial | no | topic present, so not determined | Hedged patrol sentence is the partial answer. |
| forged_lantern_unknown | maker | unknown | no | yes | Uncertainty, no invented smith. |
| what_troubles_her | personal_state | belief | yes | no | Harmless subjective plan. |
| ordinary_preference | opinion | belief | yes | no | Improvisation permitted. |
| opinion_not_canon | opinion | belief | yes | — | Canonical stays false. |
| hidden_password | hidden | withheld | no | yes | Refusal class. |
| consequential_promise | promise | unestablished | no | yes | Uncertainty, no payment. |
| secret_allegiance | hidden | withheld | no | yes | Refusal class. The reply-plan function itself stays genuine uncertainty so the older secretly/promise tests still pass. |
| unresolved_mystery | mystery | unestablished | no | yes | No culprit. |
| relationship_not_invented | relationship | unestablished | no | yes | No marriage. |
| rumor_not_invented | rumor | unestablished | no | yes | No invented rumor. |
| background_porter_preference | opinion | belief | yes | no | Porter Edric, no authored biography required. |
| contradictory_plan_after_prior_topic | maker | — | no | yes | Prior topic does not leave the plan authoritative. Speech authority is not claim_only. |

Safety outcomes in the deterministic suite: no holdout line contains “settled here,” “speech authority,” “usually a patrol,” “the password is,” “I’ll pay,” “secretly serves,” or “we’re married.”

`test_identity_topic_does_not_answer_whether_the_road_is_watched` checks the sufficiency gate directly. `test_prior_topic_does_not_claim_an_authoritative_answer` checks the reconciliation. `test_chat_unknown_question_skips_narration_and_does_not_invent` posts the watched-road question through `chat` with a provider mock that would invent a patrol and a password. Provider calls are 0, the topic is not revealed, the world NPC list is unchanged, and the commitment is non-canonical across save/load.
