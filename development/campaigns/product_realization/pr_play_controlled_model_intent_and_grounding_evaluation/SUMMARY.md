# pr_play_controlled_model_intent_and_grounding_evaluation

Verdict: **A/PASS — preparation complete**. Failure class: not a repair. This milestone designs and validates a controlled evaluation. It does not measure live-model play.

HARNESS_READY: YES

BUDGET_READY: YES

LIVE_EXECUTION_READY: NO — pending explicit authorization

The ordinary gameplay model is OpenAI `gpt-4.1-mini`. Twenty held-out cases are defined across five four-turn sequences on the frontier-gate seed. The harness scores intent, reference, admission, consequence, continuity, narrative grounding, and operational performance separately. PARTIAL is not PASS. Safe withholding is not execution success. Deterministic validation used local fixtures and two isolated provider-disabled sessions. Provider client constructions: 0. External hosts: none.

Historical scores stay 12/40 successful, minimum quality 22/40, mean actionability 1.675, supplementary executable 5/55. No comparison with a new live sample is made.

Live provider calls authorized: NO. Live provider calls executed: 0. The paused milestone `pr_play_social_check_repeat_and_legacy_stance` was not resumed. No commit and no push.

Approved spending ceiling, if a later milestone is explicitly authorized: **$0.53 USD**. Call ceiling: 40 provider requests. Per-call input cap: 24,000 tokens. Per-call output cap: 600 tokens. Per-call timeout: 45 seconds. Wall clock: 1,800 seconds.
