# 13 — Performance Comparison

## Workloads are not the same

PR-EF-R3 measured the PR-EF-R2 eleven-turn conversation at about 197,112 input tokens: 19,277 interpretation, 96,180 strict-social narration, 81,655 retries. That figure is not a before-image of this cycle’s cases. This report does not claim a global token reduction.

R4 measured six fresh single-turn shapes on disposable state, plus the ten-turn conversation above. Median conversation latency 2,411 ms. Maximum conversation latency 5,054 ms. Qualification total: 49 requests, 494,725 input tokens, 7,349 output tokens, 502,074 total. That total includes holdouts and is not comparable to the eleven-turn figure.

## Cases

| Case | Calls | Interpretation | Narration | Retry | Input | Output | Latency |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A. Established north-road dialogue | 1 | 1 | 0 | 0 | 1,820 | 181 | 2,521 ms |
| B. Who forged the lantern | 3 | 1 | 1 | 1 | 50,784 | 360 | 7,070 ms |
| C. GM description | 1 | 1 | 0 | 0 | 1,704 | 193 | 2,417 ms |
| D. Inspect the lantern | 1 | 1 | 0 | 0 | 1,704 | 172 | 3,691 ms |
| E. Ambiguous “one of them” | 1 | 1 | 0 | 0 | 1,716 | 203 | 2,389 ms |

A, C, D, and E do not call narration or retry. E’s clarification is the authorization line. D’s clue line is resolver-owned. A’s north-road line is the recalled authored topic.

B is the knowledge-gap shape R3 flagged. It still spent ~50k input tokens. The reply plan was `genuine_uncertainty`, speech authority `none`, and the retry’s accepted text was “I don’t know.” The closed-plan skip does not cover that plan, because an acceptable generated line existed. See report 10.

## Recoverable retry (case F)

Case B is the live recoverable failure. The first strict-social output failed `question_rule:first_sentence_not_explicit_answer`. One `retry_escalation` followed and an alternative was accepted. Retries were not disabled.

Conversation turn 6 is the contrasting cost: narration plus retry ended on the safe line because the plan was `authoritative_answer_available` rather than `consequential_information_request`. That chain is not removed.

## Conversation token shape

Turns that only interpret, or that do not call the provider at all: 1, 3, 4, 5, 7, 8, 9, 10. Turns that still pay a social prompt: 2 (authored line via strict-social, 26,401 input) and 6 (safe line after retry, 51,910 input).
