"""Full-payload endpoint, replay, fault, and persistence evidence over TCP."""
import sys, json, copy, statistics, time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from artifacts.pr_play_67.http_harness import *
from game.player_http_projection import project_player_state
from tests.test_pr_play_52_quarantined_integration import PRINT_CLUE

ACTIONS=['I examine the notice board.','I follow the missing patrol rumor.',
         'I examine the weathered milestone.','I examine the weathered milestone again.',
         'I examine the weathered milestone.']
def checked(row):
    assert not row['hidden_exposures'], row['hidden_exposures']
    raw=row['serialized_body']
    for key in ['gm_notes','gm_only','private_notes','discoverable_clues','state_changes','provider_prompt','validation_trace']:
        assert '"'+key+'"' not in raw,key
    return row

def main():
    all_rows=[];sequences=[];preservation=[];faults=[]
    for enabled in [False,True]:
        with seed('after_'+str(enabled),enabled),server() as request:
            sequence=[]
            for index,text in enumerate(ACTIONS):
                before=snapshot();quarantine.clear_evidence()
                row=checked(request('/api/chat',{'text':text}))
                assert row['status']==200,row
                after=snapshot()
                row.update(enabled=enabled,index=index+1,state_before=before,state_after=after,
                           narration=row['body']['gm_output']['player_facing_text'])
                if enabled and quarantine.evidence_records():
                    evidence=quarantine.evidence_records()[-1]
                    mandatory=[f['text'] for f in evidence.get('authorized_outcome_contract',{}).get('must_communicate',[])]
                    assert all(f in row['narration'] for f in mandatory)
                    row['mandatory_disclosures']=mandatory
                    row['publication']=evidence.get('publication')
                sequence.append(row);all_rows.append(row)
            assert sequence[1]['state_after']['session']['active_scene_id']=='old_milestone'
            assert PRINT_CLUE in sequence[2]['serialized_body']
            if enabled:
                assert PRINT_CLUE in sequence[2]['narration']
                assert 'nothing new' in sequence[3]['narration']
            state=checked(request('/api/state'));all_rows.append(state)
            public=state['body']['public_state']
            assert PRINT_CLUE in public['journal']['discovered_clues']
            assert public['character']['inventory']
            assert public['ui']['affordances']
            for path,body,method in [('/api/log',None,'GET'),('/api/response_mode',{'mode':'vivid'},'POST'),('/api/snapshots',None,'GET'),('/api/snapshots',{'label':'PR67 public checkpoint'},'POST')]:
                all_rows.append(checked(request(path,body,method)))
            snap=all_rows[-1]['body']['snapshot']['id']
            persisted=json.loads((storage.SNAPSHOTS_DIR/(snap+'.json')).read_text())
            assert 'CANARY_GM_NOTE' in json.dumps(persisted)
            load=checked(request('/api/snapshots/load',{'snapshot_id':snap}));all_rows.append(load)
            assert storage.load_session()['gm_notes']==['CANARY_GM_NOTE']
            assert storage.load_world()['gm_only']['motivation']=='CANARY_NPC_MOTIVE'
            preservation.append(dict(enabled=enabled,snapshot_retained_hidden=True,reload_retained_hidden=True,
                                     scene_template_retained='CANARY_UNDISCOVERED_CLUE' in storage.scene_path('old_milestone').read_text(),
                                     authoritative_state=snapshot(),persisted_snapshot=persisted))
            for path,body,method in [('/api/state?ui_mode=author',None,'GET'),('/api/state?ui_mode=debug',None,'GET'),('/api/debug_trace',None,'GET'),('/api/campaign',{},'POST'),('/api/scene',{},'POST'),('/api/world',{},'POST'),('/api/scene/activate',{'scene_id':'old_milestone'},'POST'),('/api/action',{'action_type':'observe','intent':'I look around.'},'POST'),('/api/chat',{'text':'I travel to the invented crystal palace.'},'POST'),('/api/chat',{'text':{'prompt':'SECRET_SENTINEL_ERROR'}},'POST'),('/api/snapshots/load',{'snapshot_id':'missing'},'POST'),('/api/character',storage.load_character(),'POST'),('/api/reset_combat',{},'POST'),('/api/clear_log',{},'POST'),('/api/reset_session',{},'POST'),('/api/new_campaign',{},'POST'),('/api/start_campaign',{},'POST')]:
                all_rows.append(checked(request(path,body,method)))
            sequences.append(sequence)
    # Matched deterministic actions: same states aside from run/session IDs/times.
    def normalized(v):
        volatile={'campaign_run_id','session_id','timestamp','created_at','updated_at','saved_at','last_save_timestamp','last_updated','last_seen_at'}
        if isinstance(v,dict): return {k:normalized(x) for k,x in v.items() if k not in volatile and 'debug' not in k}
        if isinstance(v,list): return [normalized(x) for x in v]
        return v
    comparisons=[dict(action=i+1,equal=normalized(sequences[0][i]['state_after'])==normalized(sequences[1][i]['state_after'])) for i in range(5)]
    save('state_comparisons.json',comparisons)
    # Injection stays scoped to test process and isolated campaign stores.
    from starlette.responses import JSONResponse
    for fault in ['unavailable','timeout','FAIL','REVIEW_REQUIRED','VALIDATION_ERROR','malformed','empty','resolution','initialization','nested_error','serialization','unknown_field','public_looking_object','wrong_session']:
        with seed('fault_'+fault,True,'old_milestone') as mp,server() as request:
            before=snapshot()
            def fail(*a,**k): raise RuntimeError('SECRET_SENTINEL_ERROR')
            if fault in ['unavailable','timeout','FAIL','REVIEW_REQUIRED','VALIDATION_ERROR','malformed','empty']:
                original=integrated.run_integrated_hook
                # seed has installed an outer replay wrapper; use the real owner.
                from artifacts.pr_play_66.harness import ORIGINAL
                def run(h,**kw):
                    result=ORIGINAL(h,generator=quarantine._Replay({} if fault=='malformed' else '' if fault=='empty' else None,'timeout' if fault=='timeout' else 'provider_error' if fault=='unavailable' else ''))
                    if fault in ['FAIL','REVIEW_REQUIRED','VALIDATION_ERROR']: result.update(validation={'decision':fault},used_fallback=True)
                    return result
                mp.setattr(integrated,'run_integrated_hook',run)
            if fault=='resolution':mp.setattr(api,'_resolve_engine_noncombat_seam',fail)
            if fault=='initialization':mp.setattr(api,'load_campaign',fail)
            if fault=='nested_error':mp.setattr(api,'chat',lambda *a,**k:{'ok':False,'error':{'message':'SECRET_SENTINEL_ERROR'},'session':storage.load_session()})
            if fault=='serialization':
                original_render=JSONResponse.render
                def render(self,content):
                    if isinstance(content,dict) and 'gm_output' in content:raise TypeError('SECRET_SENTINEL_ERROR')
                    return original_render(self,content)
                mp.setattr(JSONResponse,'render',render)
            if fault in ['unknown_field','public_looking_object']:
                original_compose=api.compose_state
                def compose():
                    result=original_compose();result['ui']['future']={'label':'SECRET_SENTINEL_ERROR'}
                    result['character']['inventory'][0]['description']={'text':'SECRET_SENTINEL_ERROR'}
                    return result
                mp.setattr(api,'compose_state',compose)
            if fault=='wrong_session':mp.setenv(quarantine.PUBLICATION_SESSION_ENV,'different-session')
            row=checked(request('/api/chat',{'text':'I examine the weathered milestone.'}))
            assert 'SECRET_SENTINEL_ERROR' not in row['serialized_body']
            if fault in ['resolution','initialization','serialization']:assert row['status']==500
            elif fault!='nested_error':
                assert row['status']==200
                if fault!='wrong_session':assert PRINT_CLUE in row['body']['gm_output']['player_facing_text']
            row.update(fault=fault,state_before=before,state_after=snapshot())
            faults.append(row)
    # Lightweight timings isolate projection and encoding from engine/provider work.
    with seed('timings'):
        state=api.compose_state();project_ms=[];serialization_ms=[]
        for _ in range(300):
            start=time.perf_counter();safe=project_player_state(state);project_ms.append((time.perf_counter()-start)*1000)
            start=time.perf_counter();JSONResponse(safe);serialization_ms.append((time.perf_counter()-start)*1000)
    before=json.loads((OUT/'original_leak_reproduction.json').read_text())
    save('http_integration.json',redact(all_rows));save('gameplay_replay.json',redact(sequences))
    save('failure_injection.json',redact(faults));save('persistence.json',redact(preservation))
    save('metrics.json',dict(http_requests=len(all_rows)+len(faults),hidden_sentinel_exposures=sum(bool(r['hidden_exposures']) for r in all_rows+faults),
        projection_mean_ms=statistics.mean(project_ms),projection_max_ms=max(project_ms),serialization_mean_ms=statistics.mean(serialization_ms),
        http_mean_ms=statistics.mean(r['http_ms'] for r in all_rows+faults),http_max_ms=max(r['http_ms'] for r in all_rows+faults),
        gameplay_mean_ms=statistics.mean(r['http_ms'] for s in sequences for r in s),
        before_action_bytes=[r['action']['bytes'] for r in before],after_action_bytes=[s[0]['bytes'] for s in sequences],
        five_actions_per_mode=True,mandatory_disclosure_omissions=0,provider_calls=0,frontend_verification='HTTP integration',state_comparisons=comparisons))
    print('Completed',len(all_rows)+len(faults),'TCP requests; zero full-body exposures.')
if __name__=='__main__':main()
