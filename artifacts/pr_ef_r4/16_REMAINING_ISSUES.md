# 16 — Remaining Issues

## Correctness

- Cold “What did you mean by the north road?” with an active-interlocutor flag and no prior visible turn was rejected as `malformed_communication` before continuation could run. The same sentence worked inside the ten-turn conversation. A malformed ownership payload still blocks the turn rather than falling through to the established interlocutor.
- “I put the question to one of them” with one NPC clarified without mutation, using the provider’s clarification sentence. A non-`INTERPRETED` record returns before addressee grounding, so the authorization template is not always the spoken line.
- Live interpretation-label agreement is 5/15 on the scored rubric. Behavior is ahead of the model’s recipient and purpose labels. That is expected, and it means label accuracy is not the acceptance metric.

## Dialogue quality

- Knowledge-gap speech is either the safe line or a short “I don’t know.” Neither is characterized beyond what current validation accepts.
- Turn 4’s GM answer repeats the road fact and also quotes the previous NPC sentence. It is consistent and redundant.

## Performance

- `genuine_uncertainty` and `authoritative_answer_available` with speech authority `none` still build the large strict-social prompt and can retry. Case B: 50,784 input tokens. Conversation turn 6: 51,910. Closing those without erasing acceptable uncertain lines needs a finer signal than the current reply-plan enum.
- Turn 2 still used strict-social (26,401 input tokens) to deliver an authored north-road line. The follow-up turn did not. The first delivery of a recalled topic is not yet on the narration skip.

## Technical debt

- `assess_addressee_grounding` is shared, but a non-interpreted record can still return before it runs.
- The pre-edit regression family was not re-run. The historical 321/20 figure is carried forward from PR-EF-R2.
- The working tree at `d31beb7` remains broadly dirty. This cycle did not isolate a commit.
- An earlier live attempt with interpretation forced off by `experiments.pr_dq` import is archived and is not evidence.
