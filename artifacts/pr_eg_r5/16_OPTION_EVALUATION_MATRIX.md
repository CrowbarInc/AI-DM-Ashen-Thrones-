# 16 — Option Evaluation Matrix

PR-EG-R5 · 2026-10-17 · investigation only

Ratings are architectural estimates, not measurements of implemented alternatives. H/M/L refer to relative desirability except explicit cost/risk fields.

| Criterion | A repairs | B consolidated host | C AI semantics/host authority | D rewrite |
|---|---|---|---|---|
| Conversational flexibility | L–M; fixtures improve | M; lexical ceiling | H expected, unqualified | H potential, unqualified |
| Information integrity | retains current controls | H if same gate retained | H conditional on source binding and scope | uncertain until all controls ported |
| State integrity | existing resolver boundary | existing boundary | host only; zero provider effects | must reconstruct integration |
| Implementation complexity | low per patch, cumulative high | medium | medium/high | very high |
| Regression risk | low local, hidden interaction risk | medium | medium/high staged | high |
| Maintainability | poor as patches accrue | good | good only after owner deletion | unknown until migration ends |
| Provider cost | unchanged tail exposure | can cap tail, usually zero semantics | one compact plan + optional expression | unknown |
| Latency | low fast path, expensive tail | predictable but may fail to understand | bounded one/two-call path; measure | unknown |
| Debuggability | many decision traces | one deterministic trace | semantic evidence spans + host reasons | design-dependent |
| Compatibility | highest | high | reuse bridge, resolvers, seal, storage | lowest |
| Migration | small fixes, no owner change | merge and remove selectors | semantic proposal → host eligibility; staged replacement | large cutover or long duplication |
| Harbor relevance | local patch | shared but limited semantic filter | explicit relation/coverage evidence | possible, not assured |
| Correction / recovery | repeated exception risk | coherent state helps | explicit correction links expected to help | possible |
| Preference / named recall | direct host fixes possible | strong consolidation benefit | shared source binding plus semantics | unnecessary for these defects |
| Incidental conversation | constrained by current categories | still constrained | flexible within separately authorized scope | broad flexibility, broad risk |

C wins conditionally because failures include relational meaning that consolidated lexical rules will still struggle with. B would be preferable if the first C slice cannot achieve relevance, authority and budget gates together. A lacks a credible generalization argument. D is premature without trying the narrower boundary change.
