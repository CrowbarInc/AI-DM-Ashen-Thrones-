# 10 — Enforcement Strategy A

LOCAL experimental deterministic claim allowlist: accept normalized whole-speech equality to an NPC-known, disclosure-permitted source, or a closed nonbinding personal-expression grammar in an incidental context. Otherwise ABSTAIN. This research grammar is not a production response catalog and has not been installed. It deliberately lacks semantic paraphrase resolution and is not a lexical risk-keyword classifier.

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

No unsafe acceptance observed; few safe lines delivered. Most exact mismatch cases abstain, including authorized high-risk paraphrases and harmless refusals. Safety on this finite corpus is not proof of arbitrary normalization correctness or contextual nonconsequence. This extreme demonstrates why reject/abstain-nearly-all is not a practical solution. Provider calls and tokens: zero; hot local timing in report 20. Complexity is low for tiny scope but maintenance scales poorly if wording variants become an expanding catalog. A complete frozen holdout was evaluated after development selection; no holdout tuning.

Evidence: STATIC = current source inspection; LOCAL = executed existing host functions with disposable fixtures; FRESH = new Responses API call; REPLAY = reuse of retained provider result; INFERENCE = recommendation beyond observed sample. No experiment changes production code. ABSTAIN prohibits delivery; it is not a safe acceptance.
