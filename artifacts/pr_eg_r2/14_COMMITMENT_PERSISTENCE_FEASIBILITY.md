# 14 — Commitment Persistence Feasibility


STATIC + LOCAL: `dialogue_authority.py:433` stores one whole delivered line as a typed opinion, refusal, partial answer or admitted uncertainty. Established facts are not stored as incidental commitments. The record includes NPC id, lexical subject, requested-information type, turn, status, text and canonical=false. `conversational_continuity.py:169` separately records up to eight delivered exchanges, preserving speaker, actual supplied text, subject and uncertainty. API call sites store the delivered result, not rejected provider drafts.

Bounds: 24 total commitment rows, eight active per NPC, line text capped at 180 characters. Differing text on the same NPC+subject marks older records revised; deduplication is textual, not a semantic consistency check. The recorder itself does not validate safety or contradictions. `persistence_probe.json` deliberately inserts evening then morning through the trusted recorder: first becomes revised, second active. That is a recorder demonstration, not unauthorized production delivery.

LOCAL: storage.save_session/load_session round-tripped the contextual records exactly; world unchanged. This demonstrates existing serialization is adequate for bounded records in this sample, not that long-term recall or eviction is solved. `storage.py:221`, `:251` persist the session document; speech is not copied into NPC topics or objective world facts.

Retain stable self-descriptions, preference choices and meaningful reasons that later questions can reference; retain refusals/uncertainty sufficiently to avoid conceding repeated consequential requests. Ephemeral delivery style and momentary emotion may stay in the short exchange window. Nonbinding anecdotes may require retention if reused, but must not establish consequential history/locations.

Smallest prospective extension: reuse the existing store and save/load, attach a validated semantic subject/fact type plus source delivered-exchange id, distinguish stable preference from ephemeral mood, and compare proposed incidental details with active commitments before delivery. Preserve the original accepted meaning when another wording is emitted; do not revise merely because the string differs. Bound truncation by semantic units; store or reference the accepted short statement, not an arbitrary cut that can lose negation. No new NPC agent database is justified. These are requirements, not an implemented schema or approved extractor.

The model must not reconstruct evicted commitments or turn unvalidated history into authoritative facts. Noncanonical speech remains relevant to continuity and player decisions; canonical=false is a persistence classification, not a safety verdict.


Evidence labels: **FRESH** = actual isolated provider response; **LOCAL** = executed production helper with disposable fixtures; **STATIC** = source inspection; **HISTORICAL** = retained PR-EG-R1/earlier evidence; **INFERENCE** = assessment beyond the measured sample. No isolated result is full production qualification.
