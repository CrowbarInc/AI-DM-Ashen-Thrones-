"""Offline analysis and evidence packaging. Never imports an application/provider client."""
import hashlib
import json
from pathlib import Path
import shutil
import socket
from datetime import datetime
import zipfile
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'artifacts/pr_play_19'
run = Path(json.loads((OUT/'live_run.json').read_text())['run'])
offline = Path(json.loads((OUT/'offline_run.json').read_text())['run'])
def load(path): return json.loads(path.read_text(encoding='utf-8'))
def write(name, value): (OUT/name).write_text(json.dumps(value, indent=2, ensure_ascii=True)+'\n', encoding='utf-8')
def report(name, content): (OUT/name).write_text(content.strip()+'\n', encoding='utf-8')
r = load(run/'reports/result.json')
captured = load(run/'diagnostics/actual_assembled_request.json')
req = captured['request']
sdk = load(run/'diagnostics/sdk_serialized_request.json')
resp = load(run/'diagnostics/provider_response.json')
render = load(run/'diagnostics/renderer_result.json')
catalog = load(run/'diagnostics/prepared_public_catalog.json')['catalog']
start = next(s['response'] for s in r['steps'] if s['action']=='start_campaign')
text = start['gm_output']['player_facing_text']
plan = json.loads(resp['response']['output'][0]['content'][0]['text'])
before = load(run/'baseline/documents.json'); after = load(run/'after/documents.json')
def norm(v): return v['payload'] if isinstance(v, dict) and 'persistence_version' in v and 'payload' in v else v
sb = norm(before['session.json']); sa = norm(after['session.json'])
def differences(a,b,path=''):
    if type(a)!=type(b): return [{'path':path,'before':a,'after':b}]
    if isinstance(a,dict):
        return [row for k in sorted(set(a)|set(b)) for row in differences(a.get(k),b.get(k),path+'/'+k)]
    if isinstance(a,list) and len(a)==len(b):
        return [row for i,(x,y) in enumerate(zip(a,b)) for row in differences(x,y,path+'/'+str(i))]
    return [] if a==b else [{'path':path,'before':a,'after':b}]
diff = {k:differences(norm(before.get(k)),norm(after.get(k))) for k in sorted(set(before)|set(after))}
write('normalized_state_diff.json', {k:v for k,v in diff.items() if v})
write('state_comparison.json',r['state_comparison'])
hidden = before['campaign.json']['character_secret']['hidden_truth']
leak = {
    'start_request_default_ui_mode':'player (api_ui_mode.py:16)',
    'start_response_hidden_field_present': start['campaign']['character_secret'].get('hidden_truth')==hidden,
    'public_state_before_hidden_field_present':'hidden_truth' in load(run/'baseline/api_state.json')['public_state']['campaign']['character_secret'],
    'public_state_after_hidden_field_present':'hidden_truth' in load(run/'after/api_state.json')['public_state']['campaign']['character_secret'],
    'provider_request_contains_hidden_value':hidden in json.dumps(req),
    'opening_narration_contains_hidden_value':hidden in text,
    'field_path':'campaign.character_secret.hidden_truth',
    'hidden_value_omitted_from_report':True,
    'source_boundary':'game.api._complete_opening_turn_persistence_like_chat -> game.api_turn_support._build_turn_response_payload',
    'rendered_ui_display':'Not tested; HTTP response disclosure is confirmed.'}
write('publication_boundary_review.json',leak)
usage=resp['response']['usage']; latency=r['provider_usage']['records'][0]['latency_ms']/1000
timings=load(OUT/'live_timings.json'); duration=next(t['seconds'] for t in timings if t['path']=='/api/start_campaign')
old={'input_tokens':26986,'output_tokens':2050,'total_tokens':29036,'provider_latency_seconds':14.19}
new={**{k:usage[k] for k in ['input_tokens','output_tokens','total_tokens']},'provider_latency_seconds':latency}
reductions={k:(1-new[k]/old[k])*100 for k in old}
perf={'actual_provider_usage':usage,'request_count':1,'provider_latency_seconds':latency,
      'sdk_invoke_latency_seconds':resp['latency_seconds'],'initialization_http_seconds':duration,
      'engine_initialization_ms':start['resolution']['metadata']['performance']['elapsed_ms'],
      'full_harness_elapsed_seconds':r['elapsed_seconds'],'pr_play_17':old,'reduction_percent':reductions,
      'message_content_characters':sum(len(m['content']) for m in req['input']),
      'compact_schema_characters':len(json.dumps(req['text']['format']['schema'],ensure_ascii=False,separators=(',',':'))),
      'cost_estimate':None,'cost_reason':'Current pricing not independently verified; no cost estimate asserted.'}
write('performance_measurements.json',perf)
source_hashes=load(OUT/'source_hashes_before.json')
unchanged={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h for f,h in source_hashes.items()}
entries={e['catalog_id']:e for e in catalog['entries']}
checks={'assembled_equals_sdk_serialized':req==sdk,'production_sources_unchanged':all(unchanged.values()),
        'one_provider_dispatch':r['provider_usage']['dispatched_requests']==1,
        'one_http_provider_response':load(run/'diagnostics/provider_http.json')['status_code']==200,
        'one_opening_commit':r['opening_commits_observed']==1,
        'no_ordinary_turns':not any(s['action']=='player_turn' for s in r['steps']),
        'published_equals_renderer':text==render['text'],
        'trace_covers_text':text==' '.join(t['rendered_text'] for t in render['trace']),
        'selected_entries_approved':all(x['variant_id'] in entries[x['catalog_id']]['variants'] for x in plan['selected_entries']),
        'required_entries_selected':set(catalog['required_ids'])<=set(x['catalog_id'] for x in plan['selected_entries']),
        'state_integrity':r['state_comparison']['integrity'],
        'trace_public_only':all(t['disclosure']=='public' for t in render['trace']),
        'hidden_not_in_provider_or_narration':not leak['provider_request_contains_hidden_value'] and not leak['opening_narration_contains_hidden_value']}
assert all(checks.values()),checks
write('evidence_verification.json',{'checks':checks,'source_hashes_unchanged':unchanged})
(OUT/'PLAYER_OPENING.txt').write_text(text+'\n',encoding='utf-8')
write('parsed_presentation_plan.json',plan)
sources=list(source_hashes)+['game/world.py','game/state_channels.py','game/api_ui_mode.py','game/api_turn_support.py','docs/state_authority_model.md','scripts/run_live_playtest.ps1']
for f in sources:
    target=OUT/'source_snapshot'/f; target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(ROOT/f,target)
write('source_references.json',{'request_assembly':'game/gm.py:5305-5427','dispatch':'game/provider_budget.py:312',
    'schema_and_renderer':'game/opening_presentation_renderer.py:264-429','initialization_tick':'game/api.py:6386-6456',
    'publication_payload':'game/api.py:6297-6342; game/api_turn_support.py:1382',
    'public_projection':'game/api.py:5024; game/state_channels.py:195','default_ui':'game/api_ui_mode.py:16'})
rel=run.relative_to(ROOT).as_posix(); offrel=offline.relative_to(ROOT).as_posix()
report('PR_PLAY_19_PREFLIGHT.md',f'''# PR-PLAY-19 Preflight
PASS. Branch feature/product-realization; HEAD {r['repository']['revision']}; working tree already dirty. repository_status.txt preserves the full status; source_changes.diff and source_snapshot preserve relevant PR-PLAY-18 integration and existing startup changes. Production source hashes are unchanged by this pass. No commit or push.

Effective permissions: workspace-write, network enabled, auto_review approval policy, Windows PowerShell/Python 3.12.0. No escalation or security bypass used. .env was read in memory; only allowlisted safe configuration and credential presence were recorded.

Offline TCP bind/listen/connect/payload exchange passed (loopback.json). Exactly one worker readiness cycle reached GET /api/state HTTP 200 and generated http_ready.json; provider prohibition enabled, zero provider dispatches. Worker stopped; port rebound successfully. See {offrel}/diagnostics and offline_summary.json. The readiness-only controlled unwind intentionally leaves an INCONCLUSIVE scenario result, not a failed readiness check.

An initial controller invocation was rejected before worker creation because its proposed artifact store was outside artifacts/atgb. The path was corrected without changing isolation. Two later live-controller bootstrap invocations failed before worker creation (an overly broad subprocess hook assertion, then a function replacing a class needed during dependency imports). These diagnostic-wrapper mistakes were corrected before any campaign initialization. Empty/bootstrap directories are preserved. They were not provider retries, worker restarts, or opening attempts. One actual live worker and one actual live opening ran.

CampaignOpening is the existing opening-only scenario: new_campaign, baseline, start_campaign, final state. No chat/action/player-turn steps. Existing scenario ceiling is one request, stricter than the authorized two. SDK retries zero, host retries disabled; upstream token probes prohibited; no fallback/judge calls. Existing output cap 3000 and aggregate ceilings 200000/20000/220000 unchanged. Effective model gpt-4.1-mini; no pin override.

ASHEN_OPENING_RENDERER=1 scoped to controller/child; both workers attest enabled/selected. Response capture enabled. Minimal artifact-local wrapper records actual unchanged dispatch kwargs, serialized SDK body, response/status and renderer results. Predispatch assertions verify model, schema, scope and budget. No provider integration, instruction, schema or validator was modified. The successful offline readiness completed before live execution; live attestation also passed.
''')
report('PR_PLAY_19_REQUEST_CONTRACT.md',f'''# PR-PLAY-19 Request Contract
PASS. This report embeds actual captured data from {rel}/diagnostics/actual_assembled_request.json, captured before original RequestAttempt.dispatch invokes the existing SDK. sdk_serialized_request.json independently records the actual HTTP JSON body; exact equality verified. These are live captures, not source-template reconstructions.

Model gpt-4.1-mini; application purpose primary_turn, logical operation scene_opening. Sequence 1, admission sequence 1; owner gm.call_gpt. The generic purpose label does not mean an ordinary turn occurred. System and user roles only; no separate developer message. max_output_tokens=3000; temperature/top_p not set by application. No tools, fallback, or judges added. Provider response reports temperature=1, top_p=1, tools=[].

Responses API text.format: type=json_schema, name=opening_presentation, strict=true. Root requires only selected_entries; every item requires catalog_id and variant_id, with per-entry enum pairing. additionalProperties=false at root and each choice. Array minItems=1/maxItems=24. Eleven public catalog choices, six required. Required coverage, order, duplicates and disclosure are independently engine validated. No legacy narration/declaration/state-change fields required or permitted. Dedicated selection instructions replace legacy narration instructions. Contract alignment passed before SDK dispatch.

Source references: game/gm.py:5305 (preparation), :5417 (kwargs), :5427 (dispatch); game/provider_budget.py:312; game/opening_presentation_renderer.py:264, :287, :330, :378, :422. Exact schema also saved separately as diagnostics/exact_schema.json. No API keys, authorization headers or environment dumps captured.

## Actual sanitized assembled request and exact schema

```json
{json.dumps(captured,indent=2,ensure_ascii=True)}
```
''')
report('PR_PLAY_19_LIVE_EXECUTION.md',f'''# PR-PLAY-19 Live Execution
Timestamp: {r['timestamp']} (2026-11-01 10:59:21 EST, America/New_York).

Exact invocation from repository root:
```powershell
.venv/Scripts/python.exe artifacts/pr_play_19/execute_validation.py live
```
The wrapper calls existing runner.run_playtest(scenario='CampaignOpening', mode='Live', authorize_live=True, capture_response=True, output_root=artifacts/atgb/pr_play_19/live). It launches the existing worker through worker_capture.py for observation. Application endpoints, adapter, admission, parsing, rendering and persistence execute normally.

| Milestone | Actual result |
| --- | --- |
| HTTP readiness | PASS; diagnostics/http_ready.json |
| Provider requests | 1 admitted, 1 dispatched, 1 completed; zero pending |
| Real provider HTTP | 200 POST /v1/responses |
| Schema acceptance | PASS; completed strict response |
| JSON parsing / plan compliance | PASS; six approved required selections in order |
| Renderer acceptance | PASS; renderer_result.json ok=true |
| Opening publication | PASS; start_campaign HTTP 200, ok=true, campaign_started=true |
| Publication confidentiality | FAIL at raw response boundary; see publication_boundary_review.json |
| Ordinary turns | 0 |
| Stop reason | Successful initialization; no subsequent action |

Provider response ID: {resp['response']['id']}. SDK request ID: {resp['sdk_request_id']}. Returned model {resp['response']['model']}. No provider error, refusal or incomplete status. Provider status completed. Worker stopped and port released (live_port_release.json); harness uses process termination and reports exit code 1, not graceful lifespan completion.

Evidence root: {rel}. Preserve diagnostics/provider_usage.jsonl, provider_http.json, provider_response.json, renderer_result.json, prepared_public_catalog.json, predipatch check (predispatch_contract_check.json), baseline/, after/, reports/result.json and existing evidence/evidence.zip. The generic parser_output_form diagnostic says malformed even though JSON parsing/structured validation, renderer, semantic checks and publication all pass. Treat that field as a telemetry inconsistency; no parser rejection occurred.

Confirmed issue: raw start response includes campaign.character_secret.hidden_truth and debug roots. Expected player-mode response applies public projection. Evidence: response in reports/result.json versus baseline/after api_state public_state, publication_boundary_review.json; game/api.py:6297-6342 calls api_turn_support._build_turn_response_payload:1382 and returns the raw composed state. Default UI mode is player (api_ui_mode.py:16). Confidence HIGH for HTTP exposure; actual browser display untested. Failure boundary: response packaging after valid rendering/persistence. Smallest next investigation: audit/project successful start_campaign responses through the established public channel; no repair performed here.
''')
report('PR_PLAY_19_OPENING_REVIEW.md',f'''# PR-PLAY-19 Opening Review
The following is the exact published player-facing opening (563 characters):

> {text}

| Criterion | Verdict | Evidence |
| --- | --- | --- |
| Setting grounding | PASS | Cinderwatch eastern gate, rainy muddy crowd, notice board, runner, noble townhouse and watcher match six required authored scene facts in baseline/scenes/frontier_gate.json and public catalog. |
| Comprehensibility | PASS | Names the gate and shows congestion, guard control, a missing-patrol notice and immediate people/objects. No explicit second-person arrival sentence, but the starting scene is understandable. |
| Coherence | PASS | Connected compact scene, no duplicated optional board/runner descriptions; environmental and social details support the same location. |
| Player agency | PASS | Board/patrol lead, runner/paid rumor, crowd and watcher provide distinct investigable opportunities; no forced action or consequence. Choices are implicit rather than an explicit menu. |
| Factual authority of prose | PASS | Every sentence equals approved authored variant text; six trace entries are public; no invented outcomes or GM-only truth in narration. |

Prose quality verdict PASS. Structured presentation is appropriate. This does not establish ordinary gameplay quality. No further model evaluation calls were used.

Publication boundary limitation: the raw successful API response exposes a hidden campaign field outside this narration, while the normal public-state projection removes it. The value is intentionally not repeated in this player-facing review. Therefore full publication confidentiality fails despite authorized opening prose. Review-only snapshots retain the original evidence.
''')
report('PR_PLAY_19_STATE_INTEGRITY.md',f'''# PR-PLAY-19 State Integrity
PASS for deterministic mutations; FAIL for confidentiality of the raw successful HTTP envelope. Before/after snapshots: {rel}/baseline and /after, including API states and persistent documents. normalized_state_diff.json records full normalized differences. Baseline follows silent new_campaign reset and precedes start_campaign; it is not the player's canonical store.

| Domain | Before / after |
| --- | --- |
| Character/location | Character identical; active_scene_id frontier_gate unchanged; scene addressability unchanged. |
| Campaign time | No separate campaign_time/date field present. Engine time_pressure clock 0 -> 1; other clocks remain 0. |
| Turn/transcript | 0 -> 1 and one appended opening log; this is internal bootstrap, zero ordinary player turns. |
| Campaign latch | false -> true. |
| Inventory/currency | Entire character document unchanged; inventory unchanged. No separate currency field introduced. |
| Quest/NPC state | No quest changes; world NPC/relationship rows unchanged. |
| Combat | Normalized combat identical; only persistence-envelope metadata changed. |
| World facts | Flags/counters unchanged; faction pressure and agenda each +1, with two existing threshold events. |
| Overlays | No overlay entries changed; zero additions/omissions. |

Accepted mutations are owned by existing initialization: game/api.py:6439-6456 tracks provisional state, increments turn, advance_world_tick and time_pressure; game/world.py:259-350 defines faction progression/threshold events. World faction pressure [2,2,1] -> [3,3,2], agenda [0,0,0] -> [1,1,1]. This is deterministic engine progression, not provider-supplied state. Runtime narration/conversation caches and one committed log are expected. No unexpected state mutation identified; harness field/overlay checks also pass.

Provider plan only selects public variants. scene_update, world_updates, activate_scene_id and new_scene_draft are null in published gm_output. No proposed state mutation required rejection; rejected initialization/rollback was not exercised in this successful live attempt. Do not infer rollback correctness from success. No unsupported consequential narration published.

Hidden-information assessment: hidden truth absent from assembled provider request and opening text; all render traces public. However raw start_campaign response includes campaign.character_secret.hidden_truth, unlike public_state in both before/after snapshots. This is a confirmed HTTP publication boundary problem; it does not alter deterministic campaign data. Debug snapshots are reviewer-only and contain internal campaign information. UI display and unrelated secret boundaries were not audited. No broad claim of full information-boundary preservation is justified.
''')
report('PR_PLAY_19_PERFORMANCE.md',f'''# PR-PLAY-19 Performance
All token counts below are actual provider usage, not character estimates. Request count 1; cached input tokens {usage['input_tokens_details']['cached_tokens']}; reasoning output tokens 0.

| Metric | PR-PLAY-17 | PR-PLAY-19 | Observed reduction |
| --- | ---: | ---: | ---: |
| Input tokens | 26,986 | 1,378 | {reductions['input_tokens']:.2f}% |
| Output tokens | 2,050 | 120 | {reductions['output_tokens']:.2f}% |
| Total tokens | 29,036 | 1,498 | {reductions['total_tokens']:.2f}% |
| Provider latency | 14.19 s | {latency:.3f} s | {reductions['provider_latency_seconds']:.2f}% |

Provider latency uses dispatch-to-completion accounting, comparable to prior provider measurement. Direct SDK invocation measured {resp['latency_seconds']:.3f} s. /api/start_campaign HTTP duration {duration:.3f} s; engine reported {perf['engine_initialization_ms']} ms. Entire harness including configuration/startup/snapshots/shutdown was {r['elapsed_seconds']:.3f} s. Initialization HTTP timing includes response transfer/processing; startup is separately documented in http_ready.json.

Captured live input has 3,220 message characters and 2,496 compact-schema characters (5,716 combined), eleven catalog entries/six required. PR-PLAY-18's ~902-token estimate was reconstructed from a smaller six-entry payload, whereas this actual initialization exposes five additional optional public entries. Tokenization of identifiers, schema and protocol overhead also differs from characters/4. This explains why the observed 1,378 input tokens exceed that estimate while remaining 94.89% below the earlier 26,986-token request. No unexpectedly large legacy context is present.

Material token/latency improvement observed in this one sample; caching contributes zero. Output is now a compact selection plan rather than narration. These are different historical requests with network/runtime variability; one sample does not establish population latency or isolate every causal factor. Current pricing was not independently verified, so cost estimate unavailable. No provider optimization or second measurement was attempted. Source: performance_measurements.json and live diagnostics/provider_response.json/provider_usage.jsonl.
''')
answers=[
'Yes: offline loopback/readiness and live worker attestation passed.',
'Yes: real provider HTTP 200 and completed strict structured response.',
'Yes: six valid required selections, approved variants and ordering.',
'Yes: renderer ok=true, public trace and engine-authored output.',
'Yes for opening text and commit; raw response confidentiality has a confirmed limitation.',
'Yes: coherent scene and several actionable leads; opportunities are implicit.',
'Yes: authored starting-scene/campaign public facts, preserved in catalog/trace.',
'Yes for deterministic state mutations; hidden-information protection fails at raw response packaging.',
'No unauthorized consequential narrative outcomes. A hidden campaign field was exposed in the raw HTTP payload.',
'One provider request; one live opening initialization; no retries, fallback or judge calls.',
'1,378 input / 120 output / 1,498 total; cached input 0.',
f'{duration:.3f} s start_campaign HTTP; {latency:.3f} s provider; {r["elapsed_seconds"]:.3f} s full harness.',
f'{reductions["total_tokens"]:.2f}% total reduction; {reductions["input_tokens"]:.2f}% input reduction.',
'Zero ordinary gameplay turns. The one turn-counter increment is expected opening bootstrap.',
'Investigate successful start_campaign response packaging against the existing public projection before ordinary gameplay validation.'
]
report('PR_PLAY_19_FINAL_VERDICT.md','''# PR-PLAY-19 Final Verdict
PARTIAL — B: PARTIALLY FUNCTIONAL.

The repaired live selection contract is accepted end to end: provider, parser, renderer and engine publication agree, and deterministic state mutations are authorized. The opening is coherent, grounded and actionable. A is withheld because the raw successful start_campaign HTTP response exposes a hidden campaign field that public_state filters out. This is a confirmed publication confidentiality limitation, not a provider schema or renderer failure. C does not fit because opening publication succeeds; B records successful initialization with the limitation. No architecture or gameplay repair was made.

'''+ '\n\n'.join(f'{i}. {answer}' for i,answer in enumerate(answers,1))+'''

Highest-priority finding: successful start_campaign response packaging bypasses the normal public-state projection, exposing campaign.character_secret.hidden_truth at the HTTP boundary. Confidence HIGH; actual UI rendering untested. Evidence: publication_boundary_review.json, live reports/result.json response, before/after public_state, source_snapshot/game/api_turn_support.py and api.py. Hidden value deliberately omitted here.

Secondary evidence caveats: parser_output_form says malformed despite positive contract/renderer/publication checks; existing harness uncertainty text mentions deterministic execution although mode/real transport are independently established Live. Preserve raw diagnostics and interpret individual milestones. Wrapper bootstrap errors occurred before workers and provider dispatch and are disclosed in preflight. Worker termination released resources; graceful lifespan completion not established.

No further provider calls, ordinary turns, commits, pushes or PR-PLAY-20 work. Stop for external review.
''')
report('README_REVIEW_ONLY.md',f'''# PR-PLAY-19 evidence index
Start with PR_PLAY_19_FINAL_VERDICT.md. Seven requested reports, exact live request/schema/SDK body, response/status, parsed plan, renderer catalog/trace, snapshots, accounting and timings are included. This is a reviewer archive: snapshots/raw API responses contain internal campaign information needed to evaluate authority; player-facing text is separately isolated in PLAYER_OPENING.txt. No hidden plot text is quoted in the public prose reports.

One offline readiness worker and one live opening worker executed. Earlier pre-worker wrapper/bootstrap failures are retained. Main live run: {rel}. Offline readiness: {offrel}. Production sources remained unchanged; no commits or pushes. Capture scripts are local diagnostics, not a new provider client. Current pricing/cost and browser UI behavior are unverified.
''')

# Bundle only this pass and selected relevant source, keeping harness artifacts intact.
selected=[]
for root in [OUT,ROOT/'artifacts/atgb/pr_play_19']:
    for p in root.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts and p.name not in {'manifest.json','archive_path.txt','archive_verification.json'}:
            selected.append(p)
manifest=[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in selected]
write('manifest.json',manifest)
selected.append(OUT/'manifest.json')
secret_values=[v for k,v in dotenv_values(ROOT/'.env').items() if v and len(v)>8 and any(x in k.lower() for x in ('api_key','secret','password','credential','access_token','auth_token'))]
for p in selected:
    if p.suffix.lower() == '.zip':
        with zipfile.ZipFile(p) as nested:
            assert nested.testzip() is None
            for member in nested.namelist():
                blob=nested.read(member)
                assert not any(v.encode() in blob for v in secret_values), 'Secret scan failed in nested archive'
    else:
        assert not any(v.encode() in p.read_bytes() for v in secret_values), 'Secret scan failed'
archive=ROOT/'handoff'/('CURRENT_REVIEW('+datetime.now().strftime('%Y%m%d-%H%M%S')+').zip')
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
    for p in selected:z.write(p,p.relative_to(ROOT).as_posix())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for entry in manifest:
        assert hashlib.sha256(z.read(entry['path'])).hexdigest()==entry['sha256']
write('archive_verification.json',{'archive':str(archive),'exists':archive.exists(),'openable':True,
      'crc_test':'passed','sha256_manifest_verification':'passed','files':len(selected),'bytes':archive.stat().st_size,
      'known_environment_secret_scan':'passed including nested harness zips','source_hashes_unchanged':all(unchanged.values())})
(OUT/'archive_path.txt').write_text(str(archive)+'\n',encoding='utf-8')
print(json.dumps({'archive':str(archive),'files':len(selected),'bytes':archive.stat().st_size,'checks':checks,'performance':new,'initialization_seconds':duration}))
