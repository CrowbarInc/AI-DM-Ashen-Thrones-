# PR-PLAY-35 — Five-turn live gameplay validation

**Verdict: C — FAIL.**

The isolated live session reached the configured provider and requested a campaign opening. The provider returned one completed structured response. The engine rejected that opening for `unauthorized_resolution_decision_fact`, showed the player a generic failure, and left `campaign_started` false. The five player turns were not submitted. They are BLOCKED.

This is a gameplay-start failure, not an infrastructure or provider-access failure. Process ownership, isolation, and the provider call succeeded. A working provider response did not produce a playable campaign.

No gameplay implementation file was changed. The user's campaign directory was not modified. Provider use was 1 request, 26,714 input tokens, 1,667 output tokens, 28,381 total tokens. The opening was not retried.
