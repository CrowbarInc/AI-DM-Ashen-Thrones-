# PR-CH Authored Answer Pipeline

A. Authoring - CONFIRMED

`KILN_FACT = "Kiln three is banked from dusk until the morning bell."` exists in the test fixture and is attached to the Kiln Tender topic `kiln_bank`.

B. Retrieval - CONFIRMED

The target HTTP reproduction logs `[CLUE DISCOVERED] social_brine_yard_kiln_tender_kiln_bank`.

C. Candidate generation - CONFIRMED

`select_best_social_answer_candidate(...)` can select `resolution:topic_revealed` as `structured_fact`.

D. Relevance - CONFIRMED

The non-HTTP tests for asking about kiln three pass. The unrelated copper-chit topic is not selected for the kiln-bank question.

E. Authority - CONFIRMED

The target speaker is explicitly addressed and scene-present. `grounding_reason_code` is `authoritative_speaker_eligible`.

F. Selection - CONFIRMED

The deterministic social resolver selects `kiln_bank`.

G. Generation - SUPPORTED

The authored-answer helper formats the selected answer as a grounded NPC line.

H. Validation - SUPPORTED

The HTTP path does not preserve that selected answer into final text. The final emission lifecycle can seal accepted/safe responses as immutable.

I. Fallback - CONFIRMED

The observed generic refusal text comes from `generic_ask_completion` through `safe_nonresolution`.

