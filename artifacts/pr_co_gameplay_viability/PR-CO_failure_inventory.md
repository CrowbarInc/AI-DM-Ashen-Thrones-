# PR-CO Failure Inventory

Earliest demonstrated failing boundary: turn 1 final emission.

The social resolver selected `ask` / subject `social` / interlocutor `guard_captain` with no interpreter call. The model answered the preference. Hard validation rejected both attempts as `unauthorized_resolution_decision_fact` (`undeclared_consequential_claim` on the captain's gesture). `safe_nonresolution` then emitted two authored banner sentences. The player never received the preference.

That boundary repeated on turns 2–4: a usable model narration was rejected, a retry was also rejected, and a safe line replaced both.

## Classes

### A. Intent/routing failure

Turn 2. The utterance asks why the captain prefers what was just said. The interpretation proposal's primary operation is `ask`, interlocutor `guard_captain`, expected resolution "explanation of preference." The stored contract operation is `perceive`, request kind `clarification`, subject `perception`, resolver `exploration`. Social stages were not permitted.

### B. NPC conversational failure

Turns 1 and 2 as played. The captain does not answer the preference or the follow-up. The model drafts did answer; the emitted lines do not.

### C. Authored-answer failure

Turn 3. The captain is authorized to know "A patrol went missing near the old milestone." The resolver revealed that topic and stored it. Attempt 2 narrated that sentence. The player heard: Guard Captain says, "I cannot answer that from what is settled here."

### D. Exploration/adjudication failure

Turn 4. The notice board was bound as an existing visible feature. Inspectability is false on this default scene because there is no interactable. The model restated the posted taxes, curfews, and missing-patrol warning. Validation rejected that paraphrase (`notice_roster_history`). The player heard that the inspection established nothing further. No inscription was retained.

Turn 5's live observation was not generated. The fallback is grounded and grammatically broken. It is not scored as a model observation failure.

### E. Passive-world progression failure

Not demonstrated. The wait turn was not sent. Clocks did advance on the turns that ran, and turn 5 recorded operation-complete events without a spoken ambush.

### F. Continuity failure

Turn 1's replacement text became the only prior answer, so turn 2 quoted banners. Turn 3's contextual lead stores the refusal, while clue knowledge stores the patrol fact. Those records cannot both be what the captain told the player.

### G. Authority violation

No durable unauthorized mutation. The authority failure in play is over-rejection: harmless captain speech and an exact authored sentence were treated as unauthorized decision facts, while the social path still committed the topic. Turn 3 attempt 1's extra crossroads claim was correctly blocked.

### H. Final-emission/provenance failure

Turns 1–4. Accepted provenance is `safe_nonresolution` on attempt 2 after regeneration. The known `initial_generation` versus `regeneration` mismatch was not the emitted label here; the emitted label is the safe replacement. Turn 5 provenance is `fallback`, and the budget guard was labeled `unknown_api_error`.

### I. Token/context inefficiency

Measured. A first-pass social generation is about 31,000 input tokens before any conversation history of substance (`recent_log` on turn 1 is empty). Turn 1 character-share estimate, not a tokenizer segmentation:

| Bucket | Share of system plus first user message |
| --- | ---: |
| System/developer instructions | 15.6% |
| Policy and authority instructions | 29.2% |
| Mechanical resolution data | 33.0% |
| World and scenario state | 11.3% |
| NPC and scene context | 8.0% |
| Conversation history | 1.5% |
| Other (current player line and JSON syntax) | 1.4% |

The largest user keys on that request are `response_policy` (19.3% of the user JSON), `instructions` (12.7%), `turn_packet` (9.1%), `scene` (8.8%), `gm_resolution_decision` (7.4%), and `decision_facing_answer_recipe` (5.9%).

### J. Latency/retry inefficiency

Every gameplay generation was hard-invalid and retried. Four retries cost 161,822 tokens, 54.8% of the run. Turn 4's retry alone took 17.068 seconds and 2,292 output tokens while repeating declared claims. The 12-request cap was reached on turn 5 because of that retry pattern, before a generation for the observation.

### K. Other

Turn 5's probe budget exception was surfaced as a nonretryable upstream API error. That mislabel is an instrumentation interaction with `call_gpt`'s exception classifier, recorded so it is not mistaken for an OpenAI outage. Preflight itself was healthy.

## Not observed

Quiet-wait repetition, invented confrontation, and a retained invented inscription were not produced in the five turns. The wait turn and the continuity-check turn were not reached.
