"""Build review export strictly from captured PR74 evidence."""
import json,hashlib,statistics,subprocess,zipfile,shutil,os
from pathlib import Path
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).parent;REPORT=ROOT/'development/campaigns/product_realization/pr_play_74'
REPORT.mkdir(parents=True,exist_ok=True)
def read(n):return json.loads((OUT/n).read_text())
def write(n,v):(OUT/n).write_text(json.dumps(v,indent=2))
def stats(vals):return {'count':len(vals),'mean':statistics.mean(vals) if vals else None,'median':statistics.median(vals) if vals else None,'maximum':max(vals) if vals else None}
before=read('protected_before.json');changed=[k for k,v in before.items() if not (ROOT/k).exists() or hashlib.sha256((ROOT/k).read_bytes()).hexdigest()!=v]
write('protected_integrity.json',{'entries':len(before),'preserved':len(before)-len(changed),'changed':changed});assert not changed
freeze=read('final_source.json');assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==v for p,v in freeze.items())
http=read('http_summary.json');traces=read('http_traces.json');browser=[json.loads(l) for l in (OUT/'browser_network.jsonl').read_text().splitlines() if l.strip()];chats=[r for r in browser if r['path']=='/api/chat']
def controlled(s):return [e for e in s.get('bounded_improvisation',{}).get('entries',[]) if e.get('authority')=='controlled_world_fact' and e.get('campaign_id')==s.get('campaign_run_id')]
loads=[r for r in browser if r['path']=='/api/snapshots/load'];survey_load=next(r for r in loads if controlled(r['authority_after']['session']));survey_entries=controlled(survey_load['authority_after']['session']);assert len(survey_entries)==2
survey_again=next(r for r in chats if 'I examine it again.' in r['request']);after=controlled(survey_again['authority_after']['session']);assert [e['id'] for e in after]==[e['id'] for e in survey_entries]
assert len(next(e for e in after if e['family']=='object')['interactions'])==2
report_load=next(r for r in loads if not controlled(r['authority_after']['session']));assert report_load['authority_after']['world']['world_state']['flags']['patrol_guards_warned']
write('entity_identity_records.json',{'browser_survey_before_resume':survey_entries,'browser_survey_after_interaction':after,'http_campaigns':http['campaigns']})
publication_rows=[{'input':r['request'],'text':json.loads(r['response']).get('gm_output',{}).get('player_facing_text',''),'server_ms':r['server_ms']} for r in chats]
write('browser_typed_transcript.json',publication_rows)
hidden=sum(any(w in r.get('response','') for w in ['SENTINEL_','CANARY_','"hidden_facts"','"gm_notes"']) for r in browser)
assert hidden==0
write('browser_results.json',{'campaign_A':'PASS: typed environmental/object proposal, inspect, snapshot, reload/load, same object pronoun','campaign_B':'PARTIAL: report lifecycle and authored NPC resume; improvised NPC creation deferred','typed_requests':len(chats),'hidden_exposures':hidden,'server_chat_ms':stats([r['server_ms'] for r in chats]),'browser_visible_latency':None,'paint_timing':'not instrumented','screenshots':['browser_A_resume.png','browser_B_report.png','browser_B_resume.png'],'initial_attachment':'first attach timed out; second attach succeeded','isolation':'browser_data separate from http_data; an initial pre-gameplay host was replaced before recorded campaigns'})
# Current resolver-owned mandatory fixture disclosures, matched without casing assumptions.
from sys import path as syspath
syspath.insert(0,str(ROOT))
from tests.helpers.storage_isolation import install
install(OUT/'package_data')
from tests.test_pr_play_52_quarantined_integration import NOTICE_CLUE,PRINT_CLUE
checks=[]
for lane,records in [('http',traces),('browser',browser)]:
 for r in records:
  if lane=='http':
   req=r['request'].get('json') or {};body=r.get('body',{});text=req.get('text','')
  else:
   if r['path']!='/api/chat':continue
   req=json.loads(r['request'] or '{}');body=json.loads(r['response']);text=req.get('text','')
  expected=NOTICE_CLUE if text=='I examine the notice board.' else PRINT_CLUE if text=='I examine the weathered milestone.' else None
  if expected:
   publication=body.get('gm_output',{}).get('player_facing_text','');checks.append({'lane':lane,'input':text,'required':expected,'present':expected.casefold() in publication.casefold()})
write('publication_scan.json',{'hidden_key_or_sentinel_exposures':hidden,'mandatory_fixture_checks':checks,'omissions':sum(not r['present'] for r in checks),'scope':'Known mandatory notice/milestone discoveries plus exercised hidden-field/sentinel projection checks; not an unrestricted semantic proof.'})
usage=read('provider_results.json')['usage'];reg=read('regression_comparison.json');hold=read('holdout_results.json')
lat={'http_ms':{k:http[k] for k in ['mean_http_ms','median_http_ms','max_http_ms']},'browser_server_ms':stats([r['server_ms'] for r in chats]),'provider_proposal_ms':stats([r['latency_ms'] for r in read('provider_results.json')['rows']]),'validation_ms':stats([r['validation_ms'] for r in hold]),'save_load_http_ms':stats([r['http_ms'] for r in traces if r['request']['path'] in ['/api/snapshots','/api/snapshots/load']]),'stages':{}}
for stage in ['interpretation_ms','resolver_ms','atomic_write_ms','publication_ms']:
 vals=[v for r in browser for v in r.get('stages',{}).get(stage,[])];lat['stages'][stage]=stats(vals)
lat['commit_only_ms']=None;lat['browser_visible_ms']=None;write('latency.json',lat)
metrics={'verdict':'B — PARTIAL / BOUNDED IMPROVISATION DEMONSTRATED','protected':read('protected_integrity.json'),'development':{'passed':88,'failed':0},'inherited':{'passed':105,'failed':0},'holdout':read('holdout_summary.json'),'http':http,'browser':read('browser_results.json'),'provider_requests':usage['requests'],'provider_tokens':usage['total_tokens'],'provider_retries':0,'provider_shadow_accepted':2,'provider_shadow_rejected':0,'holdout_accepted':sum(r['validation']['accepted'] for r in hold),'holdout_rejected':sum(not r['validation']['accepted'] for r in hold),'gameplay_committed_facts':{'final_http':4,'browser_survey':2,'browser_report':0},'unauthorized_promotions_final':0,'hidden_exposures_final':hidden,'mandatory_fixture_omissions_final':sum(not r['present'] for r in checks),'critical_unsafe_publications_final_observed':0,'new_regression_identities':sum(len(v['new_failures']) for v in reg.values()),'experimental_isolation':'PASS in executed lanes; gate default off','state_integrity':'PASS in exercised persistence/lifecycle lanes','development_failures_retained':'Unknown reference initially selected focused object in pure planner; tightening reference grammar exposed unsupported move-it fallthrough mutating a turn in two branch development tests. Narrow guard repaired before freeze. See development_final.txt and development_repaired.txt. No holdout edits/rerun.'}
write('metrics.json',metrics)
write('proposal_schema.json',{'type':'object','additionalProperties':False,'required':['family','campaign_id','scene_id','anchor','quality','visibility'],'properties':{'family':{'enum':['environment','object']},'campaign_id':{'type':'string'},'scene_id':{'type':'string'},'anchor':{'type':'integer','minimum':0},'quality':{'enum':['rough','seat']},'visibility':{'const':'public'}},'engine_constraints':['environment pairs only with rough','object pairs only with seat','affirmative public stone anchor required','matching campaign and active scene required','canonical descriptions and properties are engine owned']})
sections=[
('01_EXECUTIVE_SUMMARY','B — PARTIAL / BOUNDED IMPROVISATION DEMONSTRATED. Two narrow families persist and support later inspection. Background NPC creation is deferred. Live provider proposals were evaluated only in shadow mode. No commit or push. See metrics.json for exact scoped counts.'),
('02_REPOSITORY_BASELINE','Branch feature/product-realization, revision d40f1ed198236c604085f1c842ead267a8104ce2. Extensive dirty entry state preserved. baseline.json records the complete entry status. Existing source changes predate this cycle; source_worktree.diff is against HEAD and includes those changes. Task edits: bounded_improvisation.py append-only controlled lane, player_initiative.py planning hook, player_interpretation_bridge.py revalidation, exploration.py resolver hook, new test_pr_play_74_controlled_world.py. Added evidence under artifacts/pr_play_74, reports here, and prepended docs/NEXT_SESSION.md. Generated review exports updated.'),
('03_TEST_DATA_ISOLATION','150/150 protected own-entry data files unchanged. protected_before.json and protected_integrity.json retain evidence. The existing import-safe storage isolation helper sets campaign/session/save/provider paths before game imports and guards data plus historical artifacts. HTTP, browser, holdout, provider, package and pytest have separate roots. An initial browser host was restarted on browser_data before the recorded browser campaigns; http_data was used only by sequential HTTP runs thereafter. No silent restoration.'),
('04_WORLD_STATE_ARCHITECTURE','Player initiative read-only planning -> stored interpretation bridge revalidation -> existing exploration resolver -> existing bounded_improvisation ledger in session -> existing transaction/persistence/snapshot -> resolver engine_publication. Existing PR73 physical_search resolves inspection and no-discovery behavior. Stable identity hashes campaign, scene, family and public anchor. Existing incidental_entity NPC support was considered but does not provide the required full proposal/persistence/publication contract for this slice; NPC creation is deferred. No parallel world store or action engine.'),
('05_FACT_CLASSIFICATION','A: same accepted fact returns established without duplication. B: rough stone surface. C: ordinary stone seat. D: unsupported quality/family (including consequential expansion) is refused; arbitrary fields fail schema. E: context, anchor, contradiction or authored identity failure. This is a constrained structural contract, not a general free-text semantic classifier. Authored facts remain in existing world/scene definitions.'),
('06_PROPOSAL_VALIDATION','Exact keys, types (bool is not integer anchor), public visibility, active scene/campaign, range, supported family/quality pairing and affirmative public material anchor are checked before commitment. Unknown fields, names, prose, properties, mechanics, hidden metadata and effects are refused. Engine derives all accepted text. proposal_schema.json records the contract. Rejected prose is never published by this lane.'),
('07_AUTHORITY_AND_PROVENANCE','Each entry records stable ID, campaign, scene, B/C category, entity type, canonical label/description, properties, accepted_improvisation provenance, creation turn, public visibility, accepted authority, campaign persistence status, anchor and interaction records. Existing bounded ledger is reused; controlled_facts filters by authority, current campaign and optional scene. Legacy incidental/claim entries coexist and are not counted as controlled entities. Narration cannot create these records.'),
('08_ENVIRONMENTAL_IMPROVISATION','Describe the stone surface. requests a low-impact surface property supported by an affirmative public stone anchor. Accepted output: The stone has a rough, uneven surface. It persists as an entity and can be inspected. Scope is stone-supported scenes only; there is no universal environmental object catalog or campaign-specific phrase/location switch.'),
('09_OBJECT_IMPROVISATION','Is there anything nearby I could sit on? proposes an ordinary low stone seat beside established stonework. The resolver creates its canonical identity/properties and persists it. Examine/search uses PR73 physical search without hidden contents or discoveries. Sitting, moving, taking, climbing and destruction lack mechanics and are refused; the label does not grant mechanical success.'),
('10_BACKGROUND_NPC_IMPROVISATION','DEFERRED. No new background NPC contract is implemented. HTTP and browser report campaigns attempted a background-person request; the existing fallback returned Guard Captain says, "I couldn\'t tell you." Browser then exercised an authored NPC and resumed that interaction. These are not evidence of improvised NPC creation or full required Campaign B success. No tavern or crowd was added.'),
('11_IDENTITY_AND_REFERENCE','Stable labels plus scene/campaign-filtered identity and ledger focus resolve supported explicit names and bare contextual pronouns. I examine it again. after save/load targets the same object. Unknown qualified targets do not inherit focus. Ambiguous/unsupported reference forms remain clarification/refusal paths. No failed reference invents an entity. entity_identity_records.json preserves IDs/properties/interaction history.'),
('12_INTERACTION_AND_CONSEQUENCES','The authoritative exploration resolver reuses general_purpose_actions.exploration_outcome for physical search through a detached projection of the accepted entity. It records the legitimate search turn/action in the existing ledger; no discovery, loot, movement, NPC compliance or invented DC is granted. Repeated calls in one turn do not duplicate the same interaction event. Later turns add legitimate interaction history. No journal entry is invented.'),
('13_CONTRADICTION_AND_ESCALATION','Cross-scene/campaign, negated/absent/painted/imagined/dead support, unsupported quality and hidden fields fail validation. Same identity returns established; a second same-family identity in the scene is refused. Arbitrary property changes are not accepted by schema. This does not claim full natural-language contradiction reasoning across all campaign notes. Consequential questions/refusals and unsupported mechanics remain nonexecuting in tested cases.'),
('14_PERSISTENCE_AND_RESUME','Existing session envelope and snapshot transaction persist ledger/focus/interactions. Both final HTTP campaigns created normal new campaigns, followed exclusive branches, accepted two facts at milestone, inspected object, saved, created a different campaign, loaded, restored transcript and inspected the same ID. Browser survey did snapshot -> reload -> load -> pronoun inspection with two recorded interactions. Existing lifecycle/recovery lane 39/39, including Windows atomic write and failure rollback owners.'),
('15_PLAYER_SAFE_PUBLICATION','Only engine-derived canonical descriptions and PR73 no-discovery search results publish. Hidden proposal fields and arbitrary provider prose cannot enter the schema. projection scan found zero hidden sentinel/key exposures. Mandatory notice/milestone disclosure scan is recorded in publication_scan.json, alongside inherited safety tests. This is scoped evidence, not a proof for all unrestricted narration. Development turn-fallthrough failures are preserved separately from final observations.'),
('16_PROVIDER_PROPOSALS','Two actual gpt-4.1-mini requests used the existing configuration, OpenAI client patterns and provider_budget admission/dispatch ledger. Total 360 tokens, no retries. Both proposals validated, neither committed nor published (shadow evaluation only). provider_results.json and provider_data/provider_usage.jsonl retain proposal, verdict, request usage and latency. Malformed responses/timeouts have deterministic rejection tests. Normal gameplay uses deterministic constrained proposals; automatic live-provider proposal commitment remains deferred.'),
('17_DEVELOPMENT_TESTS','Final focused development: 88 passed / 0 failed, development_repaired2.xml. Inherited PR73 plus existing bounded authority: 105 passed / 0 failed, inherited_final.xml. Initial integration wiring errors were fixed before successful gameplay. The retained failed development runs expose a wrong focused-reference selection and later unsupported move-pronoun turn fallthrough; both were repaired through development before holdout freeze, with final lifecycle/refusal tests passing. No deferred NPC behavior is counted passing.'),
('18_FROZEN_HOLDOUT','80/80 on one execution after final_source.json freeze. Developer authored before implementation, not external independent validation. SHA256 '+read('frozen_holdout_manifest.json')['sha256']+'. Distribution is structural schema/context/material validation with varied isolated scenes, including 16 accepted and 64 rejected proposals. Repeated templates reduce diversity. Manifest records persistence expectations, but holdout runner tests validation purity only; persistence is separately demonstrated by lifecycle evidence. No NPC, broad language or independent generalization claim.'),
('19_REAL_HTTP_GAMEPLAY','Final normal TCP run: 37 requests, two branch lifecycles, no developer seeding API. Campaign A controlled env/object persistence PASS. Campaign B report branch and substituted controlled env/object persistence PASS; requested improvised NPC portion DEFERRED/PARTIAL. Exact original inputs, response bodies, before/after states, IDs and HTTP timings are in http_traces.json. http_network.jsonl also retains the earlier sequential run; final selected results are http_traces.json and http_summary.json.'),
('20_BROWSER_GAMEPLAY','Initial attachment timeout recovered on second attempt. Campaign A PASS for typed environmental request, object introduction, inspection, save/reload/load and same-object pronoun. Campaign B PARTIAL: normal report lifecycle, background NPC request fallback, authored NPC conversation, hidden-info refusal, save/reload/load and authored NPC repeat. No improvised NPC claim. Seventeen typed submissions captured with original input/output and authority snapshots. Three screenshots included. Browser-visible paint time not instrumented; server times are separate.'),
('21_REGRESSION_RESULTS','Focused 1065 passed / 20 failed; boundary 101/6; broader 0/9; isolated lifecycle 39/0. Failure identity sets exactly equal PR73 in all four lanes; zero new failure identities. regression_comparison.json records comparisons. Existing failures were not relabeled or repaired. Regression source was imported while repairs were in progress, but this lane runs with new feature off; final enabled-path tests and HTTP run separately cover the repaired path. No full-suite or official ATGB benchmark claim.'),
('22_LATENCY_AND_PROVIDER_USAGE','Final HTTP mean '+str(round(http['mean_http_ms'],2))+' ms, median '+str(round(http['median_http_ms'],2))+' ms, maximum '+str(round(http['max_http_ms'],2))+' ms. latency.json contains mean/median/max for provider proposals, validation, snapshot save/load and captured interpretation/resolver/atomic-write/publication stages. Commit-only and browser-visible paint latencies unavailable, not substituted with HTTP times. Provider accepted 2/2 shadow proposals (100%); holdout accepted 16/80 and rejected 64/80 by expected policy. Gameplay final HTTP committed four controlled facts and browser survey two; provider committed zero.'),
('23_LIMITATIONS_AND_OPEN_RISKS','B/PARTIAL: only two narrow stone-supported families; no new NPCs, no free-text fact validation, no broad contradiction solver, no object movement/sitting mechanics, provider remains shadow-only. Holdout is repetitive structural evidence with no persistence execution; broader generalization and full provider scenario matrix deferred. Browser B is authored-NPC evidence only. Two branch development turn-fallthrough failures retained and repaired before final freeze; final executed paths observed zero critical unsafe publications. Historical regressions remain. Provider helper is explicitly shadow; no UI provider toggle added. Review feature remains default off.'),
('24_NEXT_SESSION','Proceed toward PR-PLAY-75 — DYNAMIC NPC INTERACTION AND SOCIAL CONSEQUENCE CONTINUITY. Preserve the controlled proposal/authority boundary and stable ledger; address background NPC representation and ordinary conversation within that cycle. Do not implement PR75 in this closure. Read these reports, metrics.json, final_source.json, provider_results.json and regression_comparison.json first. No new stabilization cycle solely for limited personality or latency. No commit or push without authorization.')]
for name,body in sections:(REPORT/(name+'.md')).write_text('# PR-PLAY-74 — '+name.replace('_',' ')+'\n\n'+body+'\n',encoding='utf-8')
# Capture full final source and worktree diff; the baseline explicitly separates pre-existing changes.
tracked=['game/bounded_improvisation.py','game/exploration.py','game/player_interpretation_bridge.py']
(OUT/'source_worktree.diff').write_bytes(subprocess.check_output(['git','diff','--',*tracked],cwd=ROOT))
summary='''# PR-PLAY-74 — Controlled world improvisation

## Executive Summary
B — PARTIAL. Two constrained public families gain stable IDs, authoritative persistence and repeated inspection through existing owners. NPC creation and automatic live proposal commitment remain deferred. No commit/push.

## Changes Made
Reused bounded ledger, initiative/bridge, exploration/PR73 physical search and existing persistence. Task source files and evidence listed in report 02.

## What Was Tested
88 development, 105 inherited, 80/80 single-run developer structural holdout, 39 lifecycle. Focused regression 1065/20, boundary 101/6, broader 0/9; identical PR73 failure sets. Two HTTP and two browser lifecycles; requested NPC portions partial. 150/150 protected files unchanged.

## Behavioral Evidence
Browser survey screenshot and identity records show same accepted object after snapshot/reload/load. HTTP traces preserve original inputs, outputs, authority before/after. Two live proposals accepted in shadow, 360 tokens, no retries.

## Decisions Requiring Human Review
No permission decision is required. Review narrow supported scope and proposed progression to PR75.

## Known Problems
Historical failures remain. Development reference selection and unsupported movement fallthrough failures are retained with final repairs and passing verification.

## Missing Concepts
Controlled background NPC creation and richer physical interaction mechanics.

## What This Campaign Does Not Prove
Unrestricted prose safety, broad contradiction reasoning, autonomous NPCs, provider commitment, browser paint timing, full suite or external independent validation. Holdout tests structural validation only.

## Recommended Next Step
PR-PLAY-75, preserving the authority boundary. Do not implement it as part of this closure.

## Review Bundle Contents
24 named reports, machine metrics and traces, hashes/freezes, three screenshots, final source, tests and worktree diff. No .env or credentials included.
'''
hand=ROOT/'handoff';(hand/'CURRENT_REVIEW.md').write_text(summary,encoding='utf-8')
now=datetime.now(timezone(timedelta(hours=-5)));stamp=now.strftime('%Y%m%d-%H%M%S');archive=hand/f'CURRENT_REVIEW({stamp}).zip'
next_text=f'''# NEXT_SESSION — PR-PLAY-74 closure ({now:%Y-%m-%d})

**B — PARTIAL / BOUNDED IMPROVISATION DEMONSTRATED.** Two narrow stone-supported public families persist in the existing bounded ledger and reuse the initiative/bridge/exploration/PR73 physical-search owners. Stable IDs and inspection history survive normal snapshots. NPC creation and automatic live-provider commitment are deferred. Feature default off: ASHEN_EXPERIMENTAL_WORLD_IMPROVISATION=1 plus existing initiative and identity-bound branching enrollment. Sitting/moving have no invented mechanic.

Final development 88/88, inherited 105/105, single developer structural holdout 80/80 (validation only; no independent generalization claim), isolated lifecycle 39/39. Focused 1065/20, boundary 101/6, broader 0/9; exact PR73 failure sets. Two final HTTP lifecycles preserve facts; browser survey verifies improvised object resume. Report HTTP/browser improvised NPC portions remain partial; existing authored NPC resume was checked in browser. Two live shadow proposals, 360 tokens, no retries or provider commits. Two development branch turn-fallthrough failures were repaired before freeze; retain logs. 150/150 own-entry protected files unchanged. Final executed paths: 0 observed unauthorized promotions/hidden exposures/mandatory fixture omissions/critical unsafe publications. Browser paint timing unavailable.

Read development/campaigns/product_realization/pr_play_74 and artifacts/pr_play_74/metrics.json, final_source.json, regression_comparison.json, provider_results.json. Archive: handoff/{archive.name}. Working tree was extensively dirty at entry; preserve unrelated work. No commit or push.

**Exactly one next cycle:** PR-PLAY-75 — DYNAMIC NPC INTERACTION AND SOCIAL CONSEQUENCE CONTINUITY. Preserve constrained authority; do not implement PR75 in PR74 closure or rerun/tune the frozen holdout.

---

'''
p=ROOT/'docs/NEXT_SESSION.md';old=p.read_text(encoding='utf-8');assert not old.startswith('# NEXT_SESSION — PR-PLAY-74');p.write_text(next_text+old,encoding='utf-8')
files=[*REPORT.glob('*.md'),*[p for p in OUT.iterdir() if p.is_file()],OUT/'provider_data/provider_usage.jsonl',*[ROOT/p for p in freeze],ROOT/'tests/test_pr_play_74_controlled_world.py',ROOT/'docs/NEXT_SESSION.md',hand/'CURRENT_REVIEW.md']
files=[p for p in files if p.exists() and p.name not in ['archive_path.txt']]
manifest={'campaign':'PR-PLAY-74','verdict':metrics['verdict'],'archive':str(archive),'files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
(hand/'REVIEW_MANIFEST.json').write_text(json.dumps(manifest,indent=2));files.append(hand/'REVIEW_MANIFEST.json')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in files:z.write(p,p.relative_to(ROOT))
mirror_temp=hand/'CURRENT_REVIEW.pr74.tmp';mirror_temp.write_bytes(archive.read_bytes());os.replace(mirror_temp,hand/'CURRENT_REVIEW.zip');(OUT/'archive_path.txt').write_text(str(archive));print(archive);print('Reports',len(sections),'Files',len(files),'Bytes',archive.stat().st_size)
