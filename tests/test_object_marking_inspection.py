"""Internal current-state reads and atomic, ID-specific removal timelines."""
import copy
import json
from uuid import uuid4

import pytest
from game import api, storage
from game import object_marking as m
from tests.test_object_instances import saved, migrate, RUN
from tests.test_object_marking import established, request, apply, evidence


def inspect_request(c=None, index=0, **changes):
    c = c or storage.load_character()
    req = dict(version=1, operation='inspect_markings', campaign_run_id=RUN,
        character_id=c['id'], instance_id=c['inventory'][index]['instance_id'],
        context={'caller_id':'internal-test', 'purpose':'authoritative_state'})
    req.update(changes)
    return req


def inspect(c=None, index=0):
    return api.inspect_inventory_object_markings(inspect_request(c, index))


def removal(mark_id, **changes):
    c = storage.load_character()
    req = dict(version=1, operation='remove_marking', campaign_run_id=RUN,
        character_id=c['id'], instance_id=c['inventory'][0]['instance_id'],
        modification_id=mark_id, request_id='remove-1', expected_revision=c['inventory'][0]['revision'],
        authorization={'caller_id':'internal-test', 'decision_id':'remove-approved',
            'mechanics':'not_applicable',
            'preconditions':{k:'evidence:'+k for k in m.REMOVAL_PRECONDITIONS}})
    req.update(changes)
    req['request_digest'] = m.request_digest(req)
    return req


def remove(req):
    return api.remove_inventory_object_marking(req)


@pytest.fixture
def two(established):
    a = apply(request())
    b = apply(request(request_id='add-2'))  # deliberately identical text
    assert a['resulting_revision'] == 1 and b['resulting_revision'] == 2
    return a, b


def test_full_timeline_reload_snapshots_replay_and_later_revision(established):
    original = storage.load_character()
    s0 = storage.create_snapshot('S0 before marking')
    assert inspect()['markings'] == [] and inspect()['revision'] == 0
    first = apply(request()); assert len(inspect()['markings']) == 1
    second = apply(request(request_id='add-2'))
    s1 = storage.create_snapshot('S1 two markings')
    before = storage.load_character(); both = inspect()
    assert len(both['markings']) == 2 and inspect(index=1)['markings'] == []
    req = removal(first['modification_id']); result = remove(req)
    after = storage.load_character(); current = inspect()
    assert result['resulting_revision'] == 3 and result['previous_revision'] == 2
    assert current['revision'] == 3 and current['instance_id'] == original['inventory'][0]['instance_id']
    assert current['markings'] == [before['inventory'][0]['markings'][1]]
    assert after['inventory'][1] == original['inventory'][1]
    for r in (first, second): assert after[m.LEDGER]['entries'][r['request_id']] == r
    assert after[m.LEDGER]['entries'][req['request_id']] == result
    storage.save_character(after); reloaded = storage.load_character()
    raw = storage.CHARACTER_PATH.read_bytes()
    assert inspect() == current and remove(req) == result and apply(request(before, expected_revision=0)) == first
    assert storage.CHARACTER_PATH.read_bytes() == raw
    s2 = storage.create_snapshot('S2 one marking')
    later = apply(request(request_id='add-later')); assert later['resulting_revision'] == 4
    raw = storage.CHARACTER_PATH.read_bytes()
    assert remove(req) == result and storage.CHARACTER_PATH.read_bytes() == raw
    states = []
    for snapshot, expected, revision, receipts in ((s0,0,0,0),(s1,2,2,2),(s2,1,3,3)):
        assert storage.load_snapshot(snapshot['id'])
        observed = inspect(); state = storage.load_character()
        assert len(observed['markings']) == expected and observed['revision'] == revision
        assert len(state.get(m.LEDGER,{}).get('entries',{})) == receipts
        states.append(dict(snapshot=snapshot, inspection=observed, character=state))
    assert remove(req) == result
    evidence('inspection_removal_timeline.json', dict(original=original, before=before,
        inspection_request=inspect_request(), two_markings=both, removal_request=req,
        removal_result=result, after=after, current=current, reloaded=reloaded,
        replay=remove(req), snapshots=states, live_provider_calls=0))


def test_inspection_pure_detached_no_allocation_or_persistence(two, monkeypatch):
    c = storage.load_character(); before = copy.deepcopy(c); raw = storage.CHARACTER_PATH.read_bytes()
    def forbidden(*a, **kw): raise AssertionError('read side effect')
    monkeypatch.setattr(m, 'uuid4', forbidden)
    monkeypatch.setattr(storage, 'save_character', forbidden)
    monkeypatch.setattr(storage, '_atomic_write_bytes', forbidden)
    one = m.inspect_markings(c, inspect_request(c)); another = inspect()
    assert one == another == inspect() and c == before
    assert storage.CHARACTER_PATH.read_bytes() == raw
    one['markings'][0]['source']['reference'] = 'mutated detached view'
    assert c == before and inspect() == another


@pytest.mark.parametrize('change', [dict(instance_id=None),dict(instance_id='bad'),
    dict(instance_id=str(uuid4())),dict(character_id='other'),dict(campaign_run_id='other'),
    dict(context={}),dict(context={'caller_id':'x','purpose':'player_observation'}),
    dict(operation='observe'),dict(extra=True),dict(version=True)])
def test_inspection_request_refusals(established, change):
    c = storage.load_character(); raw = storage.CHARACTER_PATH.read_bytes()
    assert api.inspect_inventory_object_markings(inspect_request(c, **change))['status'] == 'rejected'
    assert storage.CHARACTER_PATH.read_bytes() == raw


@pytest.mark.parametrize('fault', ['legacy','partial_identity','malformed_identity','duplicate',
    'marking_mapping','marking_bad_record','missing_receipt','missing_inventory','legacy_string'])
def test_invalid_state_never_repaired(two, fault):
    c = storage.load_character(); req = inspect_request(c); rem = removal(two[0]['modification_id'])
    row = c['inventory'][0]
    if fault == 'legacy':
        for k in ('instance_id','revision','provenance'): row.pop(k)
    elif fault == 'partial_identity': row.pop('instance_id')
    elif fault == 'malformed_identity': row['instance_id'] = 'bad'
    elif fault == 'duplicate': c['inventory'].append(copy.deepcopy(row))
    elif fault == 'marking_mapping': row['markings'] = {'legacy':'keep'}
    elif fault == 'marking_bad_record': row['markings'][0]['content'] = []
    elif fault == 'missing_receipt': c[m.LEDGER]['entries'].pop(two[0]['request_id'])
    elif fault == 'missing_inventory': c['inventory'] = None
    else: c['inventory'][0] = 'legacy dagger'
    storage.save_character(c); raw = storage.CHARACTER_PATH.read_bytes()
    assert api.inspect_inventory_object_markings(req)['status'] == 'rejected'
    assert remove(rem)['status'] == 'rejected'
    assert storage.CHARACTER_PATH.read_bytes() == raw and storage.load_character() == c


def test_inspection_does_not_bootstrap_missing_files(established):
    req = inspect_request()
    storage.CHARACTER_PATH.unlink()
    assert api.inspect_inventory_object_markings(req)['error'] == 'missing_runtime_state'
    assert not storage.CHARACTER_PATH.exists()


def test_specific_id_and_replay_conflicts(two):
    a,b = two; req = removal(a['modification_id']); result = remove(req)
    assert inspect()['markings'][0]['modification_id'] == b['modification_id']
    raw = storage.CHARACTER_PATH.read_bytes()
    assert remove(req) == result
    assert remove(removal(b['modification_id']))['error'] == 'conflicting_request'
    assert remove(removal(a['modification_id'], request_id='new-removal'))['error'] == 'missing_marking'
    assert remove(removal(b['modification_id'],request_id=a['request_id']))['error'] == 'conflicting_request'
    assert apply(request(request_id=req['request_id']))['error'] == 'conflicting_request'
    assert storage.CHARACTER_PATH.read_bytes() == raw
    evidence('idempotency_controls.json',dict(exact_replay=remove(req),original=result,
        conflicting=remove(removal(b['modification_id'])),
        cross_operation=remove(removal(b['modification_id'],request_id=a['request_id'])),
        absent=remove(removal(a['modification_id'],request_id='new-removal'))))


@pytest.mark.parametrize('change,error', [({'expected_revision':0},'stale_revision'),
    ({'expected_revision':None},'invalid_request'),({'expected_revision':True},'invalid_request'),
    ({'expected_revision':'2'},'invalid_request'),({'expected_revision':-1},'invalid_request'),
    ({'modification_id':None},'invalid_request'),({'modification_id':'bad'},'invalid_request'),
    ({'modification_id':str(uuid4())},'missing_marking'),
    ({'instance_id':str(uuid4())},'missing_or_ambiguous_target'),
    ({'authorization':None},'unauthorized_removal'),({'authorization':{}},'unauthorized_removal'),
    ({'campaign_run_id':'wrong'},'campaign_mismatch'),({'character_id':'wrong'},'character_mismatch'),
    ({'operation':'erase_all'},'invalid_request'),({'request_digest':'0'*64},'invalid_digest')])
def test_removal_refusals_no_revision_or_receipt(two, change, error):
    req = removal(two[0]['modification_id']); req.update(change)
    if 'request_digest' not in change: req['request_digest'] = m.request_digest(req)
    raw = storage.CHARACTER_PATH.read_bytes()
    assert remove(req)['error'] == error
    assert storage.CHARACTER_PATH.read_bytes() == raw


@pytest.mark.parametrize('key', ['expected_revision','modification_id','request_id'])
def test_missing_removal_fields(two,key):
    req = removal(two[0]['modification_id']); req.pop(key); req['request_digest']=m.request_digest(req)
    assert remove(req)['error'] == 'invalid_request'


@pytest.mark.parametrize('key', ['caller_id','decision_id','mechanics','preconditions'])
def test_removal_authorization_fields(two,key):
    req = removal(two[0]['modification_id']); req['authorization'].pop(key)
    req['request_digest']=m.request_digest(req)
    assert remove(req)['error'] == 'unauthorized_removal'


@pytest.mark.parametrize('key', ['target_exists','accessible','rights','marking_exists','removable','capability'])
def test_removal_precondition_evidence(two,key):
    req = removal(two[0]['modification_id']); req['authorization']['preconditions'][key]=''
    req['request_digest']=m.request_digest(req); raw=storage.CHARACTER_PATH.read_bytes()
    assert remove(req)['error']=='unauthorized_removal' and storage.CHARACTER_PATH.read_bytes()==raw


@pytest.mark.parametrize('fault', ['save','replace','sync','post_save'])
def test_removal_failure_atomic_retry(two,monkeypatch,fault):
    req = removal(two[0]['modification_id']); raw = storage.CHARACTER_PATH.read_bytes()
    original = storage.save_character
    def fail(*a,**kw):
        if fault == 'post_save': original(*a,**kw)
        raise OSError('injected removal failure')
    with monkeypatch.context() as mp:
        if fault == 'replace': mp.setattr(storage.os,'replace',fail)
        elif fault == 'sync': mp.setattr(storage.os,'fsync',fail)
        else: mp.setattr(storage,'save_character',fail)
        with pytest.raises(OSError): remove(req)
        assert storage.CHARACTER_PATH.read_bytes() == raw
    result = remove(req)
    assert result['resulting_revision'] == 3 and remove(req)==result
    evidence('removal_failure_'+fault+'.json',dict(fault=fault,unchanged_after_failure=True,
        retry_result=result,inspection=inspect(),temporary_files=[str(p) for p in storage.CHARACTER_PATH.parent.glob('character.json.tmp.*')]))


@pytest.mark.parametrize('extension', [{'pf1e@1':{'ac':4,'damage':'1d4'}},
    {'rules_light@1':{'tags':['small']}},{'scifi@1':{'battery':99,'caliber':'9mm'}}])
def test_portable_opaque_state(two,extension):
    c=storage.load_character(); c['inventory'][0]['extensions']=extension
    storage.save_character(c); before=storage.load_character()
    req=removal(two[0]['modification_id']); result=remove(req); after=storage.load_character()
    for k,v in before['inventory'][0].items():
        if k not in ('markings','revision'): assert after['inventory'][0][k]==v
    assert after['inventory'][1:]==before['inventory'][1:]
    assert inspect()['markings']==[before['inventory'][0]['markings'][1]]
    evidence('portability_'+next(iter(extension))+'.json',dict(extension=extension,before=before,after=after,result=result,inspection=inspect()))


@pytest.mark.parametrize('field', ['request','removed_marking','resulting_revision','operation'])
def test_removal_receipt_corruption_rejected(two,field):
    req=removal(two[0]['modification_id']); remove(req); c=storage.load_character()
    c[m.LEDGER]['entries'][req['request_id']][field]=None
    storage.save_character(c); raw=storage.CHARACTER_PATH.read_bytes()
    assert inspect()['error']=='invalid_receipt_state'
    assert remove(req)['error']=='invalid_receipt_state'
    assert storage.CHARACTER_PATH.read_bytes()==raw


def test_internal_entries_have_no_http_routes(established):
    endpoints={r.endpoint for r in api.app.routes if hasattr(r,'endpoint')}
    assert api.inspect_inventory_object_markings not in endpoints
    assert api.remove_inventory_object_marking not in endpoints


def test_all_removed_and_historical_add_retry(two):
    a,b=two
    req=removal(a['modification_id']); remove(req)
    remove(removal(b['modification_id'],request_id='remove-2'))
    assert inspect()['markings']==[] and inspect()['revision']==4
    assert len(storage.load_character()[m.LEDGER]['entries'])==4
    assert remove(req)['resulting_revision']==3


def test_authority_guard_prevents_commit(two,monkeypatch):
    req=removal(two[0]['modification_id']); raw=storage.CHARACTER_PATH.read_bytes()
    def denied(*a,**kw): raise PermissionError('denied authority')
    monkeypatch.setattr(api,'assert_owner_can_mutate_domain',denied)
    with pytest.raises(PermissionError): remove(req)
    assert storage.CHARACTER_PATH.read_bytes()==raw


def test_concurrent_removal_serialized(two):
    from concurrent.futures import ThreadPoolExecutor
    req=removal(two[0]['modification_id'])
    with ThreadPoolExecutor(2) as pool:
        a,b=list(pool.map(remove,[req,copy.deepcopy(req)]))
    assert a==b and inspect()['revision']==3
    assert len(storage.load_character()[m.LEDGER]['entries'])==3


def test_replay_neither_allocates_nor_saves_after_later_mutation(two,monkeypatch):
    req=removal(two[0]['modification_id']); result=remove(req)
    apply(request(request_id='later-add'))
    def forbidden(*a,**kw): raise AssertionError('replay side effect')
    monkeypatch.setattr(storage,'save_character',forbidden)
    monkeypatch.setattr(m,'uuid4',forbidden)
    assert remove(req)==result and inspect()['revision']==4


@pytest.mark.parametrize('fault',['resurrect','drop_removal','tamper_old_add'])
def test_history_and_current_state_must_be_consistent(two,fault):
    req=removal(two[0]['modification_id']); result=remove(req);c=storage.load_character()
    if fault=='resurrect': c['inventory'][0]['markings'].insert(0,result['removed_marking'])
    elif fault=='drop_removal': c[m.LEDGER]['entries'].pop(req['request_id'])
    else: c[m.LEDGER]['entries'][two[0]['request_id']]['request_digest']='0'*64
    storage.save_character(c);raw=storage.CHARACTER_PATH.read_bytes()
    assert inspect()['error']=='invalid_receipt_state'
    assert remove(req)['error']=='invalid_receipt_state'
    assert storage.CHARACTER_PATH.read_bytes()==raw


def test_removed_modification_identity_cannot_be_reallocated(two,monkeypatch):
    from uuid import UUID
    remove(removal(two[0]['modification_id']))
    monkeypatch.setattr(m,'uuid4',lambda:UUID(two[0]['modification_id']))
    assert apply(request(request_id='new-add'))['error']=='modification_id_collision'


def test_bounded_measurements(two):
    import statistics
    import time
    req=removal(two[0]['modification_id']); c=storage.load_character()
    metrics={}
    def measure(name,fn,n=50):
        samples=[]
        for _ in range(n):
            start=time.perf_counter_ns();fn();samples.append((time.perf_counter_ns()-start)/1000)
        metrics[name]=dict(samples=n,median_us=statistics.median(samples),max_us=max(samples))
    measure('inspect_unmarked',lambda:m.inspect_markings(c,inspect_request(c,1)))
    measure('inspect_multiple',lambda:m.inspect_markings(c,inspect_request(c)))
    measure('removal_validation',lambda:m.prepare_removal(c,req))
    measure('save_reload',lambda:(storage.save_character(c),storage.load_character()),10)
    samples=[]
    for _ in range(10):
        storage.save_character(c)
        start=time.perf_counter_ns();result=remove(req);samples.append((time.perf_counter_ns()-start)/1000)
    metrics['removal_commit']=dict(samples=10,median_us=statistics.median(samples),max_us=max(samples))
    metrics['removal_receipt_compact_bytes']=len(json.dumps(result,separators=(',',':')).encode())
    metrics['character_growth_compact_bytes']=len(json.dumps(storage.load_character(),separators=(',',':')).encode())-len(json.dumps(c,separators=(',',':')).encode())
    metrics.update(live_provider_calls=0,prompt_expansion=0,inventory_size=len(c['inventory']))
    evidence('performance.json',metrics)
