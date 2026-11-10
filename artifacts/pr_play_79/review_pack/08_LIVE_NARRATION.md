# 08 — Live narration

The extended session left the provider enabled. Model: `gpt-4.1-mini-2025-04-14`.

Completed provider requests in that session: 13. Total tokens: 144,968. This is above the suggested 80,000-token budget. One opening `primary_turn` alone was 26,676 tokens. The session then stopped rather than continuing into a second opening.

Narration rewrites (`presentation` log):

- Requests: 2
- Accepted: 0
- Rejected: 2
- Published rewrites: 0
- Fallbacks: 2

Rejection reasons: `not_a_variation` plus `consequential_or_hidden` (the candidate repeated "northwest"), and `consequential_or_hidden` on a "no hidden passage" sentence. The player saw the deterministic scene text, not those candidates.

The campaign opening is the one published provider narration. Later turns did not publish a live rewrite. Browser campaigns stubbed `call_gpt` and are not live narration.
