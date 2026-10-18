# 16 — Remaining Issues

## Dialogue quality

- A follow-up that a player hears as Mara’s question can still be answered in internal language: “That has not been established in the information available to you.”
- A follow-up to a fact she just stated can discard that fact and say she couldn’t tell you.
- A harmless preference can still be answered as ignorance.
- A player clarification can be handled as an undo.
- A request for a promise can be answered as an action the engine cannot carry out.
- Determined gaps share two sentences. They are natural compared with “settled here,” and they are not particular to the person or the question.
- Public scene sentences, including that Mara looks concerned, are not used as partial answers.

## Improvisation

- Recovery needs a separable harmless quotation. A single sentence that mixes a feeling with a new world condition is rejected whole.
- The model still produces consequential color (“usually calmer,” “something’s lurking”) on personal questions. Validation is right to reject it. The player then depends on recovery or on the generic line.
- Opinions are not a personality, and they are not checked against later contradictory remarks except by replacing the same subject’s commitment.

## Performance

- One strict-social narration is still about 26,000 input tokens.
- The “what did you mean” turn spent 52,957 input tokens and a retry to reach a worse answer than the run before it.
- Determined questions avoid that narration. Ordinary answered questions do not.

## Correctness

- The passive clock still moves on executed social asks, including incidental ones.
- The commitment list retains revised rows without a hard cap on the raw list.
- `visible_supporting_sentence` is unused by the spoken line. The scene argument is accepted and not applied.
- Live interpretation can route the same follow-up differently across two fresh runs. Turn 3 is the example.

## Debt

- Request kinds are regular expressions. Wording outside them stays `general` and can still be answered with a nearby topic.
- The reply-plan function does not itself mark hidden or promise questions, so the plan label and the posture can differ. The spoken line follows the posture. A reader of the plan alone can still see `genuine_uncertainty` for a withheld password if they ignore the authority record. The live password turn did show `genuine_refusal` and the withheld line.
- The live dimension helper’s naturalness check does not match every internal phrase the classifier knows. The transcript in artifact 13 is the human score.
