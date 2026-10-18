# 08 — Final-Response Integrity

The existing accepted_response is the final speech object. It carries exact text, host provenance/source and speaker. Narration selection creates it before an unnecessary provider call. Direct run_preserve_if_valid calls use the same boundary, so superseded drafts do not become immutable final speech. Draft-proposed scene/world effects and improvisation proposals are removed; resolver-owned state mutation has already run and is retained.

restore_accepted_text preserves the accepted host line when downstream processing tries to replace it. The former late personal replacement is removed. Delivered-history insertion receives the accepted host object and rejects a mismatched text or speaker. UNIT mutation test explicitly changes accepted text to an unrelated action refusal, verifies persistence rejection, then restores the seal. Production handler test compares player text, seal and saved history.

This cycle binds host-owned conversational speech only. Applying the check to all old non-social accepted responses initially broke three mechanical presentation tests; that overbroad scope was removed. Existing non-social finalization can still replace an old acceptance with resolver-owned presentation. Those paths are not claimed repaired. Exact initial failure output is preserved in post_final_junit.xml.
