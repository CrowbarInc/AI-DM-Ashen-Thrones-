# 05 — Semantic Equivalence

Entailment must preserve referents, polarity, modality, temporal scope and disclosure entitlement. Shared tokens do not establish equivalence. F1 supports “People call that street the north road”; it does not support destination, compass direction, royal naming cause or access conditions. F2 independently authorizes a destination. B1 authorizes an attributed belief, not objective allegiance or its negation.

Controlled corpus contains 20 paraphrases, 15 expansions and 10 contradictions, with lexical variants and changed word order. Safe simplification removes rhetorical shell but not uncertainty. Harmful omission removes “I believe” or disclosure scope. Causal explanation introduces a new predicate, even when the naming clause remains exact.

Measured C development outcomes:

| Case | Gold | C verdict | Candidate |
| --- | --- | --- | --- |
| paraphrase01 | ACCEPT | ACCEPT | The road outside the gate is called the north road. |
| paraphrase02 | ACCEPT | ACCEPT | People call that street the north road. |
| paraphrase04 | ACCEPT | ACCEPT | The name of the street beyond the gate is the north road. |
| paraphrase05 | ACCEPT | ACCEPT | North road is what that street is called. |
| paraphrase07 | ACCEPT | ACCEPT | Beyond the gate, the street bears the name north road. |
| paraphrase08 | ACCEPT | ACCEPT | That thoroughfare outside the gate goes by north road. |
| paraphrase10 | ACCEPT | ACCEPT | The street you mean, just beyond the gate, is known as the north road. |
| paraphrase11 | ACCEPT | ACCEPT | The street past the gate is named north road. |
| paraphrase13 | ACCEPT | ACCEPT | For the street outside the gate, use the name north road. |
| paraphrase14 | ACCEPT | ACCEPT | You mean the street beyond the gate. Its name is north road. |
| paraphrase16 | ACCEPT | ACCEPT | The north road leads to the fortress. |
| paraphrase17 | ACCEPT | ACCEPT | The fortress is where the north road leads. |
| paraphrase19 | ACCEPT | ACCEPT | Mara thinks the captain works for smugglers; that is only a belief. |
| paraphrase20 | ACCEPT | ACCEPT | The north gate is watched all night. |
| expansion01 | REJECT | REJECT | The north road runs directly to the royal fortress. |
| expansion02 | REJECT | REJECT | The street was named by the king. |
| expansion04 | REJECT | REJECT | It is the shortest way to the fortress. |
| expansion05 | REJECT | REJECT | The road is safe after dark. |
| expansion07 | REJECT | ABSTAIN | The street has no tolls. |
| expansion08 | REJECT | ABSTAIN | The road connects to a hidden village. |
| expansion10 | REJECT | REJECT | A royal decree named it after the northern conquest. |
| expansion11 | REJECT | ABSTAIN | There are three sentries at its far end. |
| expansion13 | REJECT | ABSTAIN | The road takes one hour to walk. |
| expansion14 | REJECT | ABSTAIN | You can camp there without attracting patrols. |
| contradiction01 | REJECT | REJECT | The street beyond the gate is called the south road. |
| contradiction02 | REJECT | REJECT | That street is not called the north road. |
| contradiction04 | REJECT | REJECT | The street beyond the gate has no name. |
| contradiction05 | REJECT | REJECT | North road is the name of the street inside the gate. |
| contradiction07 | REJECT | REJECT | The north road leads only to the market, not the fortress. |
| contradiction08 | REJECT | REJECT | The north gate is never watched at night. |
| contradiction10 | REJECT | REJECT | The captain certainly does not serve smugglers. |

Several unsupported expansions were ABSTAIN rather than REJECT: these prevent delivery but lower exact three-way classification accuracy. This distinction is retained. A/B accept exact support only and therefore fail to deliver many faithful paraphrases. Existing host validator results for all 102 are retained separately; they are synthetic-resolution compatibility evidence, not a new semantic authority. No holdout C equivalence result exists because the strategy stopped.

Evidence: STATIC = current source inspection; LOCAL = executed existing host functions with disposable fixtures; FRESH = new Responses API call; REPLAY = reuse of retained provider result; INFERENCE = recommendation beyond observed sample. No experiment changes production code. ABSTAIN prohibits delivery; it is not a safe acceptance.
