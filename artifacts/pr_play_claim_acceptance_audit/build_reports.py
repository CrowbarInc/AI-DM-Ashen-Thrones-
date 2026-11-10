import json, hashlib, subprocess, xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[2]; O=Path(__file__).resolve().parent
ID='pr_play_claim_acceptance_audit'; P=R/'development/campaigns/product_realization'/ID
B=R/'artifacts/pr_play_baseline_provenance'
def write(n,s): (P/n).write_text(s.strip()+'\n',encoding='utf-8')
def save(n,x): (O/n).write_text(json.dumps(x,indent=2,default=str),encoding='utf-8')
def results(p):
 rows=[]
 for t in ET.parse(p).getroot().iter('testcase'):
  rows.append({'nodeid':t.get('classname').replace('.','/')+'.py::'+t.get('name'),'outcome':'failed' if t.find('failure') is not None else 'error' if t.find('error') is not None else 'skipped' if t.find('skipped') is not None else 'passed','seconds':t.get('time')})
 return {'counts':{k:sum(r['outcome']==k for r in rows) for k in ['passed','failed','error','skipped']}|{'tests':len(rows)},'nodes':rows}
r1=results(O/'baseline_junit.xml');r2=results(O/'authority/recovery_junit.xml')
old1=results(B/'baseline_junit.xml');old2=results(B/'authority/recovery_junit.xml')
comparison={name:{r['nodeid'] for r in a['nodes'] if r['outcome']=='failed'}=={r['nodeid'] for r in b['nodes'] if r['outcome']=='failed'} for name,a,b in [('main_failed_ids_identical',r1,old1),('authority_failed_ids_identical',r2,old2)]}
save('test_results.json',{'milestone':ID,'baseline_reference':'artifacts/pr_play_baseline_provenance/test_results.json','runs':[r1,r2],'comparison':comparison,'additional_mechanical_tests':25,'counts':{'tests':381,'passed':358,'failed':23,'errors':0,'skipped':0},'live_provider_calls':0})
traces=json.loads((O/'three_case_trace.json').read_text());acap=json.loads((O/'authority/http_capture.json').read_text())
related={}
for node,turns in acap.items():
 if any(x in node for x in ('duplicate_refusal','save_reload','http_fallback','two_refusals')):
  related[node]=[{'request':t.get('request'),'http_status':t.get('http_status'),'response':t.get('response'),'last_publication_before':t.get('before',{}).get('session',{}).get('last_publication'),'last_publication_after':t.get('after',{}).get('session',{}).get('last_publication'),'turn_before':t.get('before',{}).get('session',{}).get('turn_counter'),'turn_after':t.get('after',{}).get('session',{}).get('turn_counter')} for t in turns]
save('related_publication.json',related)
controls=[r for r in r1['nodes']+r2['nodes'] if any(s in r['nodeid'] for s in ('test_pr_play_post_npc_handoff','test_pr_play_46_mechanical_boundary','test_pr_play_79df3_classification','test_six_followups','test_case_a_invalid','test_case_b_double','test_case_c_valid','test_mechanical_contradiction','test_unsupported_bell','test_authorized_bell'))]
save('negative_controls.json',{'nodes':controls,'probes':'classification_probes.json','limits':['Acquisition controls use synthetic explicit deltas, not end-to-end loot persistence.','No repaired path: production unchanged.','Refusal controls have mixed outcomes.']})
matrix=[
 ['Physical state change','Actor/object/quantity-specific resolved outcome','mechanical_outcome(resolution), physical adjudication, permitted mutations; resolved_transition/destination','Yes for material effects, through engine owner','Only within actual grant; investigate success=True is not retrieval','False/unresolved action, compound additional item, incidental dust'],
 ['Established world / inspected record','Selected readable contents, public authored fact, authorized clue or approved fact creation','referenced_surface, revealed_information, GM decision realization claims, bounded world-fact owner','No new write for existing fact disclosure; new truth needs its owner','No contents from hidden/abstract/unsupported target','Glassport crews and overseers; allow tariff/notice clue'],
 ['Harmless description','Incidental texture permission; no consequential residual','proposition_authority / GM decision incidental classes','Not required','Yes; no universal authored-detail requirement','Wind, gesture, creak, lantern vs evidence events such as tracks/whisper/bell'],
 ['Ordinary dialogue','Resolved NPC target and dialogue authority; factual status retained','social resolution, dialogue_authority, host-speech adoption, NPC-claim authority','Optional discourse memory, not canonical truth','Opinions, questions, uncertainty, refusal, repetition within contract','Unsolicited speech on inspection; incorrect speaker'],
 ['Speculation / testimony','Epistemic ceiling and authorized inference/premises or attributed claim','epistemic_acts, premise_claim_ids, source_claim_id, modality ranks','No world mutation; testimony may persist as claim','Qualified status may pass; hedge does not license adjacent assertion','Possible passage vs confirmed culprit; incomplete records vs invented exact roster'],
 ['Unsupported established assertion','None available','Explicit blocked target / missing outcome or record source','Never invent state to make text true','No; select validated truthful nonresolution before seal','All three demonstrated defects']]
save('classification_matrix.json',{'columns':['category','authority_required','available_source','persistence','immutable_acceptance','negative_controls'],'rows':matrix})
write('SUMMARY.md',f'''# Consequential Narrative Claim Acceptance Audit

Milestone `{ID}`. Client date 2026-11-08. **Cycle verdict: A/PASS for investigation; no repair implemented.** Primary failure class: implementation. The pre-acceptance path fails to enforce existing closed-surface inspection authority. Historical origin remains unresolved — closed.

The authoritative handoff selects “Option A — Publication-authority boundary investigation” without assigning a numbered successor. This descriptive milestone follows that action; PR-PLAY-80 and AT-OPT-07 are not opened.

| Case | Finding |
|---|---|
| Hidden brass token | Unsupported acquisition and hidden-target confirmation: inspection requested, hidden/noninspectable target, no retrieval grant |
| Glassport crews | Unsupported record disclosure: only a spoken reference exists, no inspectable ledger/crew/destination contents |
| Kiln overseers | Unsupported record disclosure: no schedule or approved roster/NPC proposal exists |

All three fresh HTTP reproductions run claim auditing, return empty claim results, pass hard/perception checks, seal initial generation, skip grounding and publish the exact stub. Inventory and NPCs remain unchanged. Prose is retained in log/conversation/publication surfaces, but canonical new-fact promotion and later cascading corruption are not demonstrated.

**Earliest practical boundary: Candidate A, within run_preserve_if_valid before its first `_check`. Exactly one recommendation: pre-seal closed-surface inspection outcome projection.** Reuse resolver-stamped hidden/abstract/unsupported authority and existing surface rendering; validate the selected outcome and then seal. Keep original candidate/source/reason in metadata. Do not move the whole grounding mutator, add general fact-checking or change accepted text downstream.

A simple reorder is insufficient: hidden renderer fails claim validation; generic inspection safe_nonresolution fails in all three contexts. Existing neutral “Nothing here matches that…” template passes hard validation and perception checks against all three actual resolutions without changing their authority. Reuse that nonconfirming template for hidden outcomes; current abstract/unsupported renderings already pass. These are isolated unchanged-function probes, not an implemented repair.

Validation: **381 tests, 358 passed / 23 failed**, zero errors/skips. Original 356 baseline remains 333/23; 25 mechanical controls add 25 passes. Failure node sets match both predecessor selections. All 1,294 baseline hashes match; both runs preserve 1,292 protected runtime/test/data/static/prompt files, with zero external network attempts. Live provider calls: **0**.

Remaining uncertainty: repaired HTTP integration/precedence, arbitrary English coverage, live-model frequency and actual later reliance on invented records. Mixed refusal controls and known portal exception remain deferred. No full-suite, held-out, gameplay or live-model acceptance claim. See the eight companion reports and artifacts/pr_play_claim_acceptance_audit/trace_summary.json, three_case_trace.json and test_results.json.
''')
write('PIPELINE_TRACE.md',f'''# Actual acceptance and publication trace

Milestone `{ID}`. One-based source locations refer to current hash-verified files. Instrumentation wraps functions, records arguments/results and delegates once. It changes no implementation behavior. Three-case trace retains seven nested completion events per defect; return ordering is not an invented linear call graph.

| Actual stage | Owner / source location | Evidence |
|---|---|---|
| Interpret/classify | referenced_surface.py:350; exploration.py:396/:566 | Hidden, abstract or unsupported inspect target |
| Structured resolution | exploration.py:591 onward | investigate success=True; no clue, retrieval, state_changes or transition |
| Authority assembly / mutation | api.py:4739 `_run_resolved_turn_pipeline` | attach interaction obligation, apply authoritative mutation, reconcile movement BEFORE candidate generation |
| Candidate | api.py:3298 builder, :3877 guard around bounded call; existing test `_chat` :149 | Local fixture game.api.call_gpt stub; exact sentence survives guard |
| Preparation | immutable_valid_response.py:1624 | Host speech not adopted; resolver-fact and selected-information preparation do not replace candidate |
| Claim and hard validation | `_check` :1703 → validate_generated_response :623 → gm_resolution_decision.py:3410 | authority=[], mechanical claims=[], audit proposed_facts/claim_results/violations=[]; hard_valid=True |
| Pre-seal perception check | immutable file :1256 → perception_grounding.py:491 | checked=True, flags=[], unsupported=False |
| Acceptance / seal | immutable file :1860–1893, seal_accepted_response :1301, _finish :1811 | initial_hard_valid; attempt 1; immutable=True; initial_generation; no regeneration |
| Grounding | api.py:4461; perception_grounding.py:757/:771 | leave_text_unchanged returns before evidence and force_surface; skipped mutator recorded |
| Effects / persistence | api.py:2119, :6308 persistence helper, :6525 effects, :6705 restore | Separate effect owners; inventory/NPCs unchanged; text stored in log/exchange/publication |
| Publication | api.py:6782 finalizer, :6792 note_completed_publication; :5377 DTO projection | HTTP text equals candidate; resolution becomes empty public compatibility placeholder |

Chat enters `_chat_turn` (:7149), resolved exploration uses the shared resolved-turn pipeline, then `_complete_opening_turn_persistence_like_chat` (:8360), despite that helper's name. These three seal in the normal initial-generation lifecycle at :4021. Other routes can adopt host speech, use an engine-authored consequence before narration, or reach a second unresolved guard (:4397). No universal pipeline is claimed.

Accepted metadata in each case: adoption_status=candidate_accepted; authorization_source=initial_generation; immutable=true; authority_result=accepted; attempt=1; hard_valid=true; reasons=[], soft_flags=[]; contract_satisfying=true; grounding_result=not_a_replacement_trigger. A literal candidate_status field is absent in these acceptance records; adoption_status carries the recorded disposition. That grounding label is not proof downstream grounding evaluated the surface. The delivery digest binds accepted text; final player-visible text is identical.

Claim extraction is present but incomplete. `_check` selects audit_narration_against_decision because realization_envelope.declared_claims is absent on this legacy GM response fixture. The audit calls audit_narrated_claims and then classify_narrated_fact, which calls that recognizer again. Both calls return []. Nothing is extracted and discarded. Each governing GM decision separately contains four authored facts and no permitted mutations. Audit proposed_facts, decision proposed_facts and bounded improvisation proposals are different collections.

Mechanical recognition (mechanical_claims.py:167) does not match coordinated “You pry … and pocket …”. GM decision structural/proposition patterns do not match these record list/count sentences. Perception's hidden-fact detector (:472) compares a first six-word span: “brass token is sealed under the” is absent from the acquisition prose. Its bounded evidence/event categories do not recognize these record contents. `_unsupported_perception` checks classifier.unsupported, not the downstream force_surface policy (:821). Thus the explicit restriction is available but unenforced before sealing.

Post-seal leave_text_unchanged (:234) and restore_accepted_text (:1368) intentionally protect identity. Grounding is skipped, not applied then undone. effects_allowed (:256) is not an item/world grant. Player projection is a privacy/shape adapter, not semantic authority; public resolution={{}} is PR-PLAY-67's contract. No separate model fact-check pass or accepted new-world proposal occurs.
''')
write('CLAIM_CLASSIFICATION.md',f'''# Consequential claim classification

Milestone `{ID}`. A consequential narrative claim asserts a material actor/object/location outcome or supplies actionable evidence about the world as established fact beyond the existing resolution, disclosure or approved fact-creation grant. The unit can be a residual clause inside an otherwise authorized sentence. Persistence is neither necessary nor sufficient for consequence.

This definition follows state_authority_model (expression is not a truth store), mechanical_outcome, GM decision provenance/epistemic ceilings and referenced-surface authority. “You acquired it” can mislead without inventory changing; an authorized clue can be disclosed without creating new truth.

| Category | Authority required | Available source | Persistence necessary | Immutable acceptance | Negative controls |
|---|---|---|---|---|---|
'''+''.join('| '+' | '.join(row)+' |\n' for row in matrix)+'''
Acquiring/dropping items requires actor/item/quantity-specific authority. Opening a locked container, moving/destroying an object or injury requires the relevant adjudicated object/actor outcome, not investigate success. mechanical_outcome lacks adapters for some physical operations; absence never grants them. Genuine travel has resolved_transition and destination authority. Current recognizers do not guarantee detection of every physical assertion.

Record contents require an actual readable source, selected public clue or approved world-fact creation. A request supplies none of those. New NPC information can be authorized by the world/NPC resolver; being new is not inherently invalid. Here no such grant exists.

Wind, floorboard creak, lantern flicker and mannerism need not persist or all be preauthored. Bells are context-sensitive: current perception grounding treats an audible bell as a perceptible event requiring evidence. Existing authorized/unsupported bell tests enforce that distinction; do not declare every distant bell harmless under this architecture. Tracks, blood, whispers, signals or counted rosters may be actionable evidence.

NPC opinions, questions, uncertainty, refusal and repetition remain permissible within resolved speaker/dialogue authority. Testimony may use NPC-claim authority without being world truth. Quoted speech is not proof an item moved; dialogue may still contain factual assertions subject to its authority contract.

Existing speculation/inference/testimony distinctions use proposition_authority epistemic frames and GM decision epistemic_acts, source_claim_id, premise_claim_ids and modality ranks. They are bounded. A hedge does not authorize unrelated certainty, cause or new factual premises elsewhere in the sentence. Unknown records do not license exact counts.

The selected implementation constrains only explicitly closed inspect/investigate routes. It must not ban all new details, all empty claims, all unchanged state or all new NPCs. It may replace provider decoration on those closed routes with the existing authoritative rendering and visible surroundings; that limited style tradeoff is explicit. Protect ordinary improvisation elsewhere with baseline and post-implementation controls.
''')
descs={
'hidden_brass_token':('Hidden brass token','The player asks to inspect, not pry the hopper or retrieve an item. Hidden_facts contains “A brass token is sealed under the grain hopper.” The token is undiscovered: visibility=false, inspectability=false, no interactable id, clue or revealed-hidden entry. The canonical hopper does not authorize prying under it.','The hint explicitly forbids confirmation/reveal. No item delta, permitted mutation, physical adjudication, authored consequence, world update or transition authorizes retrieval. success=True means the investigate request was handled, not acquisition. Unchanged inventory corroborates absent authority and is not the sole proof.','Unsupported acquisition and hidden-target confirmation; inventory still has the same spellbook. No authoritative retrieval through another mechanism appears in the traced production path.'),
'shipping_record':('Glassport shipping crews','Player requests inspection of the shipping ledger. The only shipping fact is the Loft Clerk topic “I checked the shipping records this morning.” authored_abstract_reference means an abstract reference exists, not an inspectable ledger. Visibility and inspectability are false.','Resolver hint forbids instantiating a physical object or inventing contents. Four existing decision facts are scene observations, not crew/destination facts. There is no selected clue, mutation or approved improvisation/world-fact proposal for this record.','Unsupported authoritative factual disclosure: eight crews and Glassport are actionable player information. Text acceptance is demonstrated; acceptance/promoting as canonical new world truth is not. No crew NPCs, ledger or lead is created.'),
'schedule':('Kiln schedule overseers','Player requests inspection of the glass kiln schedule. No such schedule is authored; visible facts are skylight, maize and tariff slate. The sole tariff clue concerns dock fees, not overseers. Classification=unsupported, existence/visibility/inspectability=false.','The hint forbids object, contents, clue and lead invention. No clue, mutation, authorized roster/NPC creation or fact proposal grants four overseers. New NPCs are not inherently invalid; this particular context lacks authority.','Unsupported factual schedule disclosure that could affect player questions/decisions. The fixture checks unchanged NPC and lead ids, no schedule interactable and no schedule clue before its failing prose assertion. Subsequent engine acceptance of overseers is not demonstrated.')}
sections=[f'# Three-case analysis\n\nMilestone `{ID}`. Fresh provider-free HTTP and nested function captures; unchanged fixtures. Full state and authority in three_case_trace.json.']
for c in traces:
 title,request,auth,finding=descs[c['id']]; md=c['resolution']['metadata']
 sections.append(f'''## {title}

Request: `{c['request']['text']}`

Candidate and final publication (identical): **{c['published']}**

{request}

{auth}

| Stage | Evidence |
|---|---|
| Creation | Existing `_chat` local game.api.call_gpt stub via _gm_response; no live sample |
| Structured outcome | investigate success=True; state_changes={{}}, world_updates=null, no clue/discovery/transition, permitted mutations=[] |
| Extraction | audit_narrated_claims twice, both []; declared envelope absent |
| Claim validation | audit invoked; hard_valid=true; proposed_facts/claim_results/violations=[]; no decision for missed assertion |
| Hard validation | reasons=[], soft_flags=[], mechanical claims=[]; perception checked=true and unsupported=false |
| Acceptance | initial_hard_valid; authority_result=accepted; adoption_status=candidate_accepted; literal candidate_status absent |
| Seal | attempt 1 initial_generation, immutable=true, accepted delivery digest |
| Grounding | skipped at leave_text_unchanged; force_surface for {md['referenced_surface_authority']} not reached |
| Publication | HTTP 200; exact candidate; internal authority hidden by public DTO contract |
| Persistence | character unchanged={c['character_unchanged']}; world NPCs unchanged={c['world_npcs_unchanged']}; ordinary turn/log/conversation persistence occurs |

{finding}

Existing renderer candidate: `{c['renderer_probe']['text']}`

Direct hard_valid={c['renderer_probe']['validation']['hard_valid']}; reasons={c['renderer_probe']['validation']['reasons']}; unsupported_perception={c['renderer_probe']['unsupported_perception']}. Untouched lifecycle final: `{c['renderer_probe']['lifecycle_final']['player_facing_text']}`. This is an isolated owner probe, not a repaired HTTP route.
''')
sections.append('''## Persistence and empty-collection meaning

The fresh captures retain unsupported sentences in log, last_gm_exchange and last_publication. api.py:6721 records delivered exchange, :6737 stores last_gm_exchange; publication_contract records completed text. Those surfaces can supply later context, so actionable prose is a risk even without new world truth. Actual multi-turn reliance/corruption was not tested.

Each governing GM decision has four authored proposed_facts and no permitted mutations. The response audit's collections are empty because its recognizers yield no claim, not because the route skips extraction or discards results. No bounded improvisation proposal establishes these facts. The separate quarantined consequential_narration_validation gate also returns PASS/no claims for all three exact sentences in isolated probes; wiring it in alone would not fix them.
''')
write('THREE_CASE_ANALYSIS.md','\n\n'.join(sections))
write('AUTHORITY_GAP.md',f'''# Authority gap and enforcement boundary

Milestone `{ID}`. Earliest incorrect decision: a recognizer-empty inspection draft is accepted as initial_hard_valid despite explicit existing authority closing discovery/interaction. The gap is pre-seal outcome selection, not an absent inventory writer or a broken immutable restore.

| Boundary | Evidence and enforceability | Decision |
|---|---|---|
| A: before hard validation | run_preserve_if_valid already has resolution, target existence/visibility/inspectability, scene/world/session, selected clues and mutations | **Selected**: prepare existing authoritative closed-surface outcome before first _check |
| B: during validation | Same authority in validator/_check | Feasible but expands English recognition and fallback obligations; later than deterministic selection |
| C: immediately before seal | Same authority plus audit | No new truth appears; duplicates earlier policy across seal branches |
| D: after acceptance | Same plus immutable text/digest | Intentionally cannot replace accepted text; unseal/reseal breaks identity and hides earliest error |

Reuse classification_from_resolution (no hidden string output), render_referenced_surface_inspection_line, selected-information preparation and lifecycle validation/seal. Perception grounding already owns force_surface, but exits on immutable text before reaching it. Factor its minimal read-only blocked-surface selection policy; do not move the whole mutator with history, grounding replacement and preservation side effects.

Selected approach: within run_preserve_if_valid before `_check`, after selected-information preparation, choose a truthful nonresolution for explicit inspect/investigate hidden/abstract/unsupported targets with no contrary authorized reveal or physical outcome. Already accepted/host speech must keep identity. Do not extend to all observe/social/inquiry/travel or genuine readable surfaces. A genuine clue or resolved acquisition must outrank a stale/no-grant surface classification; do not use success=True alone as permission.

This enforces an existing closed authority contract instead of pretending that a complete English extractor exists. All three bad sentences are consequential by acquisition/record-disclosure meaning; prevention on their entire closed route is independent of wording. A harmless provider decoration on that closed route may also be replaced. That local style tradeoff is explicit, while ordinary description/dialogue on open/authorized paths remains possible. No universal no-state-change rule.

Renderer compatibility is required: current hidden “You find no such thing…” fails unowned_stateful_world_assertion; its lifecycle salvages only the skylight, dropping the target outcome. Generic INSPECT_SAFE_LINE fails all three as unauthorized_evidential_relation and unauthorized_certainty_upgrade. Neither is a proven complete fallback. The existing neutral unsupported-target template passes the actual hidden resolution as a candidate, as well as both other contexts; reuse its nonconfirming wording for hidden targets while KEEPING authored_hidden authority. Do not relabel hidden authority, whitelist arbitrary host strings, weaken validation or add hidden facts to a public grant.

Record original draft rejection/preparation and resolver source. Validate the prepared text, then seal once. If validation fails, existing terminal safety handling blocks effects; do not add correction loops or dispatch retries for deterministic closed outcomes. A truthful completed nonresolution is distinct from an operational admission refusal.

Missing information: none for these three outcomes. A complete arbitrary-English claim extractor is missing, and all existing recognizers are bounded; the next block need not build one. Repaired HTTP precedence, publication identity and false-positive protection remain to be tested. No post-acceptance change is recommended.

## Related publication defects (bounded triage)

| Finding | Classification | Evidence and deferral |
|---|---|---|
| Stew response mismatch | Potentially related | Unchanged raw-chat fixture expects inability to state stew price, receives Tavern Runner muttering “Word is, hot stew and rumors for coin.” Same overall response stack, but social/answer selection rather than closed-surface inspection; no demonstrated identical cause. Stopping assertion prevents second turn. Defer separate source/acceptance diagnosis |
| Refusal-publication inconsistencies | Separate mechanism | Duplicate-refusal fixture publishes a deterministic two-person clarification as engine_response; save/reload lacks expected operational_refusal log class. These are routing/classification/recording boundaries, not claim extraction misses. Two-refusal path retains AnyIO portal failure, whose semantic result is insufficient evidence |
| Fallback publication pointer | Separate mechanism | HTTP fallback fixture displays “That request addresses someone. Nothing has been attempted.” while last_publication retains earlier Gate Guard text. No invented record or acquisition needed; pointer/completion contract differs. Lower-level grounded-fallback control passes. Defer |

All three touch eventual publication, but that shared endpoint does not demonstrate one repair owner. No changes to them are recommended in the selected implementation. Exact current failures, compact HTTP state and baseline references are retained.
''')
write('NEGATIVE_CONTROLS.md',f'''# Negative controls and results

Milestone `{ID}`. Sequential provider-free unchanged tests under existing storage isolation and nonloopback network guards. Main: {r1['counts']}. Controls: {r2['counts']}. Total **381 tests, 358 passed / 23 failed**, zero errors/skips. Original 356 selection remains 333/23; 25 mechanical controls pass. Failure-id sets exactly match predecessor selections. Exact commands/flags: command.json and authority/command.json; complete failures/JUnit retained.

| Category | Existing fixture or probe | Outcome / limitation |
|---|---|---|
| Harmless detail | mechanical cross_scenario[quiet_exploration]; low-confidence immutable controls; classification_probes | Rain/mannerism and ordinary texture accepted; wind/creak/lantern probes retain bounded checks; no persistence prerequisite |
| NPC dialogue | seven post-NPC HTTP controls, 79B six_followups, quoted-speech controls, opinion/uncertainty/question probes | Pass; isolated dialogue probes do not prove target resolution |
| Authorized clue | post-NPC recorded_handoff and recall; mechanical originals_fallback_preserves_clue_without_retry | Pass; notice_patrol_route delivered/remembered, no hidden disclosure; T05 stock jab remains |
| Authorized acquisition | mechanical bounded_possession silver key/obsidian brooch explicit items_added; merchant scenario | Pass at validator/delta boundary; not end-to-end loot persistence |
| Unsupported acquisition | original token HTTP; recognized no-grant possession controls | Token remains a known failing reproduction; audit classifies it unsupported while existing recognizers miss it. Recognized frames reject |
| Failed physical action | immutable mechanical_contradiction; failed_travel; post-NPC sleeve-copy | Pass in covered frames; no claim of universal physical-verb recognition |
| Authorized travel | post-NPC genuine_travel and transition controls | Pass: old_milestone reached, local approach remains local |
| Unsupported records | original ledger and kiln HTTP | Both fail current prose assertions. Abstract/unsupported renderer probes pass; neutral template passes all actual resolutions |
| Refusal/nonpublication | classifier/direct-recorder/server-error plus 79df3 HTTP controls | Mixed: lower-level controls pass; duplicate-refusal, save/reload classification and fallback pointer fail; two-refusal path hits existing AnyIO portal exception |

Classification/renderer probes invoke unchanged functions, leave inputs unchanged, make zero provider calls. Current hidden renderer fails direct validation; generic inspection fallback fails all three; neutral existing template passes all three. The quarantined consequential validator misses all three exact bad sentences. Bell is context-sensitive: current authorized/unsupported bell controls pass and require event evidence. Do not weaken that contract as “all sensory details are harmless”.

The 23 failures retain separate meanings: nine original obsolete public-resolution assertions; three original publication defects; three additional obsolete resolution assertions; stew mismatch; four authority/publication nodes including portal exception; three unrelated KeyErrors. Stopping assertions mean later checks may not execute. No semantic acceptance is inferred from obsolete expectations.

False-positive risks: applying projection to every investigation suppresses legitimate clue/readable content; no-state-change rejection harms dialogue/description; generic rendering can fail existing authority checks. Protect exact route/authority predicate, selected-information and physical-outcome precedence, host speech and immutable identity. Baseline passes are not proof the unimplemented repair preserves those behaviors.

Missing coverage: repaired end-to-end route, actual granted-item persistence from a real loot resolver, held-out English variation, later reliance on crews/overseers, full suite, live model or Gameplay Benchmark. No frozen fixtures or expectations changed. Mixed publication refusal safety is explicitly unresolved.
''')
write('IMPLEMENTATION_OPTIONS.md',f'''# Implementation options

Milestone `{ID}`. **Exactly one selected approach: 1 — pre-seal closed-surface outcome projection.**

| Dimension | 1: existing closed-surface projection (selected) | 2: widen existing hard recognizers | 3: post-acceptance grounding rewrite |
|---|---|---|---|
| Location | immutable lifecycle preparation; minimal perception policy; referenced_surface rendering | mechanical_claims, gm_resolution_decision and lifecycle | grounding skip, API restore, seal/delivery |
| Signals | explicit inspect/investigate closed authority; visibility; reveal/outcome exceptions | same plus actor/item frames and record-content relation | same truth plus immutable record; no new authority |
| Scope | About 3 existing files, narrow helper/call, hidden template reuse | 3–4 files, multiple recognizers and validated fallback | multiple acceptance/persistence invariants |
| Three defects | All three closed routes blocked independently of candidate wording | Must add coordinated pocket and list/name/count record frames | Can overwrite if immutability bypassed |
| False positives | Provider style loss on closed inspection; bad precedence could suppress reveal | Quotes, uncertainty, nominal mentions, authorized counts | Valid accepted text may change |
| False negatives | Missing/stale classification or other routes remain outside scope | Unseen paraphrases/compound frames | Same semantic misses plus conflicting text owners |
| Improvisation | Preserved outside explicit closed routes; visible surroundings reused | Wider lexical impact | Broad downstream interference |
| Immutability | Prepare, validate, seal once | Preserved if entirely pre-seal | Broken or requires redesign |
| Provider cost | Zero extra calls/retries/prompts | Can be zero, but avoid generic regeneration | No necessary call, high architectural cost |
| Testability | Exact HTTP reproductions + deterministic precedence/controls | Broad frame/false-positive matrix | Full identity/persistence revalidation |
| Regression risk | Narrow; hidden renderer/precedence are demonstrated hazards | Larger lexical/epistemic risk | High architectural risk |

Choose 1 because authority and response owner already exist for every demonstrated case. Option 2 may later protect other routes, but broader English coverage is not justified here. Wiring the existing quarantined SemanticAuthority validator alone is insufficient: it returns PASS/no claims for all three exact candidates.

Expected production files: game/immutable_valid_response.py, game/perception_grounding.py, game/referenced_surface.py. Factor only the read-only closed-surface selection predicate/rendering policy and call it before first `_check`; preserve source metadata. game/api.py already supplies authority and needs no expected change. If evidence requires expansion, document it first.

Hidden rendering must reuse the existing neutral nonconfirmation template with actual authored_hidden authority retained and validate normally. Current abstract/unsupported renderings pass. Do not trust arbitrary host strings or silently override failed validators. Keep original draft/source/reason auditable and use existing terminal safety if selection fails. No new loop/retry.

Expected tests: unchanged three referenced-surface HTTP failures; new owner/HTTP cases for closed inspection, harmless detail, real readable clue, authorized acquisition and travel, host speech, opinions/uncertainty/follow-up, accepted/final identity and zero-extra-call invariants. Use fresh fixtures, preserve frozen holdouts. Rerun same 235 + 121 + 25 selection and compare exact failure identities; do not weaken obsolete assertions for green totals.

Cost: **zero additional requests, retries or standing prompt tokens**, no context reconstruction or per-sentence dispatch. Existing structured evidence and local rendering/validation suffice. Initial generation need not be removed in this repair; avoided-call savings/latency are not measured or claimed. No provider-dependent experiments occurred.
''')
write('NEXT_STEP_DECISION.md',f'''# Next step decision

Milestone `{ID}`. **Exactly one next action: implement pre-seal closed-surface inspection outcome projection.** This audit performs no implementation and stops after handoff.

Scope: lifecycle preparation for explicit hidden/abstract/unsupported inspect/investigate outcomes. Reuse existing classification and minimal renderer policy; validate before sealing. Reuse neutral nonconfirming wording for hidden targets without changing hidden authority. Preserve accepted/host identity, selected clues and physical-outcome precedence. Record original candidate/source/reason; no new authority store.

Acceptance criteria:

1. Three original unchanged HTTP fixtures cease publishing acquisition/crew/overseer claims. Internal surface authority remains correct; no invented inventory/NPC/lead/object or hidden existence/location disclosure.
2. Prepared text communicates a truthful inspection outcome and passes hard/perception validation. Hidden-renderer and generic-safe-line incompatibilities cannot be bypassed by weakening checks; integrate the already passing neutral template and verify HTTP behavior.
3. No extra provider call or retry for these deterministic outcomes. Accepted digest/final identity preserved. Original draft rejection/preparation is reviewable; no downstream semantic rewrite.
4. Authorized readable clues, actual item grants and genuine travel remain narratable. Never invent/rollback authoritative effects to fit text; explicit grants take precedence over stale classification.
5. Harmless texture, NPC opinions/uncertainty/questions/repetition and speculation outside closed inspection remain possible. No universal new-fact or no-state-change ban.
6. Rejection cannot advance authoritative state from prose. Operational refusals remain distinct from completed truthful nonresolution; preserve mixed refusal baseline as an explicit limitation.
7. Run reproductions, new owner/HTTP precedence tests and relevant identical regression selection against current 358/381 baseline. Preserve frozen inputs and report obsolete assertions/unrelated failures separately.

Exclusions: general English completeness, general fact-check subsystem, second LLM pass, new correction/retry loops, standing prompts/model/budget changes, hidden-fact grants, post-seal rewriting, historical provenance, live play/benchmark, PR-PLAY-80, AT-OPT-07 and unrelated cleanup.

Deferred: T05 stock jab, T04/T06 meaningful physical completion, stew mismatch, refusal/routing/classification and fallback publication pointer, AnyIO portal exception, obsolete assertions, unrelated KeyErrors and other twelve-turn gameplay problems. No broad follow-up audit is selected.
''')
write('INTEGRITY.md',f'''# Integrity

Milestone `{ID}`. Branch feature/product-realization; HEAD d40f1ed198236c604085f1c842ead267a8104ce2. Dirty work preserved; entry status retained. No commit/push/reset/clean/stash/revert. No production/test/frozen/config/data edits. “Do not alter worktree” governs investigation inputs; the explicitly requested reports/handoff are authorized outputs.

Before behavior tracing, all 1,294 predecessor manifest hashes matched and aggregate identity verified: 02fb4ccf8ae2d016aef1ba6b2d140279c04285e734cedf56764f8f3a1c8cf151. No baseline regeneration or hypothetical historical checkout. Historical origin stays closed. Relevant source hashes in source_hashes.json. Final seal rechecks all paths and branch/HEAD. Existing large baseline archives are not duplicated.

Executed from repository root:

```powershell
.\\.venv\\Scripts\\python.exe artifacts/pr_play_claim_acceptance_audit/run_audit.py
.\\.venv\\Scripts\\python.exe artifacts/pr_play_claim_acceptance_audit/run_controls.py
.\\.venv\\Scripts\\python.exe artifacts/pr_play_claim_acceptance_audit/analyze_traces.py
```

Exact pytest args/flags and collected ids retained. Disable flags, fail-closed nonloopback network guard and existing storage isolation apply before imports. Runs sequential: 235 tests 219/16; 146 tests 139/7. Total 381 tests 358 passed / 23 failed, zero errors/skips; original 356 baseline plus 25 mechanical passes. Failure-id sets match. Both report 1,292 protected files unchanged, zero additions and zero external network attempts. Final manifest check includes requirements and pytest config. Probe inputs unchanged. Live provider calls: **0**.

Nine reports created in development/campaigns/product_realization/pr_play_claim_acceptance_audit/: SUMMARY, PIPELINE_TRACE, CLAIM_CLASSIFICATION, THREE_CASE_ANALYSIS, AUTHORITY_GAP, NEGATIVE_CONTROLS, IMPLEMENTATION_OPTIONS, NEXT_STEP_DECISION, INTEGRITY (all .md).

Evidence under artifacts/pr_play_claim_acceptance_audit/: baseline verification, entry status/handoff, source hashes, guarded run/probe/report/seal scripts; exact commands, collected nodes, JUnit, failures, output and integrity; raw HTTP/stage captures; compact three-case trace/summary, classification matrix/probes, negative controls, related-publication summary and test_results. evidence_manifest.json binds hashes/sizes and packaging status; files_created.json records final inventory. All new investigative evidence, including full raw captures, is packaged. Existing large predecessor archives are referenced rather than duplicated. Final build/seal records stay external to avoid circularity.

Handoff: prepend docs/NEXT_SESSION.md preserving historical bytes; regenerate stable review Markdown/manifest/ZIP via tools/build_review_handoff.py with explicit config; create a fresh New York timestamped CURRENT_REVIEW(YYYYMMDD-HHMMSS).zip. Do not edit generated review manually.

Verification: reopen stable and dated ZIP; CRC test; internal milestone and nine reports; manifest member SHA-256/canonical bytes; packaged NEXT_SESSION/historical suffix; evidence-manifest identities and omissions; source and prior dated-archive preservation; stable/dated equality. Final cryptographic seal is external to avoid circular self-hashing. Exact archive path/hash and PASS checks are in archive_verification.json, archive_contents.txt and archive_sha256.txt. This describes the protocol; completion is claimed only after final seal PASS.
''')
entry=(O/'entry_next_session.md').read_bytes()
intro=f'''# NEXT_SESSION — PR-PLAY Consequential Narrative Claim Acceptance Audit (2026-11-08)

**A/PASS for investigation; defects are not fixed.** Milestone `{ID}`. Branch feature/product-realization; HEAD d40f1ed198236c604085f1c842ead267a8104ce2. All 1,294 baseline hashes match; dirty inputs preserved. No production/test/frozen changes or commits/pushes. Live provider calls: **0**.

All three HTTP defects reproduce. Claim audit runs but returns empty results; mechanical/perception checks miss the forms, initial hard-valid text seals, downstream grounding skips. Four authored facts still exist in each GM decision. No retrieval/new record/NPC authority found. Inventory/NPCs unchanged; text retained in log/conversation/publication. Historical origin unresolved — closed.

**Exactly one next action: implement pre-seal closed-surface inspection outcome projection.** In run_preserve_if_valid before `_check`, reuse explicit hidden/abstract/unsupported authority and existing renderer policy, then validate/seal. Hidden renderer and generic safe inspection line fail validation; existing neutral nonconfirming template passes isolated checks under all three actual resolutions. Preserve hidden authority, real clue/item/travel precedence, dialogue/improvisation and immutable identity. No extra provider calls/retries. Do not implement automatically from this handoff.

381 tests: 358 passed / 23 failed, zero errors/skips; baseline 356 (333/23) plus 25 mechanical passes. Both failure-id sets match predecessor. Seven HTTP handoff controls pass; refusal/pointer tests remain mixed with same portal exception. No repaired-path/full-suite/held-out/live-model/gameplay acceptance claim.

Reports: development/campaigns/product_realization/{ID}/. Evidence: artifacts/{ID}/. Minimum: SUMMARY, AUTHORITY_GAP, IMPLEMENTATION_OPTIONS, NEXT_STEP_DECISION; trace_summary.json, test_results.json, classification_matrix.json. Verified archive: archive_sha256.txt and archive_verification.json. Defer T05 jab, physical completion, stew/refusal/pointer defects, portal exception, obsolete assertions, unrelated KeyErrors. Do not reopen provenance, PR-PLAY-80, AT-OPT-07 or live play.

---

'''
(R/'docs/NEXT_SESSION.md').write_bytes(intro.encode()+entry)
print(json.dumps({'reports':len(list(P.glob('*.md'))),'main':r1['counts'],'controls':r2['counts'],'comparison':comparison}))
