"""Generate the 22 requested reports and CURRENT_REVIEW from recorded evidence."""
from pathlib import Path
import json,hashlib,difflib,shutil,statistics,sys,xml.etree.ElementTree as ET
H=Path(__file__).resolve().parent;R=H.parents[1];sys.path.insert(0,str(R))
def read(n):return json.loads((H/n).read_text(encoding='utf-8'))
def write(n,v):(H/n).write_text(json.dumps(v,indent=2,default=str),encoding='utf-8')
def junit(n):
 return {r.attrib['classname']+'::'+r.attrib['name']:'failed' if r.find('failure') is not None else 'error' if r.find('error') is not None else 'skipped' if r.find('skipped') is not None else 'passed' for r in ET.parse(H/n).iter('testcase')}
a={**junit('baseline.xml'),**junit('supplementary_baseline.xml')};b=junit('qualification_final.xml')
comparison=dict(baseline_counts={s:list(a.values()).count(s) for s in set(a.values())},final_counts={s:list(b.values()).count(s) for s in set(b.values())},baseline_failures=[k for k,v in a.items() if v!='passed'],final_failures=[k for k,v in b.items() if v!='passed'],new_failures=[k for k,v in b.items() if v!='passed' and a.get(k)=='passed'],resolved=[k for k,v in a.items() if v!='passed' and b.get(k)=='passed'],newly_passing=[k for k,v in b.items() if v=='passed' and a.get(k)!='passed'],lost_baseline_passes=[k for k,v in a.items() if v=='passed' and b.get(k)!='passed'],changed_expectations=[])
write('regression_comparison.json',comparison)
live=read('live_qualification.json');allrows=[r for rows in live.values() for r in rows];metrics={}
for label,rows in [*live.items(),('combined',allrows)]:
 totals={f:sum(r['calls'][f] for r in rows) for f in ['provider_calls','interpretation_calls','narration_calls','retry_calls','input_tokens','output_tokens']}
 metrics[label]=dict(turns=len(rows),**totals,calls_per_turn=totals['provider_calls']/len(rows),input_tokens_per_turn=totals['input_tokens']/len(rows),output_tokens_per_turn=totals['output_tokens']/len(rows),average_latency_ms=statistics.mean(r['elapsed_ms'] for r in rows),maximum_latency_ms=max(r['elapsed_ms'] for r in rows),failed_turns=[r['turn'] for r in rows if r['failures']],high_cost_outliers=sorted([dict(turn=r['turn'],elapsed_ms=r['elapsed_ms'],calls=r['calls']['provider_calls'],input_tokens=r['calls']['input_tokens']) for r in rows],key=lambda r:r['elapsed_ms'],reverse=True)[:3])
write('performance.json',metrics)
# The usage journal includes exploratory runs; isolate final-run records by the preserved prefix.
usage=[json.loads(l) for l in (H/'live_usage.jsonl').read_text().splitlines() if l.strip()]
prefix=sum(1 for l in (H/'live_attempt_4/live_usage.jsonl').read_text().splitlines() if l.strip())
write('final_provider_usage.json',usage[prefix:]);write('all_attempt_provider_cost.json',dict(records=len(usage),input_tokens=sum(r.get('input_tokens') or 0 for r in usage),output_tokens=sum(r.get('output_tokens') or 0 for r in usage),note='All developmental and qualification attempts; not the final 27-turn metric.'))
sources={}
for p in ['game/conversational_continuity.py','game/dialogue_authority.py','game/social.py']:
 old=(H/'before_sources'/p).read_text(encoding='utf-8');new=(R/p).read_text(encoding='utf-8');d=H/'diffs'/(Path(p).name+'.diff');d.parent.mkdir(exist_ok=True)
 d.write_text(''.join(difflib.unified_diff(old.splitlines(keepends=True),new.splitlines(keepends=True),fromfile='baseline/'+p,tofile='final/'+p)),encoding='utf-8')
 sources[p]=dict(before_sha256=hashlib.sha256((H/'before_sources'/p).read_bytes()).hexdigest(),after_sha256=hashlib.sha256((R/p).read_bytes()).hexdigest())
for p in list(read('qualification_source_hashes.json'))+['game/immutable_valid_response.py','game/storage.py','game/api.py','tests/test_pr_ef_gm_authority.py','tests/test_pr_du_player_pipeline.py']:
 d=H/'sources'/p;d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/p,d)
write('source_changes.json',sources)
assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==v for p,v in read('qualification_source_hashes.json').items())
semantic=read('live_semantic_audit.json');holdouts=read('holdout_results.json')
targets={k:v for k,v in b.items() if 'test_topic_grounding_and_recall_matrix[' in k}
gates={
 '1_topic_selection':all(r['passed'] for r in semantic) and all(v=='passed' for v in targets.values()),
 '2_reference_grounding':all(v=='passed' for v in targets.values()) and all(r['checks'].get('faithful_restatement',True) for r in semantic),
 '3_historical_recall':all(r['passed'] for r in semantic if r['adoption'].get('authorization_source')=='conversational_decision:gm_recall_of_npc_statement'),
 '4_authorized_disclosure':all(r['passed'] for r in semantic),
 '5_information_integrity':all(v=='passed' for k,v in b.items() if 'tests.test_pr_eg_r2c_speech_adoption' in k),
 '6_persistence':all(r.get('save_load',{}).get('context_equal',True) for r in allrows if r.get('save_load')) and all(r['passed'] for r in holdouts if r['case'].get('save_load')),
 '7_state_integrity':all(r['checks']['no_unexpected_world_changes'] for r in semantic),
 '8_regression':not comparison['new_failures'] and not comparison['lost_baseline_passes'],
 '9_live_qualification':len(live['primary'])>=15 and len(live['secondary'])>=12 and not any(r['failures'] for r in allrows) and all(r['passed'] for r in semantic),
 '10_performance':metrics['combined']['narration_calls']==0 and metrics['combined']['retry_calls']==0,
}
write('acceptance_gates.json',gates)
verdict='B — REPAIR QUALIFIED WITH LIMITATIONS' if all(gates.values()) else 'C — REPAIR INCOMPLETE'
summary=f'''**{verdict}.** Topic selection ranks relevant authorized authored topics after speaker and answer-sufficiency checks. Immediate repetition and subject-specific historical lookup use actual delivered speech. GM recall retains attribution. The existing R2C host-owned adoption and rejected-candidate exclusion remain in force.

Combined regression: {comparison['baseline_counts']} before; {comparison['final_counts']} after. No existing expectation was changed. Newly failing: {comparison['new_failures']}. R2C H6 now passes unchanged; the original 19 failures and 6 additional inherited owner-suite failures remain.

Final fresh-provider production /api/chat: 15 primary + 12 secondary turns, {sum(bool(r['failures']) for r in allrows)} failing turns. Relevance/authority/history/state checks: {sum(r['passed'] for r in semantic)}/27. {metrics['combined']['provider_calls']} provider calls, {metrics['combined']['narration_calls']} narration calls, {metrics['combined']['retry_calls']} retries. Independent holdouts: {sum(r['passed'] for r in holdouts)}/{len(holdouts)}, including four final-revision independent cases.

Qualification is bounded to these fictional scenes and the configured provider route. The existing delivered-history store is capped at 32 records; this is not unlimited campaign memory or arbitrary semantic understanding. Stop after PR-EG-R2C-R1; await external review before R3.'''
reports=[]
def report(n,title,body):
 p=H/f'{n:02}_{title.upper().replace(" ","_").replace("-","_")}.md';p.write_text(f'# {n:02} — {title}\n\n{body.strip()}\n',encoding='utf-8');reports.append(p)
def block(v):return '```json\n'+json.dumps(v,indent=2,default=str)+'\n```'
report(1,'Executive Summary',summary)
report(2,'Baseline and Environment',f'''Revision `{read('environment.json')['revision']}`. Python {read('environment.json')['python']}. Client date October 17, 2026, America/New_York. The starting tree already had many modified/untracked files; see working_tree_before.txt. Cycle-relative before_sources and diffs establish the worktree baseline independently of HEAD.

The original 23-file family was rerun against frozen pre-edit sources: 421 pass / 20 fail. Additional owner suites: 129 pass / 6 fail. Combined baseline: 550 pass / 26 fail. Baseline overlay copies the starting game package, restores the three pre-edit modules and points only filesystem resource roots back to the repository. Its first attempt lacked static resources and failed collection; that attempt is not counted. Sandbox-only TestClient attempts stalled and were interrupted; verified runs used local socket access.

Actual provider journal confirms configured `gpt-4.1-mini`, returned `gpt-4.1-mini-2025-04-14`, production Responses interpretation. No credentials or active campaign saves are bundled. Fixtures redirect storage into disposable_state. The complete repository suite was not run.''')
report(3,'Historical Failure Reproduction',f'''Evidence classes: CONTROLLED/DETERMINISTIC owner seams and FROZEN BASELINE. Before production edits, A/B/C/E/G failed and H passed; short D/F fixtures passed. The preserved R2C fresh transcripts contain the historical D/F failures. A later long-history probe against frozen pre-edit source reproduces D/F failures after ten competing statements; final source passes. This timing distinction is explicit: all eight failures were not reproduced in the initial short pre-edit probe.

Before: {block(read('before_reproduction.json'))}

Final: {block(read('final_reproduction.json'))}

Extended D/F evidence: extended_historical_reproduction.json. Root causes: the eight-row history cap evicts early road speech; zero-score lookup falls back to the latest remark; speaker filters can fall back to another speaker; repeat recognition misses ordinary repeat requests; subject overlap admits the first location-related topic; plain `watch` was not classified consistently; revealed facts are usually excluded; a second evidence-ref recall path bypasses current-question sufficiency. These are repaired at continuity, dialogue authority and the existing social selector.''')
report(4,'Topic-Grounding Architecture','''The path remains: player text → interpretation/ordinary communication ownership → grounded interlocutor → social.resolve_social_action → _next_topic_to_reveal → build_dialogue_authority → supplied_clarification/_best_exchange → select_host_speech → existing immutable response adoption → API delivered-exchange recording → continuity GM recall → existing storage.

The existing dialogue_authority now projects topic_grounding: speaker_id, addressee, requested_subject, requested_information, reference, candidate_sources, selected_source, ambiguous and ownership. The social result carries turn-local topic_selection from authored candidates. Stable sources use `npc:<speaker>:<authored-topic-id>`; historical sources use delivered speaker/turn/adoption provenance. Accepted-response authorization_source remains the final adoption identity. These are request diagnostics over existing sources, not another knowledge database.

Only three production modules changed. No new NPC agent, generated-dialogue lane, memory store or world authority was added. History capacity grows from 8 to 32 in the same existing delivered_exchanges list because the former cap demonstrably evicts required conversation turns.''')
report(5,'Conversational Reference Grounding','''Reference grounding removes speech-act/control terms and speaker names from current subject evidence. A named speaker restricts the candidate pool; it cannot silently fall back to someone else. Explicit subject selects relevant delivered statements ahead of recency. A deictic repeat without a subject chooses the latest statement of the grounded speaker. Equally plausible different statements/speakers clarify. A missing historical referent clarifies rather than fabricating dialogue. New factual deictic questions still go through the social resolver.

Exact and simpler repetition reuse original delivered text, including long statements and uncertainty qualifiers. No paraphrase provider call is needed. Meaning/repetition requests do not reveal an unrelated authored topic or create a new clue. T01–T08, T13–T14 and the two recall-bypass regression controls inspect selected records, not only output substrings.''')
report(6,'Authorized Information Retrieval','''Speaker grounding and authored-topic ownership remain in the existing social resolver. Eligible authored facts first pass current-question relevance and answer sufficiency. Remaining candidates rank by current subject evidence; a positive-score tie clarifies. A truly generic subject-free ask preserves existing first-available behavior. Explicit requests can retrieve an already revealed owned fact. Repeated discovery is avoided for delivered-speech references.

The legacy public-conversation evidence-ref fallback now rechecks current relevance and sufficiency against the owned authored record. Provider evidence refs cannot make a watch assertion answer the time of an unguarded interval. Hidden/unavailable subjects retain existing withholding/uncertainty posture. No new disclosure grant is inferred from a historical utterance. Authored ownership remains the pre-existing knowledge model; this cycle adds no richer access-control schema.''')
report(7,'Delivered-History Retrieval','''Actual selection policy: explicit named speaker, otherwise grounded NPC constraint; requested-information compatibility for ordinary affirmative statements; overlap with delivered subject/supplied text, falling back to the original question only to locate speech such as refusals; highest overlap wins; distinct equally scored statements clarify; identical repeated utterances use recency. With no explicit subject, latest statement is used within the constrained speaker. No positive explicit-subject match returns no record.

Topic IDs and adoption provenance are retained in the existing rows. A later uncertainty/refusal does not delete or supersede an earlier disclosure. Only adopted delivered text enters history; rejected/superseded candidates remain excluded by the untouched R2C boundary. Topic identity constrains authored source selection; natural-language subject matching remains lexical and bounded. Arbitrary synonym resolution is not claimed.''')
report(8,'GM Recall','''GM historical recall uses actual delivered NPC records and preserves original speaker and spoken content: `Mara said: "..."`. It never reports the speech as established world truth. Explicit subject/speaker constraints precede recency. Long and uncertain statements remain intact; a missing speech referent receives a historical clarification. Other GM explanation/public-evidence questions continue through their existing path.

Final primary turn 14 and secondary turn 12 select the earlier road statement after preferences, uncertainty and refusals. live_semantic_audit.json checks the exact prior delivered record and GM ownership. Deterministic owner controls separately test speaker ambiguity, absent NPCs, missing referents and lack of canonical authority from beliefs.''')
report(9,'Information-Integrity Preservation','''select_host_speech continues to feed the existing immutable accepted_response. Historical reuse has priority over an unrelated resolver candidate; an ambiguous authoritative subject receives host-owned clarification. Unknown requests do not accept generated facts. The unsafe evening/unguarded-gate candidate remains blocked; mixed safe/unsafe and superseded candidates enter neither delivered history nor world updates.

The final test family includes all unchanged R2C adversarial controls and H6 plus T15–T19/T25/T28. Two added resolver controls prove that delivered repetition reveals no competing road clue and that evidence-ref recall cannot bypass answer sufficiency. Canonical state equality alone is not counted as information-integrity evidence: adoption source, actual spoken text and recorded history are checked too.''')
report(10,'Persistence Qualification','''The existing storage schema already serializes conversational_context; no parallel memory system or new storage path was introduced. T23/T24 use actual save_session/load_session with road, watch, preference and twelve intervening uncertain statements, then inspect exact record, topic ID and speaker identity. Independent F1 and other save/load holdouts also use actual storage.

Both live conversations reload through the production request handler each turn and explicitly save/reload at turns 4, 8 and their final turn; all six context-equality checks pass. This verifies disk serialization and continuation, not a separate server/process restart or retrieval beyond the 32-record cap.''')
report(11,'Source Change Inventory',block(sources)+'''

conversational_continuity: reference_subject_tokens, _best_exchange, record_delivered_exchange, _npc_quote, _gm_quote, supplied_clarification, continuity_directive. dialogue_authority: requested_information, topic_supports_requested_information, build_dialogue_authority, select_host_speech. social: _next_topic_to_reveal, resolve_social_action.

Tests extend the existing R2C owner file; historical expected outcomes remain unchanged. tools/validate_pr_eg_r2c_r1.py is a cycle-specific derivative of the preserved R2C live runner. before_sources, sources and diffs separate these edits from the pre-existing dirty worktree.''')
report(12,'Targeted Test Results',block(targets)+'''

T01–T28 all pass in the final combined JUnit. These are deterministic owner-seam controls, with actual storage used for persistence. Five additional controls cover five competing facts across speakers, long exact/uncertain recall, watch-absence insufficiency, no competing discovery during repetition, and provider-evidence bypass rejection. Some matrix rows exercise the same underlying seam; they are not 28 independent end-to-end provider conversations.''')
report(13,'Frozen Holdouts',f'''Original R2C frozen_holdouts.json, freeze.json and H6 are unchanged. Original H6 failed in the verified baseline and passes in the final suite.

Three new cases were frozen before initial edits. Eight additional cases were frozen before their first evaluation. All eleven passed; none were tuned against a failed holdout. Later generic-ask compatibility and recall-fallback fixes arose from regression/live audits, not these holdouts. Four new final-revision fixtures F1–F4 were independently frozen after those fixes and before evaluation; all four pass. Earlier eleven are also retained as regression evidence. Natural-language subjects, NPCs, locations, competing topic order, unauthorized candidates and actual save/load vary across fixtures.

{block([dict(id=r['id'],passed=r['passed'],error=r.get('error')) for r in holdouts])}

Freeze hashes and final source hashes are supplied. All are deterministic qualification; none substitutes for fresh-provider usability.''')
report(14,'Regression Comparison',block(comparison)+'''

The baseline is rerun, not copied from historical counts. Combined results include the original 23-file selection and five additional relevance/strict-social owners. No expectations changed. Initial exploratory failures and the generic-question compatibility regression remain in post.xml, complete_final.xml and supplementary comparisons; final identities are qualification_final.xml. The full repository suite was not run. Inherited failures were not repaired outside cycle scope.''')
for number,label,title in [(15,'primary','Primary Fresh-Provider Conversation'),(16,'secondary','Secondary Fresh-Provider Conversation')]:
 lines=[]
 for r in live[label]:
  soc=(r['result'].get('resolution') or {}).get('social') or {};ac=r['adoption'];lines.append(f'''### Turn {r['turn']}

Player: {r['player']}

Delivered: {r['text']}

Topic: `{(soc.get('topic_revealed') or {}).get('id')}`. Adopted source: `{ac.get('authorization_source')}`. Calls: {r['calls']['provider_calls']}; latency: {r['elapsed_ms']:.1f} ms. Failure flags: {r['failures']}.
''')
 report(number,title,'FRESH: actual production /api/chat through FastAPI TestClient and the configured external provider; no interpretation/narration doubles or replay. Complete JSON preserves HTTP result, authority, adopted text, before/after history, world and commitment diffs, tokens and storage round-trips.\n\n'+'\n'.join(lines))
report(17,'Provider Performance',block(metrics)+'''

Compared with the historical matched 27-turn R2C workload: 14 calls, 0 narration, 0 retries, 26,094 input and 2,630 output tokens. Final workload uses the same question order; compare actual totals above. Provider timing is observed latency, not a statistically controlled benchmark. final_provider_usage.json isolates the final run; live_usage.jsonl and all_attempt_provider_cost.json retain all exploratory/qualification costs. Do not mistake cumulative usage for final-run usage.

Failed attempts remain in live_attempt_1, live_attempt_2, qualification_before_generic_compatibility_fix and live_attempt_4. One intermediate run required strict-social narration/retry for the lost preference referent; the final run does not. Requalification runs are distinct experiments, not retries inside a turn.''')
report(18,'State-Integrity Audit','''STATE: live_semantic_audit.json checks all 27 adopted deliveries, history attribution, authored source identity, exact historical referent and storage continuation. state_audit.json preserves complete world diffs and commitment changes. World changes are only existing faction/event-log ticks and faction agenda flags. No new inventory, reward, secret, security schedule or obligation is authorized by these changes.

session_state_audit.json additionally compares available response-projected session domains and inspects the final persisted canonical sessions, topic reveal/discovery consistency and clue changes on speech-reference turns. Some conversational responses omit session entirely; these omissions are not interpreted as canonical state changes. Complete pre/post persisted session diffs for every turn were not captured. Delivered repetition must not discover a different topic. The first response has the known disposable seed but the runner records only history/commitment before that turn; complete pre-turn session diffs for turn one are therefore not claimed.

active_data_historical_comparison.json confirms active data still matches predecessor hashes; no active-save copies are bundled. This is stronger than working-tree status alone but is a historical hash comparison, not a newly captured byte snapshot at cycle entry. Rejected-provider speech exclusion is separately verified by controlled adoption tests.''')
report(19,'Remaining Limitations','''History is bounded at 32 delivered rows; older statements can still be evicted. Topic grounding uses existing information types plus lexical subject evidence and stable source IDs, not broad semantic validation. Ambiguity coverage is controlled; the two final live conversations each use one active NPC, while multi-speaker competition is deterministic. Richer knowledge/disclosure permissions remain the existing resolver's responsibility.

The four final independent holdouts pass, but the final primary live conversation fails at turns 7 and 8. The provider marks north gate unresolved even though it resolves the ASK addressee to Mara; stored-interpretation eligibility blocks before social resolution. Earlier successful runs are insufficient to override this final failure. R2C closure and R3 readiness remain blocked. Earlier qualification failures are preserved. No arbitrary generated dialogue was opened. The combined relevant suite retains 25 inherited failures; full-suite qualification and process-restart persistence are outside this evidence. A pre-edit timing gap for extended D/F reproduction is documented in report 03. General GM fact lookup from public evidence remains separate from historical delivered-speech recall.''')
report(20,'Next-Cycle Recommendation','''Stop after PR-EG-R2C-R1. Review the final source diffs, all gate evidence, inherited failures and preserved failed provider transcripts before closing the R2C dependency. R2C closure is not ready: final primary turn 7 is blocked as unresolved north gate before the social resolver, and turn 8 therefore has no watch disclosure to repeat. This failure recurred across fresh-provider attempts. Further changes would alter upstream reference-eligibility/authorization policy outside this focused repair; the requested stop condition applies. R3 is not started or automatically approved; await external review.''')
report(21,'Final Verdict',f'''**{verdict}**

{block(gates)}

A passing controlled matrix is not the basis for live success: two final fresh-provider conversations are independently checked for relevant authorized answers and exact delivered-source recall. All earlier failures are retained. Review scope and limits before any next cycle.''')
# Build an explicit evidence inventory; exclude runtime caches and redundant overlays.
support=[]
for p in H.iterdir():
 if p.is_file() and not p.name.startswith('build_console') and p.name not in {'handoff_config.json','artifact_inventory.json','bundle_verification.json','bundle_build_result.json','22_SOURCE_AND_EVIDENCE_INVENTORY.md'}:support.append(p)
for directory in ['before_sources','sources','diffs','live_attempt_1','live_attempt_2','qualification_before_generic_compatibility_fix','live_attempt_4']:
 support += [p for p in (H/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
pre=R/'artifacts/pr_eg_r2c'
for n in ['frozen_holdouts.json','freeze.json','live_qualification.json','live_status.json','performance.json','regression_comparison.json','sources/tests/test_pr_eg_r2c_speech_adoption.py']:
 support.append(pre/n)
support=list(dict.fromkeys(support));inventory={p.relative_to(R).as_posix():dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in support};write('artifact_inventory.json',inventory)
report(22,'Source and Evidence Inventory','''Evidence classes: STATIC source tracing; DETERMINISTIC owner tests; CONTROLLED adoption/provider-output injection; FROZEN BASELINE pre-edit-source reruns; FRESH external-provider production /api/chat; STATE storage and canonical diffs; HISTORICAL preserved R2C logs; INFERENCE bounded limitations. No recorded replay counts as FRESH.

artifact_inventory.json contains source/evidence hashes. qualification_source_hashes.json pins the final runtime/test/runner revision; holdout freeze files pin expected cases. The portable bundle manifest hashes every included file. Source dependencies and cycle-relative patches are included; secrets, active saves, generated temp workspaces and baseline overlay copies are excluded.

Reproduction from repository root with the existing environment:

```powershell
.venv/Scripts/python.exe artifacts/pr_eg_r2c_r1/run_baseline.py
.venv/Scripts/python.exe artifacts/pr_eg_r2c_r1/run_supplementary.py
.venv/Scripts/python.exe artifacts/pr_eg_r2c_r1/reproduce.py final
.venv/Scripts/python.exe artifacts/pr_eg_r2c_r1/extended_reproduction.py
.venv/Scripts/python.exe artifacts/pr_eg_r2c_r1/evaluate_holdouts.py
.venv/Scripts/python.exe tools/validate_pr_eg_r2c_r1.py
.venv/Scripts/python.exe artifacts/pr_eg_r2c_r1/audit_evidence.py
.venv/Scripts/python.exe artifacts/pr_eg_r2c_r1/build_review.py
```

Live reruns use configured provider credentials and incur new calls. Preserve existing evidence before rerunning a script that writes the same filename. TestClient suites require local socket access in this environment. The baseline runner excludes the five new R1 owner-test functions and matrix; original test expectations are unchanged. The reviewed baseline overlay remains on disk and is regenerated by run_baseline.py from the frozen three-module snapshots plus the repository.\n\n'''+block(inventory))
support += [reports[-1],H/'artifact_inventory.json']
config=read('../pr_eg_r2c/handoff_config.json')
config.update(campaign_id='pr_eg_r2c_r1_topic_grounding_20261017',campaign_name='PR-EG-R2C-R1 — Conversational Topic Grounding & Authorized Recall',purpose='Focused implementation and qualification; stop after R2C-R1 and await external review.',objective_status=verdict,executive_summary=summary,primary_report='artifacts/pr_eg_r2c_r1/01_EXECUTIVE_SUMMARY.md',max_file_bytes=30*1024*1024,
changes=dict(production=['Repair existing topic selection, delivered-reference grounding and authorized recall in three modules; preserve R2C adoption.'],validation=['T01–T28 and five additional controls; unchanged historical H6; independent frozen holdouts.'],tooling=['Cycle-specific fresh HTTP runner and evidence/review builders.'],documentation=['22 required review reports.'],generated_artifacts=['Exact baseline/final identities, failed/final live transcripts, source hashes/diffs and state/performance audits.']),
testing=dict(focused='T01–T28 plus five additional controls pass; unchanged H6 passes.',broader=str(comparison['baseline_counts'])+' → '+str(comparison['final_counts'])+'; zero new failures.',full_suite='Not run; combined relevant family only.',runtime_validation='Two final fresh production HTTP conversations (15 + 12 turns): primary fails turns 7/8; secondary passes. Relevance/authority audited.',model_runtime_boundary='Configured gpt-4.1-mini; real interpretation provider, no live doubles or replay.',new_regressions=str(comparison['new_failures']),pre_existing='25 inherited failures retained.'),
known_problems=dict(campaign_specific=['Final primary direct guard question is blocked by upstream unresolved subject reference; its immediate follow-up lacks the requested disclosure. Repeated live failure triggers the stop condition.','Bounded lexical subject matching, 32-row history cap, controlled multi-speaker qualification only.','Initial D/F short probes passed; extended frozen-baseline reproduction executed later.'],pre_existing=['25 combined-family inherited failures; exact identities in report 14.']),missing_concepts=['Unlimited historical memory and arbitrary semantic paraphrase qualification are outside this cycle.'],decisions_requiring_human_review=['External review of R2C-R1 closure readiness and all preserved failed transcripts.'],does_not_prove=['All repository tests passing, arbitrary generated-speech safety, unlimited recall, process-restart persistence or R3 readiness.'],recommended_next_step='Stop after PR-EG-R2C-R1: live qualification fails. Await external review of the upstream reference-eligibility blocker; do not proceed to R3.',supporting_files=[dict(path=p.relative_to(R).as_posix(),role='evidence',why='R2C-R1 source, frozen expectation, exact test result, actual transcript or derived audit.',behavioral_evidence=False,human_review_required=True) for p in dict.fromkeys(support)])
write('handoff_config.json',config)
from tools.build_review_handoff import build_handoff
result=build_handoff(config,root=R,output_dir=H/'review_staging')
import os
for name in ['CURRENT_REVIEW.md','REVIEW_MANIFEST.json','CURRENT_REVIEW.zip']:
 target=(R/'handoff'/name).resolve();assert target.parent==(R/'handoff').resolve()
 os.replace(H/'review_staging'/name,target)
archive=R/'handoff/history/pr_eg_r2c_r1_topic_grounding_20261017';archive.mkdir(parents=True,exist_ok=True)
for source,name in [('CURRENT_REVIEW.md','REVIEW.md'),('REVIEW_MANIFEST.json','REVIEW_MANIFEST.json'),('CURRENT_REVIEW.zip','REVIEW.zip')]:
 shutil.copyfile(R/'handoff'/source,archive/name)
write('bundle_build_result.json',{k:v for k,v in result.items() if k not in {'included','omitted'}})
print(json.dumps(dict(verdict=verdict,gates=gates,regression={k:v for k,v in comparison.items() if k.endswith('counts') or k=='new_failures'},metrics=metrics['combined'],bundle_bytes=result['zip_size_bytes'],omitted=result['omitted']),indent=2))
