"""Create all 25 required reports and the established CURRENT_REVIEW handoff."""
from pathlib import Path
import sys,json,hashlib,shutil,difflib,zipfile
H=Path(__file__).parent;R=H.parents[1];sys.path.insert(0,str(R))
def read(n):return json.loads((H/n).read_text())
def write(n,v):(H/n).write_text(json.dumps(v,indent=2,default=str),encoding='utf-8')
def block(v):return '```json\n'+json.dumps(v,indent=2,default=str)+'\n```'
def report(n,title,body):
 p=H/f'{n:02}_{title.upper().replace(" ","_").replace("-","_")}.md';p.write_text(f'# {n:02} — {title}\n\n'+body.strip()+'\n',encoding='utf-8')
c=read('regression_comparison.json');metrics=read('performance.json');m=metrics['combined'];live=read('live_qualification.json');audit=read('live_semantic_audit.json');gates=read('acceptance_gates.json');targeted=read('targeted_results.json')
verdict='B — REPAIR QUALIFIED WITH LIMITATIONS; R2C CLOSURE RECOMMENDED' if all(gates.values()) else 'C — REPAIR INCOMPLETE'
summary=f'''**{verdict}.** Engine grounding now reconciles provider unresolved-reference annotations before interpretation eligibility and at the stored-record bridge. Existing addressee grounding and authored topic selection determine eligibility; the existing social resolver retains disclosure and immutable speech adoption. Bare repetition after an unresolved clarification repeats the actual GM question and preserves pending intent.

Relevant regression: {c['baseline_counts']} before → {c['final_counts']} after; no new failure identities or lost baseline passes. All {len(targeted)} focused checks pass. All 15 unchanged R1 holdouts pass. Final independent N01–N05 pass, as do C01–C03, S01–S05 and L01–L02. The initial F07 retention expectation is preserved as failed and superseded; it is not counted as passing independent final evidence.

Final fresh production /api/chat: 16 primary + 13 secondary turns; 29/29 provenance/relevance/state audits pass. {m['provider_calls']} interpretation calls, {m['narration_calls']} narration calls, {m['retry_calls']} retries; {m['input_tokens']:,} input / {m['output_tokens']:,} output tokens; mean {m['average_latency_ms']/1000:.2f}s, maximum {m['maximum_latency_ms']/1000:.2f}s per turn.

Qualification is bounded to the recorded scenes and configured route. Unclassified unsupported annotations remain conservative; arbitrary semantic grounding and unlimited memory are not established. Stop after R2C-R2 and await external review. Do not begin R3.'''
sources={}
for p in ['game/live_chat_interpretation.py','game/player_interpretation_bridge.py','game/conversational_continuity.py','tests/test_pr_ef_r2_social_authority.py']:
 old=(H/'before_sources'/p).read_text(encoding='utf-8');new=(R/p).read_text(encoding='utf-8');d=H/'diffs'/(Path(p).name+'.diff');d.parent.mkdir(exist_ok=True)
 d.write_text(''.join(difflib.unified_diff(old.splitlines(keepends=True),new.splitlines(keepends=True),fromfile='cycle_baseline/'+p,tofile='final/'+p)),encoding='utf-8')
 sources[p]=dict(before_sha256=hashlib.sha256((H/'before_sources'/p).read_bytes()).hexdigest(),after_sha256=hashlib.sha256((R/p).read_bytes()).hexdigest())
write('source_changes.json',sources)
source_paths=list(read('qualification_source_hashes.json'))+['game/ordinary_semantic_ownership.py','game/conversational_orchestration.py','game/provider_budget.py','experiments/pr_do/adapter.py','experiments/pr_do/eligibility.py','experiments/pr_do/schema.py','tests/test_pr_ef_gm_authority.py','tests/test_pr_du_player_pipeline.py','tests/test_pr_ef_r4_authorization.py','tests/test_pr_eg_r2c_speech_adoption.py','tools/build_review_handoff.py']
for p in source_paths:
 d=H/'sources'/p;d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/p,d)
report(1,'Executive Summary',summary)
report(2,'Baseline and Environment',block(read('environment.json'))+'''

The starting tree was already substantially dirty; working_tree_before.txt records it. Cycle-relative before_sources preserves prior production changes independently of HEAD. The selected regression family was actually run before production edits: 584 pass / 25 fail. Its count matches the historical report but was independently measured. Selection: regression_selection.json.

Configured gpt-4.1-mini / returned gpt-4.1-mini-2025-04-14, verified in the final Responses interpretation journal. Local .env was loaded without being copied. Disposable campaigns and FastAPI TestClient exercised production /api/chat. Sandbox-only TestClient attempts stalled and were interrupted; verified runs used approved local socket access. One intermediate complete run hit Windows os.replace PermissionError at R4 confirm_single_candidate; later complete runs passed that identity. The failure is retained. Full repository suite was not run.''')
report(3,'Historical Failure Reproduction','''Evidence: recorded-provider output injected at the interpretation wire, real HTTP/resolvers/adoption. One controlled wire call, zero live provider calls. reproduce.py --baseline reinstalls frozen source functions including API-imported bindings; --after uses final production source. Both JSON records contain raw input/provider JSON, annotations, handler/bypass, full persisted before/after worlds/sessions and calls.

Question: "I ask Sergeant Mara whether guards watch the north gate at night." Provider proposes ASK sergeant_mara, labels communication GM/QUESTION and reports ["north gate"]. Mara owns "Guards watch the north gate throughout the night." Before: "Which person, place, or thing do you mean?", resolver_invoked=false. After: authored night-watch disclosure, social.topic_revealed:night_watch.

Earliest veto: interpret_production_turn → adapter → evaluate_eligibility selects clarification for any unresolved list before bridge grounding. The bridge repeats this veto before its addressee check. normalize_social_scope also cleared annotations by provider subject wording alone, only for NPC ownership; it missed this GM-labeled case and could accept unsupported subject claims.

An initial probe setup assigned the fact to the wrong seeded NPC. This was corrected and the frozen-source baseline/final pair rerun with Mara owning it. The original unresolved-reference veto was already reproduced before production edits; the corrected pair demonstrates the full authorization expectation. Initial setup error is not presented as knowledge qualification.''')
report(4,'Reference Authority Contract','''Existing visible_catalog, assess_addressee_grounding, delivered history and social._next_topic_to_reveal retain authority. reconcile_reference_annotations is a turn-local eligibility projection, not another reference store/entity matcher.

GROUNDED: explicit phrase supported by unique visible target, engine scene passage or grounded speaker's authored subject vocabulary. RESOLVABLE: existing addressee grounding can supply a missing ASK target, recorded in target_handoff. AMBIGUOUS: multiple visible candidates or ambiguous addressee remain. MISSING: insufficient supported referent/annotation role. NOT_APPLICABLE: an unmentioned annotation with no visible entity match cannot veto a non-deictic question uniquely supported by the existing read-only topic selector.

Provider interpretation is evidence. Player wording plus engine-owned context decides eligibility. Subject presence is separate from knowledge/disclosure. Later resolver authorization is still mandatory. Raw provider output is preserved separately from decisions; no fact or canonical effect is adopted here.''')
report(5,'Annotation Reconciliation','''Live processing first structurally validates the provider envelope, then reconciles and re-evaluates existing adapter eligibility. The stored-record bridge invokes the same function before its unresolved veto. Malformed/forbidden fields remain rejected.

Each string annotation records explicit occurrence, role, visible candidate IDs, status and authoritative source. Existing catalog matching/addressee grounding is reused; scene/visible passages and the grounded speaker's authored topics establish subject vocabulary. Role identifiers npc_to_ask/addressee/interlocutor grant nothing without independent direct-address grounding. Missing ASK targets come only from that resolver.

Unmentioned unsupported annotations become NOT_APPLICABLE only with no visible match, no deictic dependency and a uniquely supported authored question. The selector result is not delivered; social resolution still runs. Stale CLARIFICATION_REQUIRED can be neutralized for a grounded direct ASK with no remaining references/deictic subject. Existing direct-address ownership correction is applied before eligibility. Real missing/ambiguous subjects stay unresolved. Literal player subject words such as interlocutor/addressee are never treated as metadata role labels; two failed pre-guard controls and final L01–L02 frozen checks document that distinction. Arbitrary annotation prose is not semantically classified.''')
report(6,'Addressee and Subject Grounding','''A grounded Mara does not resolve "that place"; a grounded north gate does not identify "one of them". T01–T09/T15/T24, S01–S05 and adversarial C/D/J/L inspect independent grounding, normalized targets and actual bridge acceptance. T24/L propose another visible NPC while the player names Mara: engine grounding selects Mara.

Current-scene catalog scope prevents selecting a convenient distant entity. Authored topic vocabulary can establish a conversational subject without creating an inspectable/movable entity. Unknown subjects/annotations remain conservative. Existing ambiguity and missing-person behavior is preserved independently of social knowledge.''')
report(7,'Resolver Handoff','''Path: player input → provider interpretation → structural validation → reconciliation → existing eligibility → direct-address ownership → bridge visibility/kind/addressee checks → normalized ASK → existing social resolver → topic relevance/sufficiency → dialogue authority → immutable host speech adoption → final emission → delivered history.

before_reproduction.json/after_reproduction.json capture the historical handoff. grounding_trace.json records every final parsed interpretation, annotation, reconciliation, handler/addressee/subject, resolver flag and adoption source. HTTP controls inspect owned night_watch topic, canonical speaker, authorization_source and exact delivered history. Read-only topic selection may prove eligibility but never supplies the final answer directly; disclosure/knowledge checks remain in the resolver.''')
report(8,'Knowledge vs Reference','''T10 and live maker questions reach social resolution with no topic disclosure and knowledge_posture=unknown. T11 and the live password question retain knowledge_posture=withheld. Delivered wording may be similarly conservative; inspected authority posture distinguishes knowledge restrictions from reference ambiguity. The guard fact is established with social.topic_revealed:night_watch.

Ambiguous referents receive GM clarification without social disclosure. Topic presence never bypasses requested-information sufficiency or hidden-information handling. This cycle preserves the existing knowledge/disclosure model; it does not establish a new secret-access schema.''')
report(9,'Conversational Continuity','''clarification_probe.json preserves factual disclosure → ambiguous addressee → bare repeat incorrectly replaying the old fact. continuity_directive now repeats the current-scene GM clarification only when the latest delivered row exactly matches last_gm_exchange/category CLARIFY and the request has no explicit speaker/subject. Pending intent is preserved; explicit historical lookup keeps its existing selector.

Final primary 10–12 and secondary 8–10 audit ambiguity, exact clarification repetition, pending preservation and explicit resolution. Three real HTTP repeat/meaning/simpler-word controls and independently frozen C01–C03 pass. Earlier-topic and GM speaker recall, uncertainty/refusal repetition and actual save/load remain intact. History stays at the predecessor's 32-row limit; no new persistent memory was added.''')
report(10,'Information Integrity Preservation','''Immutable adoption and host-owned speech selection are unchanged. The controlled evening/unguarded-gate candidate is rejected, not delivered or recorded; authorized guard information remains deliverable with exact topic provenance. New T13/T21/T22 and all unchanged R2C owner tests inspect accepted_response, candidate disposition, world_updates and history.

Final audits verify adoption=delivery=latest history row, correct source/speaker and no new knowledge on repeat turns. Canonical state equality alone is not treated as information integrity. Provider annotations and read-only eligibility selection create no factual authority, NPC agent, generated-dialogue lane or adoption bypass.''')
report(11,'Cross Domain Safety','''MOVE/INSPECT/PERCEIVE/ASK share the bridge. For physical operations an annotation clears only for a unique explicitly named catalog target matching the operation target; later visibility/kind/destination validation still runs. T26/F10 preserve deictic movement ambiguity; T27/F09 ground explicit inspection.

Unchanged exploration, movement, stored-player-pipeline and R4 suites protect shared safety. New physical cases are deterministic reconciliation evidence; fresh conversations are social HTTP evidence, not fresh physical-operation qualification. GM/control ownership and unsupported item/object operations retain existing behavior. No unrelated resolver functionality was added.''')
report(12,'Source Change Inventory',block(sources)+'''

Production changes: bridge reconcile_reference_annotations/normalized entry; live normalize_social_scope/interpret_production_turn; continuity_directive. Existing matching, addressee resolution, ownership correction and topic selector are reused. Social resolver, dialogue authority, immutable adoption, storage and API implementations were not edited.

New focused tests plus one old normalization assertion changed: provider subject alone no longer clears distant kingdom. Old assertion is preserved under before_sources/tests. This contract correction is explicit, not a hidden inherited failure resolution. All historical R1/R2C/R4 frozen fixtures remain unchanged. Tooling supplies HTTP qualification, provenance/state/cost audits, exact failure comparison and packaging. Unified cycle-relative diffs and source snapshots separate this work from the initially dirty tree.''')
report(13,'Targeted Tests',f'''{len(targeted)} focused checks pass. T01–T28 are represented by reference matrix, actual HTTP handoff, adoption and continuity tests. Multiple rows share seams; these are not 28 independent provider conversations. Earlier-topic and speaker-specific GM recall also retain the unchanged R1 owner checks. Exact identities:

{block(targeted)}

Assertions inspect record/scene/state immutability, per-annotation decisions, target correction, resolver-owned source identity, accepted/history text, no narration/retry, actual save/load and pending clarification preservation. F07's revised compatibility assertion is explicitly not independent qualification; final N01–N05 qualify the new contract.''')
report(14,'Adversarial Annotations',block([dict(id=x['id'],passed=x['passed'],allowed=x['expected_allowed'],target=(x['normalized_action']or{}).get('target_id'),decisions=x['decisions']['annotations'])for x in read('adversarial_annotations.json')])+'''

Full controlled provider records/bridge results: adversarial_annotations.json. A/B/E ground false annotations. C/D/J retain real subject/addressee ambiguity. F/G/K neutralize unmentioned conflict/irrelevance only when the existing selector supports the raw question. H/I separate unknown/hidden answers from reference grounding. L rejects provider target preference in favor of independently grounded player wording. HTTP controls separately prove F/G handoff to the real resolver.

These are controlled interpretation probes with zero fresh provider calls. Earlier conservative F/G/K outcomes remain under qualification_before_irrelevant_annotation_fix. No fixture is labeled fresh evidence.''')
report(15,'Frozen Holdouts','''The 15 R1 holdouts were rerun unchanged and pass 15/15. Original fixtures/freezes remain untouched and are bundled. New fixtures have SHA-256 and pre-edit UTC freeze records.

Initial F01–F10 passed on the first repair. Final contract audit showed F07's original retention expectation conflicts with raw-player authority: a supported silver-causeway question should not be blocked by an unmentioned obsidian-palace annotation. original_holdout_final_attempt.json retains 9 passes and that failed original expectation. frozen_holdouts.json was not rewritten; its active compatibility assertion is explicitly changed and not counted as independent final evidence.

C01–C03 froze before clarification repair and pass 3/3. S01–S05 froze before stale-status handling and pass 5/5. After the F07 finding, new N01–N05 with different NPCs, locations, facts and annotation patterns froze before the final selector-based repair, then passed 5/5 without tuning against their results. These are the final independent annotation qualification set. L01–L02 were frozen before the final literal-role guard; the pre-guard failures remain in literal_role_before.json and both final controls pass. L01–L02 froze before the final literal-role guard; both old failures are preserved in literal_role_before.json and both final checks pass. F09/F10 and broader regression cover non-social safety. Frozen files, failed results, final source/JUnit and evaluator commands are included.''')
report(16,'Regression Comparison',block(c)+'''

baseline.xml/final.xml preserve every identity and failure traceback for the same relevant family plus new tests. No lost baseline pass or new failing baseline identity remains. All 25 inherited failures stay outside scope. The normalization contract assertion and new F07 compatibility expectation changes are explicit in reports 12/15.

qualification_before_clarification_fix/final.xml preserves the transient Windows storage failure in R4 confirm_single_candidate; subsequent complete runs passed it without production storage changes. The complete repository suite was not run.''')
for n,label,title in [(17,'primary','Primary Fresh Provider Conversation'),(18,'secondary','Secondary Fresh Provider Conversation')]:
 rows=live[label];traces=[x for x in read('grounding_trace.json')if x['conversation']==label]
 lines=[f'{len(rows)} fresh production /api/chat turns; actual configured provider, no interpretation/narration/resolver doubles. Different NPCs/order with a second available Sentry Elin. Frozen final plan: live_plan.json/live_freeze.json. Full raw HTTP results and persisted before/after worlds/sessions are in live_qualification.json; complete diffs in state_audit.json.']
 for row,t in zip(rows,traces):
  lines.extend([f"## Turn {row['turn']}",f"Player: {row['player']}",f"Delivered: {row['text']}",block(dict(interpretation=t['raw_interpretation'],annotations=t['unresolved_annotations'],reconciliation=t['reconciliation'],handler=t['selected_handler'],resolver_invoked=t['resolver_invoked'],addressee=t['selected_addressee'],subject=t['selected_subject'],adoption=row['adoption'],calls=row['calls'],world_diff=row['world_diff'],session_diff_count=len(row['session_diff']),save_load=row['save_load'],failures=row['failures']))])
 report(n,title,'\n\n'.join(lines))
report(19,'Provider Performance',block(metrics)+'''

Final per-request journals: final_literal_qualified_live_usage.jsonl / final_provider_usage.json, with configured/returned model, request IDs, sent flags, usage consistency and provider latency. HTTP latency includes local engine work. Per-turn averages include deterministic zero-call turns; outliers are measured.

The R1 reference was 14 calls/27 turns and about 1.14s mean. Final qualification adds real ambiguity and clarification repetition with two visible NPCs, so it is not a controlled performance benchmark. There is no narration or retry escalation. development_provider_cost.json reports all five developmental/qualification runs separately; failed-run cost is retained.''')
report(20,'State Integrity Audit','''live_qualification.json stores complete persisted worlds/sessions before and after every final turn. state_audit.json preserves full diffs and commitment changes; live_semantic_audit.json checks stable inventory/party/PC/location/visited locations, existing passive faction/event-log/agenda world ticks only, no new clue knowledge on repeats, accepted=delivered=history and preserved pending clarification.

Expected session changes include runtime/debug/provenance caches, normal turn clocks, initial seed normalization such as character_name, authorized topic/lead discovery and conversation records. They are recorded rather than all labeled immutable. Only the authored road/watch information is disclosed; no reward, password, invented guard gap, obligation or new NPC is authorized by reconciliation.

Adoption/history exclusion tests protect against unsafe candidates even where world state is unchanged. Actual save/load roundtrips verify continuation, not a separate process restart. Captured campaign states are disposable fictional fixtures.''')
report(21,'Remaining Limitations','''Grounding remains bounded to current scene entities, existing direct-address/conversation context, authored vocabulary and lexical topic selection. It does not invent missing referents or interpret arbitrary annotation prose. Unclassified unsupported annotations without provable grounding/inapplicability stay conservative. Known role identifiers are npc_to_ask/addressee/interlocutor; provider-authored arbitrary labels are not new authority.

Deictic subject handling is conservative. Arbitrary synonym/reasoning competence, richer hidden-knowledge access control, unlimited history, process-restart persistence and load performance are not established. Existing history remains capped at 32 rows and the 25 inherited failures remain out of scope. These boundaries do not justify unrestricted dialogue, new memory/authority systems or R3 implementation.''')
report(22,'R2C Closure Assessment',block(gates)+'\n\nExact retained failure identities and evidence classes:\n\n'+block(read('intermediate_failure_audit.json'))+'''

All eleven gates pass within the tested grounding/authority boundary. The historical fact reaches its resolver; real ambiguity, explicit resolution, clarification repetition, unknown/withheld posture, correct topic/speaker source, immutable adoption, delivered history and canonical state are evidenced. Predecessor topic/recall behavior and its frozen holdouts remain intact.

Intermediate live failures and the controlled continuity failure are retained. The later audit additionally flags status-attempt primary turn 14: its clarification merely mentioned north road, fooling the early substring checker; final audits require actual resolver-owned topic provenance. F07's old retention expectation failed the final authority contract; independently frozen N01–N05 qualified the final repair afterward. Closure is recommended with documented limitations and external review, not as proof of universal language understanding or all repository tests passing.''')
report(23,'Next Cycle Recommendation','''Recommend R2C closure after external review of final source, exact failure identities, retained failed transcripts/holdout result, independent final expectations, 29 fresh turns and state/provenance audits. The recorded limitations do not supply concrete failed final evidence requiring another repair cycle in the tested contract.

Stop after PR-EG-R2C-R2. Do not implement R3, broad prompt optimization, unrestricted NPC improvisation, another memory/authority system or unrelated inherited fixes. Await external review.''')
report(24,'Final Verdict',summary+'\n\n'+block(gates))
commands='''.venv\\Scripts\\python.exe artifacts/pr_eg_r2c_r2/reproduce.py --baseline
.venv\\Scripts\\python.exe artifacts/pr_eg_r2c_r2/reproduce.py --after
.venv\\Scripts\\python.exe -m pytest tests/test_pr_eg_r2c_r2_reference_eligibility.py --tb=short
.venv\\Scripts\\python.exe artifacts/pr_eg_r2c_r2/run_final.py
.venv\\Scripts\\python.exe artifacts/pr_eg_r2c_r2/evaluate_predecessor_holdouts.py
.venv\\Scripts\\python.exe artifacts/pr_eg_r2c_r2/adversarial.py
.venv\\Scripts\\python.exe tools/validate_pr_eg_r2c_r2.py freeze
.venv\\Scripts\\python.exe tools/validate_pr_eg_r2c_r2.py
.venv\\Scripts\\python.exe artifacts/pr_eg_r2c_r2/audit_evidence.py
.venv\\Scripts\\python.exe artifacts/pr_eg_r2c_r2/build_review.py'''
report(25,'Source and Evidence Inventory',block(read('qualification_source_hashes.json'))+'\n\nReproduction commands; fresh-provider commands consume configured usage, and local HTTP tests require socket access:\n\n```powershell\n'+commands+'\n```\n\nEvidence classes are separated: static source/diffs; deterministic unit/owner tests; controlled interpretation-wire injection; recorded-provider reproduction; unchanged frozen expectation replay; actual fresh production /api/chat; persisted state inspection; derived audit/inference. No controlled/replayed result is live evidence. Source snapshots are review conveniences, not a complete executable repository export. artifact_inventory.json hashes evidence and REVIEW_MANIFEST.json maps portable entries to canonical paths. Credentials, caches, unrelated artifacts and active campaign saves are excluded.')
prior=H/'predecessor_current_review';prior.mkdir(exist_ok=True)
for name in ['CURRENT_REVIEW.md','CURRENT_REVIEW.zip','REVIEW_MANIFEST.json']:
 if not(prior/name).exists():shutil.copyfile(R/'handoff'/name,prior/name)
files=[]
for p in H.rglob('*'):
 if not p.is_file():continue
 parts=p.relative_to(H).parts
 if any(x in parts for x in ['__pycache__','predecessor_current_review','disposable_state','reproduction_state','adversarial_state','clarification_probe_state']):continue
 if any('tmp'in x or x.endswith('_state')for x in parts):continue
 if p.suffix not in {'.json','.jsonl','.md','.txt','.py','.diff','.xml'}:continue
 if p.name in {'handoff_config.json','bundle_build_result.json','bundle_verification.json','artifact_inventory.json','build_console.txt'}:continue
 files.append(p)
for name in ['frozen_holdouts.json','freeze.json','final_holdouts.json','final_holdouts_freeze.json','qualification_holdouts.json','qualification_holdouts_freeze.json']:
 files.append(R/'artifacts/pr_eg_r2c_r1'/name)
files.extend([R/'artifacts/pr_eg_r2c/frozen_holdouts.json',R/'artifacts/pr_eg_r2c/freeze.json',R/'artifacts/run_r2c_r2_baseline.py'])
write('artifact_inventory.json',{str(p.relative_to(R)).replace('\\','/'):dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)for p in files})
files.append(H/'artifact_inventory.json')
config=dict(campaign_id='pr_eg_r2c_r2_reference_eligibility_20261017',campaign_name='PR-EG-R2C-R2 — Reference Eligibility & Resolver Handoff',campaign_date='2026-10-17',purpose='Focused repair and qualification; stop after R2C-R2 and await external review.',objective_status=verdict,executive_summary=summary,changes=dict(production=['Reference reconciliation using existing grounding/selector and unresolved clarification continuity.'],validation=['T01–T28, adversarial/status controls and frozen expectations; retain failed evidence.'],tooling=['Production HTTP runner, exact baseline/final comparison and provenance/state/cost audits.'],documentation=['All 25 requested numbered reports.'],generated_artifacts=['Provider journals, full transcripts/states, source hashes/diffs, JUnit identities and failed-attempt archives.']),testing=dict(focused=f'{len(targeted)} focused tests pass; R1 15/15; final independent N01–N05 5/5.',broader=str(c['baseline_counts'])+' → '+str(c['final_counts']),full_suite='Not run; relevant family only.',runtime_validation='16 primary + 13 secondary fresh-provider production HTTP turns; 29/29 audits pass.',model_runtime_boundary='Configured gpt-4.1-mini; actual Responses interpretation, no live doubles/replay.',new_regressions=str(c['new_failures']),pre_existing_failures='25 unchanged identities; report 16/final.xml.'),known_problems=dict(campaign_specific=['Bounded lexical/symbolic grounding; unsupported unclassified annotations remain conservative.','F07 old retention expectation is superseded and preserved as failed; new independent N01–N05 qualify final behavior.'],pre_existing=['25 inherited relevant-family failures remain outside scope.']),missing_concepts=['Arbitrary semantic entity grounding and unlimited conversation memory were not added.'],decisions_requiring_human_review=['External review of R2C-R2 repair, evidence and closure recommendation.'],does_not_prove=['All repository tests passing, arbitrary annotation understanding, unrestricted generated-speech safety, unlimited memory or process-restart persistence.'],recommended_next_step='Recommend R2C closure with documented limitations after external review. Stop after R2C-R2; do not proceed to R3.',primary_report=str((H/'01_EXECUTIVE_SUMMARY.md').relative_to(R)).replace('\\','/'),max_file_bytes=128*1024*1024,evidence_packets=[],supporting_files=[dict(path=str(p.relative_to(R)).replace('\\','/'),role='source'if p.suffix=='.py'else'evidence',why='Requested report, exact source/diff, frozen expectation, actual transcript/provider journal, state audit or retained failure.',behavioral_evidence=False,human_review_required=True)for p in files],self_contained_review_test='Verify all 25 reports, source hashes, baseline/final identities, retained failures, frozen expectations and full fresh-provider transcripts/states/usage; no credentials or active campaign saves.')
write('handoff_config.json',config)
from tools.build_review_handoff import build_handoff
result=build_handoff(config,root=R,output_dir=R/'handoff');write('bundle_build_result.json',result)
with zipfile.ZipFile(R/'handoff/CURRENT_REVIEW.zip')as z:
 names=z.namelist();verification=dict(zip_crc_error=z.testzip(),reports_25=all(any(Path(n).name==p.name for n in names)for p in H.glob('[0-9][0-9]_*.md')),manifest_present='REVIEW_MANIFEST.json'in names,summary_present='CURRENT_REVIEW.md'in names,no_env=not any(Path(n).name.startswith('.env')for n in names),entries=len(names),omitted=result.get('omitted'),zip_sha256=hashlib.sha256((R/'handoff/CURRENT_REVIEW.zip').read_bytes()).hexdigest())
write('bundle_verification.json',verification)
print(json.dumps(dict(verdict=verdict,file_count=result['file_count'],zip_bytes=result['zip_size_bytes'],verification=verification),indent=2))
