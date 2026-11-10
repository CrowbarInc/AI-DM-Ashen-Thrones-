"""Trusted classification lifecycle through real atomic storage and observation."""
import copy
from dataclasses import asdict, replace
import hashlib
import json
import time
from uuid import uuid4

import pytest
from game import api, storage
from game import object_marking as m
from game import object_observation as o
from tests.test_object_instances import saved, migrate, RUN
from tests.test_object_marking import established, request, apply, evidence
from tests.test_object_marking_inspection import removal, remove
from tests.test_object_observation import view, contents, category, observation, grant


@pytest.fixture
def marked(established):
    return apply(request())


def classification(mark_id, kind='visible', **changes):
    c = storage.load_character()
    req = dict(version=1, operation='set_marking_visibility', campaign_run_id=RUN,
        character_id=c['id'], instance_id=c['inventory'][0]['instance_id'],
        modification_id=mark_id, visibility={'classification':kind},
        expected_revision=c['inventory'][0]['revision'], request_id='classify-1',
        authorization=dict(caller_id='trusted-fixture', decision_id='PRIVATE-CLASSIFICATION',
            mechanics='not_applicable', preconditions={k:'PRIVATE:'+k for k in m.VISIBILITY_PRECONDITIONS}))
    req.update(changes)
    req['request_digest'] = m.request_digest(req)
    return req


def classify(req):
    return api.set_marking_visibility(req, authorization=m._establish_visibility_authorization(req))


def test_timeline_reload_snapshots_replay_and_hidden_boundary(marked):
    start = storage.load_character(); mark_id = marked['modification_id']
    assert contents(view()) == [] and category(view())['knowledge'] == 'unknown'
    states = []
    s0 = storage.create_snapshot('S0 unclassified')
    states.append((s0, copy.deepcopy(start), view()))
    requests, results = [], []
    for i, kind in enumerate(('visible', 'concealed', 'visible'), 1):
        req = classification(mark_id, kind, request_id='visibility-'+str(i))
        prior = storage.load_character(); stale_grant = grant(prior)
        result = classify(req); requests.append(req); results.append(result)
        state = storage.load_character(); observed = view()
        assert state['inventory'][0]['markings'] == start['inventory'][0]['markings']
        assert state['inventory'][1] == start['inventory'][1]
        assert state['inventory'][0]['instance_id'] == start['inventory'][0]['instance_id']
        assert state['inventory'][0]['revision'] == 1+i
        assert result['resulting_revision'] == result['previous_revision']+1
        assert contents(observed) == ([] if kind == 'concealed' else ['Northwest track'])
        assert contents(view(concealed=True)) == ['Northwest track']
        assert o.observe_object(state, observation(state), authorization=stale_grant)['status'] == 'unresolved'
        storage.save_character(state)
        assert storage.load_character() == state and view() == observed
        raw = storage.CHARACTER_PATH.read_bytes()
        for r, v in zip(requests, results): assert classify(r) == v
        assert storage.CHARACTER_PATH.read_bytes() == raw
        snap = storage.create_snapshot('S'+str(i)+' '+kind)
        states.append((snap, state, observed))
    snapshots=[]
    for snap, expected, observed in states:
        assert storage.load_snapshot(snap['id'])
        restored = storage.load_character()
        assert restored == expected and view() == observed
        assert contents(view(concealed=True)) == ([] if snap == s0 else ['Northwest track'])
        snapshots.append(dict(snapshot=snap, state=restored, observation=view(),
            receipt_count=len(restored[m.LEDGER]['entries'])))
    raw = storage.CHARACTER_PATH.read_bytes(); out = json.dumps(view())
    forbidden = [mark_id, 'PRIVATE', 'request_digest', 'authorization', m.LEDGER]
    forbidden += [r['request_id'] for r in requests]+[r['request_digest'] for r in requests]
    leaks = [s for s in forbidden if s in out]
    assert not leaks and storage.CHARACTER_PATH.read_bytes() == raw
    evidence('classification_timeline.json', dict(initial=start, requests=requests, results=results,
        snapshots=snapshots, final=storage.load_character(), leakage={'leaks':leaks}, live_provider_calls=0))


def test_restricted_transitions_and_same_value_durable_noop(marked, monkeypatch):
    mid = marked['modification_id']; classify(classification(mid))
    req = classification(mid, visibility={'classification':'restricted','scope':'guild'}, request_id='restricted')
    assert classify(req)['resulting_revision'] == 3
    assert contents(view()) == [] and category(view())['knowledge'] == 'unknown'
    assert contents(view(restricted_scopes=('guild',))) == ['Northwest track']
    assert contents(view(restricted_scopes=('other',))) == []
    no = classification(mid, visibility=req['visibility'], request_id='noop')
    before = storage.load_character(); result = classify(no); after = storage.load_character()
    assert result['status'] == 'no_change' and result['resulting_revision'] == 3
    assert after['inventory'] == before['inventory']
    assert len(after[m.LEDGER]['entries']) == len(before[m.LEDGER]['entries'])+1
    raw = storage.CHARACTER_PATH.read_bytes()
    def forbidden(*a, **kw): raise AssertionError('replay attempted save')
    with monkeypatch.context() as mp:
        mp.setattr(storage, 'save_character', forbidden)
        assert classify(no) == result and storage.CHARACTER_PATH.read_bytes() == raw
    assert classify(classification(mid, request_id='visible-again'))['resulting_revision'] == 4
    assert classify(no) == result and contents(view()) == ['Northwest track']
    evidence('no_change_and_restricted.json', dict(restricted=req, no_change=result,
        before=before, after=after, later_replay=classify(no), observation=view()))


@pytest.mark.parametrize('field,value', [
    ('campaign_run_id','wrong'),('character_id','wrong'),('instance_id',str(uuid4())),
    ('modification_id',str(uuid4())),('visibility',{'classification':'concealed'}),
    ('operation','remove_marking'),('expected_revision',2),('request_id','other')])
def test_authority_is_bound_to_entire_request(marked, field, value):
    req = classification(marked['modification_id']); auth = m._establish_visibility_authorization(req)
    req[field]=value; req['request_digest']=m.request_digest(req)
    raw=storage.CHARACTER_PATH.read_bytes()
    assert api.set_marking_visibility(req, authorization=auth)['status']=='rejected'
    assert storage.CHARACTER_PATH.read_bytes()==raw


@pytest.mark.parametrize('auth', [None, True, {'authorized':True}, {'request_digest':'fake'}, 'trusted'])
def test_json_and_missing_authority_never_grant_permission(marked, auth):
    req=classification(marked['modification_id']); raw=storage.CHARACTER_PATH.read_bytes()
    assert api.set_marking_visibility(req, authorization=auth)['error']=='untrusted_visibility_authorization'
    assert m.prepare_visibility(storage.load_character(), req, authorization=auth)['status']=='rejected'
    assert storage.CHARACTER_PATH.read_bytes()==raw


@pytest.mark.parametrize('field,value', [
    ('expected_revision',None),('expected_revision',True),('expected_revision','1'),('expected_revision',-1),
    ('instance_id','bad'),('modification_id','bad'),('visibility',{'classification':'observable'}),
    ('visibility',{'classification':'restricted'}),('visibility',{'classification':[]}),
    ('visibility',{'classification':'visible','scope':'guild'}),('visibility',None),
    ('authorization',{'authorized':True}),('authorization',None),('request_digest','bad')])
def test_malformed_requests_reject_without_state_change(marked, field, value):
    req=classification(marked['modification_id']); req[field]=value
    if field!='request_digest': req['request_digest']=m.request_digest(req)
    raw=storage.CHARACTER_PATH.read_bytes()
    assert api.set_marking_visibility(req)['status']=='rejected'
    assert storage.CHARACTER_PATH.read_bytes()==raw


@pytest.mark.parametrize('field', ['expected_revision','authorization','visibility','request_digest'])
def test_required_fields(marked, field):
    req=classification(marked['modification_id']); del req[field]
    assert api.set_marking_visibility(req)['error']=='invalid_request'


@pytest.mark.parametrize('key', sorted(m.VISIBILITY_PRECONDITIONS))
@pytest.mark.parametrize('bad', [True,'',None])
def test_invalid_prerequisite_assertions(marked, key, bad):
    req=classification(marked['modification_id']); req['authorization']['preconditions'][key]=bad
    req['request_digest']=m.request_digest(req)
    assert api.set_marking_visibility(req)['error']=='unauthorized_visibility'


@pytest.mark.parametrize('fault', ['stale','missing_object','missing_mark','removed','duplicate','bad_identity',
    'legacy','bad_mark','missing_receipt','bad_metadata','bad_version','bad_leaf'])
def test_invalid_targets_and_state_never_repaired(marked, fault):
    req=classification(marked['modification_id']); c=storage.load_character(); row=c['inventory'][0]
    if fault=='stale': req['expected_revision']=0
    elif fault=='missing_object': req['instance_id']=str(uuid4())
    elif fault=='missing_mark': req['modification_id']=str(uuid4())
    elif fault=='removed':
        remove(removal(marked['modification_id'])); c=storage.load_character()
        req['expected_revision']=c['inventory'][0]['revision']
    elif fault=='duplicate': c['inventory'].append(copy.deepcopy(row))
    elif fault=='bad_identity': row['instance_id']='bad'
    elif fault=='legacy':
        for k in ('instance_id','revision','provenance'): row.pop(k)
    elif fault=='bad_mark': row['markings'][0]['content']=[]
    elif fault=='missing_receipt': c[m.LEDGER]['entries'].clear()
    elif fault=='bad_metadata': row['marking_visibility']=[]
    elif fault=='bad_version': row['marking_visibility']={'version':True,'markings':{}}
    else: row['marking_visibility']={'version':1,'markings':{marked['modification_id']:{'classification':'future'}}}
    req['request_digest']=m.request_digest(req); storage.save_character(c)
    raw=storage.CHARACTER_PATH.read_bytes()
    assert classify(req)['status']=='rejected' and storage.CHARACTER_PATH.read_bytes()==raw


def test_conflicts_replay_after_removal_and_all_operation_pairs(marked):
    mid=marked['modification_id']; req=classification(mid); result=classify(req)
    raw=storage.CHARACTER_PATH.read_bytes()
    assert classify(classification(mid,'concealed',expected_revision=1))['error']=='conflicting_request'
    assert classify(classification(mid,request_id=marked['request_id']))['error']=='conflicting_request'
    assert apply(request(request_id=req['request_id']))['error']=='conflicting_request'
    assert remove(removal(mid, request_id=req['request_id']))['error']=='conflicting_request'
    assert storage.CHARACTER_PATH.read_bytes()==raw
    rem=removal(mid); removed=remove(rem)
    assert removed['status']=='applied'
    assert classify(classification(mid,request_id=rem['request_id']))['error']=='conflicting_request'
    raw=storage.CHARACTER_PATH.read_bytes()
    assert classify(req)==result and storage.CHARACTER_PATH.read_bytes()==raw
    assert contents(view())==[] and category(view())['knowledge']=='unknown'
    evidence('visibility_idempotency_controls.json', dict(request=req,result=result,removed=removed,
        replay_after_removal=classify(req),shared_ledger=storage.load_character()[m.LEDGER]))


def test_identical_content_reorder_cross_object_unknown_fields_and_extensions(marked):
    second=apply(request(request_id='same-content'))
    c=storage.load_character(); row=c['inventory'][0]
    row['markings'][0]['future']={'private':[1,2]}; row['unknown']={'keep':True}
    row['marking_visibility']={'version':1,'markings':{},'future':{'keep':True}}
    storage.save_character(c); req=classification(marked['modification_id']); c['inventory'].reverse()
    storage.save_character(c); before=storage.load_character()
    assert classify(req)['status']=='applied'; after=storage.load_character()
    assert after['inventory'][0]==before['inventory'][0]
    assert after['inventory'][1]['markings']==before['inventory'][1]['markings']
    assert second['modification_id'] not in after['inventory'][1]['marking_visibility']['markings']
    assert after['inventory'][1]['marking_visibility']['future']=={'keep':True}
    assert after['inventory'][1]['unknown']=={'keep':True}


@pytest.mark.parametrize('extension', [
    {'pf1e@1':{'perception_dc':18,'ac':4}}, {'rules_light@1':{'tags':['rune']}},
    {'scifi@1':{'sensor':'encrypted','battery':9}}])
def test_ruleset_independence(marked, extension):
    c=storage.load_character(); c['extensions']=copy.deepcopy(extension)
    c['inventory'][0]['extensions']=copy.deepcopy(extension)
    c['inventory'][0]['markings'][0]['extensions']=copy.deepcopy(extension)
    storage.save_character(c); req=classification(marked['modification_id'])
    assert classify(req)['status']=='applied'; after=storage.load_character()
    for owner in (after,after['inventory'][0],after['inventory'][0]['markings'][0]): assert owner['extensions']==extension
    assert contents(view())==['Northwest track']
    evidence('visibility_portability_'+next(iter(extension))+'.json', dict(extension=extension, state=after, observation=view()))


@pytest.mark.parametrize('stage', ['serialization','create','partial_write','flush','sync','replace','ambiguous'])
def test_atomic_classification_failures(marked, monkeypatch, stage):
    req=classification(marked['modification_id']); before=storage.CHARACTER_PATH.read_bytes()
    def fail(*a, **kw): raise OSError('injected '+stage)
    with monkeypatch.context() as mp:
        if stage=='serialization':
            original_prepare=m.prepare_visibility
            def unserializable(*a,**kw):
                proposal=original_prepare(*a,**kw)
                proposal['character']['unserializable_fixture']=object()
                return proposal
            mp.setattr(m,'prepare_visibility',unserializable)
        elif stage=='create': mp.setattr(storage.tempfile,'mkstemp',fail)
        elif stage in ('partial_write','flush'):
            original=storage.os.fdopen
            class Broken:
                def __init__(self,fd,*a,**kw): self.f=original(fd,*a,**kw)
                def __enter__(self): return self
                def __exit__(self,*a): self.f.close()
                def write(self,data):
                    if stage=='partial_write': self.f.write(data[:3]); fail()
                    return self.f.write(data)
                def flush(self): fail()
                def fileno(self): return self.f.fileno()
            mp.setattr(storage.os,'fdopen',Broken)
        elif stage=='sync': mp.setattr(storage.os,'fsync',fail)
        elif stage=='replace': mp.setattr(storage.os,'replace',fail)
        else:
            original=storage.save_character
            def ambiguous(c): original(c); fail()
            mp.setattr(storage,'save_character',ambiguous)
        with pytest.raises((OSError,TypeError)): classify(req)
    assert storage.CHARACTER_PATH.read_bytes()==before
    assert 'marking_visibility' not in storage.load_character()['inventory'][0]
    assert not list(storage.CHARACTER_PATH.parent.glob('character.json.tmp.*'))
    result=classify(req); assert result['status']=='applied' and classify(req)==result
    evidence('classification_failure_'+stage+'.json',dict(stage=stage, unchanged=True,
        before_sha256=hashlib.sha256(before).hexdigest(),retry=result,receipt_atomic=True))


def test_no_public_route_or_gameplay_callers_and_observation_purity(marked, monkeypatch):
    assert not any('visibility' in r.path or 'marking' in r.path for r in api.app.routes)
    c=storage.load_character(); req=classification(marked['modification_id']); classify(req)
    current=storage.load_character(); raw=storage.CHARACTER_PATH.read_bytes(); rev=current['inventory'][0]['revision']
    def fail(*a,**kw): raise AssertionError('observation wrote')
    monkeypatch.setattr(storage,'save_character',fail)
    assert contents(view())==['Northwest track']
    assert storage.CHARACTER_PATH.read_bytes()==raw and storage.load_character()['inventory'][0]['revision']==rev
    assert o.observe_object(c, observation(c))['status']=='unresolved'


def test_bounded_performance(marked):
    mid=marked['modification_id']; initial=classification(mid)
    c=storage.load_character(); auth=m._establish_visibility_authorization(initial)
    def measure(fn, n=25):
        begin=time.perf_counter()
        for _ in range(n): fn()
        return round((time.perf_counter()-begin)*1e6/n,3)
    metrics={'initial_validation_us':measure(lambda:m.prepare_visibility(c,initial,authorization=auth)),
        'observation_before_us':measure(lambda:view(c))}
    start=time.perf_counter(); classify(initial); metrics['atomic_initial_us']=(time.perf_counter()-start)*1e6
    metrics['exact_replay_us']=measure(lambda:classify(initial))
    metrics['observation_after_us']=measure(lambda:view())
    transition=classification(mid,'concealed',request_id='transition'); start=time.perf_counter(); classify(transition)
    metrics['atomic_transition_us']=(time.perf_counter()-start)*1e6
    current=storage.load_character(); metrics['receipt_bytes']=len(json.dumps(current[m.LEDGER]).encode())
    metrics['receipt_count']=len(current[m.LEDGER]['entries']); metrics['live_provider_calls']=0
    evidence('visibility_performance.json',metrics)


def test_ambiguous_commit_reconciles_original_request_id(marked, monkeypatch):
    req=classification(marked['modification_id']); original=storage.save_character
    def uncertain(c): original(c); raise OSError('lost completion after replacement')
    def no_rollback(*a,**kw): raise OSError('rollback unavailable')
    with monkeypatch.context() as mp:
        mp.setattr(storage,'save_character',uncertain)
        mp.setattr(storage,'_restore_runtime_bytes',no_rollback)
        with pytest.raises(storage.RuntimePersistenceCoherencyError): classify(req)
    committed=storage.load_character(); raw=storage.CHARACTER_PATH.read_bytes()
    result=classify(req)
    assert result==committed[m.LEDGER]['entries'][req['request_id']]
    assert storage.CHARACTER_PATH.read_bytes()==raw and contents(view())==['Northwest track']
    evidence('ambiguous_reconciliation.json',dict(request=req,reconciled=result,
        no_duplicate=True,state=committed))


@pytest.mark.parametrize('field,value', [('status','proposed'),('resulting_revision',99),
    ('operation','remove_marking'),('modification_id',str(uuid4())),('request_digest','0'*64),('extra',True)])
def test_visibility_receipt_corruption_fails_closed(marked, field, value):
    req=classification(marked['modification_id']); classify(req); c=storage.load_character()
    c[m.LEDGER]['entries'][req['request_id']][field]=value; storage.save_character(c)
    raw=storage.CHARACTER_PATH.read_bytes()
    assert classify(req)['error']=='invalid_receipt_state' and storage.CHARACTER_PATH.read_bytes()==raw


@pytest.mark.parametrize('changes,error', [({'campaign_run_id':'wrong'},'campaign_mismatch'),
    ({'character_id':'wrong'},'character_mismatch'),({'expected_revision':0},'stale_revision')])
def test_new_trusted_request_still_checks_authoritative_scope_and_revision(marked, changes, error):
    req=classification(marked['modification_id'], **changes); raw=storage.CHARACTER_PATH.read_bytes()
    assert classify(req)['error']==error and storage.CHARACTER_PATH.read_bytes()==raw


def test_noop_receipt_failure_is_atomic(marked, monkeypatch):
    mid=marked['modification_id']; classify(classification(mid))
    req=classification(mid,request_id='noop'); raw=storage.CHARACTER_PATH.read_bytes()
    with monkeypatch.context() as mp:
        def fail(*a,**kw): raise OSError('noop receipt replacement failure')
        mp.setattr(storage.os,'replace',fail)
        with pytest.raises(OSError): classify(req)
    assert storage.CHARACTER_PATH.read_bytes()==raw
    assert classify(req)['status']=='no_change'


@pytest.mark.parametrize('fault', ['insert','change','drop','rebind','duplicate'])
def test_whole_character_http_cannot_author_visibility(marked, fault):
    from fastapi.testclient import TestClient
    mid=marked['modification_id']
    if fault!='insert': classify(classification(mid))
    payload=storage.load_character(); row=payload['inventory'][0]
    if fault=='insert': row['marking_visibility']={'version':1,'markings':{mid:{'classification':'visible'}}}
    elif fault=='change': row['marking_visibility']['markings'][mid]['classification']='concealed'
    elif fault=='drop': row.pop('marking_visibility')
    elif fault=='rebind': row['instance_id']=str(uuid4())
    else: payload['inventory'].append(copy.deepcopy(row))
    payload['authorized']=True; raw=storage.CHARACTER_PATH.read_bytes()
    # Fixture supplies runtime files directly; do not run full-campaign startup.
    client=TestClient(api.app)
    try:
        result=client.post('/api/character?ui_mode=player',json=payload).json()
    finally:
        client.close()
    assert result['ok'] is False and result['error']
    # Existing player HTTP projection deliberately replaces internal errors.
    from starlette.requests import Request
    internal=api.update_character(Request({'type':'http','query_string':b'ui_mode=player','headers':[]}),payload)
    assert internal['error']=='trusted_visibility_operation_required'
    assert 'trusted_visibility_operation_required' not in json.dumps(result)
    assert storage.CHARACTER_PATH.read_bytes()==raw
    evidence('http_bypass_'+fault+'.json',dict(rejected=True,error=result['error'],internal_error=internal['error'],unchanged=True))


def test_whole_character_http_preserves_unchanged_classification_and_reordering(marked):
    from fastapi.testclient import TestClient
    classify(classification(marked['modification_id']))
    c=storage.load_character(); c['inventory'].reverse(); c['name']='Edited character'
    client=TestClient(api.app)
    try:
        result=client.post('/api/character?ui_mode=player',json=c).json()
    finally:
        client.close()
    assert result['ok'] is True and storage.load_character()==c
    assert contents(view(c,req=observation(c,index=1)))==['Northwest track']


def test_existing_add_and_remove_share_visibility_history(marked):
    req=request(expected_revision=0); initial=classification(marked['modification_id'])
    classify(initial); assert apply(req)==marked
    second=apply(request(request_id='later-add'))
    assert second['resulting_revision']==3
    assert classify(initial)['resulting_revision']==2
    assert remove(removal(second['modification_id']))['resulting_revision']==4
    assert contents(view())==['Northwest track']


def test_whole_character_compare_save_serializes_with_classification(marked, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor, TimeoutError
    from threading import Event
    from starlette.requests import Request
    entered,release=Event(),Event(); original=m._client_visibility_unchanged
    def guarded(current, proposed):
        entered.set()
        assert release.wait(5)
        return original(current,proposed)
    monkeypatch.setattr(m,'_client_visibility_unchanged',guarded)
    payload=storage.load_character(); payload['name']='Concurrent edit'
    req=classification(marked['modification_id'])
    http_request=Request({'type':'http','query_string':b'ui_mode=player','headers':[]})
    with ThreadPoolExecutor(max_workers=2) as pool:
        edit=pool.submit(api.update_character,http_request,payload)
        assert entered.wait(5)
        mutation=pool.submit(classify,req)
        try:
            with pytest.raises(TimeoutError): mutation.result(timeout=.1)
        finally:
            release.set()
        assert edit.result(timeout=5)['ok'] is True
        assert mutation.result(timeout=5)['status']=='applied'
    assert storage.load_character()['name']=='Concurrent edit' and contents(view())==['Northwest track']
    evidence('client_writer_serialization.json',dict(shared_lane=True,classification_preserved=True))
