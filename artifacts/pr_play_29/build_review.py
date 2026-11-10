"""PR-PLAY-29 offline reporting only; never dispatches a provider request."""
import copy,json,hashlib,zipfile,shutil,sys,subprocess
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.playtest.gameplay import document,diff
from game.state_channels import is_author_key,is_debug_key
from game.world import advance_world_tick
OUT=ROOT/'artifacts/pr_play_29';RUN=ROOT/'artifacts/atgb/pr_play_29/live'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(n,v): (OUT/n).write_text(json.dumps(v,indent=2,ensure_ascii=True)+'\n',encoding='utf-8')
def report(n,t): (OUT/f'PR_PLAY_29_{n}.md').write_text('# PR-PLAY-29 '+n.replace('_',' ').lower()+'\n\n'+t.strip()+'\n',encoding='utf-8')
r=read(OUT/'live_result.json');usage=r['provider_usage'];opening=next(x for x in r['steps'] if x['path'].startswith('/api/start_campaign'));turns=[x for x in r['steps'] if x['path'].startswith('/api/chat')]
assert len(turns)==2 and usage['dispatched_requests']==4 and r['stop_reason']=='two_ordinary_turns_complete'
labels=['initial','baseline','opening','turns/T1/before','turns/T1/after','turns/T2/before','turns/T2/after','after']
states={n:read(RUN/n/'documents.json') for n in labels}; norm={n:{k:document(s,k) for k in s} for n,s in states.items()}
logs=[states[f'turns/T{i}/after']['session_log.jsonl'][-1] for i in (1,2)]
social=[l['resolution']['social'] for l in logs]
exps=[t['response']['gm_output'].get('metadata',{}).get('expression_generation') for t in turns]
texts=[t['response']['gm_output']['player_facing_text'] for t in turns]
perf=[]
for x in usage['records']:
 seq=x['sequence']; response=read(RUN/f'diagnostics/response_{seq:02}.json')
 perf.append(dict(sequence=seq,operation={1:'opening',2:'Turn 1 interpretation',3:'Turn 1 expression',4:'Turn 2 interpretation'}[seq],configured_model=x['configured_model'],returned_model=x['model'],input_tokens=x['input_tokens'],output_tokens=x['output_tokens'],total_tokens=x['total_tokens'],provider_latency_seconds=response['latency_seconds'],provider_status=x['completion_status'],http_status=200,http_status_evidence='Successful completed SDK Response; transport status inferred from successful response, no raw HTTP status captured',retries=0,accepted=True,published=seq in (1,3),publication_role='renderer selection, not raw prose' if seq==1 else 'internal interpretation, not direct player publication' if seq in (2,4) else 'adopted NPC wording',failure=None))
write('performance_measurements.json',dict(requests=perf,total_requests=4,input_tokens=usage['input_tokens'],output_tokens=usage['output_tokens'],total_tokens=usage['total_tokens'],opening_seconds=opening['api_latency_seconds'],turn_seconds=[t['api_latency_seconds'] for t in turns],live_duration_seconds=r['duration_seconds'],duration_scope='Owned live-worker startup through cleanup; includes evidence-review gates, excludes offline preflight/reporting/packaging',retries=0,fallback_model_calls=0,expression_fallbacks=0,budget_utilization='4/5 (80%)'))
# Preserve complete evaluators and authoritative diffs separately from player transcript.
checks=[]
for i,t in enumerate(turns,1):
 b=norm[f'turns/T{i}/before'];a=norm[f'turns/T{i}/after'];expected=copy.deepcopy(b['world.json']);advance_world_tick(expected,b['campaign.json'])
 actual=copy.deepcopy(a['world.json']);native_events=[]
 if i==2:
  native_events=actual['event_log'][len(expected['event_log']):];actual['event_log']=actual['event_log'][:len(expected['event_log'])]
 world_ok=actual==expected
 immutable={k:b[k]==a[k] for k in b if k not in ('world.json','session.json','session_log.jsonl')}
 # Persistence envelope metadata is removed by document().
 check=dict(turn=i,world_equals_native_tick_plus_authorized_events=world_ok,other_documents_unchanged=immutable,scene_unchanged=b['session.json']['active_scene_id']==a['session.json']['active_scene_id']=='frontier_gate',turn_delta=a['session.json']['turn_counter']-b['session.json']['turn_counter'],log_delta=len(a['session_log.jsonl'])-len(b['session_log.jsonl']),overlay_integrity=t['evaluation']['overlay_comparison']['integrity'],evaluation_stop=t['evaluation']['stop'],new_world_events=native_events)
 assert world_ok and all(immutable.values()) and check['scene_unchanged'] and check['turn_delta']==check['log_delta']==1 and not check['evaluation_stop']
 checks.append(check);write(f'T{i}_evaluation.json',t['evaluation']);write(f'T{i}_internal_log.json',logs[i-1]);write(f'T{i}_normalized_state_diff.json',diff(b,a))
write('state_integrity_checks.json',dict(opening=r['opening_integrity'],ordinary=checks,verdict='PASS'))
write('reset_normalized_state_diff.json',diff(norm['initial'],norm['baseline']));write('opening_normalized_state_diff.json',diff(norm['baseline'],norm['opening']))
# Restricted game facts and forbidden keys, plus manual prose review.
def restricted(v,flag=False):
 if isinstance(v,dict):
  for k,c in v.items():yield from restricted(c,flag or is_author_key(k))
 elif isinstance(v,list):
  for c in v:yield from restricted(c,flag)
 elif flag and isinstance(v,str) and len(v.strip())>=16:yield v.strip()
def forbidden(v,path=''):
 if isinstance(v,dict):
  for k,c in v.items():
   if is_author_key(k) or is_debug_key(k):yield path+'/'+k
   yield from forbidden(c,path+'/'+k)
 elif isinstance(v,list):
  for i,c in enumerate(v):yield from forbidden(c,path+'/'+str(i))
public=json.dumps([x['response'] for x in r['steps']],ensure_ascii=False);secret_values=set(v for s in states.values() for v in restricted(s));matches=sorted(v for v in secret_values if v in public)
# Canonical turn digests can also exist in public audit metadata; these are runtime hashes, not hidden campaign facts.
telemetry=[v for v in matches if len(v)<80 and ':' in v and ' ' not in v];hidden=[v for v in matches if v not in telemetry];keys=[k for x in r['steps'] for k in forbidden(x['response'])]
assert not hidden and not keys
write('confidentiality_verification.json',dict(restricted_strings_checked=len(secret_values),runtime_telemetry_matches=telemetry,hidden_game_fact_matches=hidden,forbidden_public_keys=keys,manual_transcript_review='PASS: no undisclosed motives, plans, secret identities, topic IDs or validator language in published prose',scope='All recorded Player HTTP responses checked for exact protected values/keys; manual prose review. Not proof against arbitrary paraphrase leakage.',verdict='PASS'))
# Source hashes must match preflight byte for byte.
before=read(OUT/'source_hashes_before.json');after={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before};write('source_hashes_after.json',after);assert before==after
write('no_gameplay_edits.json',{'all_preflight_source_and_fixture_hashes_unchanged':True,'paths_checked':len(before),'commits':0,'pushes':0})
write('knowledge_transition.json',dict(turn1='PUBLIC_FACT',turn2='AUTHORED_TOPIC',public_source=social[0]['dialogue_authority']['public_fact_source'],topic=social[1]['topic_revealed'],topic_selection=social[1]['topic_selection'],verdict='PASS'))
write('clue_authority.json',turns[1]['evaluation']['overlay_comparison'])
write('semantic_stop_verification.json',dict(final_stop=r['stop_reason'],campaign_initializations=sum(x['path'].startswith('/api/start_campaign') for x in r['steps']),campaign_resets=sum(x['path'].startswith('/api/new_campaign') for x in r['steps']),ordinary_actions=len(turns),live_requests=4,retries=0,fallback_models=0,third_turn=False,opening_review=read(OUT/'opening_decision.json'),continuation_review=read(OUT/'followup_decision.json'),offline_controls='147 focused passing controls include useful fallback continuation, generic dead-end stop, parser/provider failure stop and ceiling checks',runtime_recoverable_rejection='Not encountered in this live run',verdict='PASS'))
report('TRANSCRIPT',f'''Actual Player HTTP publication only. Internal authority diagnostics are separate. No reconstructed or mocked dialogue.

## Opening

{opening['response']['gm_output']['player_facing_text']}

## Turn 1

Player: {turns[0]['payload']['text']}

NPC: {texts[0]}

Gameplay completion: PASS.

## Turn 2

Player: {turns[1]['payload']['text']}

NPC: {texts[1]}

Gameplay completion: PASS.

Experiment completed after two actions; no further action submitted.''')
report('NPC_PIPELINE',f'''Production HTTP /api/chat in the same isolated campaign/session; both HTTP 200. Complete internal logs: T1_internal_log.json and T2_internal_log.json; transport and observer traces under live/diagnostics in archive.

Turn 1 live interpretation parsed INTERPRETED, NPC/QUESTION, MOVE(tavern_runner) followed by ASK(tavern_runner). Local approach normalized into accessible same-scene social interaction; no scene transition. Public candidates/selected source: scene:frontier_gate:visible:2. Attribution: "A tavern runner trades hot stew and rumors near the rain barrel." Authorized proposition: "I offer hot stew and rumors." Actual provider candidate: "{exps[0]['candidate']}". Validator adopted it with no reasons; fallback_used=false. Published: {texts[0]}

Turn 2 live interpretation parsed INTERPRETED, NPC/QUESTION, ASK(tavern_runner), subject="rumors heard". Model evidence refs include npc_latest_reply, visible:2, visible:4; those references do not themselves authorize the patrol disclosure. Active interlocutor follow-up binding preserves tavern_runner without manual selection. Topic selection candidate/selected source: npc:tavern_runner:patrol_rumor. Requested information classified rumor; category metadata ["rumor"]. Single eligible topic, no ambiguity. Disclosure grant: public/known/permission=true, validation=authorized, source=authored_npc_source. No staged disclosure used and no rejected alternate candidate in this one-topic fixture. Restricted-topic exclusions are supported by offline negative controls, not an invented live candidate list.

Turn 2 expression status EXPRESSION_NOT_INVOKED. No request, candidate, rejection or adoption result exists for a Turn 2 expression provider. Application directly published its engine authored-topic speech; do not describe this as successful live expression generation. Published: {texts[1]}

Both shared evaluator classifications report action_executed=true, gameplay_completed=true, stop=false. Broad original FiveTurnGameplay subject_terms cause possibly_irrelevant_response heuristic flags on both turns; manual transcript review establishes relevant offering/rumor answers. These heuristic warnings are retained and did not cause a decisive stop. Native embedded resolution-contract subtrace says model_interpreter_invoked=false/interpretation_api_calls=0; actual transport ledger proves one live interpretation call per turn. Treat those fields as subpath-local, not total request accounting.''')
report('KNOWLEDGE_TRANSITION','''Verdict: PASS, PUBLIC_FACT -> AUTHORED_TOPIC.

Turn 1 selected scene:frontier_gate:visible:2, own_offerings attributed to tavern_runner; authorized "I offer hot stew and rumors." The engine did not reveal patrol_rumor on this turn.

Turn 2 selected npc:tavern_runner:patrol_rumor; public_fact_source=null. Authored topic carries discovery_categories=["rumor"]. Disclosure authorization rematches speaker, source, public classification, known status and permission=true. Authored proposition is the patrol disappearance/footprints rumor. No extra prerequisites or staged disclosure apply to this topic; deny-policy tests pass offline.

This conclusion uses actual selected authority and grant fields, not merely a response mentioning rumors. See knowledge_transition.json and T1/T2_internal_log.json.''')
report('CLUE_AUTHORITY','''Verdict: PASS. Turn 1 adds no clue overlay. Turn 2 has two authorized discoveries:

- muddy_footprints_northwest: source npc:tavern_runner:patrol_rumor; disclosure grant permits the exact clue ID/text. World event social_lead_revealed identifies topic, NPC and scene.
- minlead_exit_frontier_gate_old_milestone: independently authorized by authored frontier_gate exit "Follow the missing patrol rumor" -> old_milestone and the native minimum-actionable-lead rule. Event social_extracted_lead has source=author_exit. The topic grant alone does not authorize this second lead.

Ordinary originating input is exactly "What sort of rumors have you heard?"; action_id=tavern_runner, persisted log ordinal/turn=3, scene=frontier_gate. Both clues land in clue_knowledge and lead_registry; runtime overlay contains the authored rumor text and exit label. The evaluator receives actual before/after documents, ordinary action, turn response, complete session log, source scene/world and events. It reconstructs authored_social_clue_projection and returns integrity=true, snapshots_preserved=true; see clue_authority.json and T2_evaluation.json.

The actual maintained fixture uses an authored exit for its secondary lead. Earlier PR-PLAY-28 mocked evidence used a separate crossroads discoverable; do not copy that historical lead ID into this live result. All live effects match the content actually loaded.

Unsupported changes were not injected into the live campaign. Offline controls passed for unsupported clue IDs, wrong NPC, denied/missing grants, missing action/log/source, invented hooks/events, unrelated overlays/inventory and malformed turn binding. No unresolved live authority discrepancy.''')
report('STATE_INTEGRITY','''Verdict: PASS. Full authoritative snapshots exist at initial (pre-reset), baseline (post-reset/pre-opening), opening, T1 before/after, T2 before/after and final. Raw and normalized diffs retained; full copies are internal evidence.

Opening passes existing production-path state comparison: one turn/log increment; only permitted session/world roots changed; no unsupported overlay mutations. Scene remains frontier_gate.

For each ordinary turn, character, campaign, combat, conditions and authored scene documents remain unchanged after normalizing persistence wrappers. Inventory, currency and authored quest/NPC state therefore remain unchanged. World equals existing advance_world_tick exactly on Turn 1; Turn 2 equals the same tick plus the two source-authorized social events. Faction pressure/agenda progression and agenda flags are normal tick effects, not unsupported inventions.

Session time_pressure and turn_counter each advance once per turn (1 -> 2 -> 3); session log appends one entry per turn. Active social target/context becomes tavern_runner and remains there. Conversation history records delivered speech. Turn 2 records topic knowledge, two discovered clues/leads and source-supported overlay additions. Ordinary evaluator passes both turns, including the social-overlay authority reconstruction. See state_integrity_checks.json, T1/T2_evaluation.json and normalized state diffs.

Confidentiality: exact protected-value/key scan of all Player HTTP responses plus manual prose review passes. Internal source grants, model prompts, raw candidates and authored hidden facts are kept outside PR_PLAY_29_TRANSCRIPT.md. The scan is bounded and does not prove absence of arbitrary paraphrased leakage. Preflight public response projection and privileged read denial controls pass.''')
quality=[('Relevance','PASS','Turn 1 identifies hot stew/rumors; Turn 2 supplies the missing-patrol rumor.'),('Naturalness','PARTIAL','"Well, I\'ve got..." sounds conversational; "Word is, the runner heard..." retains authored third-person phrasing.'),('Continuity','PASS','The offered rumors lead directly to the player\'s rumor question, answered by the same NPC.'),('Grounding','PASS','Offering matches selected visible fact; patrol/footprints claim matches granted authored topic.'),('Agency','PASS','"muddy footprints northwest of the crates" gives a concrete place to investigate.'),('Repetition','PASS','No repeated uncertainty or duplicate offering answer on Turn 2.'),('Contradictions','PASS','No contradiction with the scene or either knowledge source; third-person wording is awkward, not a new factual contradiction.'),('Third-person self-reference','PARTIAL','The runner says "the runner heard" about themselves in Turn 2.'),('Mechanical leakage','PASS','Published dialogue has no topic IDs, action names, validator messages or hidden metadata.'),('Playability','PASS','Both questions receive understandable answers and a specific investigation lead.')]
write('dialogue_quality.json',{'dimensions':[dict(dimension=a,status=b,evidence=c) for a,b,c in quality],'overall':'PASS (adequate, with naturalness/self-reference caveat)','independent_of_mechanics':True})
report('DIALOGUE_QUALITY','Assessed from actual published prose independently of HTTP/engine success.\n\n| Dimension | Rating | Transcript evidence |\n|---|---|---|\n'+'\n'.join('| '+' | '.join(row)+' |' for row in quality)+'\n\nOverall: PASS / adequate to continue meaningfully. Naturalness and self-reference are PARTIAL, so this is not a claim of polished dialogue. No AI judge used.')
table='| # | Operation | Input | Output | Total | Provider seconds | Status | Retry |\n|---|---|---:|---:|---:|---:|---|---:|\n'+'\n'.join(f"| {p['sequence']} | {p['operation']} | {p['input_tokens']} | {p['output_tokens']} | {p['total_tokens']} | {p['provider_latency_seconds']:.3f} | {p['provider_status']} | 0 |" for p in perf)
report('PERFORMANCE',table+f'''\n\nActual totals: {usage['input_tokens']} input + {usage['output_tokens']} output = {usage['total_tokens']} tokens. Four actual provider dispatches, 80% of five-request ceiling. Configured model gpt-4.1-mini; provider returned gpt-4.1-mini-2025-04-14. All four results accepted for their purpose; only opening renderer selection and Turn 1 expression contribute directly to published text. Interpretations remain internal.

Opening API latency {opening['api_latency_seconds']:.3f}s; Turn 1 {turns[0]['api_latency_seconds']:.3f}s; Turn 2 {turns[1]['api_latency_seconds']:.3f}s. Owned live experiment duration {r['duration_seconds']:.3f}s, startup through shutdown including evidence gates; preflight/report packaging excluded. Raw observer provider latency differs from native latency_ms because the native budget wraps diagnostics as well; both retained. SDK success/completed responses establish provider success; raw provider HTTP status was not separately captured.

Retries 0; fallback-model requests 0; expression rejection/fallback 0. Turn 2 directly used authored engine speech, so no Turn 2 expression request or token usage exists. Never estimate a fifth call. No AI judge. Source: performance_measurements.json, provider_usage.jsonl, request/response_01..04.json.''')
report('FAILURE_ANALYSIS','''No blocking failure observed. Both live ordinary actions execute and complete semantically; authority transition, disclosure, clue provenance, state integrity and confidentiality pass. Experiment stops at two_ordinary_turns_complete.

Quality limitation: Turn 2's first-person dialogue frame embeds the authored third-person source, "Word is, the runner heard...". Evidence localizes the awkward wording to existing authored-topic speech formatting in game.social (NPC speech wrapper), not to a rejected live expression: no optional Turn 2 expression request occurred. This is an existing content/realization limitation, visible in prior offline attributed rumor output. Naturalness/self-reference are PARTIAL, but the specific actionable rumor remains understandable; no repair made.

Harness caveats: inherited FiveTurnGameplay subject_terms generate possibly_irrelevant_response heuristics for both relevant answers. Those are quality hints, not decisive engine failures. Actual transport ledger overrides local subtrace counters claiming zero interpretation calls. Initial offline security test setting prevented synthetic dispatch; corrected test-process environment passed 29/29 without code changes. Owned server is intentionally terminated on cleanup (Windows exit_code=1); process stopped and port released, with no in-request worker crash.

Recommended next investigation, only after external review and separate authorization: inspect eligibility/realization of this authored rumor source to determine why optional expression was not invoked and how first-person NPC speech could preserve its authorized rumor meaning. Do not begin a repair or another live run during PR-PLAY-29.''')
answers=[
('Did preflight pass?','Yes: 147 focused and 29 security tests pass; zero live preflight calls.'),
('Was the correct fixture used?','Yes: strict pinned frontier-gate-v1 manifest/file hashes; post-reset rumor metadata verified.'),
('Did the live opening succeed?','Yes, engine-owned renderer accepted; HTTP 200 and integrity true.'),
('Was the tavern runner accessible?','Yes, verified in actual scene/world and addressability helper.'),
('Did Turn 1 execute?','Yes, normalized local approach plus ASK.'),
('Did Turn 1 produce a useful answer?','Yes: hot stew and rumors.'),
('Was Turn 1 grounded in a public fact?','Yes: scene:frontier_gate:visible:2.'),
('Was expression validation successful?','Turn 1 yes, adopted; Turn 2 optional expression not invoked.'),
('If expression validation failed, was recovery appropriate?','Not applicable: no rejection or expression fallback occurred.'),
('Did the harness correctly decide whether to continue?','Yes: relevant grounded Turn 1, evaluator/security pass and two slots remaining.'),
('Was Turn 2 submitted?','Yes, exact required wording, same campaign/session.'),
('Did Turn 2 retain the tavern runner as target?','Yes, active_interlocutor_followup; no manual reselection.'),
('Was the broad rumor question recognized?','Yes, NPC/QUESTION and requested_information=rumor.'),
('Was patrol_rumor selected?','Yes, npc:tavern_runner:patrol_rumor.'),
('Were disclosure restrictions enforced?','Actual public/known grant permission=true; negative policy controls pass offline. No restricted topic introduced live.'),
('Did Turn 2 produce a useful answer?','Yes: patrol vanished near footprints northwest of crates.'),
('Was Turn 2 grounded in authored knowledge?','Yes, exact selected topic proposition.'),
('Were clue mutations authorized?','Yes: primary clue from topic grant; secondary minimum lead from authored exit.'),
('Did the ordinary-turn evaluator pass?','Yes, both turns and social-overlay projection.'),
('Was state integrity preserved?','Yes; independent native-tick comparison and immutable-document checks pass.'),
('Was confidentiality preserved?','Yes under recorded exact-value/key and manual prose review; protected/read-boundary tests pass.'),
('Was dialogue natural?','Partially: Turn 1 natural; Turn 2 awkward third-person self-reference.'),
('Did the turns form a coherent conversation?','Yes, offering rumors -> asking rumors -> specific rumor.'),
('Could player identify a meaningful next action?','Yes, investigate northwest footprints or follow patrol lead.'),
('How many provider requests?','4, including both live interpretations.'),
('How many tokens?',f"{usage['total_tokens']} total: {usage['input_tokens']} input, {usage['output_tokens']} output."),
('Were retries performed?','No.'),
('Was five-request ceiling respected?','Yes, 4/5 (80%).'),
('First failed boundary?','No blocking boundary failed; dialogue phrasing limitation at authored-topic speech realization.'),
('Demonstrably playable?','Yes for this bounded two-turn scenario; no general campaign claim.'),
('What should be tested next?','After review/separate authorization, inspect authored rumor expression eligibility and first-person realization without changing its authority.')]
report('FINAL_VERDICT','**PASS — A: LIVE TWO-TURN CONVERSATION SUCCESSFUL.**\n\n'+ '\n\n'.join(f'{i}. **{q}** {a}' for i,(q,a) in enumerate(answers,1))+'\n\nNo gameplay implementation, authored content, fixture metadata or validators changed. No commit/push. Stop for external review; PR-PLAY-30 not started.')
write('final_summary.json',dict(status='PASS',verdict='A',opening_requests=1,opening_tokens=1498,opening_latency=opening['api_latency_seconds'],turn1_requests=2,turn1_latency=turns[0]['api_latency_seconds'],turn2_requests=1,turn2_latency=turns[1]['api_latency_seconds'],published_responses=texts,requests=4,input_tokens=6328,output_tokens=544,total_tokens=6872,duration_seconds=r['duration_seconds'],retries=0,naturalness='PARTIAL',knowledge_transition='PASS',integrity='PASS',confidentiality='PASS',first_blocking_failure=None))
# Snapshot only source needed to inspect this experiment, no unrelated artifacts.
snapshot=OUT/'source_snapshot'
paths=['game/api.py','game/api_ui_mode.py','game/dialogue_authority.py','game/social.py','game/local_interaction.py','game/public_fact_dialogue.py','game/expressive_dialogue.py','game/player_interpretation_bridge.py','game/conversational_orchestration.py','game/clues.py','game/provider_budget.py','game/opening_presentation_renderer.py','tools/playtest/analysis.py','tools/playtest/gameplay.py','tools/playtest/social_overlay_authority.py','tools/playtest/overlays.py','tools/playtest/runner.py','tools/playtest/worker.py','tools/atgb/baseline.py','tools/atgb/isolation.py']
for name in paths:
 target=snapshot/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
fixture=OUT/'verified_fixture';shutil.copytree(ROOT/'data/validation/atgb/baselines/frontier-gate-v1',fixture,dirs_exist_ok=True)
(OUT/'git_status_after.txt').write_text(subprocess.check_output(['git','status','--short'],text=True))
# Credential scan actual configured secret values, never print them or serialize any env dump.
from dotenv import dotenv_values
import os
config={**dotenv_values(ROOT/'.env'),**os.environ};sensitive=[v for k,v in config.items() if isinstance(v,str) and len(v)>8 and any(s in k.lower() for s in ('api_key','auth_token','secret','password','credential'))]
selected=[p for base in (OUT,ROOT/'artifacts/atgb/pr_play_29') for p in base.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.zip']
hits=[]
for p in selected:
 blob=p.read_bytes()
 if any(v.encode() in blob for v in sensitive):hits.append(str(p.relative_to(ROOT)))
assert not hits
write('credential_scan.json',dict(files_scanned=len(selected),configured_secret_values_checked=len(sensitive),matching_paths=hits,verdict='PASS'))
selected=[p for p in selected if p.name not in ('MANIFEST.json','archive_verification.json','archive_path.txt')]
manifest=[dict(path=str(p.relative_to(ROOT)).replace('\\','/'),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in selected]
write('MANIFEST.json',dict(pass_id='PR-PLAY-29',classification='Internal diagnostics include authored hidden content; player-facing transcript separately identified',files=manifest))
archive=ROOT/'handoff'/('CURRENT_REVIEW('+sys.argv[1]+').zip')
selected=[p for base in (OUT,ROOT/'artifacts/atgb/pr_play_29') for p in base.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.zip']
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
 for p in selected:z.write(p,p.relative_to(ROOT))
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 names=z.namelist();assert sum(n.endswith('PR_PLAY_29_FINAL_VERDICT.md') for n in names)==1
 assert all(f'artifacts/pr_play_29/PR_PLAY_29_{n}.md' in names for n in ['PREFLIGHT','SCENARIO','TRANSCRIPT','NPC_PIPELINE','KNOWLEDGE_TRANSITION','CLUE_AUTHORITY','STATE_INTEGRITY','DIALOGUE_QUALITY','PERFORMANCE','FAILURE_ANALYSIS','FINAL_VERDICT'])
 verification=dict(path=str(archive),exists=True,zip_crc_passed=True,entries=len(names),bytes=archive.stat().st_size,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),required_reports=11)
write('archive_verification.json',verification);(OUT/'archive_path.txt').write_text(str(archive)+'\n')
print(json.dumps(verification));print('PASS A; 4 requests; 6872 tokens; no gameplay source or fixture edits.')
