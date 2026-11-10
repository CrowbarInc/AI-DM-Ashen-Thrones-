# 12 Player-facing publication

Two live sentences were published because combined validation returned PASS:

1. The first notice-board examination.
2. The repeated notice-board examination.

The rain-barrel and gate-observation candidates were not published. In the original live capture, those two responses were the sentence "Provider calls are disabled for this run, so no live narration was generated." That happened because ordinary model narration was disabled so only the integrated hook could call the provider.

The publication path now replaces that stub with the engine fallback when validation did not pass. `artifacts/pr_play_61/replay_results.json` shows the same four provider sentences going through the application again:

- PASS sentences remain the published narration.
- FAIL and REVIEW_REQUIRED publish the engine fallback.
- `rejected_text_published` is false for every action.

The player UI rendered those four corrected lines in order. Suggested actions included "Examine the Notice board (already searched)," which matches the engine.
