# 11 — Enforcement Strategy B

FRESH + LOCAL: provider returns a fixed candidate's speech plus claim source ids, incidental/uncertainty/commitment annotations; host checks speech identity, source-id existence, and whole-speech support through A. It never accepts a source id as entailment. Unknown ids reject; otherwise unresolved semantics abstain.

This is a structured provenance/annotation surrogate on a frozen candidate corpus. The model did not freely generate fresh dialogue under this contract, so the experiment does not measure structured generation quality, its naturalness, or a production structured generator's total cost. It does measure whether self-reported provenance resolves host semantic verification. It does not: A's paraphrase limitations remain. An unsafe candidate can cite a real source while introducing unrelated claims; forged tests show the host does not accept that as support.

development: 72 evaluated, 0 untested. 

| Gold / actual | ACCEPT | REJECT | ABSTAIN |
| --- | --- | --- | --- |
| ACCEPT | 5 | 0 | 25 |
| REJECT | 0 | 0 | 39 |
| ABSTAIN | 0 | 0 | 3 |

holdout: 30 evaluated, 0 untested. 

| Gold / actual | ACCEPT | REJECT | ABSTAIN |
| --- | --- | --- | --- |
| ACCEPT | 0 | 0 | 12 |
| REJECT | 0 | 0 | 16 |
| ABSTAIN | 0 | 0 | 2 |

The first response used Markdown fences despite a JSON instruction and failed the original parser. Raw failure retained; exact fence removal added on development data, without changing prompts, labels or decision policy. Subsequent fixed strategy evaluated 102 candidates, plus repeated/single annotation probes. `forged_provenance.json` includes malicious real-id claims, fabricated ids and mixed speech. Structured output aids audits and catches malformed references but moves semantic work to the verifier. Costs and repeatability are measured, not treated as evidence of authority.

Evidence: STATIC = current source inspection; LOCAL = executed existing host functions with disposable fixtures; FRESH = new Responses API call; REPLAY = reuse of retained provider result; INFERENCE = recommendation beyond observed sample. No experiment changes production code. ABSTAIN prohibits delivery; it is not a safe acceptance.
