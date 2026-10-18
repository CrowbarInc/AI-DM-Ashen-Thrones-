# Regression Debt

Relevant inherited broad failures are documented in `artifacts/pr_dy_live_gameplay/PR-DY_regression_results.md`:

- 228 collected in the same file list, 199 passed, 29 failed.
- Failure names cluster around dialogue contract preservation, direct NPC questions, known follow-up bypass, unresolved question retry, repeated social questions, social pressure vs adjudication, embedded adjudication in mixed turns, mixed object investigation questions, social output repair, strict social speaker repair, attack mechanical resolution, observe resolution kwarg, and exploration parsed routing.

Direct relevance: conversational routing, NPC dialogue, action interpretation, mixed actions, response integrity, and player questions are high. Scene transitions/movement are moderate to high.

Interpretation: these failures are not random test noise. They are the same architectural stress point observed in human play: a turn must pass through several brittle contract/router/emission layers, and many tests assert that one layer must not erase meaning established by another.

No tests were repaired or expected outputs updated in PR-DZ.
