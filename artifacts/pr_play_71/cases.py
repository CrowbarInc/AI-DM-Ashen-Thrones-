"""Frozen lifecycle case executor. Real HTTP adapters; provider fixture explicitly offline."""
import sys,copy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tests.test_pr_play_71_lifecycle import *

def run_case(row,tmp,mp):
    group=row['group'];v=row['variant'];branch=row['branch']
    if group=='publication':
        from tests.test_pr_play_66_publication import test_publication_http
        test_publication_http(tmp,mp,v)
        return {'publication_fixture':v,'safe_fallback':True}
    configure(tmp,mp)
    # Unknown/private server fields must survive disk and fail closed over HTTP.
    world=storage.load_world();world['gm_notes']='CANARY_WORLD_PRIVATE';storage.save_world(world)
    scene=storage.load_scene('old_milestone');scene['scene']['gm_notes']='CANARY_SCENE_PRIVATE'
    storage._save_json(storage.scene_path('old_milestone'),scene)
    with TestClient(api.app,raise_server_exceptions=False) as cl:
        identity=create(cl)
        if group=='start':
            if v=='new_twice':assert create(cl)!=identity;identity=storage.load_session()['campaign_run_id']
            if v.endswith('_retry'):
                good=api.call_gpt
                def fail(*a,**k):
                    if v=='timeout_retry':raise TimeoutError('CANARY_PROVIDER_PRIVATE')
                    if v=='failure_retry':raise RuntimeError('CANARY_PROVIDER_PRIVATE')
                    return {} if v=='malformed_retry' else {'player_facing_text':''}
                mp.setattr(api,'call_gpt',fail)
                r=cl.post('/api/start_campaign');assert r.status_code>=400
                assert 'CANARY_' not in r.text and not storage.load_session()['campaign_started']
                mp.setattr(api,'call_gpt',good)
            initial=start(cl)
            if v=='duplicate':
                count=storage.load_session()['turn_counter'];r=cl.post('/api/start_campaign')
                assert r.status_code==409 and storage.load_session()['turn_counter']==count
            safe(cl.get('/api/state'));chat(cl,'I examine the notice board.')
            return {'identity':identity,'scene':initial['session']['active_scene_id'],'first_action':True}
        if group=='recovery' and v!='stale_resume':
            before=copy.deepcopy(storage.load_session())
            if v in ['corrupt_snapshot','incomplete_snapshot']:
                storage.SNAPSHOTS_DIR.mkdir(exist_ok=True)
                (storage.SNAPSHOTS_DIR/'broken.json').write_text('{' if v=='corrupt_snapshot' else '{"version":1}')
            payload={} if v=='missing_id' else {'snapshot_id':'broken' if 'snapshot' in v else 'does-not-exist'}
            b=safe(cl.post('/api/snapshots/load',json=payload));assert not b['ok']
            assert storage.load_session()['campaign_run_id']==before['campaign_run_id']
            return {'recoverable_error':b['error'],'identity_preserved':True}
        start(cl);reach(cl);follow=choose(cl,branch)
        committed=copy.deepcopy(flags());session=storage.load_session();character=storage.load_character()
        state=safe(cl.get('/api/state'))['public_state']
        saved=safe(cl.post('/api/snapshots',json={'label':row['id']}))['snapshot']['id']
        # A real New Campaign displaces active state; restoration uses normal save API.
        other=create(cl);assert other!=identity
        assert not any(flags().get(k) for k in committed if k.startswith('patrol_'))
        safe(cl.post('/api/snapshots/load',json={'snapshot_id':saved}))
        restored=safe(cl.get('/api/state'))['public_state']
        assert storage.load_session()['campaign_run_id']==identity
        assert storage.load_session()['active_scene_id']==session['active_scene_id']
        assert storage.load_character()==character and flags()==committed
        assert restored['journal']==state['journal']
        assert restored['ui']['affordances']==state['ui']['affordances']
        if group=='continuity':
            attempted='patrol_'+('report' if branch=='survey' else 'survey') if 'opposite' in v else follow if 'followup' in v else 'patrol_'+branch
            act(cl,attempted);assert flags()==committed
        if group=='isolation':
            saved2=safe(cl.post('/api/snapshots',json={'label':'A'}))['snapshot']['id']
            create(cl);start(cl);reach(cl);choose(cl,'report' if branch=='survey' else 'survey')
            assert not flags().get('patrol_'+branch)
            safe(cl.post('/api/snapshots/load',json={'snapshot_id':saved2}));assert flags()==committed
        chat(cl,'I examine the mud prints.' if branch=='survey' else 'I examine the notice board.')
        assert flags()==committed
        assert storage.load_world()['gm_notes']=='CANARY_WORLD_PRIVATE'
        return {'identity':identity,'displaced_identity':other,'selected_flag':row['expected']['branch_flag'],'followup_flag':row['expected']['followup_flag'],'resume':True,'continued':True,'sentinels_excluded':True}
