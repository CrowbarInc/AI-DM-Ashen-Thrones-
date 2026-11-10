"""One-shot frozen developer-authored HTTP holdout, not external validation."""
import sys,json,hashlib,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from artifacts.pr_play_67.http_harness import *
from artifacts.pr_play_67.integration import checked
from tests.test_pr_play_52_quarantined_integration import PRINT_CLUE

def put(data,path,value):
    node=data
    for pos,key in enumerate(path[:-1]):
        next_key=path[pos+1]
        if isinstance(node,list):
            while len(node)<=key:node.append({})
            node=node[key]
        else:
            if key not in node:node[key]=[] if isinstance(next_key,int) else {}
            node=node[key]
    if isinstance(node,list):
        while len(node)<=path[-1]:node.append({})
    node[path[-1]]=value

def main():
    assert not (OUT/'holdout_results.json').exists(),'One-shot holdout already executed'
    manifest=json.loads((OUT/'frozen_holdout_manifest.json').read_text())
    assert hashlib.sha256((OUT/'frozen_holdout.json').read_bytes()).hexdigest()==manifest['sha256']
    freeze=json.loads((OUT/'implementation_freeze.json').read_text())
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in freeze.items())
    cases=json.loads((OUT/'frozen_holdout.json').read_text());results=[]
    for case in cases:
        try:
            with seed('holdout_'+case['id'],case.get('name')!='disabled','old_milestone') as mp,server() as request:
                api.compose_state();before=snapshot();group=case['group'];name=case.get('name')
                if 'path' in case:
                    source=api.compose_state()
                    # Nested cases place an object under the named source field;
                    # scalar leaves must never stringify that object.
                    value={'innocuous':case['value']} if group=='nested' else case['value']
                    put(source,case['path'],value)
                    mp.setattr(api,'compose_state',lambda:copy.deepcopy(source))
                    row=checked(request('/api/state'))
                    assert case['value'] not in row['serialized_body']
                    assert row['body']['public_state']['character']['name']=='Galinor'
                    assert snapshot()==before
                elif group=='discovery':
                    if name=='unknown_clue':
                        row=checked(request('/api/state'));assert PRINT_CLUE not in row['serialized_body']
                    else:
                        row=checked(request('/api/chat',{'text':'I examine the weathered milestone.'}))
                        assert PRINT_CLUE in row['body']['gm_output']['player_facing_text']
                        if name in ['known_clue','repeat']:row=checked(request('/api/chat',{'text':'I examine the weathered milestone again.'}))
                        assert PRINT_CLUE in row['body']['journal']['discovered_clues']
                elif group=='error':
                    if name=='exception':
                        def fail(*a,**k):raise RuntimeError('HOLDOUT_SENTINEL_ERROR')
                        mp.setattr(api,'load_campaign',fail)
                    if name=='error_metadata':mp.setattr(api,'chat',lambda *a,**k:{'ok':False,'error':{'note':'HOLDOUT_SENTINEL_ERROR'},'world':before['world']})
                    if name in ['fallback','malformed']:
                        from artifacts.pr_play_66.harness import ORIGINAL
                        mp.setattr(integrated,'run_integrated_hook',lambda h,**kw:ORIGINAL(h,generator=quarantine._Replay({} if name=='malformed' else None,'provider_error' if name=='fallback' else '')))
                    row=checked(request('/api/chat',{'text':{'details':'HOLDOUT_SENTINEL_ERROR'}} if name=='validation_input' else {'text':'I examine the weathered milestone.'}))
                    assert 'HOLDOUT_SENTINEL' not in row['serialized_body']
                    if name in ['fallback','malformed']:assert PRINT_CLUE in row['body']['gm_output']['player_facing_text']
                    if name=='exception':assert row['status']==500
                    if name=='validation_input':assert row['status']==422
                elif group=='frontend':
                    row=checked(request('/api/state'));public=row['body']['public_state']
                    assert public['scene']['scene']['id']=='old_milestone'
                    assert public['character']['name']=='Galinor'
                    assert public['character']['inventory'][0]['id']=='spellbook'
                    assert public['ui']['affordances'] and public['session']['campaign_run_id']
                elif group=='isolation':
                    if name in ['author','debug']:row=checked(request('/api/state?ui_mode='+name));assert row['status']==403
                    else:
                        if name=='wrong_session':mp.setenv(quarantine.PUBLICATION_SESSION_ENV,'other')
                        row=checked(request('/api/chat',{'text':'I examine the weathered milestone.'}))
                        assert row['status']==200
                        if name=='enabled':assert PRINT_CLUE in row['body']['gm_output']['player_facing_text']
                        if name in ['disabled','wrong_session']:assert not any(r.get('publication') for r in quarantine.evidence_records())
                else:
                    row=checked(request('/api/state'));assert snapshot()==before
                    if name=='reload':
                        saved=checked(request('/api/snapshots',{'label':'Holdout checkpoint'}));sid=saved['body']['snapshot']['id']
                        row=checked(request('/api/snapshots/load',{'snapshot_id':sid}))
                        assert storage.load_session()['gm_notes']==before['session']['gm_notes']
                    assert 'CANARY_GM_NOTE' in json.dumps(storage.load_session())
                    assert 'CANARY_NPC_MOTIVE' in json.dumps(storage.load_world())
                results.append(dict(case=case,passed=True,http=redact(row)))
        except Exception as error:
            results.append(dict(case=case,passed=False,error=type(error).__name__+': '+str(error)[:300]))
        save('holdout_results.json',results)
    save('holdout_summary.json',dict(cases=len(results),passed=sum(r['passed'] for r in results),failed=sum(not r['passed'] for r in results),
         developer_authored=True,independent_external_validation=False,one_shot=True,sha256=manifest['sha256']))
    print('Holdout:',sum(r['passed'] for r in results),'/',len(results))
if __name__=='__main__':main()
