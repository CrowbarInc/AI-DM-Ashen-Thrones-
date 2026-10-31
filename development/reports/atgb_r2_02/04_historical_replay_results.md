# 04 — Historical Replay Results

Replay used the captured adapted interpretations, the frontier-gate roster, and a social focus on `tavern_runner`. No model was called. Artifact: `artifacts/atgb/atgb_r2_02/historical_replay_after.json`. The before state is `baseline_reproduction.json`.

## S03.3

| | Before | After |
|---|---|---|
| Extracted candidate | you again later | you |
| Grounded target | none | tavern_runner |
| Provenance | provider_candidate_only | established_interlocutor |
| Eligibility | requires_clarification | executable |
| Decision | CLARIFY / unresolved_addressee | EXECUTE / single_authoritative_component |
| Player-facing decision text | Which person do you mean... | empty |

The which-person question is gone. No pending ambiguous-addressee record is created. The decision does not invent a promise that the runner will repeat the rumor. With the rumor already revealed, the existing resolver returns `genuine_uncertainty`, speech authority `none`, and no new topic. That is the same resolver result as an explicit address of the runner.

## S05.3

| | Before | After |
|---|---|---|
| Extracted candidate | me more | me |
| Grounded target | none | tavern_runner |
| Provenance | provider_candidate_only | established_interlocutor |
| Eligibility | requires_clarification | executable |
| Decision | CLARIFY / unresolved_addressee | EXECUTE / single_authoritative_component |
| Player-facing decision text | Which person do you mean... | empty |

"me more" is not an NPC. The decision text does not contain the rumor and does not add muddy-footprint wording. The captured public-evidence map is unchanged. The resolver, given the already revealed rumor, again returns `genuine_uncertainty` and reveals no topic. The model's subject string is not copied into a new world fact.

## Remaining ambiguity

S05.3's subject is still not answered. The host now knows the recipient. It does not decide whether "that" means the rumor or the refused board question. The resolver's existing uncertainty plan is not a focused which-account question. This pass does not add that question.

## Downstream disposition

Both turns are handed to the existing single-ASK execution path. Grounding and the decision function do not mutate the session or world state. Resolver bookkeeping was checked on copies. World flags and factions stayed unchanged.
