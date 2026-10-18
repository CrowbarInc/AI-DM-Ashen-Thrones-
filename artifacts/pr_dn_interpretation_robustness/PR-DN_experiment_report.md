# PR-DN Experiment Report

MODE: LIVE INTERPRETATION ROBUSTNESS

PRODUCTION INTEGRATION: NONE

HEAD: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`

The worktree was dirty at start and was preserved. Production save writes were blocked by `ProductionSaveGuard`; engine provider paths were blocked by `forbid_provider_calls`; only the explicit PR-DN interpretation calls were allowed.

Provider model: gpt-4.1-mini

Live request count: 12

Actual input tokens: 9347

Actual output tokens: 1810

Actual total tokens: 11157

Useful interpretations: 2 full, 5 partial, 5 failed among executed live rows.

Authority-control failures: DN05, DN07, DN08, DN09, DN10.

Decision: D
