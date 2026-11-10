# PR-PLAY-24 failure analysis

First decisive conversational failure: NPC knowledge source selection / contextual grounding (boundary 10, NPC knowledge authority). Confidence HIGH from live function input/output, provider contract and published response.

Expected: runner can describe the already advertised hot stew and paid rumors, without inventing a price, sale, quest or consequential world fact.

Observed: Tavern Runner says, "I couldn't tell you." The action interpreter, local approach normalization, binding, target resolution and social resolver all execute successfully. _next_topic_to_reveal returns null even though the scene input contains the public offerings sentence; authority grants no proposition and expression is constrained to uncertainty.

Evidence: trace_013 input (scene visible_facts and normalized metadata), trace_014 output null, trace_017 genuine_uncertainty, trace_018 empty authorized_proposition, request_03 empty authorized facts, trace_021 host selection, final accepted_response and public response. Source: social.py:1611 and 4460 onward; dialogue_authority.py:509 and 766.

Secondary failure: expressive_dialogue.py:_uncertainty_reasons/_closure_reasons/validate_expression reject the generated uncertainty for unsupported_addition (right/now). No useful grounded narration was generated and rejected. Publication successfully delivers the authorized engine fallback. Stop after the first completed HTTP action is correct; no retry or follow-up occurred. All three requests also exhausted the budget.

Known-failure relationship: reproduces the uninformative response already observed offline in PR-PLAY-23. PR-PLAY-22's action-binding failure is repaired and did not recur. No evidence identifies this exact conversational-source gap as one of the 17 baseline or eight expanded functional test failures; do not claim such a match. No broad test suite or unrelated repairs were attempted.

Smallest recommended repair investigation: an offline regression using these exact public scene/runner/question inputs, then a narrowly authorized mapping of the existing public offerings sentence into the selected NPC answer source. Keep unrelated patrol knowledge, private sources and state authority restricted. Do not start PR-PLAY-25 automatically. Expression lexicon inspection is secondary and cannot solve the primary gap alone.

Harness caveat: its native completion fields score structural completion, not usefulness. The custom quality guard stopped on the actual generic uncertainty. stop_and_quality_analysis.json explicitly records zero useful conversational turns rather than presenting the raw legacy meaningful counter as success.
