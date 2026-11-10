import hashlib, json, shutil
from pathlib import Path
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
def save(name,value): (OUT/name).write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')
def rows(path): return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s.strip()]
identities=[
('tests.test_pr_play_61_player_facing::test_four_actions_keep_authority_and_recover','ROUTE in played[2]["gm_output"]["player_facing_text"]','ROUTE absent from repeat final engine sentence','source-bound knowledge was discarded'),
('tests.test_pr_play_66_publication::test_publication_http[no_new]',"trace['publication']['invariant'] == 'PASS'","KeyError: 'publication'",'direct engine finalizer returned before request-local verifier'),
('tests.test_pr_play_66_publication::test_publication_http[continuity]',"trace['publication']['invariant'] == 'PASS'","KeyError: 'publication'",'same finalizer early return'),
('tests.test_pr_play_66_publication::test_publication_http[fast_path]',"trace['publication']['invariant'] == 'PASS'","KeyError: 'publication'",'same finalizer early return'),
('tests.test_pr_play_47_controlled_renderer::test_matrix[5]','row == original','resolution metadata changed during selector','read-only repeat selector stamped publication metadata')]
save('regression_inventory.json',[dict(identifier=i, original_baseline='PASS: absent from PR78A failures',pr79c='FAIL: archived initial historical run',
    current_preimplementation='reproduced',assertion=a,actual_before=b,root_cause=c,final_result='PASS',
    evidence='renderer_before.xml / single.xml / repro_s.xml; final_source_development.xml') for i,a,b,c in identities])
network=rows(OUT/'browser_network.jsonl')
turns=rows(OUT/'browser_publication.jsonl')
transcript=json.loads((OUT/'browser_transcript.json').read_text(encoding='utf-8'))
repeat=next(t for t in transcript if t['input']=='I examine the notice board again.')
save('source_provenance.json',dict(original_input=repeat['input'],original_response=repeat['response'],
    disclosed_records=repeat['knowledge_before'],records_after=repeat['knowledge_after'],knowledge_unchanged=repeat['knowledge_unchanged'],
    publication_records=repeat['publication_records']))
ledger=[]
for p in OUT.glob('browser_provider_usage*.jsonl'):
    data=rows(p)
    ledger.append(dict(file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
        first_event=data[0],completed_requests=sum(r.get('event')=='completed' and r.get('sent') is True for r in data)))
prior=[]
for path in [ROOT/'artifacts/pr_play_79c/live_data/provider_usage.jsonl', ROOT/'artifacts/pr_play_79c/browser_data/provider_usage.jsonl']:
    data=rows(path)
    completed=[r for r in data if r.get('event')=='completed' and r.get('sent') is True]
    prior.append(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        requests=len(completed),total_tokens=sum(r.get('total_tokens',0) for r in completed)))
save('provider_ledger_isolation.json',dict(fresh_execution_ledgers=ledger,prior_usage_read_only=prior,
    admission_controls='unchanged exclusive ledger creation',campaign_fixture_ledger='excluded, not erased',
    production_data_hashes='protected_after.json'))
loaded=next(r for r in network if r['path']=='/api/snapshots/load')
sid=json.loads(loaded['request'])['snapshot_id']
shutil.copy2(OUT/'browser_data/snapshots'/(sid+'.json'),OUT/'browser_snapshot.json')
save('save_reload_evidence.json',dict(snapshot_id=sid,request=loaded['request'],status=loaded['status'],
    campaign_identity_before=loaded['before'].get('campaign_run_id'),campaign_identity_after=loaded['after'].get('campaign_run_id'),
    knowledge_before=loaded['before'].get('clue_knowledge'),knowledge_after=loaded['after'].get('clue_knowledge'),
    last_post_reload_input=transcript[-1]['input'],last_post_reload_response=transcript[-1]['response'],
    live_post_reload=transcript[-1]['live_dialogue_published']))
print('Saved exact regression identities, source records, ledger provenance and normal snapshot evidence.')
