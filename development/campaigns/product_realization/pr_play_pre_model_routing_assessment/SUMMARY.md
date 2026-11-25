# Pre-model routing assessment

Milestone: `pr_play_pre_model_routing_assessment`. Verdict: **A/PASS for assessment completion**, not a product or model-quality pass.

Verified ordinary HTTP ordering includes whole-request admission before deterministic conversational handling, then marking overrides, deterministic early returns, interpretation bridging, live interpretation eligibility, host validation, ordinary admission, resolver consequences, narration/publication and deferred time commitment. The supplied hypothesis omitted several important owners and the provider-disabled continuation.

36 cases: 31 across ten required categories, plus five historical reconstructions. Two offline modes produce 72 traces. Routing correctness **26/36 (72.22%)**; player-facing adequacy **15/36 (41.67%)**; consequence integrity **34/36 (94.44%)** in the disabled full runs. These are separate judgments with explicit per-case reasons, not a composite. Historical duplicates are not independent evidence.

Ten cases reach the interpretation function boundary when availability is forced true at a test seam. No model is invoked. Twenty-six cases bypass that boundary, including all five historical cases. This establishes route reachability, not production provider readiness or model competence.

Principal recommendation: separate uncertain semantic coverage from execution admission at `full_request_admission` / `_chat_turn` before the return at api.py:7989. Preserve whole-request execution withholding while allowing bounded interpretation or read-only information handling of UNCERTAIN wording. Keep genuinely independent compound actions on single-action clarification. Do not implement in this milestone.

A4 mistakes noncontact context for an unknown affirmative action; B1 mistakes orientation-plus-speech for uncertain multiple actions. Both protect state but prevent appropriate understanding. Other findings include mixed-request truncation, object-only clarification for social intent, and fallback time commitment for an unmatched search and an unresolved trailing condition. Missing Spellbook pages are a content limitation, not evidence that narration should invent them.

Current combined regression: 455 passed / 17 inherited failures. Focused: 470 passed / 1 inherited failure. New failure identities: zero. All 405 protected game/data files match the entry digest snapshot. Extensive prior dirty changes remain untouched.

PRODUCTION GAMEPLAY CHANGES: 0

LIVE PROVIDER CALLS: 0

See ROUTING_RESULTS, ARCHITECTURAL_RECOMMENDATION, REGRESSION_RESULTS and INTEGRITY. No implementation, commit, push, live benchmark, or paused social work was performed.
