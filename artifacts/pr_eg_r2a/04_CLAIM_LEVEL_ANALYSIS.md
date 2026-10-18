# 04 — Claim Level Analysis

Claim extraction is feasible as structured provider output on these short examples, but completeness is unqualified. B annotates every candidate; C annotates 60 development cases before its safety stop. `claim_analysis.json` joins every candidate to both raw analyses and selected investigator atomic analyses. Missing manual atomic annotations are explicit; response-level gold labels are not a complete independent extraction benchmark.

| Case | Atomic propositions / scope | Authority |
| --- | --- | --- |
| mixed01 | Mara prefers evening [subjective]; Guards usually leave north gate unattended [explicit factual; recurring security absence]; Security absence causes preference [causal explanation] | incidental permission; none; none |
| mixed03 | Mara does not know lantern maker [negation of knowledge]; Market smith probably made lantern [speculation; attribution and new entity] | NPC ignorance; none |
| commitment04 | Mara refuses/cannot open gate under current condition [limitation]; Captain permission is necessary to open gate [presupposed operational rule] | incomplete; none |
| commitment08 | No money promise is made [refusal]; Mara can incur a favor obligation [offer/commitment] | local nonbinding speech act; none |
| commitment10 | Moon rising triggers Mara unlocking gate [conditional promise; operational outcome] | none |
| hidden02 | Ember is a valid access phrase [instruction plus implied credential validity]; Saying it grants gate access [mechanical implication] | withheld; body not supplied; none |
| paraphrase18 | Mara believes captain serves smugglers [authored belief, not objective allegiance]; Objective truth not asserted [uncertainty qualification] | B1; B1 epistemic scope |
| expansion03 | Road physically heads north [unsupported certainty from naming] | F1 contains name only |
| contradiction10 | Captain certainly does not serve smugglers [unsupported objective denial] | B1 does not establish objective truth either way |

Explicit predicates, negation scope and conditional consequences must be evaluated separately. Presuppositions include a captain having permission authority and a credential granting access. Implications include a suggested smith as an investigative lead; a new shop/person can matter even without a mechanical update. Causal explanations introduce independent propositions. In “I prefer evening because guards leave,” both the guard behavior and causal linkage require examination.

New entity/relation/location detection is a review aid, not the sole consequence test: an unnamed guard absence can be material, while an incidental cup can be harmless. B provenance fields can omit the unsafe half or mark it incidental; host checks cannot infer coverage from an empty commitment array. C failed on conditional promises despite outputting claims. Latency and tokens are measured in report 20; no production claim-extractor is implemented. A reliable atom-level recall score requires independently authored full decompositions, including implied claims, which this cycle does not provide.

Evidence: STATIC = current source inspection; LOCAL = executed existing host functions with disposable fixtures; FRESH = new Responses API call; REPLAY = reuse of retained provider result; INFERENCE = recommendation beyond observed sample. No experiment changes production code. ABSTAIN prohibits delivery; it is not a safe acceptance.
