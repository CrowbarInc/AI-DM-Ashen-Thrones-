# Next step decision

Ranked remaining foundational gaps:

1. Real model interpretation and unfamiliar reference language are unmeasured; deterministic authority checks do not prove understanding.
2. Sustained continuity/grounded recovery remain limited; the broad sample still has only 12/40 successful gameplay cases.
3. Live provider latency, retry and timeout behavior is unmeasured.
4. Unsupported-action recovery lacks capability, and legacy scene requests lack durable cross-process HTTP receipts.

Recommend `pr_play_controlled_model_intent_and_grounding_evaluation`, an evaluation milestone before adding mechanics. Use held-out unfamiliar paraphrases, short follow-ups and state-grounded judgments, separating interpretation, admission, commitment and publication errors. This is selected because the deterministic authority defect is repaired while model-facing behavior remains unmeasured.

Proposed design only: 20 cases, at most two attempts each (40 calls maximum), explicit per-call input/output token caps, retry/timeout limits and budget refusal. Select a provider/model and calculate an agreed dollar ceiling from its current prices before authorizing execution. No model or prices were selected here; a dollar figure would be invented. Obtain approval of that concrete design/cost ceiling before future live calls. Nothing from this next milestone was executed.

Defer new subsystems, providers, universal frameworks and the paused `pr_play_social_check_repeat_and_legacy_stance`. Do not automatically start the recommendation.
