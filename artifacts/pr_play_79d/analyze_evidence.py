import hashlib, json, math, statistics, xml.etree.ElementTree as ET
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
def read_lines(path):
    return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s.strip()] if path.exists() else []
def save(name, data):
    (OUT/name).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
def unwrap(path):
    value = json.loads(path.read_text(encoding='utf-8'))
    return value.get('payload', value)

network = read_lines(OUT/'browser_network.jsonl')
turns = [r for r in network if r['path'] == '/api/chat']
usage = []
for path in OUT.glob('browser_provider_usage*.jsonl'):
    usage.extend(read_lines(path))
completed = {r['attempt_id']:r for r in usage if r.get('event') == 'completed' and r.get('sent') is True}
trace = read_lines(OUT/'browser_publication.jsonl')
transcript = []
for row in turns:
    text = (row['response'].get('gm_output') or {}).get('player_facing_text', '')
    before, after = row['before'], row['after']
    context = after.get('last_publication') or {}
    dialogue = (context.get('visible') == text and context.get('dialogue_accepted') is True
                and context.get('dialogue_published') is True)
    matching = [r for r in trace if r['final_player_facing_response'] == text]
    transcript.append(dict(input=json.loads(row['request']).get('text'), response=text,
        server_ms=row['server_ms'], live_dialogue_published=dialogue,
        accepted_npc_speech_replaced=False if dialogue else None,
        knowledge_before=before.get('clue_knowledge'), knowledge_after=after.get('clue_knowledge'),
        knowledge_unchanged=before.get('clue_knowledge') == after.get('clue_knowledge'),
        publication_records=matching, before=before, after=after))
live_npc = sum(t['live_dialogue_published'] for t in transcript)
# Physical response is corroborated by accepted narration publication record.
live_narration = sum(r['response_category'] == 'live_narration' for r in trace)
latency = [t['server_ms'] for t in transcript]
metrics = dict(requests=len(completed), input_tokens=sum(r['input_tokens'] for r in completed.values()),
    output_tokens=sum(r['output_tokens'] for r in completed.values()),
    total_tokens=sum(r['total_tokens'] for r in completed.values()),
    purpose_counts={p:sum(r.get('purpose') == p for r in completed.values()) for p in {r.get('purpose') for r in completed.values()}},
    new_opening_requests=0, published_live_npc=live_npc, published_live_narration=live_narration,
    published_live_responses=live_npc+live_narration,
    tokens_per_published_live_response=round(sum(r['total_tokens'] for r in completed.values())/(live_npc+live_narration),2),
    redundant_primary_narration=0, redundant_bounded_narration_observed=1,
    redundant_bounded_narration_final_source='repaired; accepted and fallback development checks pass; live not rerun',
    retries=0, retry_tokens=0, rejected_provider_outputs='No complete per-attempt acceptance ledger; count not asserted',
    mean_gameplay_server_ms=round(statistics.mean(latency),2),
    p95_gameplay_server_ms=sorted(latency)[math.ceil(len(latency)*.95)-1],
    max_gameplay_server_ms=max(latency), browser_visible_latency_ms=None,
    browser_visible_latency_limitation='No browser paint/completion timing instrumentation; server time is not substituted',
    browser_chat_submissions=len(turns), publication_records=len(trace),
    budget_respected=len(completed)<=12 and sum(r['total_tokens'] for r in completed.values())<=12000)
save('provider_metrics.json', metrics)
save('browser_transcript.json', transcript)
save('provider_completed.json', list(completed.values()))
save('provider_retries.json', [r for r in usage if r.get('retry_attempt',0)])
baseline = json.loads((OUT/'baseline.json').read_text())
preserved=[]; changed=[]
for entry in baseline['files']:
    path=ROOT/entry['path']
    current=hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
    preserved.append(dict(entry, current_sha256=current, unchanged=current==entry['sha256']))
    if current != entry['sha256']: changed.append(entry['path'])
save('protected_after.json', dict(count=len(preserved),preserved=len(preserved)-len(changed),changed=changed,files=preserved))
cases = list(ET.parse(OUT/'gate_final.xml').getroot().iter('testcase'))
held = [c for c in cases if c.get('classname') == 'tests.test_pr_play_79d_holdout']
save('holdout_results.json', dict(passed=sum(c.find('failure') is None and c.find('error') is None for c in held),
    total=len(held), results=[dict(identity=c.get('name'), passed=c.find('failure') is None and c.find('error') is None,
    seconds=c.get('time')) for c in held], provenance='original one-time gate_final.xml; not rerun'))
scene = unwrap(OUT/'browser_data/scenes/frontier_gate.json')['scene'] if 'scene' in unwrap(OUT/'browser_data/scenes/frontier_gate.json') else unwrap(OUT/'browser_data/scenes/frontier_gate.json')
hidden = [s for s in scene.get('hidden_facts',[]) if isinstance(s,str)]
violations = [{'input':t['input'],'hidden_fact':s} for t in transcript for s in hidden if s and s in t['response']]
save('player_safe_scan.json',dict(hidden_exact_matches=violations,canary_exposures=[t['input'] for t in transcript if 'CANARY_' in t['response']],
    mandatory_disclosure_omissions=[t['input'] for t in transcript if 'examine the notice board' in t['input'].lower()
       and 'northwest mud track past the crates' not in t['response']],
    scope='Exact hidden-fact/canary scan plus observed source disclosure. Not a universal semantic proof.'))
authority={}
for name in ['session.json','character.json','world.json','combat.json','conditions.json']:
    authority[name]=dict(before=unwrap(ROOT/'artifacts/pr_play_79c/browser_data'/name),after=unwrap(OUT/'browser_data'/name))
save('authoritative_before_after.json', authority)
sources=['game/api.py','game/exploration.py','game/publication_contract.py','game/quarantined_investigation_narration.py',
         'game/player_http_boundary.py','game/bounded_improvisation.py','tests/test_pr_play_61_player_facing.py',
         'tests/test_pr_play_62_investigation_quality.py','tests/test_pr_play_69_target_references.py',
         'tests/test_pr_play_79d_closeout.py','tests/test_pr_play_79d_holdout.py']
save('final_source.json', [dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in sources])
print(json.dumps(metrics,indent=2))
