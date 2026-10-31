"""Derive review reports and package CURRENT_REVIEW using the established builder."""
import difflib, hashlib, json, shutil, statistics, subprocess, sys, xml.etree.ElementTree as ET
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];sys.path.insert(0,str(R))
def read(name):return json.loads((H/name).read_text(encoding='utf-8'))
def write(name,value):(H/name).write_text(json.dumps(value,indent=2,default=str),encoding='utf-8')
def report(number,title,body):
    path=H/f'{number:02}_{title.upper().replace(" ","_").replace("-","_")}.md'
    path.write_text(f'# {number:02} — {title}\n\n{body.strip()}\n',encoding='utf-8');return path
def junit(name):
    root=ET.parse(H/name); rows={}
    for c in root.iter('testcase'):
        rows[c.attrib['classname']+'::'+c.attrib['name']]='failed' if c.find('failure') is not None else 'error' if c.find('error') is not None else 'skipped' if c.find('skipped') is not None else 'passed'
    return rows
baseline=junit('baseline_local_junit.xml');final=junit('final_junit.xml')
renamed={'tests.test_pr_ed_provider_efficiency::test_dialogue_still_uses_the_provider':'tests.test_pr_ed_provider_efficiency::test_authorized_dialogue_skips_provider_restatement'}
base_fail=[k for k,v in baseline.items() if v=='failed'];post_fail=[k for k,v in final.items() if v=='failed']
new_fail=[k for k in post_fail if k not in base_fail]
resolved=[k for k in base_fail if final.get(k)=='passed']
lost_passes=[k for k,v in baseline.items() if v=='passed' and final.get(renamed.get(k,k))!='passed']
comparison=dict(baseline_counts={s:list(baseline.values()).count(s) for s in set(baseline.values())},post_counts={s:list(final.values()).count(s) for s in set(final.values())},baseline_failures=base_fail,post_failures=post_fail,new_failures=new_fail,resolved_failures=resolved,lost_baseline_passes=lost_passes,renamed=renamed,qualification='six existing tests intentionally updated for host selection; initial unmodified expectation failures retained in post_junit.xml')
write('regression_comparison.json',comparison)
live=read('live_qualification.json');all_rows=[row for rows in live.values() for row in rows]
metrics={}
for name,rows in [*live.items(),('combined',all_rows)]:
    totals={field:sum(row['calls'][field] for row in rows) for field in ['provider_calls','interpretation_calls','narration_calls','retry_calls','input_tokens','output_tokens']}
    metrics[name]=dict(turns=len(rows),**totals,avg_input_tokens=totals['input_tokens']/len(rows),avg_output_tokens=totals['output_tokens']/len(rows),calls_per_turn=totals['provider_calls']/len(rows),avg_latency_ms=statistics.mean(r['elapsed_ms'] for r in rows),max_latency_ms=max(r['elapsed_ms'] for r in rows),p50_latency_ms=statistics.median(r['elapsed_ms'] for r in rows),raw_failure_flags=sum(len(r['failures']) for r in rows),failed_turns=[r['turn'] for r in rows if r['failures']])
write('performance.json',metrics)
audit=[]
for conversation,rows in live.items():
    for row in rows:
        if row['failures']:
            audit.append(dict(conversation=conversation,turn=row['turn'],flags=row['failures'],adjudication='Content failure retained. delivered_history_mismatch compares the bounded retained NPC history with a GM recall; the history limit can evict the new GM row. This is not evidence of persisting a rejected NPC candidate.' if 'delivered_history_mismatch' in row['failures'] else 'Content failure retained.',source=row['adoption'].get('authorization_source')))
write('live_failure_audit.json',audit)
state=[]
for conversation,rows in live.items():
    for row in rows:
        classifications=[]
        for change in row['world_diff']:
            path=change['path']
            kind='authorized_passive_world_tick' if path.startswith(('/factions','/event_log')) or (path.startswith('/world_state/flags/faction_') and path.endswith('_agenda_advanced')) else 'requires_review'
            classifications.append(dict(**change,classification=kind))
        state.append(dict(conversation=conversation,turn=row['turn'],world_changes=classifications,commitment_diff=row['commitment_diff'],save_load=row['save_load']))
write('state_audit.json',state)
before=read('before_hashes.json')
changed=[p for p,h in before.items() if not (R/p).exists() or hashlib.sha256((R/p).read_bytes()).hexdigest()!=h]
new_sources=['tests/test_pr_eg_r2c_speech_adoption.py','tools/validate_pr_eg_r2c.py']
source_list=changed+new_sources
source_hashes={}
for path in source_list:
    dst=H/'sources'/path;dst.parent.mkdir(exist_ok=True,parents=True);shutil.copyfile(R/path,dst)
    source_hashes[path]=dict(before_sha256=before.get(path),after_sha256=hashlib.sha256((R/path).read_bytes()).hexdigest())
for path in ['game/api.py','game/dialogue_authority.py','game/immutable_valid_response.py','game/conversational_continuity.py']:
    original=(H/'before_sources'/Path(path).name).read_text(encoding='utf-8').splitlines(keepends=True)
    current=(R/path).read_text(encoding='utf-8').splitlines(keepends=True)
    dest=H/'diffs'/(Path(path).name+'.diff');dest.parent.mkdir(exist_ok=True)
    dest.write_text(''.join(difflib.unified_diff(original,current,fromfile='baseline/'+path,tofile='final/'+path)),encoding='utf-8')
write('source_changes.json',dict(changed_existing=changed,new_sources=new_sources,hashes=source_hashes,active_data_changed=[p for p in changed if p.startswith('data/')]))
summary='''**C — CONTAINMENT INCOMPLETE.** A narrow host-owned adoption boundary is implemented using the existing accepted_response object, resolver-selected topics and conversational continuity. The historical unsupported north-gate claim no longer reaches delivery or NPC history; matched authorized security disclosure survives. Rejected/superseded draft text supplies neither speech nor proposed state effects.

The acceptance gates do not all pass. Frozen H6 fails to repeat an established archive statement. Fresh production HTTP conversations complete all 15 + 12 turns with real configured-provider interpretation, but both lose requested disclosures and earlier topics. Primary turns 3, 7, 8, 13, 14 and secondary turns 1, 2, 6, 7, 12 have content failures. Do not describe this as usable-dialogue qualification or proceed to R3.

Regression: 393 baseline passes / 19 failures; final 421 passes / 20 failures including 28 new passes and H6. All baseline passes remain passing (one test renamed); six existing tests were deliberately updated to the new containment contract. The same 19 inherited failures remain. Six separate actual-storage persistence controls pass.

Evidence classes: STATIC source inspection; UNIT deterministic test; CONTROLLED external-provider output injection or direct host-adoption seam; FRESH actual /api/chat with configured model and real provider interpretation; STATE storage/diff inspection; HISTORICAL retained predecessor measurement; INFERENCE limitations. No recorded replay is counted as FRESH. No active campaign data changed.'''
reports=[]
reports.append(report(1,'Executive Summary',summary))
reports.append(report(2,'Baseline and Environment',f'''Revision `{read('environment.json')['revision']}`. Existing dirty tree is recorded in working_tree_before.txt; the baseline is the entire starting worktree, not HEAD. before_hashes.json records source/data hashes. Runtime: {read('environment.json')['python']}. Client date October 17, 2026, America/New_York.

The 22-file historical regression selection was extracted from PR-EG-R1 junit and rerun: 393 passing / 19 failing. Exact identities are in regression_comparison.json and report 12. An initial sandbox TestClient run stalled; it was interrupted, then the same baseline ran successfully with local socket access. The failed sandbox attempt is not a regression result.

Observed fresh route: configured gpt-4.1-mini, returned gpt-4.1-mini-2025-04-14; production interpretation Responses path. No model substitution, recorded reply, or provider double was used in live qualification. The production routing code selected its configured model; no narration was required by these contained interactions. Usage/request identifiers and timing are in live_usage.jsonl. Credentials are excluded; active saves were not exported or sent. Disposable fictional fixtures only.'''))
reports.append(report(3,'Root Cause and Repair','''STATIC + CONTROLLED. Player communication passes conversational authorization, grounding and the social resolver. build_dialogue_authority identifies posture and prior commitments. Previously, an incidental/ordinary question could reach provider narration without any content-level grant. validate_generated_response and its lexical proposition checks could accept an unsupported causal security claim. run_preserve_if_valid then sealed the candidate as initial_generation. Passing hard validation was incorrectly sufficient for speech adoption.

Later social absence projection could replace a legitimate commitment with ignorance/refusal. A separate post-seal personal-ignorance repair could change text immediately before remembering commitments. record_delivered_exchange trusted its string argument without an accepted-response identity; storage preserved whichever string arrived.

Repair: select_host_speech derives host wording from existing resolver topics, explicitly reused delivery, bounded personal lines and knowledge posture. adopt_host_speech seals it with authorization provenance in accepted_response before narration; run_preserve_if_valid also applies the same selection for already-created candidates. Existing conflict, target and mechanical-check restrictions remain. Continuity responses use the same seal. A final restore precedes commitment/history persistence, and host records are checked against delivery. No broad new semantic validator or parallel world store is introduced.'''))
reports.append(report(4,'Source Change Inventory','''Cycle-relative changes, not the repository's much larger HEAD diff:

| File | Functions and rationale |
| --- | --- |
| game/dialogue_authority.py | select_host_speech: source-based selection with target/conflict/check guards |
| game/immutable_valid_response.py | adopt_host_speech, seal_host_speech, run_preserve_if_valid: use existing immutable object and exclude discarded draft effects |
| game/api.py | narration selection, nonmutating conversational response, completion persistence: seal host text and restore before retention; remove late independent replacement |
| game/conversational_continuity.py | existing personal-question grammar accepts optional personal modifier; record_delivered_exchange validates optional adoption identity, retains complete delivered text and source reference |
| tests/test_pr_ed_provider_efficiency.py | restatement now expects zero narration calls and authorized host seal |
| tests/test_pr_eg_dialogue_quality.py | no extraction of an unverified supposedly harmless provider fragment |
| tests/test_turn_pipeline_shared.py | four expectations updated for host selection instead of provider/repair execution |
| tests/test_pr_eg_r2c_speech_adoption.py | 29 targeted/adversarial/holdout cases |
| tools/validate_pr_eg_r2c.py | bounded 27-turn production HTTP live qualification |

The four production baseline snapshots, cycle-only unified diffs, final source snapshots, before/after hashes and all generated evidence are included. No canonical data file changed. The delivered history still has eight records; the individual delivered text is no longer truncated at 500 characters, so it agrees with adoption. Commitment count and text bounds are unchanged. This trades a bounded per-record text cap for exact delivery retention within the existing eight-entry window.'''))
reports.append(report(5,'Speech Adoption Authority','''AUTHORIZATION_HOST_SPEECH is represented by accepted_response.speech_adoption = AUTHORIZED_HOST_SPEECH, with authorization_source, speaker_id, text, canonical=false, and the existing immutable fields. Generated text that differs is marked UNAUTHORIZED_GENERATED_CANDIDATE and discarded. Exact host wording can be selected regardless of a matching candidate. No broad AUTHORIZED_GENERATED_EXPRESSION category is enabled. A return of None means this nonmechanical ask lane is inapplicable, not a grant to invent information.

Selection: explicit delivered-repeat/clarification binding first; then resolver-selected topic; then existing authority player_line (commitment or uncertainty/refusal); then the existing bounded personal line; then knowledge-appropriate inability. Explicit reuse precedes a topic because the resolver can select an unrelated topic during clarification. That differs from the suggested topic-first priority, and live evidence exposes unresolved mismatches between topic discovery and speech selection.

Resolved speaker identity is required. Pending checks, non-ask operations, explicit authority conflicts, ambiguous contracts, mismatched interlocutors and executable primary obligations do not take this bypass. Existing mechanical authority remains responsible. Host text supplies no new world grant, generated paraphrase or inferred information. Continuity decisions retain their existing host authorization and are sealed through the same final-response constructor.'''))
reports.append(report(6,'Information-Integrity Tests','''CONTROLLED baseline security claim was delivered verbatim after two narration calls and entered retained context. Post repair: “I prefer the evening.”; zero narration calls; host source reference; unsupported guard claim absent from commitments/history. Authorized control: existing resolver text about guards watching all night is delivered with the existing hearsay frame and zero narration calls. The source remains social.topic_revealed:north_gate.

Eleven adversarial outputs include mixed preferences, schedules, guard weaknesses, secret stairways, rewards, conditional obligations, faction ties, hidden passwords, rumors and causal explanations. All are discarded at adoption; the safe existing host sentence is delivered. Five direct authorized topic controls pass, including schedules, security, ownership and partial knowledge. Content, accepted source, effects removal, history and continuity are asserted, not just surface wording. Complete handler payloads are baseline_reproduction.json and post_reproduction.json; deterministic results are final_junit.xml.

The live disclosure control fails in multi-topic context. This is recorded as a qualification failure, despite the passing matched controlled case. No keyword blacklist is used to decide adoption.'''))
reports.append(report(7,'Conversational Relevance','''Controlled preference follow-up initially became “I don't know”; final host speech retains “I prefer the evening.”. Existing supplied clarifications and known repeats reuse their established statements; actual-storage clarification repeated twice remains the north-road statement. Unknown facts receive inability, hidden requests withheld wording, and existing negotiation decisions make no reward promise.

FROZEN H6: “Can you repeat that in simpler words?” receives inability instead of the archive statement. No expectation or implementation was retuned against H6. LIVE primary 3 “Can you repeat that?” similarly fails. Both conversations lose their road topic and fail security disclosure/recall. Preference follow-ups, explicit reward declines and unknown maker questions work in this sample; exact repeated preference wording is rigid. Relevant answer correctness therefore remains inadequate. Generic ignorance counts as failure when an answer was available; zero provider calls is not a quality success.'''))
reports.append(report(8,'Final-Response Integrity','''The existing accepted_response is the final speech object. It carries exact text, host provenance/source and speaker. Narration selection creates it before an unnecessary provider call. Direct run_preserve_if_valid calls use the same boundary, so superseded drafts do not become immutable final speech. Draft-proposed scene/world effects and improvisation proposals are removed; resolver-owned state mutation has already run and is retained.

restore_accepted_text preserves the accepted host line when downstream processing tries to replace it. The former late personal replacement is removed. Delivered-history insertion receives the accepted host object and rejects a mismatched text or speaker. UNIT mutation test explicitly changes accepted text to an unrelated action refusal, verifies persistence rejection, then restores the seal. Production handler test compares player text, seal and saved history.

This cycle binds host-owned conversational speech only. Applying the check to all old non-social accepted responses initially broke three mechanical presentation tests; that overbroad scope was removed. Existing non-social finalization can still replace an old acceptance with resolver-owned presentation. Those paths are not claimed repaired. Exact initial failure output is preserved in post_final_junit.xml.'''))
reports.append(report(9,'Persistence Integrity','''Six CONTROLLED adoption + actual storage cases pass: factual answer, bounded preference, authorized security disclosure, rejected security candidate, superseded candidate, and clarification followed by two resolutions. persistence_results.json contains exact candidates, seals and reloaded contexts. No rejected candidate is retained; canonical world files remain equal in these isolated seam trials. The HTTP-style handler test independently exercises real save/load and host-history equality. Speaker and source identity persist.

FRESH conversations explicitly save/load after turns 4, 8 and final turn; all conversational contexts remain equal. Unknown-answer commitments can be retained and cause later bad recall; this is a relevance failure, not evidence of unsupported security text being accepted. The eight-record window can discard a new GM recall when all existing rows are NPC rows; raw live scorer flags at primary14/secondary12 are retained and separately explained in live_failure_audit.json. Full per-turn canonical session snapshots were not exported; the live artifact captures world diffs, delivered-history snapshots, commitment diffs, result/trace and explicit save/load comparisons.'''))
reports.append(report(10,'Adversarial Qualification','''CONTROLLED outputs are listed verbatim in tests/test_pr_eg_r2c_speech_adoption.py (ADVERSARIAL). Eleven cases all select existing host preference instead of adopting the candidate. Unsupported patrol schedule, guard weakness, location, unconditional/conditional reward, faction relationship, obligation, password, mixed sentence, rumor and causal claim are covered. Matching topic controls independently demonstrate that authorized consequential subjects are allowed.

No fresh narration output was sampled in the contained lane because production now bypasses it. These injections exercise candidate adoption, not provider competence. The historical exact handler injection and authorized control are separately reproduced through api.chat. Frozen H1–H5 pass; H6 fails relevance. Qualification is therefore not a general conversational success.'''))
reports.append(report(11,'Frozen Holdouts',f'''frozen_holdouts.json and freeze.json were created by setup_baseline.py before production edits. SHA-256 `{read('freeze.json')['sha256']}`. Six independent inputs vary wording, speakers (Iona/Orr/Vel/Sela/Tam), subjects (archives/ferry/vault/mill/reward), epistemic posture and repeat references. Expectations were never rewritten. H1–H5 pass; H6 fails. Original first run: holdout_first_junit.xml / holdout_first_console.txt; final run: final_junit.xml. No tuning against the failing held-out expression was performed.

Separate live_plan.json was frozen before fresh execution; SHA-256 `{read('live_freeze.json')['sha256']}`. It remains byte-identical. All failures and raw scorer flags are retained. Direct frozen holdouts use JSON roundtrip; the separate six-case matrix and both live conversations use actual storage. These evidence levels are distinguished.'''))
reports.append(report(12,'Regression Comparison',f'''Baseline: 393 passing / 19 failing across the 22 historical family files. Final: 421 passing / 20 failing across that family plus 29 new tests. Existing-family post result is 393 passing / the same 19 failing. No baseline passing identity is lost after the documented single rename. No historical failing identity is resolved.

New failure: {', '.join(new_fail)}. It is a new frozen relevance qualification case. Six existing assertions were intentionally updated to reflect host selection; the initial unmodified run (385 pass / 27 fail) is preserved. Two of its failures exposed an actual authority-conflict bug and were fixed before the final run. Three later scope errors from non-social history enforcement were removed; their evidence is retained. No new critical regression in the existing family remains unexplained.

Inherited failing identities:\n\n'''+ '\n'.join('- `'+k+'`' for k in base_fail)+'''

Exact machine comparison: regression_comparison.json. Entire repository suite was not run; the required relevant historical family and all added tests were run. No unrelated inherited repair was attempted.'''))
for n,label,title in [(13,'primary','Fresh-Provider Primary Conversation'),(14,'secondary','Fresh-Provider Secondary Conversation')]:
    rows=live[label]
    transcript='\n\n'.join(f'### Turn {r["turn"]}\n\nPLAYER: {r["player"]}\n\nDELIVERED: {r["text"]}\n\nCalls: {r["calls"]["provider_calls"]}; input/output: {r["calls"]["input_tokens"]}/{r["calls"]["output_tokens"]}; elapsed: {r["elapsed_ms"]:.1f} ms; source: `{r["adoption"].get("authorization_source", "unavailable")}`; raw flags: {r["failures"]}.' for r in rows)
    reports.append(report(n,title,f'''FRESH actual FastAPI TestClient POST /api/chat?ui_mode=player. No provider replay/doubles. {len(rows)} independent campaign turns; real provider interpretation uses configured production route. Different speaker/order/wording in the secondary fixture. Complete result payloads, state diffs, history and usage are retained in live_qualification.json. Metrics: {json.dumps(metrics[label])}. This conversation fails usable-dialogue qualification.

{transcript}'''))
reports.append(report(15,'Provider Performance',f'''FRESH measured totals and turn averages:\n\n```json\n{json.dumps(metrics,indent=2)}\n```

All sent calls are interpretation. No narration, semantic validation provider call, or retry is observed in these 27 turns. Deterministic host adoption is not a semantic-validation call. live_usage.jsonl supplies actual token usage and returned models; live_qualification.json has wall-clock turn timing and provider-call counts. High-latency outliers are the individual interpretation turns; all turn timings are retained. No unbounded loop or large prompt escalation is observed.

HISTORICAL PR-EG-R1 measured 6 calls / 56,440 input tokens for its primary15 and 4 calls / 53,374 input tokens for secondary12, including two narration calls each. R2 experiments were isolated compact-generation/validator calls, not a comparable production conversation. The present fixture adds security questions and uses a second speaker; it is not an apples-to-apples performance comparison. Lower input totals follow bypassing narration, while relevance fails. This is not an overall performance/quality improvement claim.'''))
reports.append(report(16,'State-Integrity Audit','''STATE: state_audit.json retains all world diffs and commitment changes. All live canonical world diffs are existing passive faction/event changes or faction agenda threshold flags. game/world.py creates faction_*_agenda_advanced with reason world_tick_agenda_threshold. These are authorized existing world ticks, not invented faction relationships. No new quest, reward, NPC obligation, location, patrol schedule or secret was observed in world diffs.

Resolver topic discovery/lead retention is visible in response metadata and session history. During clarification the resolver can mark night_watch discovered while host speech faithfully repeats the prior road statement. This is a real unresolved resolver/disclosure synchronization problem; it must not be called successful information delivery. Canonical world equality by itself is not proof of safe speech. Commitment and delivered-history records remain noncanonical; unknown answers can still pollute relevance/recall without becoming world truth.

Active data/ source hash comparison shows no data file changed. The isolated six-case persistence matrix has exact world equality; the handler test permits only passive faction/event changes. Full session-domain canonical diffs were not exported for every live turn, limiting the breadth of the state claim.'''))
reports.append(report(17,'Remaining Limitations','''Critical qualification limitations: multi-topic resolver answer selection and recalled-topic availability can suppress legitimate facts; repetition grammar and GM topic retrieval fail; downstream session topic discovery can disagree with repeated delivery. Frozen H6 remains failing. Both live conversations have five content-failing turns, so safe ignorance and zero narration are not accepted as success.

The validator cannot enforce arbitrary generated information; generated paraphrases are bypassed in the contained lane. Existing bounded personal wording is rigid and some choices are generic (the pre-existing helper is watch/morning/evening oriented). No template catalog was added. Legacy delivered statements/commitments remain trusted continuity; this cycle does not retrospectively certify old saves against historical unsupported speech. The eight-entry history can evict a new GM row; this is documented rather than rearchitected.

Non-social/mechanical finalization remains outside the narrow speech binding. The full repository test suite was not run. Nineteen inherited relevant-suite failures remain. Gate 8 has sufficient fresh execution evidence to fail quality; the verdict is not merely insufficient live evidence.'''))
reports.append(report(18,'Next-Cycle Recommendation','''Do not begin PR-EG-R3. Stop after PR-EG-R2C and await external review. The narrow host adoption approach contains the historical exploit but cannot qualify the current conversational product.

Review the cycle diffs and failing transcripts first. Required dependency is resolver/continuity synchronization: preserve a factual topic's availability after clarification, bind repeat and recall to the requested earlier subject, and ensure disclosure persistence corresponds to the line actually delivered. This should be separately reviewed before widening generation or introducing new semantic validation. Keep H6 and the 27-turn failed evidence unchanged as regression evidence; prepare new untouched holdouts for any future repair.'''))
gates=[('1 Information integrity','PASS for controlled historical defect'),('2 Legitimate disclosure','FAIL qualification: controlled control passes, live multi-topic delivery fails'),('3 Response relevance','FAIL: H6 and both live conversations'),('4 Final-response integrity','PASS in tested contained host lane; non-social paths excluded'),('5 Persistence integrity','PASS targeted candidate exclusion/save-load; legacy-history caveats'),('6 State integrity','PASS observed world domains; complete session audit limited'),('7 Regression','PASS explained existing-family status; new H6 failure retained'),('8 Fresh-provider qualification','FAIL quality despite complete 15+12 fresh HTTP turns'),('9 Performance','PASS bounded calls; no quality improvement claim')]
write('acceptance_gates.json',dict(verdict='C — CONTAINMENT INCOMPLETE',gates=gates))
reports.append(report(19,'Final Verdict','''**C — CONTAINMENT INCOMPLETE.**

| Gate | Result |
| --- | --- |
'''+ '\n'.join('| '+name+' | '+status+' |' for name,status in gates)+'''

Stop conditions apply: legitimate resolver information is not reliably communicated in live conversations, and repairing disclosure/continuity synchronization exceeds this bounded adoption change. Do not broaden into unrestricted generation or declare containment qualified. Implementation and complete failed evidence are ready for external review. No R3 work was begun.'''))
reports.append(report(20,'Source and Evidence Inventory','''source_changes.json: cycle-relative modified/new source hashes and active-data integrity. before_hashes.json + working_tree_before.txt + environment.json: actual starting worktree. before_sources/, diffs/, sources/: baseline/final production sources, cycle-only patches, modified/new tests and live runner.

baseline_local_junit.xml, post_junit.xml, post_final_junit.xml, final_junit.xml and console files: baseline, intermediate failures, final relevant-family and targeted/holdout evidence. holdout_first_* preserves the first frozen failure. regression_selection.json and regression_comparison.json retain identities. setup_baseline.py records the freeze. frozen_holdouts.json / freeze.json and live_plan.json / live_freeze.json retain immutable inputs.

baseline_reproduction.json / post_reproduction.json: complete controlled api.chat outputs and state/retention snapshots. baseline_historical_reproduction.json: exact historical matched security pair. reproduce.py reruns the three controls. persistence_matrix.py / persistence_results.json: six actual-storage controlled roundtrips.

live_qualification.json: complete 27-turn fresh HTTP results, history changes, commitment/world diffs, adoption decisions, timing and save/load. live_usage.jsonl / live_console.txt / live_status.json: provider accounting and failures. performance.json, state_audit.json, live_failure_audit.json and acceptance_gates.json: derived assessments. build_review.py generates all 20 reports and established CURRENT_REVIEW package. artifact_inventory.json lists hashes of packaged evidence. Disposable saves, credentials, caches and pytest temporary roots are excluded.

Reproduction commands from repository root (PowerShell; .venv/Scripts/python.exe):

```
.venv/Scripts/python.exe artifacts/pr_eg_r2c/reproduce.py post
.venv/Scripts/python.exe artifacts/pr_eg_r2c/persistence_matrix.py
$selection = Get-Content artifacts/pr_eg_r2c/regression_selection.json | ConvertFrom-Json
& .venv/Scripts/python.exe -m pytest @selection tests/test_pr_eg_r2c_speech_adoption.py
.venv/Scripts/python.exe tools/validate_pr_eg_r2c.py live
.venv/Scripts/python.exe artifacts/pr_eg_r2c/build_review.py
```

The live command spends configured-provider requests and overwrites its transcript; copy existing evidence before a future rerun. The baseline setup command must not be rerun on the modified source and represented as a pre-change baseline. No recorded replay is claimed as fresh evidence.'''))
for old in ['artifacts/pr_eg_r1/11_PROVIDER_EFFICIENCY.md','artifacts/pr_eg_r2/01_EXECUTIVE_SUMMARY.md']:
    dst=H/'historical'/Path(old).name;dst.parent.mkdir(exist_ok=True);shutil.copyfile(R/old,dst)
excluded={'disposable_state','baseline_tmp','baseline_local_tmp','post_tmp','post_final_tmp','final_tmp','target_tmp','__pycache__'}
excluded_names={'handoff_config.json','artifact_inventory.json','bundle_verification.json'}
files=[p for p in H.rglob('*') if p.is_file() and not excluded.intersection(p.relative_to(H).parts) and p.name not in excluded_names]
inventory={p.relative_to(R).as_posix():dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size) for p in sorted(files)}
write('artifact_inventory.json',inventory);files.append(H/'artifact_inventory.json')
config=dict(campaign_id='pr_eg_r2c_host_owned_speech_20261017',campaign_name='PR-EG-R2C — Host-Owned Speech Adoption & Information-Integrity Containment',campaign_date='2026-10-17',purpose='Bounded implementation and qualification; stop after R2C.',objective_status='C — CONTAINMENT INCOMPLETE',executive_summary=summary,
 changes=dict(production=['Host-owned speech adopts through existing immutable response; explicit source, candidate exclusion, identity-checked retention.'],validation=['29 new tests: 28 pass, H6 fails. Six existing tests updated to containment behavior.'],tooling=['27-turn fresh production HTTP runner; controlled/persistence probes and review builder.'],documentation=['20 review artifacts and exact failure inventories.'],generated_artifacts=['Baselines, cycle-only diffs, source hashes, controlled traces, frozen holdouts, fresh HTTP transcripts and usage.']),
 testing=dict(focused='28 new passes / 1 frozen failure; six persistence controls pass.',broader='Baseline 393 pass / 19 fail; final 421 pass / 20 fail with new tests. Same 19 inherited failures; H6 new.',full_suite='Relevant historical family only; full repository suite not run.',runtime_validation='Controlled synchronous production handler plus two fresh HTTP conversations (15+12 turns).',model_runtime_boundary='Configured gpt-4.1-mini; real production interpretation; zero narration calls; no replay or live doubles.',new_regressions='No lost baseline passes after six documented expectation updates; frozen H6 fails.',pre_existing_failures='Exact 19 identities retained in report 12.'),
 known_problems=dict(campaign_specific=['Live multi-topic disclosure, repetition and recall fail; adoption alone cannot qualify usable dialogue.','Frozen H6 fails; complete original results retained.','Topic discovery can disagree with the line actually delivered.'],pre_existing=['19 relevant-suite failures.','Legacy accepted non-social response presentation is outside this bounded repair.']),
 missing_concepts=['Reliable resolver/continuity topic synchronization; legacy history certification.'],decisions_requiring_human_review=['Review incomplete R2C containment and failed qualification; do not proceed to R3.'],does_not_prove=['Qualified usable dialogue, arbitrary generated-speech safety, or an overall quality/performance improvement.','All canonical session domains audited; all repository tests passing.'],recommended_next_step='Stop after PR-EG-R2C. Await external review of resolver/continuity synchronization dependency.',primary_report=reports[0].relative_to(R).as_posix(),max_file_bytes=20*1024*1024,evidence_packets=[],supporting_files=[dict(path=p.relative_to(R).as_posix(),role='evidence',why='R2C source, cycle-relative patch, original controlled/frozen/live result or derived review.',behavioral_evidence=p.suffix in {'.json','.jsonl','.xml'},human_review_required=p.suffix=='.md') for p in sorted(files)],self_contained_review_test='20 required reports, source snapshots/diffs/hashes, exact baseline/final failures, frozen H6 failure and complete 27-turn real-provider HTTP results; no active saves or credentials.')
write('handoff_config.json',config)
from tools.build_review_handoff import build_handoff
result=build_handoff(config,root=R,output_dir=R/'handoff',archive_history=True)
write('bundle_verification.json',dict(files=result['file_count'],zip_bytes=result['zip_size_bytes'],omitted=result.get('omitted'),warning=result.get('warning')))
print(json.dumps(dict(verdict=config['objective_status'],regression=comparison['post_counts'],metrics=metrics['combined'],zip_bytes=result['zip_size_bytes'],omitted=result.get('omitted')),default=str))
