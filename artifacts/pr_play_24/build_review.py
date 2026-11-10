"""Post-run evidence analysis and packaging; never contacts a provider."""
import json, hashlib, sys, zipfile
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.playtest.gameplay import document,diff
from game.state_channels import is_author_key
OUT=ROOT/'artifacts/pr_play_24';RUN=ROOT/'artifacts/atgb/pr_play_24/live'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(name,obj): (OUT/name).write_text(json.dumps(obj,indent=2,ensure_ascii=True)+'\n',encoding='utf-8')
def report(name,text): (OUT/('PR_PLAY_24_'+name+'.md')).write_text(text.strip()+'\n',encoding='utf-8')
r=read(OUT/'live_result.json');opening=next(s for s in r['steps'] if s['path'].startswith('/api/start_campaign'));turn=next(s for s in r['steps'] if s['path'].startswith('/api/chat'));gm=turn['response']['gm_output'];reply=gm['player_facing_text'];action=turn['payload']['text'];audit=gm['metadata']['expression_generation'];accepted=gm['metadata']['accepted_response'];usage=r['provider_usage'];state=read(OUT/'state_comparison.json')
before=read(RUN/'turns/T1/before/documents.json');after=read(RUN/'turns/T1/after/documents.json');baseline=read(RUN/'baseline/documents.json');postopening=read(RUN/'opening/documents.json')
rows=[]
for record in usage['records']:
 seq=record['sequence'];resp=read(RUN/f'diagnostics/response_{seq:02}.json');rows.append({'sequence':seq,'purpose':record['purpose'],'configured_model':record['configured_model'],'returned_model':record['model'],'input_tokens':record['input_tokens'],'output_tokens':record['output_tokens'],'total_tokens':record['total_tokens'],'provider_latency_seconds':resp['latency_seconds'],'ledger_dispatch_latency_ms':record['latency_ms'],'total_api_latency_seconds':opening['api_latency_seconds'] if seq==1 else turn['api_latency_seconds'],'api_operation':'campaign opening' if seq==1 else 'first NPC interaction (shared API duration, not additive)','status':record['completion_status'],'retry_count':0})
write('performance_measurements.json',{'requests':rows,'totals':{k:usage[k] for k in ('dispatched_requests','input_tokens','output_tokens','total_tokens')},'opening_api_seconds':opening['api_latency_seconds'],'first_interaction_api_seconds':turn['api_latency_seconds'],'live_experiment_seconds':r['duration_seconds'],'offline_preflight_seconds':read(OUT/'offline_result.json')['duration_seconds'],'duration_definition':'Live controller start through snapshot capture, cleanup and port-release check; reporting/packaging excluded.'})
def restricted(v,flag=False):
 if isinstance(v,dict):
  for k,c in v.items():yield from restricted(c,flag or is_author_key(k))
 elif isinstance(v,list):
  for c in v:yield from restricted(c,flag)
 elif flag and isinstance(v,str) and len(v.strip())>=16:yield v
# Compare public HTTP bodies against authored restricted strings and field names.
secrets=set(restricted(baseline))|set(restricted(postopening))|set(restricted(after));public=json.dumps([s['response'] for s in r['steps']],ensure_ascii=False)
matches=[s for s in secrets if s in public]
# A runtime stamp is telemetry, not an authored hidden world fact. Preserve rather than suppress the finding.
telemetry_matches=[s for s in matches if s=='2:2c1042f7040:8ba522ba']
leaks=[s for s in matches if s not in telemetry_matches]
write('confidentiality_verification.json',{'restricted_strings_checked':len(secrets),'exact_restricted_value_matches':matches,'classified_runtime_telemetry_matches':telemetry_matches,'hidden_game_fact_matches':leaks,'scope':'All captured Player-mode HTTP responses; exact strings only. Manual transcript inspection also performed. Paraphrased-leak absence is not proven.','player_modes':[s['response'].get('ui_mode') for s in r['steps'] if s['path'].startswith('/api/state')],'final_response_hard_valid':accepted['hard_validation']['hard_valid']})
write('initialization_state_diff.json',diff({k:document(baseline,k) for k in baseline},{k:document(postopening,k) for k in postopening}))
write('stop_and_quality_analysis.json',{'status':'PARTIAL','overall_verdict':'B','response_quality':'FAIL','stop_reason':r['stop_reason'],'budget_exhausted_also':usage['dispatched_requests']==3,'followup_submitted':False,'structural_gameplay_completion_count':r['meaningful_gameplay_turns_completed'],'useful_conversational_turn_count':0,'decisive_conversational_failures':1,'counter_caveat':'Raw classifier completion is structural; legacy meaningful_gameplay_turns_completed=1 and decisive_failures=0 are not conversational quality judgments. The controller quality guard stopped on the actual generic answer.','first_failure_boundary':'NPC knowledge source selection / contextual grounding','expression_rejection_secondary':audit['reasons'],'expression_unlicensed_tokens':['right','now']})
targets=read(RUN/'opening/available_npc_targets.json');targetlines='\n'.join('- '+k+': '+v['row'].get('name','')+'; location='+v['row'].get('location','') for k,v in targets.items())
report('SCENARIO',f'''# PR-PLAY-24 scenario

Published opening (exact):

> {r['opening']}

Authoritative same-scene NPC catalog:

{targetlines}

Selected: Tavern Runner (tavern_runner). Published explicitly; catalog kind=npc, authored location=frontier_gate, canonical addressability confirmed using existing is_actor_addressable_in_current_scene before submission. No NPC or access state was created for the test. Public state also supplies scene-addressable actors; full public snapshots and target rows are preserved.

Exact initial action:

> {action}

Question asks only for already advertised offerings, not a purchase, price, quest or travel.

Closed follow-up decision tree, authored before live execution: after a successful nonpartial response, reject generic uncertainty; stew -> ingredients, rumor -> source, stated price -> inclusions, patrol -> last known location. No matching useful answer -> stop. Check production request budget before constructing any follow-up. No judge call.

Actual follow-up: none. First response was generic uncertainty and all three requests had been consumed. One reset/new_campaign plus one start_campaign; one ordinary action. The FiveTurnGameplay fixture/worker contract was reused for server compatibility; this controller never runs its five-turn action loop.
''')
publicstate=read(RUN/'opening/public_state.json')
report('TRANSCRIPT',f'''# PR-PLAY-24 complete player-facing transcript

Opening:

{r['opening']}

Player:

{action}

NPC:

{reply}

No follow-up or follow-up response occurred.

Relevant public-state sentence before the question:

A tavern runner trades hot stew and rumors near the rain barrel.

Player state: ui_mode=player, current scene frontier_gate. Same scene remained active after interaction. Full serialized public responses: live/opening/public_state.json, live/turns/T1/before/public_state.json, live/turns/T1/after/public_state.json. All HTTP interactions are in live/reports/interactions.json and live_result.json. No unhelpful response has been substituted or rewritten.
''')
report('NPC_PIPELINE',f'''# PR-PLAY-24 NPC pipeline

1. Player interpretation: live provider request 02 (2306 input/226 output) correctly produced MOVE(tavern_runner) then ASK(tavern_runner), recipient NPC, purpose QUESTION, subject offerings. Its public evidence includes the actual opening and visible:2 offerings sentence. Raw provider JSON remains in diagnostics/response_02.json.
2. Local normalization: trace_006 (also trace_008) records rule authored_same_scene_interaction_preamble, retains ASK, marks movement_executed=false. No scene travel occurred.
3. Binding: trace_007/009 normalized_action_from_interpretation returns question with target_id and targetEntityId tavern_runner; bridge accepted=true. Exact player text and public_conversation_evidence survive in normalized metadata.
4. Target resolution and authorization: trace_013 resolve_social_action input/output shows target_resolved=true, source=explicit_target, candidate_valid=true, actor_addressable=true, native_npc, no promotion. No skill check is required. Disclosure trace_015 allows the authored patrol_rumor; it is not an answer to the offerings question. Trace_016 is denial for an empty source record, not evidence that this public offerings sentence is secret.
5. Social execution: native question resolver runs. _next_topic_to_reveal returns null (trace_014), topic_selection candidate_sources=[]; topic_revealed=null. Hint explicitly says no authored answer was available. This is an executed question with an informational failure/unknown answer, not binding refusal.
6. Knowledge plan: trace_017 sets genuine_uncertainty, reply_kind=unknown, npc_speech_authority=none, objective_world_fact_authority=none, no durable mutation. trace_018 authority returns unknown posture, empty authorized_proposition, no candidate sources, no improvisation.
7. Narration/expression: trace_021 selects exact host fallback {reply!r}. Provider request 03 then asks for an uncertainty sentence with AUTHORIZED FACTS=(none). It does not ask for a grounded offerings answer or receive scene/opening context.
8. Provider returns: I’m not sure what the tavern runner is offering right now. Expression validation rejects unsupported_addition. Stored audit identifies decision=rejected, fallback_used=true, delivered_generated=false. Offline token inspection of the unchanged closure predicate finds unlicensed tokens right and now. This rejection is secondary: even acceptance would deliver only uncertainty.
9. Final validation/publication: accepted_response authorization_source=dialogue_authority.knowledge_posture; provenance=authorized_host_speech; expression_adoption=HOST_FALLBACK; hard_valid=true, no hard reasons, interaction_completion=true. HTTP 200 publishes exact host sentence. Publication works; no useful answer is lost at this stage.

Final dialogue source: ENGINE. Provider expression WAS invoked and rejected; it would be incorrect to report zero narration calls or blame the provider for failing to generate an answer it was forbidden to supply.

Raw evidence: live/diagnostics/request_01..03.json, response_01..03.json, trace_* input/output, native_diagnostics.jsonl, provider_usage.jsonl; live/turns/T1/api_response.json. Production anchors are packaged in source_snapshot with original line numbering: game/local_interaction.py:normalize_local_approach; game/player_interpretation_bridge.py:normalized_action_from_interpretation (197); game/social.py:resolve_social_action (3895), _next_topic_to_reveal (1611), no-topic branch (4460 onward); game/dialogue_authority.py:build_dialogue_authority (509), select_host_speech (766); game/expressive_dialogue.py:validate_expression (754), request_expression (786).

Structural classifier: transport/pipeline/execution/completion=true. Quality assessment: FAIL. Legacy raw counter meaningful_gameplay_turns_completed=1 denotes structural completion only; use stop_and_quality_analysis.json for the explicit zero useful turns and one conversational dead end. No follow-up after the failure.
''')
report('KNOWLEDGE_DIAGNOSTICS',f'''# PR-PLAY-24 knowledge diagnostics

Confirmed primary cause: existing public scene information is not selected as an answer source for this general offerings question. Confidence HIGH.

| Boundary | Actual information |
| --- | --- |
| Published opening | Runner shouts offers of hot stew and paid rumor. |
| Authoritative visible scene facts | A tavern runner trades hot stew and rumors near the rain barrel. |
| Interpreter input | Both public sentence and actual opening; evidence survives parsing/normalization. |
| Social resolver input | Full scene containing the offerings sentence, NPC roster and normalized public_conversation_evidence. |
| NPC topic selector | Only NPC topics/knowledge; runner has patrol_rumor, not an offerings topic. Selection returns null. |
| Dialogue authority input | Scene supplied (trace_018 kwargs.scene), but topic-based authority selects no proposition for requested_information=general. |
| Expression provider input | Exact player question, operation uncertainty, no authorized facts; no opening/visible sentence. |
| Final answer | Only unknown posture; no stew, rumor or other useful content. |

This is not absence of all authoritative information: the basic requested fact is already authored in scene.visible_facts. It is also not missing scene as a social-resolver function argument. The gap is promotion/selection of an existing public sentence into this NPC's authorized answer source, then omission from the expression contract. No new persistent world fact or speculative improvisation is necessary merely to repeat the public offering.

Source path: game/social.py:1611 _next_topic_to_reveal reads npc.topics or npc.knowledge, checks disclosure/relevance/sufficiency, and does not select scene visible facts. It returned null in the observed call. game/dialogue_authority.py:509 build_dialogue_authority takes scene but the observed general-request path uses topic/partial/history and returns no source. visible_supporting_sentence (486) explicitly excludes general requests and is not used by this captured authority path. No fact was withheld as secret: the public sentence is absent from candidate selection. The authored patrol rumor is authorized (trace_015); correctly refusing to treat an unrelated topic as the offerings answer does not justify widening disclosure rules.

Contributing categories: B contextual source-selection gap (context present at resolver, unavailable as selected provider authority); C downstream authority confines expression to uncertainty because no source was selected; G deterministic host fallback selected/delivered after expression rejection. Category A applies narrowly to absent offerings in NPC.topics, not to the campaign's public scene data. Category E occurs for an unhelpful uncertainty candidate, not a useful answer. D provider omission and F useful-answer publication failure are NOT supported.

Secondary issue: expression candidate "I’m not sure what the tavern runner is offering right now." was rejected for unsupported_addition; closure lexicon does not license right/now. This consumed the third request and delivered the preselected host fallback. Fixing that rejection alone would not make the answer useful.

Quality against the actual question: relevance FAIL (no offered item named); contextual grounding FAIL (advertised stew/rumors unused); usefulness FAIL; identity consistency weak (friendly seller cannot describe advertised offering); authority compliance PASS (no invented consequential facts); continuation potential FAIL. Overall response classification FAIL, overall playability B because interaction execution works but answer is uninformative.

Missing information that remains genuinely unauthored: a price, ingredients, transaction availability/details. The first question needs none of these. Descriptive elaboration and persistent consequences remain distinct: simply restating the authored offering grants no food, currency, quest, promise or persistent NPC fact. Current engine instead emits noncanonical host uncertainty and prohibits durable mutation.

Smallest next investigation: add an offline regression from these captured inputs to trace a supported public scene sentence into an authorized offerings answer, preserving disclosure and state invariants. No authority/prompt/gameplay repair was made here.
''')
report('STATE_INTEGRITY',f'''# PR-PLAY-24 state integrity

Snapshots: live/baseline (after new_campaign, before start_campaign), live/opening (post-initialization), live/turns/T1/before and after, live/after. Offline/baseline also records isolated preflight state before any campaign initialization. Each has public_state.json and persistent authoritative documents. No post-follow-up snapshot exists because no follow-up occurred.

Initialization succeeds and selects frontier_gate; initialization_state_diff.json preserves all normalized before/after changes, including ordinary opening tick and opening/session logs. Full authoritative snapshots retain envelopes and bookkeeping.

First interaction integrity PASS within this captured run:

- Location remains frontier_gate; calendar Day 1 unchanged; turn_counter 1 -> 2; time_pressure clock 1 -> 2.
- Character (including inventory/currency), campaign, combat, conditions and all scene documents unchanged after the question.
- World after question exactly equals a detached copy of the before-world advanced once by existing advance_world_tick. world_remaining_diff=[] in state_comparison.json. Faction pressures 3/3/2 -> 4/4/3, agenda_progress 1 -> 2, and normal threshold event appended. No dialogue-authored world consequence.
- NPC roster/topics/relationships unchanged. Runtime trust/attitude/fear/suspicion remain 0; no known/revealed topic added; runner last_interaction_turn becomes 2.
- Interaction context, discourse focus and current_interlocutor bind tavern_runner; delivered-exchange log records the actual uncertainty. No durable factual proposition or obligation established.
- Other session changes are turn telemetry, interpretation, response policy, narration/context caches and scene-runtime bookkeeping. Full field diffs are preserved rather than silently ignored.

Unauthorized consequential changes: none observed. Narration/state mismatch: the unknown answer conflicts with what the player was publicly told about the offerings, but it does not grant or mutate a resource. This is a conversational grounding defect.

Confidentiality: {len(secrets)} distinct restricted authored strings checked across captured Player HTTP bodies; hidden game-fact matches={len(leaks)}; one runtime telemetry stamp matched. Final reply contains only the generic uncertainty; transcript manually inspected. Player projections remain player mode and privileged adapter helper rejected author/debug offline. No privileged HTTP mode used. A runtime CTIR stamp (2:2c1042f7040:8ba522ba) is publicly present under session runtime metadata; the restricted-key scan flags this telemetry identifier, not an authored secret or NPC fact. This exposure is recorded in confidentiality_verification.json. Exact matching cannot prove absence of all paraphrased leaks; no hidden gameplay disclosure observed in this evidence. Internal snapshots/requests are review-only evidence and may contain hidden game facts.

No provider-supplied descriptive or consequential additions were adopted. The current expression contract sets new_facts=false and commitment=false; fallback is canonical=false. Source and runtime evidence agree.

Owned live worker stopped; accounting saved; port released. Established terminate/wait returned process exit_code=1; ASGI graceful-shutdown completion was not demonstrated. No process was left listening.
''')
table='\n'.join(f"| {x['sequence']} {x['purpose']} | {x['input_tokens']} | {x['output_tokens']} | {x['total_tokens']} | {x['provider_latency_seconds']:.3f} | {x['total_api_latency_seconds']:.3f} | completed | 0 |" for x in rows)
report('PERFORMANCE',f'''# PR-PLAY-24 performance

All configured requests gpt-4.1-mini; provider returned gpt-4.1-mini-2025-04-14. No retries, escalations, fallbacks or judge requests.

| Request/purpose | Input | Output | Total | Provider seconds | API seconds | Status | Retries |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
{table}

Rows 2 and 3 belong to ONE HTTP action; the shared 5.500s API duration must not be summed twice. Provider seconds measure SDK invocation wall time; dispatch ledger latencies are preserved separately. Model selection was not changed.

Totals: 3 provider requests, 3847 input + 361 output = 4208 tokens. Opening: 1498 tokens, {opening['api_latency_seconds']:.3f}s API. Ordinary question: TWO provider calls, 2710 tokens, {turn['api_latency_seconds']:.3f}s API. No follow-up; remaining provider budget zero. Expression request was attempted once, not a retry of interpretation.

Live controller duration: {r['duration_seconds']:.3f}s (start through state capture, cleanup and port verification). Offline preflight controller: {read(OUT/'offline_result.json')['duration_seconds']:.3f}s; combined measured controllers {r['duration_seconds']+read(OUT/'offline_result.json')['duration_seconds']:.3f}s. Repository inspection/report writing/packaging excluded from runtime; no claim that these durations measure the entire human review session. Request timestamps and detailed timing preserved in performance_measurements.json and provider ledger.

Output limits unchanged: opening 3000 (existing), expression 80 (existing); aggregate ceilings 200000 input, 20000 output, 220000 total. Production request ceiling 3 was reached without a fourth admission attempt.
''')
report('FAILURE_ANALYSIS',f'''# PR-PLAY-24 failure analysis

First decisive conversational failure: NPC knowledge source selection / contextual grounding (boundary 10, NPC knowledge authority). Confidence HIGH from live function input/output, provider contract and published response.

Expected: runner can describe the already advertised hot stew and paid rumors, without inventing a price, sale, quest or consequential world fact.

Observed: {reply} The action interpreter, local approach normalization, binding, target resolution and social resolver all execute successfully. _next_topic_to_reveal returns null even though the scene input contains the public offerings sentence; authority grants no proposition and expression is constrained to uncertainty.

Evidence: trace_013 input (scene visible_facts and normalized metadata), trace_014 output null, trace_017 genuine_uncertainty, trace_018 empty authorized_proposition, request_03 empty authorized facts, trace_021 host selection, final accepted_response and public response. Source: social.py:1611 and 4460 onward; dialogue_authority.py:509 and 766.

Secondary failure: expressive_dialogue.py:_uncertainty_reasons/_closure_reasons/validate_expression reject the generated uncertainty for unsupported_addition (right/now). No useful grounded narration was generated and rejected. Publication successfully delivers the authorized engine fallback. Stop after the first completed HTTP action is correct; no retry or follow-up occurred. All three requests also exhausted the budget.

Known-failure relationship: reproduces the uninformative response already observed offline in PR-PLAY-23. PR-PLAY-22's action-binding failure is repaired and did not recur. No evidence identifies this exact conversational-source gap as one of the 17 baseline or eight expanded functional test failures; do not claim such a match. No broad test suite or unrelated repairs were attempted.

Smallest recommended repair investigation: an offline regression using these exact public scene/runner/question inputs, then a narrowly authorized mapping of the existing public offerings sentence into the selected NPC answer source. Keep unrelated patrol knowledge, private sources and state authority restricted. Do not start PR-PLAY-25 automatically. Expression lexicon inspection is secondary and cannot solve the primary gap alone.

Harness caveat: its native completion fields score structural completion, not usefulness. The custom quality guard stopped on the actual generic uncertainty. stop_and_quality_analysis.json explicitly records zero useful conversational turns rather than presenting the raw legacy meaningful counter as success.
''')
answers=[
('Did campaign initialization succeed?','Yes, one new_campaign reset and one start_campaign, HTTP 200, opening accepted/published.'),
('Which NPC was selected?','Tavern Runner (tavern_runner), authored, present and addressable in frontier_gate.'),
('What question was asked?',action),
('Did the action bind successfully?','Yes. MOVE preamble normalized away; ASK bound as question to tavern_runner.'),
('Did the social resolver execute?','Yes, native resolve_social_action; no check required; no authored answer selected.'),
('Was the NPC response generated by provider or engine?','Final text ENGINE. One provider expression candidate was requested and rejected.'),
('Did the response address the question?','No substantive answer; only generic uncertainty. Response quality FAIL.'),
('Was the response useful?','No; names no offering and provides no usable next step.'),
('Did it use published opening context?','Interpreter and resolver receive it, but final answer does not use the public stew/rumor information.'),
('Did knowledge system restrict the answer?','Yes downstream: empty authorized proposition forces uncertainty; primary gap is existing public context not selected as answer authority, not a confirmed secret-policy denial.'),
('Did provider generate rejected narration?','Yes, one uncertainty expression, rejected for unsupported_addition. It was not a useful offerings answer.'),
('Was a follow-up submitted?','No. Generic answer cannot support meaningful continuation; budget also exhausted.'),
('Was conversational continuity preserved?','Not demonstrated across two actions. Current NPC/topic bookkeeping persisted; no follow-up tested.'),
('Were consequential state changes authorized?','Yes for observed changes: normal one-turn tick and bookkeeping. No unauthorized changes observed.'),
('Was hidden information protected?','No disclosure observed; no hidden game facts found by exact-match/public response checks and transcript review; a runtime telemetry stamp is exposed and separately recorded.'),
('How many provider requests occurred?','3 live requests; 0 live preflight calls; 0 retries/judges/model fallbacks.'),
('Total token consumption?','3847 input + 361 output = 4208 tokens.'),
('Ordinary-interaction latency?',f"{turn['api_latency_seconds']:.3f}s API, including interpretation and expression calls."),
('Did harness stop appropriately?','Yes, after the first generic answer, with no follow-up or restart; snapshots/diagnostics saved, worker stopped, port released. Native classifier structural completion is not a usefulness PASS.'),
('Is system capable of a functional short NPC conversation?','Not demonstrated by this run. It executes a question but fails to provide a useful first answer. Overall B / PARTIAL; a broad claim that all NPC conversations are impossible is unsupported.'),
('Single highest-priority next step?','Trace an already authored public offerings sentence into a scoped NPC answer source using an offline captured-input regression, preserving existing state/disclosure boundaries.')]
report('FINAL_VERDICT','# PR-PLAY-24 final verdict\n\nSTATUS: PARTIAL. Overall verdict B — PARTIALLY FUNCTIONAL NPC INTERACTION. Response quality FAIL.\n\n'+ '\n\n'.join(f'{i}. **{q}** {a}' for i,(q,a) in enumerate(answers,1))+'\n\nExact published NPC response:\n\n'+reply+'\n\nStopped awaiting external review. No gameplay/prompt/provider-contract changes, commits, pushes or PR-PLAY-25 work.\n')
# Preserve source evidence, not unrelated repository files.
sources=['scripts/run_live_playtest.ps1','tools/playtest/runner.py','tools/playtest/worker.py','tools/playtest/gameplay.py','game/api.py','game/api_ui_mode.py','game/social.py','game/dialogue_authority.py','game/expressive_dialogue.py','game/local_interaction.py','game/player_interpretation_bridge.py','game/conversational_orchestration.py','game/provider_budget.py','game/world.py','game/opening_presentation_renderer.py']
for name in sources:
 dest=OUT/'source_snapshot'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/name).read_bytes())
posthash={k:hashlib.sha256((ROOT/k).read_bytes()).hexdigest() for k in read(OUT/'live_source_hashes.json')}
write('source_hashes_after.json',{'hashes':posthash,'all_observed_production_sources_unchanged':posthash==read(OUT/'live_source_hashes.json')})
assert posthash==read(OUT/'live_source_hashes.json')
assert not leaks
assert usage['dispatched_requests']==3 and len(rows)==3
assert state['world_matches_one_authorized_tick']
assert r['ordinary_attempted']==1 and r['cleanup']['stopped'] and r['port_released']
report('INDEX','''# PR-PLAY-24 evidence index

Read FINAL_VERDICT, KNOWLEDGE_DIAGNOSTICS and NPC_PIPELINE first. All nine requested reports are present. The exact transcript is in TRANSCRIPT.

Live and offline directories preserve configuration, readiness, provider ledger, sanitized requests/responses, native diagnostics and function traces, public/authoritative snapshots, state diffs, HTTP responses and stop reason. Internal evidence contains hidden game data for review; it was not served through privileged HTTP.

Repository status captures pre-existing work. Test-only execute_validation.py and worker_capture.py are the only execution additions; build_review.py is post-run analysis. No production changes. Source hashes and snapshots preserve the observed implementation. No broad test runs or provider judge calls.

Legacy counters have structural semantics: meaningful_gameplay_turns_completed=1 does not mean the NPC answer was useful. stop_and_quality_analysis.json supplies the explicit quality assessment and conversational stop.
''')
# Build only scoped evidence; never include .env, caches, unrelated historical runs or live mutable data.
from dotenv import dotenv_values
credentials=[v for k,v in dotenv_values(ROOT/'.env').items() if v and len(v)>6 and any(s in k.lower() for s in ('key','secret','token','password','credential'))]
selected=[]
for p in OUT.rglob('*'):
 if p.is_file() and '__pycache__' not in p.parts and p.name not in ('MANIFEST.json','archive_path.txt','archive_verification.json'):
  selected.append((p,'artifacts/pr_play_24/'+p.relative_to(OUT).as_posix()))
for mode in ('offline','live'):
 run=ROOT/'artifacts/atgb/pr_play_24'/mode
 for p in run.rglob('*'):
  if p.is_file() and 'data' not in p.relative_to(run).parts and '__pycache__' not in p.parts:
   selected.append((p,'artifacts/pr_play_24/'+mode+'/'+p.relative_to(run).as_posix()))
manifest=[];payload=[]
for p,name in selected:
 data=p.read_bytes()
 if p.suffix in ('.json','.jsonl','.txt','.log','.md','.py','.ps1'):
  raw=data.decode('utf-8')
  for credential in credentials:raw=raw.replace(credential,'[REDACTED]')
  data=raw.encode('utf-8')
 assert not any(c.encode() in data for c in credentials)
 manifest.append({'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()});payload.append((name,data))
write('MANIFEST.json',{'files':manifest,'manifest_self_hash':'Excluded to avoid recursion','scope':'PR-PLAY-24 only; credentials removed; authoritative game facts retained for review.'})
import os
stamp=os.environ['PR_PLAY24_ARCHIVE_STAMP'];archive=ROOT/'handoff'/f'CURRENT_REVIEW({stamp}).zip'
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
 for name,data in payload:z.writestr(name,data)
 z.write(OUT/'MANIFEST.json','artifacts/pr_play_24/MANIFEST.json')
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for item in manifest:assert hashlib.sha256(z.read(item['path'])).hexdigest()==item['sha256']
 count=len(z.namelist())
write('archive_verification.json',{'exists':archive.exists(),'readable':True,'crc_test':'PASS','all_manifest_hashes_verified':True,'credential_scan':'PASS','entries':count,'bytes':archive.stat().st_size,'absolute_path':str(archive)})
(OUT/'archive_path.txt').write_text(str(archive)+'\n')
print(json.dumps({'archive':str(archive),'entries':count,'bytes':archive.stat().st_size,'status':'PARTIAL','verdict':'B','source_unchanged':True}))

