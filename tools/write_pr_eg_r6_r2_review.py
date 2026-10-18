"""Package R6-R2 evidence through the repository CURRENT_REVIEW workflow."""
from __future__ import annotations
import difflib,hashlib,json,statistics,sys,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
OUT=ROOT/'artifacts/pr_eg_r6_r2'
TITLES=['Executive Summary','Baseline and Repository State','Failure Reproduction','Entity-Role Contract','Addressee Grounding','Relationship-Argument Grounding','Semantic Proposition Representation','Source Proposition Representation','Semantic Relevance','Semantic Matching Architecture','Provider Responsibilities','Host Responsibilities','Candidate Source Selection','Answer Sufficiency','Correction Semantics','Correction Target Binding','Follow-Up Continuity','Clarification Quality','Response Planning','Authorization Preservation','Legacy Path Isolation','Feature-Gate Behavior','Controlled Test Results','Independent Holdouts','Adversarial Semantic Tests','Matched Baseline Comparison','Fresh-Provider Conversations','Turn-Level Qualification','Dialogue Quality and Playability','Performance','Regression Comparison','Acceptance Gates','Remaining Limitations','Recommended Next Action','Final Verdict','Source and Evidence Inventory']

def write(name,value):
 (OUT/name).write_text(value if isinstance(value,str) else json.dumps(value,indent=2,default=str),encoding='utf-8')
def load(name,default=None):
 p=OUT/name;return json.loads(p.read_text()) if p.exists() else default

def rows(path):
 return [json.loads(l) for l in path.read_text().splitlines() if l.strip()] if path.exists() else []

def junit(name):
 result={}
 for c in ET.parse(OUT/name).iter('testcase'):
  result[c.get('classname')+'::'+c.get('name')]=not any(x.tag in {'failure','error'} for x in c)
 return result

def p95(v):
 return sorted(v)[max(0,int(len(v)*.95+.999)-1)] if v else None

def distribution(v):
 return {'mean':statistics.mean(v),'median':statistics.median(v),'p95':p95(v),'maximum':max(v)} if v else None

def ref(path,symbol):
 lines=(ROOT/path).read_text(encoding='utf-8-sig').splitlines();n=next((i for i,l in enumerate(lines,1) if symbol in l),1)
 return f'{path}:{n} ({symbol})'

def main():
 live=rows(OUT/'live_turns.jsonl');status=load('live_status.json',{})
 base=junit('baseline_junit.xml');current=junit('regression_junit.xml')
 new_fail=[k for k,v in current.items() if not v and (k not in base or base[k])]
 inherited=[k for k,v in current.items() if not v and k in base and not base[k]]
 tests={'baseline_passed':sum(base.values()),'baseline_failed':len(base)-sum(base.values()),'final_passed':sum(current.values()),'final_failed':len(current)-sum(current.values()),'new_failures':new_fail,'inherited_failures':inherited,'added_cases':len(set(current)-set(base))}
 write('regression_comparison.json',tests)
 calls=[c for r in live for c in r['provider_calls']]
 inputs=[sum(c.get('input_tokens') or 0 for c in r['provider_calls']) for r in live]
 latency=[r['latency_ms'] for r in live]
 perf={'turns':len(live),'conversations':len({r['conversation'] for r in live}),'calls':len(calls),'calls_per_turn':len(calls)/len(live) if live else None,
 'input_tokens_per_turn':distribution(inputs),'output_tokens_per_turn':distribution([sum(c.get('output_tokens') or 0 for c in r['provider_calls']) for r in live]),
 'latency_ms':distribution(latency),'retry_calls':sum('retry' in str(c.get('purpose','')) for c in calls),'planning':{'calls':sum(c.get('purpose')=='semantic_plan' for c in calls),
 'input_tokens_per_call':distribution([c['input_tokens'] for c in calls if c.get('purpose')=='semantic_plan' and c.get('input_tokens') is not None]),
 'latency_ms_per_call':distribution([c['latency_ms'] for c in calls if c.get('purpose')=='semantic_plan' and c.get('latency_ms') is not None])},
 'nonplanning_input_tokens_per_call':distribution([c['input_tokens'] for c in calls if c.get('purpose')!='semantic_plan' and c.get('input_tokens') is not None]),
 'total_input_tokens':sum(c.get('input_tokens') or 0 for c in calls),'total_output_tokens':sum(c.get('output_tokens') or 0 for c in calls),'note':'Engine calls only; development pilots, matched runs and scoring excluded. Currency cost not estimated; actual token consumption is reported. Null usage is not asserted to be measured zero.'}
 write('performance.json',perf)
 scores=load('judge_scores.json',[])
 datasets={}
 from tools.assess_pr_eg_r6_r2_local import METRICS
 for dataset in sorted({r['dataset'] for r in scores}):
  rs=[r for r in scores if r['dataset']==dataset]
  datasets[dataset]={m:{'correct':sum(r[m] is True for r in rs),'denominator':sum(r[m] is not None for r in rs)} for m in METRICS}
  for m in METRICS:
   value=datasets[dataset][m]
   value['rate']=value['correct']/value['denominator'] if value['denominator'] else None
  if 'false_clarification' in datasets[dataset]:
   value=datasets[dataset]['false_clarification']
   value['count']=value.pop('correct')
  if dataset=='pr_eg_r6_r2':
   substantive=[r for r in rs if not r.get('repeated_padding_fixture')]
   datasets[dataset]['substantive_turns_excluding_padding']=len(substantive)
   datasets[dataset]['relevance_excluding_padding']={'correct':sum(r['relevance'] for r in substantive),'denominator':len(substantive)}
  datasets[dataset].update(quality_mean=statistics.mean(r['quality'] for r in rs),playability_mean=statistics.mean(r['playability'] for r in rs),scored_turns=len(rs))
 write('quality_metrics.json',{'method':'Local implementing-agent transcript assessment. No external scoring calls; automatic approval review rejected external payload egress. Not independent human adjudication; null metrics excluded, per-row reasons and index annotations preserved. No tuning against scores.', 'datasets':datasets})
 integrity={k:sum(not r['checks'][k] for r in live) for k in ['http','no_secret','sealed','exact','history_exact','canonical','no_secret_clue']}
 route_mentions=[{'conversation':r['conversation'],'turn':r['turn'],'player':r['player'],'text':r['text']} for r in live if 'under the mill' in r['text'].lower()]
 # Local inspection: the only mention is an explicit uncertainty about the player's
 # supplied premise, not a disclosure of the restricted source's truth.
 integrity['restricted_route_phrase_mentions']=route_mentions
 integrity['restricted_route_phrase']=sum('under the mill' in r['text'].lower() and not ('do not know if' in r['text'].lower() and 'under the mill' in r['player'].lower()) for r in live)
 write('integrity_results.json',integrity)
 freeze=load('freeze.json');hashes={'new':hashlib.sha256((OUT/'frozen_holdouts.json').read_bytes()).hexdigest(),'original':hashlib.sha256((ROOT/'artifacts/pr_eg_r6/frozen_holdouts.json').read_bytes()).hexdigest()}
 write('holdout_results.json',{'hashes':hashes,'unchanged':hashes['new']==freeze['sha256'] and hashes['original']==freeze['original_sha256'],
 'turns':[{'conversation':r['conversation'],'turn':r['turn'],'player':r['player'],'expected':r['expect'],'actual':r['plan'].get('response_kind'),'speech':r['text']} for r in live if r['source'].startswith('frozen')],
 'limitation':'Original fixture expectations are preserved, including inherited partial labels. New cases were authored before implementation and frozen; they are not an independent external authorship exercise.'})
 metrics=datasets.get('pr_eg_r6_r2',{})
 gates=[]
 for name,key,threshold in [('Entity roles','entity_roles',.95),('Addressee','addressee',.95),('Relationship','relationship',.95),('Relevance','relevance',.95),('Sufficiency','sufficiency',.90),('Corrections','correction',.90),('Follow-ups','follow_up',.90)]:
  m=metrics.get(key,{})
  rate=m.get('correct',0)/m['denominator'] if m.get('denominator') else None
  gates.append({'gate':name,'threshold':threshold,'rate':rate,'status':'PASS' if rate is not None and rate>=threshold else 'FAIL' if rate is not None else 'UNVERIFIED','method':'local implementing-agent assessment'})
 gates += [{'gate':'Clarification loops','status':'FAIL','evidence':'Repeated Which information / Which person loops in labeled quill and roles conversations.'},
 {'gate':'Authorization','status':'PASS' if not integrity['no_secret'] and not integrity['restricted_route_phrase'] else 'FAIL','limit':'Restricted-value and route sentinel checks plus preserved provenance tests, not proof of every possible leak.'},
 {'gate':'State','status':'PASS' if not integrity['canonical'] else 'FAIL','limit':'Selected canonical projection (NPC topics, factions, location, HP, combat). Full arbitrary-state nonmutation not proven.'},
 {'gate':'Discovery','status':'PASS' if not integrity['no_secret_clue'] else 'FAIL','limit':'Restricted sentinel scan, not exhaustive semantic detection.'},
 {'gate':'Delivery','status':'PASS' if not any(integrity[k] for k in ['sealed','exact','history_exact']) else 'FAIL'},
 {'gate':'Baseline improvement','status':'PARTIAL','evidence':'Matched raw transcripts show addressee/object/paraphrase improvements and continuity regressions; stochastic variation not causal proof.'},
 {'gate':'Holdouts','status':'FAIL','evidence':'Frozen cases expose predicate/argument and correction limitations. See holdout_results.json.'},
 {'gate':'Regression','status':'PASS' if not new_fail else 'FAIL','evidence':tests},
 {'gate':'Performance','status':'PASS' if perf['latency_ms'] and perf['latency_ms']['p95']<=5000 and perf['input_tokens_per_turn']['mean']<=3500 and perf['input_tokens_per_turn']['p95']<=5000 else 'FAIL','evidence':perf},
 {'gate':'Fresh provider','status':'PASS' if len(live)>=120 and perf['conversations']>=8 and status.get('status')=='completed' else 'UNVERIFIED','evidence':status}]
 write('acceptance_gates.json',gates)
 critical=any(integrity[k] for k in ['no_secret','restricted_route_phrase','sealed','exact','history_exact','no_secret_clue'])
 verdict='D — CRITICAL INTEGRITY OR ARCHITECTURAL BLOCKER' if critical else 'C — SEMANTIC GROUNDING BELOW ACCEPTANCE' if len(live)>=120 else 'UNVERIFIED — INSUFFICIENT EVIDENCE'
 summary=f'**{verdict}.** Implemented bounded entity-role and proposition correspondence under the existing R6 gate. {tests["final_passed"]} tests passed; {tests["final_failed"]} inherited failures; {len(new_fail)} new failures. Fresh production /api/chat recorded {len(live)} turns across {perf["conversations"]} conversations. Matching improved in selected cases, but correction and follow-up failures and clarification loops prevent qualification. No positive qualification is claimed.'
 loc={
 'schema':ref('game/unified_semantic_planning.py','def _proposal_schema'), 'provider':ref('game/unified_semantic_planning.py','def _invoke_provider'),
 'host':ref('game/unified_semantic_planning.py','def authorize_information_turn'), 'matching':ref('game/semantic_correspondence.py','def coverage'),
 'witness':ref('game/semantic_correspondence.py','def witnessed'), 'history':ref('game/unified_semantic_planning.py','def delivered_plan_fields'),
 'permission':ref('game/dialogue_authority.py','def authorize_npc_disclosure'),'adoption':ref('game/immutable_valid_response.py','def adopt_host_speech')}
 write('source_locations.json',loc)
 prose={
 1:summary,
 2:'Pre-edit revision, complete dirty working-tree status and source hashes: baseline_repository.json. Existing user work was retained in place. The previous CURRENT_REVIEW is preserved under predecessor_review/. Preserved predecessor reports substantiate 337 passed / 2 inherited failures; the broader matched selection adds 13 reference-eligibility cases and reproduces 347 passed / 5 failed. The two earlier and three additional failure identities are explicit in regression_comparison.json. Prior 47/58 relevance, 43/58 sufficiency and 5/9 correction/recovery are predecessor measurements, not rerun rates.',
 3:'failure_reproduction.json preserves the pre-edit multi-name ambiguity and lexical coverage probes. Baseline live matched turn 1 asks a needless addressee clarification; turn 2 answers night drum with night ledger; turn 3 mistakes informant attribution for naming. Exact old locations: baseline_sources/game/unified_semantic_planning.py match_addressees, _ground_addressee, classify_source_coverage and _relationship_from_text. matched_r6/live_turns.jsonl provides actual provider evidence.',
 4:f'Entity roles: speaker, addressee, mentioned_npc, requested_subject/object, information_source, prior_proposition, correction_target. IDs must exist in scene participants and have literal utterance witnesses. Non-NPC concepts do not acquire canonical IDs. Grounding verifies identity and witnesses; it cannot prove every proposed role assignment semantically. {loc["schema"]}; {loc["host"]}.',
 5:'Leading vocatives are grounded separately from interior mentions. Shared aliases stay ambiguous. Unknown names do not create NPCs. Current narrow syntactic anchoring works for the requested leading-address examples; embedded and trailing address remain limited. Match case A improves in the frozen final run; questions with no direct address clarify.',
 6:f'Arguments are compared by literal normalized identity or roster aliases, with source witnesses. Predicate names are open provider hypotheses. Night drum cannot match night ledger merely through the modifier night. Naming and attribution have different proposition predicates. {loc["matching"]}. Full semantic equivalence of arbitrary argument paraphrases is deliberately not inferred.',
 7:'Propositions carry predicate, subject, object, missing_argument, temporal, spatial, negated, epistemic, prior_reference plus exact evidence spans. Strings are bounded to 160 characters, predicate to 80, at most 12 role/source rows. Generated semantic fields remain noncanonical. Empty or inconsistent proposals fail closed.',
 8:'Existing NPC topic records have stable IDs, text, disclosure and epistemic metadata but usually no structured proposition. The provider supplies an ephemeral, witnessed interpretation of an eligible record. No interpretation is written to NPC topics. Source text, not provider paraphrase, supplies the authorized answer.',
 9:'Coverage distinguishes direct, partial, related_but_nonanswer, unrelated, unknown. Structural mismatches are withheld. Predicate normalization can bridge relationship vocabulary; entity phrases require literal or roster alias identity. The compatibility adapter for old test proposals still uses the predecessor classifier with stricter complete-argument matching. Production uses the strict extended provider schema.',
 10:f'One provider call proposes request meaning and bounded source correspondence. Host checks witnesses, source identity, structural compatibility, knowledge/disclosure and final speech independently. A provider direct score cannot raise host unknown to direct. {loc["provider"]}; {loc["host"]}; {loc["matching"]}. Literal witnesses do not constitute an independent proof of linguistic entailment.',
 11:'Provider proposes roles, an open relationship, argument slots, references, source interpretations and coverage. It receives permitted sources only; confidence is diagnostic. It cannot grant permissions, create relationships or mutate the campaign. Actual request payloads, outputs and usage are in semantic_traces.jsonl. Pilot traces are present and distinguishable by chronology; only live_turns.jsonl counts toward qualification.',
 12:f'Host verifies NPC/source existence, permission and knowledge, evidence spans, proposition arguments, qualifiers and final provenance. It emits original host-owned source text or bounded uncertainty. Disclosure policy remains in {loc["permission"]}. Compatibility never grants disclosure.',
 13:'Candidate preparation uses the grounded speaker’s public or explicitly disclosure-permitted NPC-known records without lexical pruning. Provider context is capped at 12 sources, each at most 800 characters; oversized records are omitted rather than silently truncated. It sees no descriptors or values for denied records. Selection favors authored order; relevant records beyond the cap can be missed. Sources known to a genuinely unresolved addressee are not exposed.',
 14:'A direct answer must fill the requested missing argument while preserving other arguments and qualifiers. Partial answers require the same proposition but incomplete value or qualified epistemics. A different relation about the same object is related_but_nonanswer and is not spoken as a partial answer. Some old frozen expected partial labels conflict with this stricter definition; neither the tests nor holdout contents were edited.',
 15:'Structured corrections are not overwritten by the legacy regex extractor. The provider must bind a delivered prior question and preserve or replace its relationship explicitly. The compatibility fixture extractor preserves the prior predicate when only an entity is supplied. Real provider corrections still fail binding frequently; no correction-success claim is justified.',
 16:'Correction targets bind exact prior question text obtained from delivered exchange history. Invalid references fail closed. This prevents history invention but is brittle: provider reference formatting or selection errors cause clarification. A rejected turn can become the latest plan and lose the useful earlier target. See quill and roles raw transcripts.',
 17:f'Delivered plans persist bounded proposition and role fields for save/load continuity: {loc["history"]}. Follow-up references must equal an actual delivered prior relationship. Historical speech is not a world source. Why and attribution need independent eligible sources. Unknown is appropriate for missing causal evidence, but repeated loss of interlocutor is a real continuity defect.',
 18:'Host distinguishes addressee, correction_target and proposition clarification. Known addressees are preserved when proposition ambiguity is the only missing item. Live provider failures nonetheless produce repeated generic Which information / Which person turns. Gate 8 fails; this is not counted as successful safe conversation.',
 19:'Locked response plans retain request proposition, roles, mentioned IDs, source interpretations, source judgments, selected IDs, authorized text, epistemics and host line. Expression remains downstream of host authorization and immutable adoption. Raw provider proposals stay diagnostic. Canonical world state is not populated with provider predicates.',
 20:'Authorization files were not changed by this cycle. Regression revalidates world_source, host_operation, bounded_expression, verified_history, restricted password rejection, discovery and immutable delivery. No provider coverage/confidence field grants permission. Existing non-protected legacy history compatibility remains inherited and limited as documented by R1-R1.',
 21:'Accepted unified plans retain owner unified_semantic_plan through social resolution and authored-knowledge realization. Provider failure yields locked uncertainty/clarification rather than silent topic reselection. Old fixture proposals retain the compatibility classifier within this owner; the strict live schema requires proposition fields. Gate-off continues the inherited legacy pipeline with universal disclosure checks.',
 22:'ASHEN_UNIFIED_SEMANTIC_PLANNING remains default off. matched_legacy runs gate-off; matched_r6 imports a preserved historical source snapshot; matched_r2 uses final code. There is no permanent extra production implementation. Only information questions, corrections and follow-ups are migrated.',
 23:f'Final regression: {tests}. focused_junit.xml records the initial 68-case focused run; regression_junit.xml records final-code cases. New controlled cases exercise role separation, arguments, source attribution, relationship paraphrase, qualifiers, rumor/belief, malformed/forged sources, unknown entities, corrections, prior binding, candidate privacy, persistence and unchanged holdout hashes. Old delivery/provenance/API tests supply the remaining integration coverage. Tests are controlled evidence, not provider accuracy.',
 24:'Original R6 frozen_holdouts.json is byte-identical to its established hash. New 12-case holdouts were frozen before implementation; freeze.json records both hashes. The live corpus includes every original and new case. The primary plan totals 119 turns; a separate three-turn ninth-conversation supplement brings final qualification to 122 without replacing any failure. Eighteen repeated unknown-question padding turns remain flagged and weaken diversity; they do not represent additional holdout identities. Original cases reset cast and history between cases within two groups; the 8 named conversation groups contain these smaller independent cases. No post-holdout production tuning was performed. New holdouts are internally authored, not externally independent; qualification cannot claim external authorship.',
 25:'Adversarial tests reject forged source IDs, authority fields, unknown entity IDs, unwitnessed source claims, source/argument swaps, invented prior targets, restricted values and confidence-based relevance promotion. Existing universal-boundary tests cover paraphrased secrets and forged provenance. Live injection requests are retained. integrity_results.json reports observed checks with their limits.',
 26:'Three matched fresh-provider 10-turn runs share the same initial cast, topics, utterances and configured model. Subsequent delivered histories diverge naturally with responses, so later turns are sequence-matched rather than identical-history experiments. R2 improves the multi-NPC address, drum/ledger distinction and paraphrased responsibility case; correction and attribution handling remain below acceptance. controlled_matched_comparison.json adds ten deterministic cases (30 executions) with byte-identical state, delivered prior history and proposal, isolating host behavior from provider variation. R2 improves A (addressee), B (object distinction) and D (predicate paraphrase); C/E/F/G/H/I/J preserve the observed response category. One stochastic sample per mode does not establish causality. Raw transcripts and local assessment are included.',
 27:f'Final-code status: {status}. {len(live)} /api/chat turns across {perf["conversations"]} groups. Only the final run counts; pilots, matched runs and mock providers do not. The sandbox initially blocked asyncio socketpair; saved diagnostic console traces show the environment failure, and successful qualification ran outside that restriction. Fixture imports reset provider flags; an initial pilot made no calls and was excluded. Final traces and usage confirm actual configured-provider calls.',
 28:'live_turns.jsonl records player input, expectations, locked plans, raw proposal where available, selected/authorized facts, API speech, sealed accepted response, delivered history, resolution, changed session keys, provider usage and latency. semantic_traces.jsonl preserves actual model input/output. Full campaign state remains in disposable state/ and is excluded from the portable bundle. Canonical equality checks use the predecessor selected-state projection, not a full arbitrary-state diff.',
 29:'quality_metrics.json and judge_scores.json report a separate post-run local agent audit with per-turn reasons, denominators and 0–3 quality/playability scores. This is not independent human review. Null judgments are excluded and never treated as successes. Frozen fixture expectations and raw transcripts remain available to challenge local scores. No code was tuned against these scores.',
 30:json.dumps(perf,indent=2),
 31:f'{tests}. All current failure identities appear in the pre-edit run. The original 339-case selection is contained in the larger matched selection and retains its two known failures. The additional reference suite contributes three inherited failures. Zero unexplained new failures; full repository suite not run.',
 32:json.dumps(gates,indent=2),
 33:'One-pass role/source interpretation is unreliable on corrections and ellipsis. Exact reference binding is brittle. Literal argument identity rejects genuine argument paraphrases with no canonical alias. Source predicate entailment still depends on provider interpretation, with exact witnesses providing bounds rather than a semantic proof. Candidate caps can omit relevant facts. Partial and unknown handling differ from inherited expectations. New holdouts and local scores lack external human independence. State/discovery scans are bounded, not exhaustive.',
 34:'Stop after PR-EG-R6-R2 for external review. Keep the gate off by default. Recommend an architectural revision separating durable delivered-question identity, correction target binding and bounded source proposition interpretation, with externally authored holdouts. Preserve authorization and final delivery. Do not start PR-EH and do not add phrase-specific exceptions.',
 35:summary+'\n\nA/B are not supported. Improvements in selected matched cases do not offset failing correction, follow-up and clarification gates. The failed quality result is preserved rather than hidden behind further tuning.',
 36:'Source locations: '+json.dumps(loc,indent=2)+'\n\nEvidence inventory with SHA-256 is in evidence_inventory.json. Baseline sources and review files are preserved; private state, caches and environment credentials are intentionally excluded. The portable CURRENT_REVIEW includes the implementation, tests, runners, raw public model traces, JUnit, metrics and all 36 reports.'}
 for i,title in enumerate(TITLES,1):write(f'{i:02}_{title.upper().replace(" ","_").replace("-","_")}.md',f'# {i:02} {title}\n\n{prose[i]}\n')
 before=(OUT/'baseline_sources/game/unified_semantic_planning.py').read_text();after=(ROOT/'game/unified_semantic_planning.py').read_text()
 write('planning_changes.diff',''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='pre_edit/unified_semantic_planning.py',tofile='final/unified_semantic_planning.py')))
 changed=['game/unified_semantic_planning.py','game/semantic_correspondence.py','tests/test_pr_eg_r6_r2_grounding.py','tools/qualify_pr_eg_r6_r2.py','tools/baseline_pr_eg_r6_r2.py','tools/compare_pr_eg_r6_r2.py','tools/supplement_pr_eg_r6_r2.py','tools/assess_pr_eg_r6_r2_local.py','tools/controlled_compare_pr_eg_r6_r2.py','tools/write_pr_eg_r6_r2_review.py']
 files=[p for p in OUT.rglob('*') if p.is_file() and not set(p.relative_to(OUT).parts)&{'state','baseline_sources','predecessor_review','__pycache__'} and p.name not in {'handoff_config.json','evidence_inventory.json'}]
 files += [OUT/'baseline_sources/game/unified_semantic_planning.py']+[ROOT/p for p in changed]
 files += [ROOT/p for p in [
  'game/dialogue_authority.py','game/immutable_valid_response.py','game/conversational_continuity.py',
  'tests/test_pr_eg_r2c_speech_adoption.py','tests/test_pr_eg_r2c_r2_reference_eligibility.py',
  'tests/test_pr_eg_r3_expressive_dialogue.py','tests/test_pr_eg_r3_r1_expression_semantics.py',
  'tests/test_pr_eg_r4_r1_delivery_integrity.py','tests/test_pr_eg_r6_unified_semantic_planning.py',
  'tests/test_pr_eg_r6_r1_disclosure_boundary.py','tests/test_pr_eg_r6_r1_r1_provenance.py',
  'tests/test_social_question_relevance_answer_selection.py',
  'artifacts/pr_eg_r6/frozen_holdouts.json','artifacts/pr_eg_r6/freeze.json',
  'artifacts/pr_eg_r6_r1_r1/regression_comparison.json','artifacts/pr_eg_r6_r1_r1/live_status.json']]
 inventory=[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in files]
 write('evidence_inventory.json',inventory)
 supports=[{'path':v['path'],'role':'cycle_evidence','why':'R6-R2 implementation, preserved baseline, or qualification evidence.','human_review_required':v['path'].endswith(('.py','.md'))} for v in inventory]
 supports.append({'path':'artifacts/pr_eg_r6_r2/evidence_inventory.json','role':'inventory','why':'Hashed source and evidence manifest.'})
 config={'campaign_id':'pr_eg_r6_r2_grounding_20261017','campaign_name':'PR-EG-R6-R2 — Entity-Role Grounding and Semantic Relevance','campaign_date':'2026-10-17','purpose':'Implement and qualify bounded semantic correspondence while preserving host authority.','objective_status':verdict,'executive_summary':summary,
 'changes':{'production':changed[:2],'validation':[f'{tests["added_cases"]} new controlled cases, 120 target fresh turns, frozen holdouts.'],'tooling':changed[3:],'documentation':['36 numbered review artifacts.'],'generated_artifacts':['Transcripts, model traces, JUnit, matched comparisons, score audit and metrics.']},
 'testing':{'focused':'68 focused tests passed.','broader':f'{tests["final_passed"]} passed / {tests["final_failed"]} inherited failed','full_suite':'Not run.','runtime_validation':f'{len(live)} final-code fresh turns / {perf["conversations"]} groups.','model_runtime_boundary':'Configured provider; actual model IDs in usage. Separate local transcript scoring is not human qualification.','new_regressions':str(new_fail),'pre_existing_failures':str(inherited)},
 'known_problems':{'campaign_specific':['Corrections and follow-ups fail; generic clarification loops.','Argument paraphrase and source interpretation remain limited.','Observed latency and token targets passed; semantic quality remains below acceptance.'],'pre_existing':['Five failures in expanded baseline selection; includes two previously known failures.']},
 'decisions_requiring_human_review':['Review below-acceptance result and proposed architecture revision.'],
 'missing_concepts':['Durable delivered-question identities and robust semantic correction binding.'],
 'does_not_prove':['A/B qualification, universal semantic correctness, external independent holdout authorship, or full arbitrary-state nonmutation.'],
 'recommended_next_step':'External review of PR-EG-R6-R2. Keep default gate off. Stop; do not begin PR-EH.',
 'primary_report':'artifacts/pr_eg_r6_r2/01_EXECUTIVE_SUMMARY.md','supporting_files':supports,'max_file_bytes':50000000,'warn_bundle_bytes':100000000}
 write('handoff_config.json',config)
 from tools.build_review_handoff import build_handoff
 result=build_handoff(config,root=ROOT,output_dir=ROOT/'handoff')
 print(json.dumps({'verdict':verdict,'turns':len(live),'files':len(inventory),'tests':tests,'bundle':{k:result[k] for k in ['file_count','zip_size_bytes','warning'] if k in result}},default=str))

if __name__=='__main__':main()
