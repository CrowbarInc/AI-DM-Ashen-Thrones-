# Three-case analysis

Milestone `pr_play_claim_acceptance_audit`. Fresh provider-free HTTP and nested function captures; unchanged fixtures. Full state and authority in three_case_trace.json.

## Hidden brass token

Request: `I inspect the brass token.`

Candidate and final publication (identical): **You pry up the hopper and pocket the brass token.**

The player asks to inspect, not pry the hopper or retrieve an item. Hidden_facts contains “A brass token is sealed under the grain hopper.” The token is undiscovered: visibility=false, inspectability=false, no interactable id, clue or revealed-hidden entry. The canonical hopper does not authorize prying under it.

The hint explicitly forbids confirmation/reveal. No item delta, permitted mutation, physical adjudication, authored consequence, world update or transition authorizes retrieval. success=True means the investigate request was handled, not acquisition. Unchanged inventory corroborates absent authority and is not the sole proof.

| Stage | Evidence |
|---|---|
| Creation | Existing `_chat` local game.api.call_gpt stub via _gm_response; no live sample |
| Structured outcome | investigate success=True; state_changes={}, world_updates=null, no clue/discovery/transition, permitted mutations=[] |
| Extraction | audit_narrated_claims twice, both []; declared envelope absent |
| Claim validation | audit invoked; hard_valid=true; proposed_facts/claim_results/violations=[]; no decision for missed assertion |
| Hard validation | reasons=[], soft_flags=[], mechanical claims=[]; perception checked=true and unsupported=false |
| Acceptance | initial_hard_valid; authority_result=accepted; adoption_status=candidate_accepted; literal candidate_status absent |
| Seal | attempt 1 initial_generation, immutable=true, accepted delivery digest |
| Grounding | skipped at leave_text_unchanged; force_surface for authored_hidden not reached |
| Publication | HTTP 200; exact candidate; internal authority hidden by public DTO contract |
| Persistence | character unchanged=True; world NPCs unchanged=True; ordinary turn/log/conversation persistence occurs |

Unsupported acquisition and hidden-target confirmation; inventory still has the same spellbook. No authoritative retrieval through another mechanism appears in the traced production path.

Existing renderer candidate: `You find no such thing among what is actually present. A soot-stained skylight leaks pale noon light onto the loft floor.`

Direct hard_valid=False; reasons=['unauthorized_resolution_decision_fact']; unsupported_perception=False. Untouched lifecycle final: `A soot-stained skylight leaks pale noon light onto the loft floor.`. This is an isolated owner probe, not a repaired HTTP route.


## Glassport shipping crews

Request: `I inspect the shipping ledger.`

Candidate and final publication (identical): **The ledger lists eight named crews bound for Glassport.**

Player requests inspection of the shipping ledger. The only shipping fact is the Loft Clerk topic “I checked the shipping records this morning.” authored_abstract_reference means an abstract reference exists, not an inspectable ledger. Visibility and inspectability are false.

Resolver hint forbids instantiating a physical object or inventing contents. Four existing decision facts are scene observations, not crew/destination facts. There is no selected clue, mutation or approved improvisation/world-fact proposal for this record.

| Stage | Evidence |
|---|---|
| Creation | Existing `_chat` local game.api.call_gpt stub via _gm_response; no live sample |
| Structured outcome | investigate success=True; state_changes={}, world_updates=null, no clue/discovery/transition, permitted mutations=[] |
| Extraction | audit_narrated_claims twice, both []; declared envelope absent |
| Claim validation | audit invoked; hard_valid=true; proposed_facts/claim_results/violations=[]; no decision for missed assertion |
| Hard validation | reasons=[], soft_flags=[], mechanical claims=[]; perception checked=true and unsupported=false |
| Acceptance | initial_hard_valid; authority_result=accepted; adoption_status=candidate_accepted; literal candidate_status absent |
| Seal | attempt 1 initial_generation, immutable=true, accepted delivery digest |
| Grounding | skipped at leave_text_unchanged; force_surface for authored_abstract_reference not reached |
| Publication | HTTP 200; exact candidate; internal authority hidden by public DTO contract |
| Persistence | character unchanged=True; world NPCs unchanged=True; ordinary turn/log/conversation persistence occurs |

Unsupported authoritative factual disclosure: eight crews and Glassport are actionable player information. Text acceptance is demonstrated; acceptance/promoting as canonical new world truth is not. No crew NPCs, ledger or lead is created.

Existing renderer candidate: `That remains something spoken of, not a surface you can inspect here. What you can actually see is a soot-stained skylight leaks pale noon light onto the loft floor.`

Direct hard_valid=True; reasons=[]; unsupported_perception=False. Untouched lifecycle final: `That remains something spoken of, not a surface you can inspect here. What you can actually see is a soot-stained skylight leaks pale noon light onto the loft floor.`. This is an isolated owner probe, not a repaired HTTP route.


## Kiln schedule overseers

Request: `I inspect the glass kiln schedule.`

Candidate and final publication (identical): **The kiln schedule names four new overseers.**

Player requests inspection of the glass kiln schedule. No such schedule is authored; visible facts are skylight, maize and tariff slate. The sole tariff clue concerns dock fees, not overseers. Classification=unsupported, existence/visibility/inspectability=false.

The hint forbids object, contents, clue and lead invention. No clue, mutation, authorized roster/NPC creation or fact proposal grants four overseers. New NPCs are not inherently invalid; this particular context lacks authority.

| Stage | Evidence |
|---|---|
| Creation | Existing `_chat` local game.api.call_gpt stub via _gm_response; no live sample |
| Structured outcome | investigate success=True; state_changes={}, world_updates=null, no clue/discovery/transition, permitted mutations=[] |
| Extraction | audit_narrated_claims twice, both []; declared envelope absent |
| Claim validation | audit invoked; hard_valid=true; proposed_facts/claim_results/violations=[]; no decision for missed assertion |
| Hard validation | reasons=[], soft_flags=[], mechanical claims=[]; perception checked=true and unsupported=false |
| Acceptance | initial_hard_valid; authority_result=accepted; adoption_status=candidate_accepted; literal candidate_status absent |
| Seal | attempt 1 initial_generation, immutable=true, accepted delivery digest |
| Grounding | skipped at leave_text_unchanged; force_surface for unsupported not reached |
| Publication | HTTP 200; exact candidate; internal authority hidden by public DTO contract |
| Persistence | character unchanged=True; world NPCs unchanged=True; ordinary turn/log/conversation persistence occurs |

Unsupported factual schedule disclosure that could affect player questions/decisions. The fixture checks unchanged NPC and lead ids, no schedule interactable and no schedule clue before its failing prose assertion. Subsequent engine acceptance of overseers is not demonstrated.

Existing renderer candidate: `Nothing here matches that. What you can actually see is a soot-stained skylight leaks pale noon light onto the loft floor.`

Direct hard_valid=True; reasons=[]; unsupported_perception=False. Untouched lifecycle final: `Nothing here matches that. What you can actually see is a soot-stained skylight leaks pale noon light onto the loft floor.`. This is an isolated owner probe, not a repaired HTTP route.


## Persistence and empty-collection meaning

The fresh captures retain unsupported sentences in log, last_gm_exchange and last_publication. api.py:6721 records delivered exchange, :6737 stores last_gm_exchange; publication_contract records completed text. Those surfaces can supply later context, so actionable prose is a risk even without new world truth. Actual multi-turn reliance/corruption was not tested.

Each governing GM decision has four authored proposed_facts and no permitted mutations. The response audit's collections are empty because its recognizers yield no claim, not because the route skips extraction or discards results. No bounded improvisation proposal establishes these facts. The separate quarantined consequential_narration_validation gate also returns PASS/no claims for all three exact sentences in isolated probes; wiring it in alone would not fix them.
