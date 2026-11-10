"""Bounded disclosure contracts, adversarial payloads, and real saved timelines."""
import copy
from dataclasses import asdict, replace
import hashlib
import json
import time
from uuid import uuid4

import pytest
from game import api, storage
from game import object_instances, object_marking
from game import object_observation as o
from tests.test_object_instances import saved, migrate, RUN
from tests.test_object_marking import established, request, apply, evidence
from tests.test_object_marking_inspection import removal, remove


def observation(c, index=0, **changes):
    req = dict(version=1, campaign_run_id=RUN, character_id=c['id'],
        instance_id=c['inventory'][index]['instance_id'], observer_id='observer-1',
        scope='established-visual-inspection', categories=['markings'])
    req.update(changes)
    return req


def grant(c, req=None, **kw):
    return o._establish_observation_authorization(c, req or observation(c),
        decision_ref='PRIVATE-DECISION', visibility_ref='PRIVATE-VISIBILITY',
        access_ref='PRIVATE-ACCESS', **kw)


def view(c=None, req=None, **kw):
    c = c or storage.load_character()
    req = req or observation(c)
    return o.observe_object(c, req, authorization=grant(c, req, **kw))


def category(result):
    return result['properties'][0]


def contents(result):
    return [v['content'] for v in category(result)['values']]


def add(content, key, visibility=None, index=0):
    c = storage.load_character()
    req = request(c, instance_id=c['inventory'][index]['instance_id'],
        expected_revision=c['inventory'][index]['revision'], request_id=key, content=content,
        authorization=dict(request(c)['authorization'],
            content_sha256=hashlib.sha256(content.encode()).hexdigest()))
    result = apply(req)
    assert result['status'] == 'applied'
    if visibility is not None:
        c = storage.load_character()
        # Trusted fixture authoring, not an observation/mutation API.
        c['inventory'][index].setdefault('marking_visibility',
            dict(version=1, markings={}))['markings'][result['modification_id']] = visibility
        storage.save_character(c)
    return result


@pytest.fixture
def mixed(established):
    add('visible-one', 'add-visible', {'classification':'visible'})
    add('CONCEALED-CONTENT', 'add-concealed', {'classification':'concealed'})
    add('RESTRICTED-CONTENT', 'add-restricted', {'classification':'restricted', 'scope':'guild'})
    add('LEGACY-CONTENT', 'add-legacy')
    return storage.load_character()


def test_visible_multiple_and_detached_repeat(established):
    add('one', 'add-one', {'classification':'visible'})
    add('two', 'add-two', {'classification':'visible'})
    c = storage.load_character(); before = copy.deepcopy(c)
    result = view(c)
    assert contents(result) == ['one','two']
    assert category(result)['knowledge'] == 'known_present'
    assert result == view(c) and c == before
    result['properties'][0]['values'][0]['content'] = 'detached'
    assert contents(view(c)) == ['one','two']


@pytest.mark.parametrize('kind', ['concealed','restricted','legacy'])
def test_inaccessible_marking_does_not_assert_absence(established, kind):
    cls = None if kind == 'legacy' else {'classification':kind}
    if kind == 'restricted': cls['scope'] = 'guild'
    add('PRIVATE-CONTENT', 'private', cls)
    result = view()
    assert category(result) == dict(category='markings', knowledge='unknown', coverage='subset', values=[])
    assert 'PRIVATE-CONTENT' not in json.dumps(result)


def test_mixed_hidden_and_restricted_authority(mixed):
    assert contents(view(mixed)) == ['visible-one']
    assert contents(view(mixed, concealed=True)) == ['visible-one','CONCEALED-CONTENT']
    assert contents(view(mixed, restricted_scopes=('guild',))) == ['visible-one','RESTRICTED-CONTENT']
    assert contents(view(mixed, restricted_scopes=('other',))) == ['visible-one']
    # Even full authority cannot invent missing legacy classification.
    full = view(mixed, concealed=True, restricted_scopes=('*',), complete=True)
    assert contents(full) == ['visible-one','CONCEALED-CONTENT','RESTRICTED-CONTENT']
    assert category(full)['coverage'] == 'subset'


def test_empty_unknown_versus_authorized_absence(established):
    assert category(view())['knowledge'] == 'unknown'
    full = view(concealed=True, restricted_scopes=('*',), complete=True)
    assert category(full) == dict(category='markings',knowledge='known_absent',coverage='complete',values=[])
    evidence('absence_semantics.json', dict(partial=view(), complete=full))


@pytest.mark.parametrize('kwargs', [dict(complete=True),dict(complete=True, concealed=True),
    dict(complete=True,restricted_scopes=('*',)),dict(concealed='yes'),dict(restricted_scopes=['guild']),
    dict(restricted_scopes=('guild','guild')),dict(restricted_scopes=('',)),dict(complete=1)])
def test_conflicting_or_malformed_upstream_decision_rejected(established, kwargs):
    with pytest.raises(ValueError): grant(established, **kwargs)


@pytest.mark.parametrize('authorization', [None, {}, True, 'trusted', {'authoritative':True},
    {'observer_id':'observer-1','decision_ref':'PRIVATE-DECISION'}])
def test_client_json_never_grants_authority(established, authorization):
    result = o.observe_object(established, observation(established), authorization=authorization)
    assert result == o._unavailable()


def test_serialized_internal_grant_not_accepted(mixed):
    assert o.observe_object(mixed, observation(mixed), authorization=asdict(grant(mixed))) == o._unavailable()


@pytest.mark.parametrize('change', [dict(observer_id='other'),dict(scope='other'),dict(campaign_run_id='other'),
    dict(character_id='other'),dict(instance_id=str(uuid4())),dict(observer_id=None),dict(scope=None),
    dict(categories=['all']),dict(categories=['damage']),dict(categories=['markings','markings']),
    dict(categories=['markings','receipts']),dict(categories=[]),dict(version=True),dict(extra='private'),
    dict(instance_id='malformed')])
def test_wrong_binding_or_request_is_uniform_refusal(mixed, change):
    req = observation(mixed); authorization = grant(mixed)
    req.update(change)
    assert o.observe_object(mixed, req, authorization=authorization) == o._unavailable()


@pytest.mark.parametrize('field,value', [('decision_ref',''),('access_ref',None),('visibility_ref',''),
    ('revision',99),('state_digest','forged'),('categories',('damage',)),('observer_id','other'),
    ('scope','other'),('instance_id',str(uuid4())),('concealed','yes'),('complete',True)])
def test_tampered_grant_rejected(mixed, field, value):
    auth = replace(grant(mixed), **{field:value})
    assert o.observe_object(mixed, observation(mixed), authorization=auth) == o._unavailable()


def test_stale_revision_and_changed_metadata_or_content(mixed):
    req = observation(mixed); auth = grant(mixed)
    for key in ('revision','marking_visibility','markings'):
        changed = copy.deepcopy(mixed)
        if key == 'revision': changed['inventory'][0]['revision'] += 1
        elif key == 'marking_visibility': changed['inventory'][0].pop(key)
        else: changed['inventory'][0]['markings'][0]['content'] = 'changed-without-revision'
        assert o.observe_object(changed, req, authorization=auth) == o._unavailable()


@pytest.mark.parametrize('fault', ['duplicate','malformed','missing','wrong_campaign','partial','inventory'])
def test_invalid_durable_identity_is_never_repaired(mixed, fault):
    req = observation(mixed); auth = grant(mixed); c = copy.deepcopy(mixed)
    if fault == 'duplicate': c['inventory'].append(copy.deepcopy(c['inventory'][0]))
    elif fault == 'malformed': c['inventory'][0]['instance_id'] = 'bad'
    elif fault == 'missing': c['inventory'][0].pop('instance_id')
    elif fault == 'partial': c['inventory'][0].pop('revision')
    elif fault == 'wrong_campaign': c['inventory'][0]['provenance']['campaign_run_id'] = 'other'
    else: c['inventory'] = None
    before = copy.deepcopy(c)
    assert o.observe_object(c, req, authorization=auth) == o._unavailable() and c == before


def test_cross_object_reordering_and_repeated_requests(established):
    add('only A', 'A', {'classification':'visible'})
    add('only B', 'B', {'classification':'visible'}, index=1)
    c = storage.load_character(); req = observation(c); auth = grant(c)
    second = observation(c,1)
    assert contents(view(c)) == ['only A'] and contents(view(c,second)) == ['only B']
    assert o.observe_object(c, second, authorization=auth) == o._unavailable()
    c['inventory'].reverse()
    assert contents(o.observe_object(c,req,authorization=auth)) == ['only A']
    for _ in range(3): assert contents(view(c,second)) == ['only B']
    evidence('cross_object.json', dict(a=view(c,req),b=view(c,second),inventory_reordered=True))


def test_hidden_state_noninterference(mixed):
    expected = view(mixed)
    # No hidden count, class, content length, metadata or historical count in DTO.
    for keep in (1,2,3,4):
        c = copy.deepcopy(mixed); c['inventory'][0]['markings'] = c['inventory'][0]['markings'][:keep]
        assert view(c) == expected
    c = copy.deepcopy(mixed)
    c['inventory'][0]['markings'][1]['content'] = 'DIFFERENT-SECRET'*100
    c['object_marking_receipts'] = {'PRIVATE-RECEIPT':'REMOVED-HISTORICAL-CONTENT'}
    c['inventory'][0]['extensions'] = {'private':'HIDDEN-RULESET-STATE'}
    assert view(c) == expected
    evidence('noninterference.json', dict(result=expected,hidden_variants_equal=True))


def test_structured_and_serialized_leakage_allowlist(mixed):
    c = copy.deepcopy(mixed)
    c['inventory'][0]['private_property'] = 'UNRELATED-PROPERTY'
    result = view(c); raw = json.dumps(result)
    prohibited = ['CONCEALED-CONTENT','RESTRICTED-CONTENT','LEGACY-CONTENT','UNRELATED-PROPERTY',
        'PRIVATE-DECISION','PRIVATE-VISIBILITY','PRIVATE-ACCESS','authorization','request_id',
        'request_digest','modification_id','provenance','applied_revision','revision','marking_visibility']
    prohibited += [m[k] for m in c['inventory'][0]['markings']
                   for k in ('modification_id','request_id','request_digest')]
    for value in prohibited: assert value not in raw
    assert set(result) == {'version','status','target','properties','limitations','evidence'}
    assert set(category(result)['values'][0]) == {'content','presentation','evidence_ref','content_sha256'}
    evidence('information_leakage.json', dict(result=result,prohibited_values=prohibited,leaks=[]))


@pytest.mark.parametrize('metadata', [None,{}, {'version':True,'markings':{}},
    {'version':2,'markings':{}},{'version':1,'markings':[]},'visible'])
def test_missing_or_unsupported_visibility_is_unknown(established, metadata):
    add('legacy', 'legacy')
    c = storage.load_character(); c['inventory'][0]['marking_visibility'] = metadata
    assert category(view(c))['knowledge'] == 'unknown'


@pytest.mark.parametrize('metadata', [{'classification':'unknown'}, {'classification':'restricted'},
    {'classification':'restricted','scope':''}, {'classification':'visible','private':'PRIVATE'},
    {'classification':['visible']}, None])
def test_ambiguous_per_mark_classification_never_guessed(established, metadata):
    added=add('private','private')
    c=storage.load_character()
    c['inventory'][0]['marking_visibility']=dict(version=1,markings={added['modification_id']:metadata})
    result=view(c,concealed=True,restricted_scopes=('*',),complete=True)
    assert category(result)['knowledge']=='unknown' and contents(result)==[]


@pytest.mark.parametrize('fault', ['mapping','too_many','duplicate','bad_uuid','bad_revision',
    'bool_revision','bad_type','bad_version','blank_content','too_long','bad_unicode'])
def test_malformed_active_state_is_unresolved(established, fault):
    add('visible','visible',{'classification':'visible'})
    c=storage.load_character(); req=observation(c); auth=grant(c); row=c['inventory'][0]
    if fault=='mapping': row['markings']={}
    elif fault=='too_many': row['markings']*=17
    elif fault=='duplicate': row['markings']*=2
    else:
        mark=row['markings'][0]
        key,value={'bad_uuid':('modification_id','bad'),'bad_revision':('applied_revision',99),
            'bool_revision':('applied_revision',True),'bad_type':('type','remove_marking'),
            'bad_version':('version',2),'blank_content':('content',' '),
            'too_long':('content','x'*2049),'bad_unicode':('content','\ud800')}[fault]
        mark[key]=value
    result=o.observe_object(c,req,authorization=auth)
    assert result==o._unavailable()
    # A fresh trusted assertion cannot make malformed state observable either.
    try: fresh=grant(c)
    except (ValueError,TypeError): return
    assert o.observe_object(c,req,authorization=fresh)==o._unavailable()


def test_removed_classifications_and_huge_receipt_history_are_not_observation_inputs(mixed):
    result=view(mixed); auth=grant(mixed)
    c=copy.deepcopy(mixed)
    c['inventory'][0]['marking_visibility']['markings'][str(uuid4())]={'classification':'concealed'}
    c['object_marking_receipts']={'entries':{'private-history-'+str(i):{'content':'REMOVED'} for i in range(100)}}
    assert o.observe_object(c,observation(c),authorization=auth)==result


def test_real_save_reload_removal_and_snapshot_timeline(established):
    empty = storage.create_snapshot('empty')
    a = add('mark A', 'A', {'classification':'visible'})
    add('mark B', 'B', {'classification':'visible'})
    before = storage.load_character(); req = observation(before); auth = grant(before)
    marked = storage.create_snapshot('before removal')
    result_before = view(before)
    remove(removal(a['modification_id']))
    current = view(); c = storage.load_character()
    assert contents(current) == ['mark B']
    assert o.observe_object(c,req,authorization=auth) == o._unavailable()
    storage.save_character(c)
    assert storage.load_character() == c and view() == current
    after = storage.create_snapshot('after removal')
    states=[]
    for snapshot, expected in ((empty,[]),(marked,['mark A','mark B']),(after,['mark B'])):
        assert storage.load_snapshot(snapshot['id'])
        state = storage.load_character(); result = view(state)
        assert contents(result) == expected
        states.append(dict(snapshot=snapshot,character=state,result=result))
    evidence('observation_timeline.json',dict(before=before,current=c,before_result=result_before,
        current_result=current,reloaded_result=current,snapshots=states,live_provider_calls=0))


def test_observation_no_side_effects_no_provider_no_write(mixed, monkeypatch):
    c = copy.deepcopy(mixed); req = observation(c); auth = grant(c)
    before = copy.deepcopy(c)
    disk = {p:hashlib.sha256(p.read_bytes()).hexdigest() for p in storage.DATA_DIR.rglob('*') if p.is_file()}
    def forbidden(*a, **kw): raise AssertionError('observation side effect')
    monkeypatch.setattr(storage,'save_character',forbidden)
    monkeypatch.setattr(storage,'save_session',forbidden)
    monkeypatch.setattr(storage,'save_world',forbidden)
    monkeypatch.setattr(storage,'_atomic_write_bytes',forbidden)
    monkeypatch.setattr(object_instances,'uuid4',forbidden)
    monkeypatch.setattr(object_marking,'uuid4',forbidden)
    from game import gm
    if hasattr(gm,'generate_gm_response'): monkeypatch.setattr(gm,'generate_gm_response',forbidden)
    result=o.observe_object(c,req,authorization=auth)
    assert result == o.observe_object(c,req,authorization=auth) and c == before
    assert disk == {p:hashlib.sha256(p.read_bytes()).hexdigest() for p in disk}
    evidence('read_only.json',dict(before_hash=hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest(),
        after_hash=hashlib.sha256(json.dumps(c,sort_keys=True).encode()).hexdigest(),
        disk_hashes={str(p):v for p,v in disk.items()},state_equal=True,disk_equal=True,live_provider_calls=0))


@pytest.mark.parametrize('ruleset,extension', [('pf1e@1',{'ac':4,'perception_dc':99}),
    ('rules_light@1',{'tags':['mysterious'],'secret':'HIDDEN-RULESET-STATE'}),
    ('scifi@1',{'sensor':'thermal','battery':90,'encrypted':'HIDDEN-RULESET-STATE'})])
def test_ruleset_extensions_opaque_and_persistent(established, ruleset, extension):
    add('same inscription', 'same', {'classification':'visible'})
    c=storage.load_character(); c['inventory'][0]['extensions']={ruleset:extension}
    storage.save_character(c); before=storage.load_character(); result=view(before)
    assert contents(result)==['same inscription']
    assert storage.load_character()==before
    assert extension == before['inventory'][0]['extensions'][ruleset]
    assert ruleset not in json.dumps(result) and 'HIDDEN-RULESET-STATE' not in json.dumps(result)
    evidence('observation_portability_'+ruleset+'.json',dict(before=before,after=storage.load_character(),result=result))


def test_no_routes_or_implicit_gameplay_integration():
    assert not any('observe_object' in str(getattr(r,'endpoint','')) for r in api.app.routes)
    import ast
    from pathlib import Path
    owners=[]
    for p in Path('game').glob('*.py'):
        if p.name == 'object_observation.py': continue
        tree=ast.parse(p.read_text(encoding='utf-8-sig'))
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom) and node.module == 'game.object_observation': owners.append(p.name)
    assert owners==[]


def test_bounded_performance(established):
    samples={}
    for name in ('unmarked','visible','mixed'):
        if name=='visible': add('one','one',{'classification':'visible'})
        if name=='mixed': add('concealed','two',{'classification':'concealed'})
        c=storage.load_character(); req=observation(c); auth=grant(c)
        rows=[]
        for _ in range(100):
            start=time.perf_counter_ns(); result=o.observe_object(c,req,authorization=auth)
            rows.append(time.perf_counter_ns()-start)
        start=time.perf_counter_ns()
        for _ in range(100): grant(c)
        auth_us=(time.perf_counter_ns()-start)/100/1000
        start=time.perf_counter_ns()
        for _ in range(100): raw=json.dumps(result)
        serialization_us=(time.perf_counter_ns()-start)/100/1000
        samples[name]=dict(mean_us=sum(rows)/len(rows)/1000,max_us=max(rows)/1000,
            authorization_us=auth_us,serialization_us=serialization_us,payload_bytes=len(raw.encode()))
    evidence('observation_performance.json',dict(samples=samples,iterations=100,live_provider_calls=0,
        prompt_expansion=0,provider_retries=0))
