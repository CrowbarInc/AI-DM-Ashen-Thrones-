# Limitations and risks

1. Interpretation admission refusals do not advance `session.last_publication`.

   On the final source, `Good day, Gate Guard.` was submitted twice.

   - First, the repaired server had replaced the superseded process. Provider accounting refuses to adopt an existing ledger (`open` with exclusive create). The refusal reason was `provider admission accounting unavailable`. No request was sent.
   - After a fresh ledger capped at the remaining budget, the same input went to live interpretation. The token estimate exceeded the remaining input ceiling. Reason: `input-token ceiling`. No request was sent.

   Both turns returned `I couldn't interpret that just now, so no gameplay action was taken.` The HTTP publication event recorded that sentence as `engine_or_grounded_fallback`. `session.last_publication` stayed on the previous accepted gameplay sentence. The return is marked `authoritative_mutation: false` and does not call `note_completed_publication`.

   This is the remaining publication-state gap. It is not the NPC fallback defect from PR-PLAY-79D-F. That fallback path now advances the pointer.

   Smallest correction: keep the refusal non-mutating, and stop classifying it as a completed gameplay publication. The alternative, writing the pointer on that return, risks historical tests that require the session to stay unchanged.

2. A new server process cannot continue an existing provider ledger. Restarting for a source fingerprint requires a new ledger. Caps must be set to the remaining cycle budget or the process would see a fresh allowance.

3. The holdout field name was aligned to `campaign_run_id` before the final recorded run. It is developer-authored.

4. Historical broader authority remains 0/9. Those failures are historical.

5. `game/api.py` contains unrelated uncommitted work from earlier cycles. This cycle did not revert it and did not commit it.
