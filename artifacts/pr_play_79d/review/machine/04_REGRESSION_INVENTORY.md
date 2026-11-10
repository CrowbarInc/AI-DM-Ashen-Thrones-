# Pre-implementation inventory

79C initial archive: eight new identities against PR78A. Later report says three repaired without a final full rerun. Current reproduction is retained in XML.

| Exact identity | Original baseline | 79C | Assertion / cause |
|---|---|---|---|
| tests.test_pr_play_61_player_facing::test_four_actions_keep_authority_and_recover | pass | fail | Repeated notice examination must include the previously disclosed ROUTE; final engine sentence discarded recall. |
| tests.test_pr_play_66_publication::test_publication_http[no_new] | pass | fail | trace['publication']['invariant'] == 'PASS'; final engine early return skips verifier. |
| tests.test_pr_play_66_publication::test_publication_http[continuity] | pass | fail | Same absent publication record. |
| tests.test_pr_play_66_publication::test_publication_http[fast_path] | pass | fail | Same absent record; also requires deterministic repeat with zero generation. |
| tests.test_pr_play_47_controlled_renderer::test_matrix[5] | pass | fail | row == original; narration_skip stamps caller-owned resolution metadata during a read-only selection. |

Additional candidates rechecked: PR62 action-specific fallback, PR69 structured/chat repeat. Their original expectations must be evaluated against the explicit new recall contract; any changed assertions will be documented.
