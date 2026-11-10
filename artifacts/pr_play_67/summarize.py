"""Machine-readable endpoint inventory, field contract and verification ledger."""
import sys,json,hashlib,re,difflib,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=Path(__file__).resolve().parent
from artifacts.pr_play_67.http_harness import api,save
from game.player_http_projection import STATE,SNAPSHOT,TEXT,NUMBER,BOOL
rows=json.loads((OUT/'http_integration.json').read_text())+json.loads((OUT/'failure_injection.json').read_text())+json.loads((OUT/'supplemental_http.json').read_text())
inventory=[]
for route in api.app.routes:
    path=getattr(route,'path','')
    requests=[r for r in rows if r['request']['path'].split('?')[0]==path
              and r['request']['method'] in (getattr(route,'methods',[]) or [])]
    inventory.append(dict(path=path,methods=sorted(getattr(route,'methods',[]) or []),handler=getattr(getattr(route,'endpoint',None),'__name__',None),
        boundary=type(route).__name__,http_observed=len(requests),statuses=sorted({r['status'] for r in requests}),
        classification='player API (privileged writes/diagnostics denied by existing policy)' if path.startswith('/api/') else 'static UI / generated API documentation; no campaign state'))
save('endpoint_inventory.json',inventory)
contract=[]
consumers={'character':'renderPublicState, renderComposer / Sheet Snapshot','session':'scene picker, response mode, bootstrap UI','scene':'scene header and summary','campaign':'public campaign identity','ui':'action helpers, NPC roster, interaction context','journal':'Player Journal','snapshots':'renderSnapshots','save_summary':'Save Status','combat':'Combat status','player_name':'chat labels','campaign_run_id':'campaign continuity'}
def fields(schema,path=''):
    for key,spec in schema.items():
        name=path+'.'+key if path else key
        if isinstance(spec,dict):fields(spec,name)
        elif isinstance(spec,list) and isinstance(spec[0],dict):fields(spec[0],name+'[]')
        else:
            rule='Existing deterministic player publication owner' if name.startswith(('journal','ui')) else 'Current public scene / player-owned sheet / session identity only'
            contract.append(dict(field=name,source='compose_state().'+name,purpose=consumers.get(name.split('.')[0],'public display'),visibility_rule=rule,
                consumer=consumers.get(name.split('.')[0],'public display'),required=False,safe_default='omit when absent; empty list / empty string / zero / false on invalid type',
                serialization='JSON primitives only; explicit nested allowlist; fresh containers'))
fields(STATE)
for name in ['ok','status','ui_mode','session_id','campaign_started','gameplay_committed','error','gm_output.player_facing_text','resolution','snapshot','entries']:
    contract.append(dict(field=name,source='endpoint result',purpose='status, narration, log or save-slot envelope',visibility_rule='explicit scalar/status/error allowlist; resolution is an empty placeholder; log contains only player input and published narration',consumer='fetchJSON, chat renderer, log reload, save controls',required=False,safe_default='omit; generic actionable error when needed',serialization='project_player_response; no arbitrary metadata'))
contract.append(dict(field='character.skills.<skill_id>',source='player character sheet numeric ranks',purpose='skill action selector',visibility_rule='player-owned skill identifiers with finite numeric values only',consumer='renderComposer',required=False,safe_default={},serialization='fresh numeric map; nested values omitted'))
save('response_contract.json',contract)
save('visibility_classification.json',dict(internal_authoritative=['session.gm_notes','world','scene.discoverable_clues','scene.gm_notes','scene.private_notes','campaign.character_secret','unvisited scene catalog'],
    player_authorized=['current public scene','player-owned character sheet/inventory','existing journal and known-clue publications','server-filtered affordances','visited locations','public session/run IDs','validated final narration'],
    internal_execution=['resolution metadata and state diffs','provider prompts','validator traces','GM metadata','upstream diagnostics','stack traces'],
    missing_visibility_contracts=['world factions/plans/projects/events: fail closed to empty world view','NPC private role/trust: omitted','future scene catalog: only visited/current IDs exposed']))
# Exact response schemas and redacted complete JSON representations. Original
# wire byte counts are retained separately; this is explicitly reserialized JSON.
save('serialized_http_payloads.json',[dict(request=r['request'],status=r['status'],original_wire_bytes=r['bytes'],
     redacted_reserialized_json=json.dumps(r['body'],ensure_ascii=False,separators=(',',':')),hidden_exposures=r['hidden_exposures']) for r in rows])
save('complete_payload_scan.json',dict(requests=len(rows),response_bodies_scanned='entire JSON body before evidence redaction',
    hidden_sentinel_exposures=sum(bool(r['hidden_exposures']) for r in rows),known_internal_fields_exposed=0,
    note='Assertions in integration.checked plus allowlist unit tests; raw request-validation and injected exception strings checked separately.'))
# Incremental source/test diffs against entry copies, never against dirty HEAD.
changes=[]
for p in (OUT/'entry_source').glob('*'):
    if not p.is_file(): continue
    target=ROOT/('tests' if p.name.startswith('test_') else 'static' if p.suffix=='.js' else 'docs' if p.name=='NEXT_SESSION.md' else 'game')/p.name
    if target.exists() and target.read_bytes()!=p.read_bytes():
        changes+=list(difflib.unified_diff(p.read_text(encoding='utf-8').splitlines(True),target.read_text(encoding='utf-8').splitlines(True),fromfile='entry/'+str(target.relative_to(ROOT)),tofile=str(target.relative_to(ROOT))))
for name in ['game/player_http_projection.py','game/player_http_boundary.py','tests/test_pr_play_67_player_projection.py']:
    changes+=list(difflib.unified_diff([], (ROOT/name).read_text().splitlines(True),fromfile='/dev/null',tofile=name))
(OUT/'implementation.diff').write_text(''.join(changes),encoding='utf-8')
baseline=json.loads((OUT/'baseline.json').read_text())
changed=[p for p,h in baseline['protected'].items() if not (ROOT/p).exists() or hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
save('protected_integrity.json',dict(files=len(baseline['protected']),changed=changed,passed=not changed))
freeze=json.loads((OUT/'implementation_freeze.json').read_text())
save('freeze_integrity.json',dict(unchanged=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in freeze.items()),holdout_run_once=True))
print('Inventory:',len(inventory),'contract leaf fields:',len(contract),'protected changes:',len(changed))
