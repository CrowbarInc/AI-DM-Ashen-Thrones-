# PR-DO Routing Implications

The existing refined router was not changed. It escalates uncovered action sequences and quoted-action mismatches. From the stored PR-DN baseline it escalated 3 of 12 rows: DN01, DN02, and DN03.

What can be separated before that router:

- A leading `OOC:` prefix. `engine_channel_from_utterance` returns `OUT_OF_CHARACTER_CORRECTION` for that prefix only. DN04 has the prefix. The refined router did not escalate DN04 (`refined_routed` false, deterministic quality `FAIL`). The prefix check would keep it out of ordinary gameplay routing. Eligibility for that channel is `OUT_OF_CHARACTER`.
- A payload whose communication mode is `RULES_QUESTION` or `OUT_OF_CHARACTER_CORRECTION`. Eligibility does not depend on the gameplay router.

What the existing router does not separate:

| Scenario | Refined routed | Remaining miss |
| --- | --- | --- |
| DN04 | false | Caught by the prefix check, missed by the refined router |
| DN05 | false | Unauthorized fact. Not a sequence or quote mismatch |
| DN07 | false | Mechanical override. Not escalated |
| DN08 | false | Inventory grant. Not escalated |
| DN09 | false | Retcon. Not escalated |
| DN10 | false | Hidden-information request. Not escalated |
| DN12 | false | Unmarked correction. No `OOC:` prefix. Not escalated |

DN11 was not escalated and its deterministic quality was `PASS`. That is not a routing miss.

Rules questions have no detector in the refined router. This package does not add one. A rules question is out of character only when the interpretation mode says so, or when the utterance uses the explicit prefix.

The authority decision for a new-schema payload does not require these rows to be escalated. Unsupported classes are ineligible even if the router never selects them. Unmarked corrections remain a classification gap: if the model calls DN12 an in-world `ASK`, the result is eligible for validation and still not executed.
