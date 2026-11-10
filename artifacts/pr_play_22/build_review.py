"""Offline review and evidence packaging. Never invokes the game or provider."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import zipfile
from datetime import datetime, timezone, timedelta

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from game.state_channels import deep_project_public_payload, is_author_key, is_debug_key
from tools.playtest.gameplay import diff
OUT=ROOT/'artifacts/pr_play_22'
RUN=ROOT/'artifacts/atgb/pr_play_22/live'
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def write(name,value): (OUT/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def md(name,lines): (OUT/name).write_text('\n'.join(lines)+'\n',encoding='utf-8')
def un(v): return v.get('payload',v) if isinstance(v,dict) else v
def docs(label): return {k:un(v) for k,v in load(RUN/label/'documents.json').items()}
result=load(OUT/'live_result.json')
steps=result['steps']
posts=[s for s in steps if s['method']=='POST']
turns=[s for s in posts if '/api/chat?' in s['path']]
opening=next(s for s in posts if '/api/start_campaign?' in s['path'])
def text(row): return (row['response'].get('gm_output') or {}).get('player_facing_text','')
usage=result['provider_usage']
records=usage['records']
latencies=[t['api_latency_seconds'] for t in turns]
average=sum(latencies)/len(latencies)
request_rows=[]
for i,r in enumerate(records,1):
    cap=load(RUN/'diagnostics'/f'response_{i:02}.json')
    v=cap['response']
    request_rows.append({'sequence':i,'turn':'opening' if i==1 else f'T{i-1}',
        'purpose':r['purpose'],'model':v['model'], **{k:r[k] for k in ('input_tokens','output_tokens','total_tokens')},
        'cached_tokens':v['usage'].get('input_tokens_details',{}).get('cached_tokens'),
        'provider_seconds':cap['latency_seconds'],'ledger_seconds':r['latency_ms']/1000,
        'api_seconds':posts[i]['api_latency_seconds'],'provider_status':v['status'],'retry_count':0})
write('performance_measurements.json',{'requests':request_rows,'total_input':usage['input_tokens'],
      'total_output':usage['output_tokens'],'total_tokens':usage['total_tokens'],'ordinary_api_average_seconds':average,
      'ordinary_api_max_seconds':max(latencies),'ordinary_tokens_per_attempt':sum(r['total_tokens'] for r in records[1:])/len(turns),
      'ordinary_tokens_per_provider_request':sum(r['total_tokens'] for r in records[1:])/3,
      'live_duration_seconds':result['duration_seconds'],'preflight_duration_seconds':load(OUT/'offline_result.json')['duration_seconds']})

# Check complete recorded HTTP payloads against the existing public key boundary,
# and compare authored hidden scalar strings to actual responses without printing secrets.
def hidden_strings(value, restricted=False):
    if isinstance(value,dict):
        return [s for k,v in value.items() for s in hidden_strings(v,restricted or is_author_key(k))]
    if isinstance(value,list): return [s for v in value for s in hidden_strings(v,restricted)]
    return [value] if restricted and isinstance(value,str) and len(value)>20 else []
initial=docs('baseline'); postopen=docs('opening'); final=docs('after')
hidden=set(s for k,v in initial.items() if k!='session_log.jsonl' for s in hidden_strings(v))
boundary=[]
for i,s in enumerate(steps):
    raw=json.dumps(s['response'],ensure_ascii=False)
    boundary.append({'step_index':i,'path':s['path'],'public_projection_equal':s['response']==deep_project_public_payload(s['response']),
                     'authored_hidden_string_matches':sum(h in raw for h in hidden)})
write('http_boundary_verification.json',{'checks':boundary,'hidden_string_candidates':len(hidden),
    'limitation':'Key boundary and exact authored hidden strings only; not an exhaustive semantic confidentiality proof. No injected secret or privileged HTTP request used.'})
boundary_pass=all(b['public_projection_equal'] and not b['authored_hidden_string_matches'] for b in boundary)

comparisons=[]
for i in range(1,5):
    b,a=docs(f'turns/T{i}/before'),docs(f'turns/T{i}/after')
    changes=diff(b,a)
    (RUN/f'turns/T{i}/normalized_state_diff.json').write_text(json.dumps(changes,indent=2)+'\n',encoding='utf-8')
    stable=[k for k in ('campaign.json','world.json','character.json','combat.json','conditions.json') if b[k]==a[k]]
    s0,s1=b['session.json'],a['session.json']
    comparisons.append({'turn':i,'stable_documents':stable,'active_scene_before':s0['active_scene_id'],'active_scene_after':s1['active_scene_id'],
        'date_unchanged':s0['current_date']==s1['current_date'],'clocks_unchanged':s0['clocks']==s1['clocks'],
        'turn_counter_before':s0['turn_counter'],'turn_counter_after':s1['turn_counter'],
        'changed_paths':[c['path'] for c in changes]})
write('state_comparison.json',{'label':'INTERNAL DIAGNOSTIC EVIDENCE','opening_changed_paths':[c['path'] for c in diff(initial,postopen)],'ordinary':comparisons})

deviation='PROTOCOL DEVIATION: T1 already made the intended NPC sequence unusable. The controller checked HTTP/provider errors but failed to detect this host-generated semantic dead end. It submitted T2–T4 before stopping, and its raw ordinary_completed=4 counter counts HTTP success, not gameplay success. Those raw records are preserved. Review counts: 4 attempted, 4 HTTP responses, 0 successful NPC/gameplay interactions. T2–T4 are post-failure diagnostic observations, not a valid continuation or recovery. No restart, provider retry, replacement initialization, or extra live run occurred.'
write('review_summary.json',{'status':'PARTIAL','overall':'C','campaign_initialized':True,'provider_requests':4,
    'ordinary_attempted':4,'ordinary_http_completed':4,'ordinary_gameplay_completed':0,'first_decisive_failure':'T1 unsupported MOVE to present NPC blocks ASK',
    'controller_stop_reason':result['stop_reason'],'protocol_deviation':deviation,'hidden_boundary_pass':boundary_pass})

scenario=['# PR-PLAY-22 scenario','', '## Actual published opening','',text(opening),'',
    'Objective: approach an opening NPC, ask about offerings, follow up, investigate a detail, make a supported choice, and follow through.',
    '', 'Planned deterministic rules: select the first present published name in tavern runner / gate serjeant / guard. T1 asks about offerings for the runner, otherwise the situation. T2 quotes the first preceding sentence longer than 25 characters and asks for elaboration; T3 asks how the NPC knows that sentence. T4 examines the notice board only if published; T5 examines the missing-patrol posting only if T4 mentions a patrol. No planning model or judge calls.',
    '', 'Adaptation: the published opening contains the tavern runner. T1 selected it. After T1 the quote rules incorrectly treated a host refusal as NPC material; T2/T3 consequently asked about system inability, not stew or rumors. T4 selected the notice board from the opening despite the conversation already failing. T5 was not submitted because T4 did not mention a patrol.', '', deviation,'','## Actually executed actions','']
for i,t in enumerate(turns,1): scenario += [f'{i}. {t["payload"]["text"]}']
md('PR_PLAY_22_SCENARIO.md',scenario)

transcript=['# PR-PLAY-22 complete player-facing transcript','', 'This document contains exact player input and published narration. Full HTTP payloads and authoritative snapshots are INTERNAL diagnostic evidence elsewhere in this archive.',
    '', '## Opening','', '[New Campaign; Start Campaign]', '',text(opening),'', 'Public location: frontier_gate. Opening succeeded.','']
analysis=['# PR-PLAY-22 turn analysis','', deviation,'']
for i,t in enumerate(turns,1):
    r=t['response']['resolution']; m=r.get('metadata',{}); li=m.get('live_chat_interpretation') or {}; decision=m.get('conversational_decision') or {}
    diag={'resolution':r,'accepted_response':t['response'].get('gm_output',{}).get('metadata',{}).get('accepted_response')}
    (RUN/f'turns/T{i}/parser_validation_diagnostics.json').write_text(json.dumps(diag,indent=2)+'\n',encoding='utf-8')
    transcript += [f'## Turn {i}'+(' — post-failure observation' if i>1 else ''),'','Player: '+t['payload']['text'],'','AI-DM: '+text(t),'',
        f'Public state: frontier_gate; no scene transition; no discovered clues. HTTP {t["http_status"]}; resolution {r["kind"]}.',
        'Outcome: FAIL for the intended connected NPC session.' if i<4 else 'Outcome: PARTIAL as a standalone clarification; FAIL as the planned meaningful choice.', '']
    intent=['Approach the visible runner and ask about offerings.','Ask the runner for elaboration; generated action instead quotes the engine refusal.','Ask how the runner knows the quoted refusal; generated action has no sound in-world basis.','Read the posted notices by walking over to the opening notice board.'][i-1]
    assessment=[
        'Provider understood the actual target and question: MOVE tavern_runner followed by ASK tavern_runner. Host marked MOVE unsupported and ASK supported, then declined the whole sequence. No NPC speech, offer, or conversational foothold resulted. This is the first decisive gameplay failure.',
        'Provider classified the quote as a request for GM explanation (OTHER/EXPLANATION). Host emitted the identical T1 refusal, without explaining the restriction. The NPC question was not answered. This is not a valid follow-up to NPC dialogue.',
        'Provider again classified the question as GM explanation. Host repeated the identical refusal for a third time. It preserved the refusal text, not an interactive NPC conversation. The harness action itself wrongly attributes host wording to the runner.',
        'No provider request. Deterministic compound handling recognized INSPECT as a supported first action, marked the later walking/examination step unsupported, and asked permission to do the first step. It did not inspect or move. This offers a possible narrow continuation but did not rescue the original NPC scenario.'
    ][i-1]
    analysis += [f'## T{i}','', 'Player intent: '+intent,'',
        f'Technical: PASS (HTTP {t["http_status"]}, ok=true). Provider: '+('completed structured interpretation; parsed into native decision metadata.' if i<4 else 'not invoked; deterministic fast path.'),'',
        f'Parser/validator: interpretation status {li.get("interpretation_status","N/A")}; bridge status {li.get("status","N/A")}, reason {li.get("reason","N/A")}; host decision {decision.get("reason")}. Gameplay parser, resolver and narration invoked: {m.get("gameplay_parser_invoked")}, {m.get("resolver_invoked")}, {m.get("narration_invoked")}. No ordinary narration candidate was generated, so narration hard-validation is N/A, not PASS. Structured provider output was not rejected as malformed; action eligibility was blocked.','',
        'Player received: '+text(t),'',assessment,'',
        'Engine authorized: nonmutating conversational bookkeeping and log publication only. Location, time, inventory/currency, relationships, quest/world facts and combat unchanged. No unsupported consequential outcome was narrated. No NPC answer was emitted, so NPC setting appropriateness, useful information and omniscience are untested. No evidence of refusing an improvised biographical detail solely for lack of a catalog entry.','',
        f'Latency: {t["api_latency_seconds"]:.3f}s API. Verdict: '+('FAIL.' if i<4 else 'PARTIAL standalone; FAIL for connected gameplay.'),'',
        f'Evidence: live/turns/T{i}/api_response.json; parser_validation_diagnostics.json; normalized_state_diff.json; before/after snapshots.','']
md('PR_PLAY_22_TRANSCRIPT.md',transcript)
md('PR_PLAY_22_TURN_ANALYSIS.md',analysis)

state=['# PR-PLAY-22 state integrity','', 'INTERNAL DIAGNOSTIC REVIEW. Full initial authoritative snapshot: live/baseline/documents.json; post-opening: live/opening/documents.json; each turn: live/turns/Tn/before and after/documents.json. Public snapshots are adjacent public_state.json files. Persistence envelopes and integrity hashes are preserved.','',
    f'Opening: campaign_started {initial["session.json"]["campaign_started"]} -> {postopen["session.json"]["campaign_started"]}; turn_counter {initial["session.json"]["turn_counter"]} -> {postopen["session.json"]["turn_counter"]}; location {initial["session.json"]["active_scene_id"]} -> {postopen["session.json"]["active_scene_id"]}. Engine opening pipeline publishes the renderer output and commits opening bookkeeping. Full path changes: state_comparison.json and live/opening/state_diff.json.', '',
    'Ordinary turns: campaign, world, character, combat, conditions and scene files are unchanged. Inventory, currency and relationships therefore unchanged. Session location/date/clocks/turn_counter unchanged. Session changes concern delivered conversational exchanges, last exchange/category/subject, save timestamps and integrity hashes. T4 adds pending_clarification for the compound sequence. Each request appends a session-log record but does not claim a resolved gameplay transition. Full snapshots reconstruct list content omitted from bounded diff previews.','']
for c in comparisons: state += [f'T{c["turn"]}: {len(c["stable_documents"])} core documents stable; location {c["active_scene_before"]}; counter {c["turn_counter_before"]}->{c["turn_counter_after"]}; date/clocks unchanged = {c["date_unchanged"]}/{c["clocks_unchanged"]}.','']
state += ['Authorized mutations: opening publication and host conversation/log bookkeeping. Unauthorized mutations: none observed. Narration/state mismatches: none consequential; all ordinary responses explicitly deny execution. NPC remains authoritatively present despite approach being unsupported. Descriptive opening facts came from the renderer catalog, not new provider-authored consequences.','',
    f'Hidden boundary: {"PASS within observed scope" if boundary_pass else "FAIL; inspect verification"}. All {len(boundary)} complete recorded HTTP bodies equal their deep public projection; exact authored hidden string matching found no matches. See http_boundary_verification.json for candidate count and per-response checks. This checks existing key policy plus long hidden strings, not arbitrary semantic inference. No privileged HTTP or secret injection performed. Player-facing metadata includes host authorization/interpretation diagnostics; that is an observable exposure of implementation details, but no authored GM secret was found.','',
    'Authority limits: no purchase, quest progression, combat or relationship mutation was exercised. These subsystems are INCONCLUSIVE; observed nonmutation safety does not prove successful deterministic action resolution.']
md('PR_PLAY_22_STATE_INTEGRITY.md',state)

performance=['# PR-PLAY-22 performance','', '| Request | Purpose | Model | Input | Output | Total | Cached | Provider seconds | API seconds | Status | Retries |', '|---|---|---|---:|---:|---:|---:|---:|---:|---|---:|']
for r in request_rows: performance += [f'| {r["sequence"]} ({r["turn"]}) | {r["purpose"]} | {r["model"]} | {r["input_tokens"]} | {r["output_tokens"]} | {r["total_tokens"]} | {r["cached_tokens"]} | {r["provider_seconds"]:.3f} | {r["api_seconds"]:.3f} | {r["provider_status"]} | 0 |']
performance += ['',f'T4: zero provider requests/tokens; API latency {turns[3]["api_latency_seconds"]:.3f}s. All four provider responses completed. No transport retries, judge calls or alternate model dispatches.', '',
    f'Totals: {usage["input_tokens"]} input + {usage["output_tokens"]} output = {usage["total_tokens"]} tokens; 4 live requests. Opening: 1498 tokens. Ordinary: 7997 tokens over 3 provider requests / 4 API turns. Mean ordinary tokens: {7997/4:.2f} per attempted turn; {7997/3:.2f} per ordinary provider request.', '',
    f'Ordinary API latency mean {average:.3f}s, maximum {max(latencies):.3f}s. Live experiment duration {result["duration_seconds"]:.3f}s from worker spawn through shutdown. Offline readiness duration {load(OUT/"offline_result.json")["duration_seconds"]:.3f}s separately; report-writing time excluded. Provider times measured around real SDK invocation; durable-accounting latency is separately retained in performance_measurements.json. API latency excludes subsequent snapshot requests.', '',
    'PR-PLAY-19 reference: opening 1378 input / 120 output / 1498 total, ~2.26s. This opening has identical usage, 2.756s provider time. Ordinary requests: 2509 / 2689 / 2799 tokens (1.67–1.87x opening), despite producing no NPC dialogue.', '',
    'Context contributors (exact assembled request content characters, not token estimates): ordinary system interpretation instructions 5168 characters each; ordinary user JSON 3113, 3784, 4508 characters. Opening system 1381 / user 1839. The interpreter system instructions are the largest single content segment. User context grows with the quoted refusal and recent exchanges. Response JSON schema adds serialization overhead. Requests preserve full schemas and content for independent token analysis; no unsupported per-section token counts are inferred. No narration-generation context was exercised.']
md('PR_PLAY_22_PERFORMANCE.md',performance)

failure=['# PR-PLAY-22 failure analysis','',
    'First decisive failure: T1. Expected: the visible, present tavern runner responds to a harmless approach/question about offerings. Observed: provider correctly identifies MOVE tavern_runner + ASK tavern_runner; engine marks first step unsupported and emits a nonmutating refusal. NPC is present, ASK is supported, but neither action executes. Confidence: high for observed boundary; moderate for generality across other phrasings. A pure ASK was not attempted; do not infer all possible ordinary actions fail.', '',
    'Exact player request: '+turns[0]['payload']['text'],'', 'Exact published response: '+text(turns[0]),'',
    'Failure boundary: game/conversational_orchestration.py:_compound_clarification rejects when the first step is unsupported (around lines 1685–1710). game/player_interpretation_bridge.py maps MOVE to scene_transition and target kind exit; the provider proposes an NPC target instead. HTTP resolution records proposal_not_eligible, MOVE supported=false, ASK supported=true; resolver_invoked=false and narration_invoked=false. This is host action binding/orchestration, not a malformed provider response, missing narration transport, hidden-state mutation, or exhausted request budget.', '',
    'Known-test correlation: the preexisting test_chat_active_target_direct_command_routes_to_social_exchange expects social_probe but receives conversational_clarify (PR-PLAY-21 repaired_tests.txt lines 205–210). The live T1 also routes a grounded NPC intention to conversational_clarify instead of social execution: a concrete output-routing resemblance. That test uses a different utterance and does not establish the identical MOVE-to-NPC cause. test_direct_npc_question_keeps_dialogue_contract_and_question_relevant_unknown_fallback has captured_inputs=[] (lines 162–165), resembling the absence of NPC narration generation here, but its stub setup differs. No causal equivalence established. Retry-expectation failures, output-shape mismatch and parser rejection do not explain this live failure.', '',
    'Later observations: T2/T3 repeated the refusal verbatim; T4 asked clarification about unsupported later compound steps. These do not establish NPC continuity, and the generated T2/T3 inputs themselves confuse host refusal with NPC knowledge.', '',deviation,'',
    'Smallest next investigation: offline reproduction of the exact T1 interpretation and bridge decision for a present NPC; inspect whether intra-scene approach should bind to a local interaction rather than an exit MOVE. Keep authoritative validation intact. Separately repair the test controller semantic stop predicate before another live authorization. No defect repaired in this pass.']
md('PR_PLAY_22_FAILURE_ANALYSIS.md',failure)

verdict=['# PR-PLAY-22 final verdict','', 'Status: PARTIAL (experiment executed and evidenced; stop-rule deviation). Overall: C — NOT CURRENTLY PLAYABLE for the tested ordinary NPC sequence. A functional short RPG session was not demonstrated. This does not establish that every possible single-action phrasing fails.','',
    '| Dimension | Verdict | Evidence |','|---|---|---|',
    '| Responsiveness | FAIL | Correctly understood T1 question yields host refusal rather than answer. |',
    '| Continuity | FAIL | No NPC dialogue established; T2/T3 repeat T1 refusal. Post-failure inputs are themselves flawed. |',
    '| NPC interaction | FAIL | Zero NPC lines or offering answers. |',
    '| Agency | PARTIAL | No action executed; T4 offers a clarification choice for a supported first step. |',
    '| State integrity | PASS in observed scope | Consequential state unchanged; no invented completion. Mutating subsystems untested. |',
    '| Narrative coherence | FAIL | Opening offers an NPC; routine approach/question leads to system-level refusal. |',
    '| Reliability | PARTIAL | All HTTP calls complete, but zero successful NPC turns. |',
    '| Performance | PARTIAL | Short API times, but tokens purchase no useful NPC dialogue; successful-session cost untested. |','',
    '1. Initialization succeeded: accepted structured plan, renderer success, published opening and campaign_started=true.',
    '2. Provider requests: 4 total (1 opening, 3 interpretation).',
    '3. Ordinary turns attempted: 4.',
    '4. Ordinary turns completed: 4 HTTP responses; 0 successful intended gameplay interactions.',
    '5. AI-DM addresses actions: interpretation recognizes T1; player-facing response fails to answer it.',
    '6. NPC interaction: failed; no dialogue reached.',
    '7. Conversational continuity: no viable NPC sequence established; repeated refusal and flawed post-failure prompts.',
    '8. Meaningful choices: not realized; T4 limited clarification only.',
    '9. State changes: authorized opening and conversation/log bookkeeping; no unauthorized mutation observed.',
    '10. Unsupported consequences narrated: none observed.',
    f'11. Hidden information: protected in observed payloads ({boundary_pass}); key/exact-string checks are bounded, not a semantic proof.',
    '12. Provider responses rejected: no malformed/schema/parser response rejection observed. Host blocked T1 action eligibility, distinct from provider contract rejection.',
    f'13. Average ordinary API latency: {average:.3f}s.',
    f'14. Total consumption: {usage["total_tokens"]} tokens ({usage["input_tokens"]} input, {usage["output_tokens"]} output).',
    '15. Known failure correlation: concrete conversational_clarify instead of social route resembles existing routing test; identical root cause not proved.',
    '16. Functional short RPG session: not demonstrated; tested opening-to-NPC path blocked at T1.',
    '17. Highest-priority next step: offline investigation of exact approach-NPC MOVE binding and compound rejection, without relaxing authority.','',
    'First decisive failure: T1 proposal_not_eligible. Actual controller stop: no_supported_consequence_followup before T5; budget still had two requests. No new live attempt authorized or performed.','',deviation,'',
    'No production changes, commits or pushes. Stop and await external review.']
md('PR_PLAY_22_FINAL_VERDICT.md',verdict)

# Freeze relevant source, baseline evidence and test-only scripts for independent review.
source_paths=list(load(OUT/'live_source_hashes.json'))+['game/conversational_orchestration.py','game/player_interpretation_bridge.py',
    'game/live_chat_interpretation.py','game/state_channels.py','tools/playtest/scenarios/FiveTurnGameplay.json']
source_hashes={}
for p in source_paths:
    target=OUT/'source_snapshot'/p; target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(ROOT/p,target)
    source_hashes[p]=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
write('source_hashes_after.json',source_hashes)
assert all(source_hashes[p]==h for p,h in load(OUT/'live_source_hashes.json').items())
baseline=OUT/'known_test_baseline';baseline.mkdir(exist_ok=True)
for p in ['PR_PLAY_21_TEST_RESULTS.md','repaired_tests.txt']:
    shutil.copy2(ROOT/'artifacts/pr_play_21'/p,baseline/p)
md('README.md',['# PR-PLAY-22 review archive','', 'Start with PR_PLAY_22_FINAL_VERDICT.md. Review counts supersede raw HTTP-only counters; protocol deviation is disclosed.', '',
    'PR_PLAY_22_TRANSCRIPT.md is the player-facing transcript. All live/ and offline/ snapshots, HTTP captures, prompts, provider responses, diagnostics, diffs and source are INTERNAL DIAGNOSTIC EVIDENCE and may contain GM-only campaign material. Do not serve this archive to players.', '',
    'live/ is the single live campaign. offline/ is one readiness cycle plus a clearly separate synthetic budget test (six fake dispatches, zero live calls). No historical campaigns packaged. Configuration contains no credential values. Native raw records remain unchanged. Request_01..04 and response_01..04 reconstruct all provider interactions.', '',
    'Test controller semantic stop missed T1; T2–T4 retained as post-failure observations. Do not replay execute_validation.py against the provider. Its durable single-run marker blocks another live attempt. No PR-PLAY-23 work performed.'])

# This authorized run is on November 1, 2026 after the New York DST transition.
stamp=datetime.now(timezone(timedelta(hours=-5))).strftime('%Y%m%d-%H%M%S')
archive=ROOT/'handoff'/f'CURRENT_REVIEW({stamp}).zip'
files=[]
for root,prefix in [(OUT,'review'),(RUN,'live'),(RUN.parent/'offline','offline')]:
    for p in root.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.zip' and p.name not in {'archive_path.txt','archive_verification.json','MANIFEST.json'}:
            files.append((p,prefix+'/'+p.relative_to(root).as_posix()))
from dotenv import dotenv_values
secret_values=[v for k,v in {**dotenv_values(ROOT/'.env'),**os.environ}.items() if isinstance(v,str) and len(v)>10 and any(s in k.lower() for s in ('api_key','secret','password','credential','access_token','auth_token'))]
for p,name in files:
    data=p.read_bytes()
    assert not any(s.encode() in data for s in secret_values), f'Secret detected in {name}'
manifest=[{'path':name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p,name in files]
write('MANIFEST.json',{'files':manifest,'manifest_self_hash':'excluded'})
files.append((OUT/'MANIFEST.json','review/MANIFEST.json'))
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
    for p,name in files:z.write(p,name)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    assert all(hashlib.sha256(z.read(m['path'])).hexdigest()==m['sha256'] for m in manifest)
    assert all('PR_PLAY_22_'+n+'.md' in '\n'.join(z.namelist()) for n in ('PREFLIGHT','SCENARIO','TRANSCRIPT','TURN_ANALYSIS','STATE_INTEGRITY','PERFORMANCE','FAILURE_ANALYSIS','FINAL_VERDICT'))
write('archive_verification.json',{'path':str(archive),'files':len(files),'bytes':archive.stat().st_size,'crc_ok':True,'manifest_hashes_ok':True,'secrets_scan_passed':True,'source_unchanged':True})
(OUT/'archive_path.txt').write_text(str(archive)+'\n',encoding='utf-8')
print(json.dumps({'archive':str(archive),'files':len(files),'hidden_boundary_pass':boundary_pass,'average_ordinary_latency':average,'total_tokens':usage['total_tokens']}))
