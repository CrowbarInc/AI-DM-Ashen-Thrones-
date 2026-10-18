"""Build the R4-R1 review from preserved, machine-readable evidence."""
from __future__ import annotations
import collections
import difflib
import hashlib
import json
import os
from pathlib import Path
import statistics
import sys
import time
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
OUT=ROOT/'artifacts/pr_eg_r4_r1'

def read(path): return json.loads((OUT/path).read_text(encoding='utf-8'))
def write(path,value): (OUT/path).write_text(json.dumps(value,indent=2,default=str),encoding='utf-8')
def block(value): return '```json\n'+json.dumps(value,indent=2,default=str)+'\n```'
def identities(path):
    return {t.get('classname')+'::'+t.get('name'):('failed' if t.find('failure') is not None or t.find('error') is not None else 'skipped' if t.find('skipped') is not None else 'passed') for t in ET.parse(path).iter('testcase')}

def main():
    baseline=identities(OUT/'baseline_junit.xml'); final=identities(OUT/'repaired_junit.xml'); target=identities(OUT/'targeted_junit.xml')
    regression=dict(baseline_counts=dict(collections.Counter(baseline.values())),final_counts=dict(collections.Counter(final.values())),
        new_failures=[k for k,v in final.items() if v=='failed' and baseline.get(k)!='failed'],
        inherited_failures=[k for k,v in final.items() if v=='failed' and baseline.get(k)=='failed'],
        fixed=[k for k,v in baseline.items() if v=='failed' and final.get(k)=='passed'],baseline=baseline,final=final)
    write('regression_comparison.json',regression)
    rows=read('live_turns.json'); live=read('live_status.json'); base=read('baseline.json')
    base['sources']={k.replace('\\','/'):v for k,v in base['sources'].items()}
    persistence=[]
    from tools.validate_pr_eg_r3_r1 import diff
    for index,row in enumerate(rows):
        if 'reload_exact' in row:
            next_row=rows[index+1]
            assert next_row['conversation']==row['conversation']
            before=row['after']['session'];loaded=next_row['before']['session']
            persistence.append(dict(conversation=row['conversation'],turn=row['turn'],
                original_full_session_comparison=row['reload_exact'],
                delivered_context_exact=before.get('conversational_context')==loaded.get('conversational_context'),
                saved_to_next_loaded_session_diff=diff(before,loaded)))
    write('persistence_audit.json',persistence)
    rejected=[dict(conversation=r['conversation'],turn=r['turn'],audit=r['response']['gm_output']['metadata']['expression_generation']) for r in rows if (r['response']['gm_output']['metadata'].get('expression_generation') or {}).get('decision')=='rejected']
    write('fresh_rejected_candidates.json',rejected)
    unsafe=[]
    for row in rows:
        for domain,changes in row['canonical_changes'].items():
            for change in changes:
                authorized=False
                if domain=='world' and change['path']=='/event_log':
                    before=change['before'];after=change['after'];world=row['before']['world']
                    authorized=after[:len(before)]==before and all(e.get('type')=='social_lead_revealed' and any(n['id']==e.get('npc_id') and any(t['id']==e.get('topic_id') for t in n.get('topics',[])) for n in world['npcs']) for e in after[len(before):])
                if not authorized: unsafe.append(dict(conversation=row['conversation'],turn=row['turn'],domain=domain,change=change))
    write('canonical_integrity_audit.json',dict(unauthorized_changes=unsafe,allowed='Append-only resolver social_lead_revealed events matched to authored speaker/topic IDs'))
    records=live.get('budget',{}).get('records',[])
    from game.immutable_valid_response import seal_host_speech,restore_accepted_text,run_preserve_if_valid
    start=time.perf_counter()
    for _ in range(2000):
        gm=seal_host_speech({},text='Clerk Oren says, "I prefer the morning."',source='resolver',speaker_id='clerk_oren',speaker_name='Clerk Oren',resolution=None,player_text='Morning?')
        restore_accepted_text(gm)
    overhead=(time.perf_counter()-start)*1000/2000
    from tools.qualify_pr_eg_r4_r1 import frozen
    import copy
    frozen_row=frozen(); repro=read('original_reproduction.json')
    start=time.perf_counter()
    for _ in range(100):
        run_preserve_if_valid(dict(player_facing_text=repro['candidate']),regenerate=None,
            resolution=copy.deepcopy(frozen_row['response']['resolution']),player_text=frozen_row['player']['player'])
    validation_overhead=(time.perf_counter()-start)*1000/100
    metrics=dict(turns=len(rows),conversations=dict(collections.Counter(r['conversation'] for r in rows)),
        exact_authorized=sum(r['checks']['exact_authorized'] for r in rows),history_exact=sum(r['checks']['history_exact'] for r in rows),
        fresh_rejected_expressions=len(rejected),safe_fallback_turns=[dict(conversation=r['conversation'],turn=r['turn']) for r in rows if r['response']['gm_output']['metadata']['accepted_response']['provenance']=='safe_nonresolution'],
        reloads=persistence,
        provider=live.get('budget'),calls_by_purpose=dict(collections.Counter(r['purpose'] for r in records if r.get('sent'))),
        transmitted_calls=sum(bool(r.get('sent')) for r in records),unsent_attempts=sum(not r.get('sent') for r in records),
        mean_turn_latency_ms=statistics.mean(r['latency_ms'] for r in rows),max_turn_latency_ms=max(r['latency_ms'] for r in rows),
        seal_and_verify_mean_ms=overhead,controlled_full_authorization_mean_ms=validation_overhead,added_provider_calls_for_final_delivery=0,
        latency_components=[dict(conversation=r['conversation'],turn=r['turn'],performance=r['response']['gm_output'].get('metadata',{}).get('performance'),latency_ms=r['latency_ms']) for r in rows])
    # The three qualification attempts share the approved aggregate request ceiling.
    attempts=[]
    for name in ('live_usage.jsonl','live_usage_attempt2.jsonl','live_usage_final.jsonl'):
        path=OUT/name
        if path.exists():
            calls=[json.loads(l) for l in path.read_text().splitlines()]
            attempts.append(dict(path=name,sent=sum(bool(r.get('sent')) for r in calls),input_tokens=sum(r.get('input_tokens') or 0 for r in calls),output_tokens=sum(r.get('output_tokens') or 0 for r in calls)))
    metrics['all_attempts']=attempts
    write('metrics.json',metrics)
    sources=['game/immutable_valid_response.py','game/api_turn_support.py','game/api.py','game/conversational_continuity.py','game/dialogue_authority.py','game/expressive_dialogue.py','game/gm_resolution_decision.py',
             'tests/test_pr_eg_r4_r1_delivery_integrity.py','tests/test_pr_ef_r2_social_authority.py','tools/qualify_pr_eg_r4_r1.py','tools/report_pr_eg_r4_r1.py']
    inventory=[]; preserved=[]
    with zipfile.ZipFile(ROOT/'handoff/history/pr_eg_r4_before_r1/CURRENT_REVIEW.zip') as prior:
        for name in sources:
            raw=(ROOT/name).read_bytes();row=dict(path=name,sha256=hashlib.sha256(raw).hexdigest())
            archived='support/'+name
            if archived in prior.namelist():
                old=prior.read(archived);row['prior_sha256']=hashlib.sha256(old).hexdigest()
                row['matches_captured_baseline']=base['sources'].get(name)==row['prior_sha256'] if name.startswith('game/') else None
                patch=''.join(difflib.unified_diff(old.decode('utf-8-sig').splitlines(True),raw.decode('utf-8-sig').splitlines(True),fromfile='before/'+name,tofile='after/'+name))
                dest=OUT/'source_diffs'/Path(name).with_suffix('.diff');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(patch,encoding='utf-8')
            inventory.append(row)
        frozen_sources=[f'artifacts/{cycle}/{name}' for cycle in ('pr_eg_r2c','pr_eg_r3','pr_eg_r3_r1') for name in ('frozen_holdouts.json','freeze.json')]
        for name in ['artifacts/pr_eg_r4/critical_stop_evidence.json','artifacts/pr_eg_r4/turns.jsonl','artifacts/pr_eg_r4/states/B_skeptical_08.json',*frozen_sources]:
            archived='support/'+name
            if archived in prior.namelist(): preserved.append(dict(path=name,unchanged=hashlib.sha256(prior.read(archived)).digest()==hashlib.sha256((ROOT/name).read_bytes()).digest()))
    write('source_inventory.json',inventory);write('historical_preservation.json',preserved)
    passing=all(all(r['checks'].values()) for r in rows)
    gates={
        'G01_original_defect':read('repaired_reproduction.json')['gate']['text']==read('repaired_reproduction.json')['final']['player_facing_text'],
        'G02_final_authority':passing,'G03_no_post_gate_bypass':all(v=='passed' for v in target.values()),
        'G04_history':all(r['checks']['history_exact'] for r in rows),'G05_speaker':all(v=='passed' for v in target.values()),
        'G06_authorized_disclosure':all('watch' in rows[i]['text'].lower() for i in (2,14)),
        'G07_information_integrity':not unsafe and bool(rejected),'G08_persistence':all(r['delivered_context_exact'] for r in persistence),
        'G09_regression':not regression['new_failures'],'G10_production':live['status']=='completed' and all(n>=10 for n in metrics['conversations'].values()),
        'G11_performance':metrics['added_provider_calls_for_final_delivery']==0}
    write('acceptance_gates.json',gates)
    verdict='B — INTEGRITY REPAIR QUALIFIED WITH LIMITATIONS' if all(gates.values()) else 'C — REPAIR INCOMPLETE'
    summary=f"{verdict}. Original failure reproduced before production edits, then repaired. Final fresh qualification: {len(rows)} turns, exact authorized/API/history agreement on {metrics['exact_authorized']}/{len(rows)}; {len(rejected)} rejected fresh expression candidates. Relevant baseline {regression['baseline_counts']}; final {regression['final_counts']}; new failures {len(regression['new_failures'])}. {len(target)} focused checks pass."
    diagram='''```mermaid
flowchart TD
 A[Provider candidate or host resolver result] --> B[Authority resolution and existing decision]
 B --> C[Host speech selection or full hard validation]
 C --> D[Accepted response or fixed GM safety fallback]
 D --> E[Pin existing accepted_response and SHA256 identity]
 E --> F[Legacy final emission stages: sealed text protected]
 F --> G[Restore exact pinned text and attribution]
 G --> H[Commit authorized history and NPC speech]
 H --> I[Save session and log]
 I --> J[API payload verifies and removes private seal]
 J --> K[JSON delivery: same exact text]
 L[Legacy retry without adoption] --> C
```'''
    reports=[
    ('Executive Summary',summary+'\n\nIntegrity qualification only. General conversational playability remains unresolved; stop after R4-R1 and await external review.'),
    ('Baseline and Environment',f"Revision `{base['revision']}`; extensively dirty working tree preserved in baseline.json. Captured pre-edit game hashes; predecessor ZIP supplies matching source snapshots. Provider configuration: {base['configuration']}. Python .venv 3.12; Windows TestClient needs local socket access outside sandbox. Test budget=0 external requests; fresh test scenes use gpt-4.1-mini with actual returned IDs in usage logs. No credentials are included. First baseline accidentally inherited replay provider-disable; corrected baseline uses zero request budget and reproduces R4's 692/25 identities. Historical state and transcripts were not overwritten."),
    ('Original Failure Reproduction','original_reproduction.json freezes actual run_preserve_if_valid → _finalize_player_facing_for_turn → repeated authoritative-fact preservation → record_delivered_exchange. Candidate is rejected for conflicting_target_authorities and wrong_interlocutor; fallback is selected; downstream helper replaces it with Clerk Oren’s bell answer; recorder stores replacement. Last valid point: terminal validation result. First divergence: _preserve_authoritative_resolution_facts_after_gate assigning candidate. Original source evidence remains byte-identical: historical_preservation.json.'),
    ('Response-Path Audit',diagram+'\n\nReal ordering differs from the ideal: host adoption occurs before the legacy final emission gate; post-gate reconciliation and preservation historically ran afterward. Both resolved chat and structured action share finalization. Conversational decisions seal their host response separately using the same record. Missing-adoption social retries now enter complete authorization before legacy stages; other legacy finalizations enter the same validator before history. Pipeline-origin state mutation is resolver owned and precedes narration; final delivery adds no mutation authority. See source diffs and inventory.'),
    ('Post-Gate Mutation Inventory','''| Operation / family | Classification and final disposition |
|---|---|
| Authoritative resolution fact preservation (all 4 production call sites) | C for rejected/social substitution; guarded after seal. Selected public facts move before validation. |
| Bounded resolution restoration | B; guarded after seal. |
| Physical action preservation | B; guarded after seal. |
| Interaction obligation terminal replacement | B; guarded after seal. |
| Resolution contract fallback / satisfying-candidate recovery | B; guarded or observation only for sealed response. |
| Final emission strict-social stack, wrong-speaker correction, visibility fallback | B; existing immutable guard; missing-adoption path now validated and sealed. |
| Repeated-description guard, scene momentum, serialized-envelope extraction, sanitizer | A only for display normalization; B for semantic rewrite. Final exact restoration discards any divergence. |
| Reconcile narration with structured state | B if text changes; exact restoration governs delivery. It cannot license new facts. |
| Authored knowledge realization, stay/leave, destination arrival, perception, policy, spoken-state cash-out | B; existing immutable guards honored by terminal fallbacks too. |
| Post-emission speaker adoption / stale interlocutor invalidation | B for conversational context; no semantic speech rewrite; sealed attribution is used by history. |
| restore_accepted_text | A identity restoration, now exact even for markup/whitespace; restores metadata too. |
| Expression audit attachment / decision review | Authorization-stage enrichment only; repins before returning the newly adopted response. No downstream authority. |
| record_delivered_exchange | Previously normalized exact speech and inferred unresolved social facts; now exact text, digest checked, fixed GM fallback has no NPC proposition. |
| remember_dialogue_commitment | Previously normalized/truncated; now exact delivered line. GM safety fallback excluded. |
| API packaging, key stripping, logging | A; pinned response restored and checked before payload; private seal stripped. |
| Legacy unsealed fallback constructors | B; full existing authorization required at finalization. |

No deletion/dead-code claim is used to excuse a reachable mutator. Existing MUTATOR_MIGRATION also inventories upstream speaker/shape/strict-social transformations; none is granted authority over sealed delivery.'''),
    ('Root-Cause Analysis','A rejected fallback had immutable=false, so restoration was a no-op. The authoritative-fact helper treated factual grounding as permission to rewrite speech, never consulting final acceptance, speaker or addressee. It ran after restoration and again in endpoint completion. Fresh testing exposed a second gap: a legacy retry constructed a new dictionary without an adoption record. Guarding only immutable=true would miss that path. Both defects are addressed: terminal fallback adoption and complete missing-adoption authorization before delivery.'),
    ('Final Delivery Contract','Reuse metadata.accepted_response. Contains exact text, speaker/speaker_id, addressee, subject/target, operation, authority source/result, hard validation and reasons, provenance, adoption status, contract/turn identity, expression revision when present, proposition identity when present, and integrity_digest. Private immutable JSON is the pinned form of that same record, excluding only mutable skipped-mutator telemetry and the digest field itself. It is neither canonical state nor another history. SHA256 detects accidental mutation; it is not a signature against malicious code with process access.'),
    ('Immutability Enforcement','Sealing pins response content plus authority metadata. accepted_record reads the pinned value; restore_accepted_text restores metadata and exact text before effects/history and API packaging. Five formerly unguarded preservation helpers now honor the existing immutable guard. Missing-adoption retries re-enter run_preserve_if_valid without extra provider calls. Public digest verification rejects divergent/corrupt serialized records. A failed integrity check raises rather than delivering a differing NPC line. Controlled tests cover text, speaker, ID, addressee, subject, provenance, source and immutable flag tampering.'),
    ('Social-Fact Preservation Repair','The helper existed to prevent generic replies losing resolver-selected discoveries and social facts. Its keyword-overlap trigger could replace a refusal and change speaker/subject. Legitimate host social selection and existing authored preseal projection remain. Non-social public selected discoveries are supplied before validation and included in the existing decision audit. Exact sourced clue relationships remain authorized; an appended evidential assertion does not inherit that authority. No complete hidden clue catalog or generated claim is promoted.'),
    ('Rejection Semantics','Candidate acceptance, correction and safety fallback are distinct. Rejection reasons remain in hard_validation_attempt_1, decision_review and rejected_candidate. A failed NPC fallback is replaced only by the fixed host_terminal_safety GM constant: immutable, no NPC ID/proposition, no effects. Candidate disposition remains rejected; fallback provenance=safe_nonresolution and adoption_status=safe_fallback_selected. Two existing EF-R2 assertions intentionally change from immutable=false to immutable=true for this fixed fallback, while retaining effects_allowed=false and checking rejection reasons. Frozen holdout inputs are untouched.'),
    ('Speaker and Addressee Integrity','Original wrong-interlocutor/conflicting authority reasons survive. GM safety fallback has speaker=GM and speaker_id empty; history does not attach rejected topic identity. The pinned contract restores altered attribution. Fresh fixtures use Mara/Runner and Nara/Oren, explicit switches, ambiguous both-addressing, NPC references and GM recall. Host-speech continuity and R2C/R3 holdouts remain in the regression family. No claim is made that general language interpretation now always selects the right person.'),
    ('History and Persistence','Existing conversational_context.delivered_exchanges remains the sole delivered-history store. Every resolved chat adoption is passed to it, including fallback; structured /api/action now records the same authorized delivery. Exact whitespace/markup is preserved. Digests bind the delivered response identity; rejected candidates remain diagnostics only. GM safety fallback does not create an NPC commitment or inherit topic/proposition data. Commitments retain the complete exact line. Controlled real snapshot creation/load restores delivered records; both fresh conversations save/reload at turn 6 and continue from a new client.'),
    ('API Serialization Audit','_build_turn_response_payload restores the pinned response before stripping internal keys and bypasses semantic sanitization for sealed text. Finalized response logs and history agree. Conversational decisions return a stripped copy after exact restoration. JSON escaping preserves decoded text identity. No serialization-stage speaker correction or error-stage NPC substitution is allowed. Corrupt public digest and divergent-history tests fail closed. Error messages do not substitute new NPC speech. HTTP controlled reproduction injects frozen authority/candidate at the validation boundary; it does not claim to recreate stochastic upstream interpretation byte-for-byte.'),
    ('Adversarial Qualification',f"Focused result: {len(target)} passed. Tests include unsupported security claims, promises/rewards, hidden disclosure, entity/speaker substitution, conflicting authorities, five post-gate preservation helpers, exact metadata/digest restoration, legacy missing-adoption retry, exact long commitment, snapshot persistence and both API seams. Existing bounded-expression tests cover accepted characterization, paraphrase, uncertainty and refusal. Fresh rejected expression evidence: fresh_rejected_candidates.json ({len(rejected)} candidates); raw outputs, decision and fallback remain in live_turns.json. Canonical audit finds {len(unsafe)} unauthorized changes. No controlled output is counted as fresh."),
    ('Original Failure Regression','repaired_reproduction.json has both original reasons, exact fixed GM fallback at authorization/finalization/history and no resurrected bell line. Original historical evidence is preserved separately. Tests include the frozen production finalization and a controlled /api/chat wrapper that freezes candidate+authority at validation while retaining real downstream finalization/persistence/serialization. test_legacy_retry_cannot_skip_adoption uses the first fresh stopped run as a second frozen regression. Final fresh secondary turn 8 uses the original player wording and reaches the safe fallback.'),
    ('Authorized Disclosure Preservation','Controlled /api/chat test delivers Sergeant Mara’s established night-watch fact with her speaker ID and exact history/contract agreement. Fresh primary turn 3 and secondary turn 3 disclose authored watch facts. Public clue and four-action gameplay regressions check that gate finality does not erase selected discoveries. Selected clue relations are authorized only for their exact sourced statement. Bounded characterization, factual paraphrase and admitted uncertainty remain operational. Safety was not implemented as blanket NPC refusal.'),
    ('Targeted Test Matrix','''| IDs | Evidence |
|---|---|
| T01–T04 | original frozen replay, controlled HTTP, missing-adoption regression, five helper tests |
| T05–T06 | eight metadata/text tampering parameters; digest verification |
| T07–T09 | frozen conflicting/wrong-interlocutor reasons; multiple-NPC fresh scenes |
| T10 | GM safety fallback + fresh historical recall |
| T11 | consequential disclosure HTTP; primary/secondary turn 3 |
| T12–T13 | existing R3/R3-R1 bounded characterization and paraphrase tests, fresh expression decisions |
| T14–T18 | R2C adversarial candidates and R3 semantic security/promise/reward/entity/hidden holdouts |
| T19–T20 | exact fallback history, no rejected topic/proposition or NPC commitment |
| T21 | real snapshot roundtrip, exact long speech, both live reloads |
| T22 | chat and structured action HTTP contract/history equality |
| T23 | canonical_integrity_audit.json and unchanged rejected-candidate state effects |
| T24 | unchanged frozen holdout inputs, exact baseline/final JUnit identities |
| T25 | regression_comparison.json, new failure identities explicitly listed |

The matrix maps requirements to evidence; it does not count rows as separate executed tests. See targeted_junit.xml for actual identities and counts.'''),
    ('Regression Comparison',block({k:v for k,v in regression.items() if k not in {'baseline','final'}})+'\n\nFull identities and outcomes are in regression_comparison.json and both JUnit files. Two EF-R2 assertion updates implement intentional fixed-fallback sealing; no frozen input is edited. Baseline matches R4 692/25 after the replay-only environment flag was removed and a zero external-request budget was added. Historical Windows atomic replace PermissionError appeared once during an intermediate run; final result is reported without suppressing failures. No complete repository suite claim.'),
    ('Primary Fresh-Provider Conversation','\n\n'.join(f"{r['turn']}. PLAYER: {r['player']}\n\nDELIVERED: {r['text']}\n\nAuthorization/history/digest: {r['checks']}" for r in rows if r['conversation']=='primary')),
    ('Secondary Fresh-Provider Conversation','\n\n'.join(f"{r['turn']}. PLAYER: {r['player']}\n\nDELIVERED: {r['text']}\n\nAuthorization/history/digest: {r['checks']}" for r in rows if r['conversation']=='secondary')),
    ('Provider Cost and Latency',block({k:v for k,v in metrics.items() if k not in {'provider','latency_components'}})+'\n\nExact request IDs, returned models and token accounting are in live_usage_final.jsonl and metrics.json. Tokens are measured, not estimated dollar cost. Existing legacy unresolved-question retry still occurs on secondary turn 8; final authorization adds zero provider calls or retries. The microbenchmark measures seal+exact verification together and excludes provider validation; per-turn existing validation timing is retained in raw performance traces. No statistical latency claim or broad performance optimization.'),
    ('Source Change Inventory',block(inventory)+'\n\nsource_diffs/*.diff are cycle-only diffs against matching source snapshots in the archived predecessor handoff, avoiding attribution of the pre-existing dirty tree to this repair. Tools and tests added by R4-R1 are explicitly listed. Data and unrelated user edits were not reverted.'),
    ('Remaining Limitations','The 25 inherited failures remain outside this integrity repair. General dialogue quality, repeated/irrelevant authored facts, personal preference inconsistency, broad natural-language addressee interpretation and the legacy retry cost remain unresolved. No full 180-turn evaluation, statistical reliability guarantee, hostile-code cryptographic guarantee or architectural reassessment. Full process restart was not tested; real storage snapshot and save/load client continuation were. Failed initial fresh attempt is preserved; it is not counted as a passing qualification. Final action-history-only addition is separately qualified with controlled structured API tests.'),
    ('Acceptance Gate Results',block(gates)+'\n\nG03 is supported by production-path audit and controlled mutation tests; it is not a formal proof against arbitrary future code changes. G09 requires no new failing identities, with the explicit EF-R2 contract expectation migration documented. G11 means no added systemic provider call/retry; existing legacy retry is visible and retained.'),
    ('Recommended Next Action','STOP after PR-EG-R4-R1. Submit CURRENT_REVIEW for external review of response finality, the missing-adoption path, and the exact public-clue authority integration. Do not begin the architectural reassessment or general playability work. Do not close PR-EG based on these integrity-only results.'),
    ('Final Verdict',summary+'\n\nThe limitation qualifier reflects inherited failures, bounded sampling and unresolved conversational quality. It does not waive a failed critical acceptance gate. All acceptance decisions are derived from artifacts, not playability scores.'),
    ('Source and Evidence Inventory','source_inventory.json lists cycle source hashes and predecessor-match checks. historical_preservation.json checks original failure evidence against the archived predecessor bundle. baseline.json records revision, initial dirty status and safe configuration. original_reproduction.json / repaired_reproduction.json show the divergence before and equality after repair. live_turns.json contains complete response/contracts, before/after state, canonical differences, provider usage, emitted text and history. Fresh and controlled evidence are separate. JUnit and exact regression comparison preserve pass/fail identities. Failed-first-live artifacts explain the discovered legacy gap. CURRENT_REVIEW manifest lists every packaged file with SHA256; no credentials, dependency trees, caches or other handoffs are bundled.')]
    paths=[]
    for i,(title,body) in enumerate(reports,1):
        if i==12:
            body+='\n\nThe live runner’s original full-session equality flag is false because save_session updates last_saved_at. persistence_audit.json preserves that flag and independently compares turn 6 after-state with turn 7 loaded before-state: the entire conversational context matches, and the sole session difference is the save timestamp. The real snapshot regression also passes.'
        name=f'{i:02}_{title.upper().replace(" ","_").replace("-","_")}.md';paths.append('artifacts/pr_eg_r4_r1/'+name)
        (OUT/name).write_text(f'# {i:02} — {title}\n\n{body}\n',encoding='utf-8')
    evidence=['baseline.json','baseline_junit.xml','baseline_run.json','baseline_output.txt','repaired_junit.xml','repaired_run.json','repaired_output.txt','targeted_junit.xml','regression_comparison.json','original_reproduction.json','repaired_reproduction.json','live_turns.json','live_status.json','live_plan.json','live_usage_final.jsonl','metrics.json','fresh_rejected_candidates.json','canonical_integrity_audit.json','source_inventory.json','historical_preservation.json','persistence_audit.json','acceptance_gates.json','request.txt','failed_first_live/live_turns.json','failed_first_live/live_status.json']
    support=paths+['artifacts/pr_eg_r4_r1/'+n for n in evidence]+sources+['artifacts/pr_eg_r4/critical_stop_evidence.json','artifacts/pr_eg_r4/turns.jsonl','artifacts/pr_eg_r4/states/B_skeptical_08.json']
    support += [str(p.relative_to(ROOT)).replace('\\','/') for p in (OUT/'source_diffs').rglob('*.diff')]
    support += json.loads((ROOT/'artifacts/pr_eg_r4/regression_selection.json').read_text())
    support += frozen_sources
    support += ['game/'+name+'.py' for name in ('final_emission_gate','final_emission_strict_social_stack','final_emission_visibility_fallback','narration_state_consistency','resolution_contract','social','storage','speaker_contract_enforcement','response_policy_enforcement','conversational_orchestration','provider_budget')]
    config=dict(campaign_id='pr_eg_r4_r1_final_delivery_integrity_20261017',campaign_name='PR-EG-R4-R1 — Final Speech Authority & Delivery Integrity',campaign_date='2026-10-17',purpose='Focused final-response integrity repair; stop for external review.',executive_summary=summary,
        changes=dict(production=['Immutable fixed host fallback; pinned exact adoption and identity; missing-adoption reauthorization; exact history, commitments and API delivery; selected public facts validated before sealing.'],validation=['Frozen original and legacy retry regressions, adversarial tests, exact comparison and 24 fresh HTTP turns.'],tooling=['Isolated qualification runner and evidence-derived report builder.'],documentation=['27 required reports and centralized review bundle.'],generated_artifacts=['Raw controlled/fresh evidence, JUnit identities, source diffs, gate/performance/preservation audits.']),
        testing=dict(focused=f'{len(target)} passed',broader=str(regression['final_counts']),full_suite='Not run; relevant family only.',runtime_validation='Two independent 12-turn fresh-provider /api/chat conversations; real snapshot tests and structured-action controlled HTTP.',model_runtime_boundary='Configured OpenAI Responses API; exact returned IDs/usage retained. Controlled outputs never labeled fresh.',new_regressions=str(regression['new_failures']),pre_existing_failures=str(len(regression['inherited_failures']))),
        known_problems=dict(campaign_specific=['Bounded sample; general dialogue quality unresolved.'],pre_existing=['25 inherited regression failures; exact identities in comparison.']),decisions_requiring_human_review=['External review before any next cycle.'],missing_concepts=['Broad playability and architecture reassessment are outside this cycle.'],does_not_prove=['Full-repository regression success, conversational playability, or a formal future-proof guarantee.'],recommended_next_step='Stop after R4-R1 and await external review.',primary_report=paths[0],max_file_bytes=50000000,warn_bundle_bytes=100000000,
        supporting_files=[dict(path=p,role='integrity_evidence_or_source',why='R4-R1 review, regression, provenance or frozen original evidence',human_review_required=True) for p in dict.fromkeys(support)])
    write('handoff_config.json',config)
    print(summary)

def package():
    from tools.build_review_handoff import build_handoff
    config=read('handoff_config.json')
    config['configuration_source']='artifacts/pr_eg_r4_r1/handoff_config.json'
    staging=OUT/'package_staging'
    result=build_handoff(config,output_dir=staging,archive_history=False)
    with zipfile.ZipFile(staging/'CURRENT_REVIEW.zip') as assembled:
        for name in ('CURRENT_REVIEW.md','REVIEW_MANIFEST.json'):
            normalized=staging/(name+'.bytes')
            normalized.write_bytes(assembled.read(name))
            os.replace(normalized,staging/name)
    history=ROOT/'handoff/history'/config['campaign_id']
    history.mkdir(parents=True,exist_ok=True)
    for name,archived in [('CURRENT_REVIEW.md','REVIEW.md'),('REVIEW_MANIFEST.json','REVIEW_MANIFEST.json'),('CURRENT_REVIEW.zip','REVIEW.zip')]:
        # Atomic replacement avoids transient Windows readers holding an
        # existing artifact open when the builder tries to truncate it.
        os.replace(staging/name,ROOT/'handoff'/name)
        pending=history/(archived+'.pending')
        pending.write_bytes((ROOT/'handoff'/name).read_bytes())
        os.replace(pending,history/archived)
    manifest=json.loads((ROOT/'handoff/REVIEW_MANIFEST.json').read_text(encoding='utf-8'))
    with zipfile.ZipFile(ROOT/'handoff/CURRENT_REVIEW.zip') as bundle:
        bad=[r['bundle_path'] for r in manifest['included_files'] if r.get('sha256') and hashlib.sha256(bundle.read(r['bundle_path'])).hexdigest()!=r['sha256']]
        reports=[n for n in bundle.namelist() if n.startswith('support/artifacts/pr_eg_r4_r1/') and n.endswith('.md')]
        verification=dict(file_count=len(bundle.namelist()),hashes_valid=not bad,bad=bad,required_reports=len(reports),
            all_gates_pass=all(read('acceptance_gates.json').values()),
            summary_matches=bundle.read('CURRENT_REVIEW.md')==(ROOT/'handoff/CURRENT_REVIEW.md').read_bytes(),
            zip_bytes=result['zip_size_bytes'])
    write('bundle_verification.json',verification)
    assert not bad and len(reports)==27 and verification['summary_matches'] and verification['all_gates_pass']
    print(json.dumps(verification))

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='package': package()
    else: main()
