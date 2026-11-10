"""Offline presentation experiment. All provider transports blocked by conftest."""
import copy
from dataclasses import asdict
import inspect
import json
from pathlib import Path
import statistics
import time
import tracemalloc

import pytest

from game import controlled_investigation_renderer as cr
from game.authorized_information import revealed_information
from game.api_turn_support import _authoritative_resolution_fact_text
from game.defaults import default_character, default_session, default_world
from game.exploration import resolve_exploration_action
from game.immutable_valid_response import validate_generated_response

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'artifacts/pr_play_47'
STYLES = {
    'concise': dict(cr.DEFAULT_PLAN),
    'atmospheric': {**cr.DEFAULT_PLAN, 'structure': 'setting_first', 'pace': 'flowing',
        'tone': 'reflective', 'sensory_focus': 'visual', 'detail': 'extended',
        'perspective': 'close_observation', 'transition': 'pause'},
    'investigative': {**cr.DEFAULT_PLAN, 'structure': 'evidence_first', 'pace': 'measured',
        'tone': 'intent', 'sensory_focus': 'texture', 'detail': 'standard',
        'transition': 'question', 'information_order': 'known_first'},
}
SECRETS = ['CANARY_UNDISCOVERED', 'CANARY_GM_NOTE', 'CANARY_NPC_MOTIVE',
           'CANARY_FACTION_ACTIVITY', 'CANARY_DESTINATION', 'CANARY_WORLD_STATE']


def write(name, value):
    OUT.mkdir(exist_ok=True)
    (OUT/('evidence_'+name+'.json')).write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')


class Stub:
    def __init__(self, response): self.response, self.calls, self.payload = response, 0, None
    def select(self, payload):
        self.calls += 1
        self.payload = copy.deepcopy(payload)
        return copy.deepcopy(self.response)


def payload(scene, known=()):
    # Reuse GM's existing public-scene extraction, then the production disclosure
    # projection inside the adapter. The clue catalog is deliberately supplied
    # as a hostile convenience field, never as player knowledge.
    from game.gm import _scene_layers
    public, _, _ = _scene_layers(scene)
    return {'scene': {'public': public, 'discovered_clues': [{'text': t} for t in known],
                      'discoverable_clues': scene['scene'].get('discoverable_clues', [])},
            'world': {'private': SECRETS[-1]}, 'metadata': {'gm_notes': SECRETS[1]}}


def synthetic_scene(target, text=None):
    return {'scene': {'id': 'unfamiliar_site', 'location': 'Unfamiliar Site',
        'visible_facts': [('Loose fibres lie in plain view.' if target == 'fibres' else f'A {target} lies in plain view.'),
                          'Light catches the uneven surface.'],
        'summary': 'A quiet place for a closer look.',
        'interactables': [{'id': target, 'label': target, 'type': 'investigate',
                           **({'reveals_clue': 'selected'} if text else {})}],
        'discoverable_clues': ([{'id': 'selected', 'text': text}] if text else []) +
                             [{'id': 'hidden', 'text': SECRETS[0]}],
        'hidden_facts': [SECRETS[4]], 'gm_notes': [SECRETS[1]],
        'npcs': [{'hidden_motivation': SECRETS[2]}], 'hidden_faction': SECRETS[3],
        'exits': []}}


def resolve(scene, target, player=None):
    session = default_session()
    session['active_scene_id'] = scene['scene']['id']
    return resolve_exploration_action(copy.deepcopy(scene), session, default_world(),
        {'id': target, 'type': 'investigate', 'target_id': target,
         'label': target, 'prompt': player or f'I examine the {target}.'},
        raw_player_text=player or f'I examine the {target}.', character=default_character())


def scenarios():
    rows = []
    for sid, target, player in [('frontier_gate', 'notice_board', 'I examine the notice board.'),
                                ('old_milestone', 'prints', 'I examine the footprints.')]:
        scene = json.loads((ROOT/f'data/scenes/{sid}.json').read_text(encoding='utf-8'))
        rows.append({'id': sid, 'category': 'canonical', 'scene': scene,
                     'resolution': resolve(scene, target, player), 'known': [], 'player': player})
    cases = [
        ('success', 'successful discovery', 'ledger', 'The ledger records twelve ingots arriving, but only nine entered stock.'),
        ('partial', 'partial discovery', 'cipher', 'Only the first symbol can be read: a crescent. The rest remains illegible.'),
        ('failed', 'failed investigation', 'seal', 'CANARY_UNDISCOVERED opening sequence'),
        ('known', 'previously discovered clue', 'rubbing', 'The rubbing bears the mason\'s mark; its date is unknown.'),
        ('uncertain', 'uncertain evidence', 'fibres', 'The fibres may be wool or flax; their source cannot be determined.'),
        ('mundane', 'mundane observation', 'basin', None),
        ('npc', 'NPC-related evidence', 'receipt', 'The receipt names porter Iven as the recipient, without explaining his involvement.'),
        ('no_clue', 'no significant clue', 'tile', None),
    ]
    for sid, category, target, text in cases:
        scene = synthetic_scene(target, text)
        r = resolve(scene, target)
        known = []
        origin = 'actual exploration resolver on synthetic scene'
        if sid == 'failed':
            # The actual failed-check resolver is separately exercised below.
            r = {**r, 'kind': 'investigate', 'success': False,
                 'discovered_clues': [], 'clue_text': text,
                 'state_changes': {'skill_check_failed': True}}
            origin = 'explicit failed-check outcome fixture; actual failed resolver separately tested'
        if sid == 'known':
            known = [text]
            r = {**r, 'kind': 'already_searched', 'success': False,
                 'discovered_clues': [], 'state_changes': {'already_searched': True}}
            origin = 'explicit repeat-search outcome fixture; actual repeat resolver separately tested'
        rows.append({'id': sid, 'category': category, 'scene': scene, 'resolution': r,
                     'known': known, 'origin': origin, 'player': f'I examine the {target}.'})
    return rows


@pytest.mark.parametrize('case', range(10))
def test_matrix(case):
    row = scenarios()[case]
    original = copy.deepcopy(row)
    view = cr.authorize_investigation(row['resolution'], payload(row['scene'], row['known']))
    fact_text, fact_source = _authoritative_resolution_fact_text(resolution=row['resolution'], scene=row['scene'], world={})
    from game.api import deterministic_provider_skip_line
    from game.immutable_valid_response import safe_nonresolution
    from game.resolution_contract import contract_mapping_from_resolution
    selected = deterministic_provider_skip_line(resolution=row['resolution'], scene=row['scene'],
        world={}, session=default_session(), player_text=row['player'])
    if selected:
        host, source = selected
    elif fact_text:
        host, source = fact_text, fact_source
    else:
        host = safe_nonresolution(contract_mapping_from_resolution(row['resolution']),
                                 resolution=row['resolution'], player_text=row['player'])
        source = 'existing safe_nonresolution; deterministic fallback comparison, not claimed provider skip'
    variants = []
    for style, plan in STYLES.items():
        stub = Stub(plan)
        artifact = cr.preview_investigation(view, stub, enabled=True)
        assert not artifact.used_fallback
        assert stub.calls == 1
        assert all(text in artifact.text for text in view.revealed + view.known)
        assert all(s not in artifact.to_json() + json.dumps(stub.payload) for s in SECRETS)
        assert all(s not in artifact.to_json() + json.dumps(stub.payload)
                   for s in row['scene']['scene'].get('hidden_facts', []))
        audit = validate_generated_response(artifact.text, resolution=row['resolution'])
        assert audit['hard_valid'], audit
        assert cr.validate_plan(json.loads(artifact.to_json())['plan']) == plan
        variants.append({'style': style, 'plan': plan, 'narration': artifact.text,
                         'mechanical_validator': audit,
                         'information_complete': all(x in artifact.text for x in view.revealed + view.known)})
    assert len({v['narration'] for v in variants}) == 3
    assert row == original
    write('scenario_'+row['id'], {**row, 'authorized_view': asdict(view),
        'hidden_information': SECRETS if row['category'] != 'canonical' else row['scene']['scene'].get('hidden_facts', []),
        'selection_payload': stub.payload, 'host_speech': host, 'host_source': source,
        'host_fact_emitter': {'text': fact_text, 'source': fact_source},
        'variants': variants, 'state_unchanged': row == original})


def test_canonical_resolver_clues():
    notice, prints = scenarios()[:2]
    assert notice['resolution']['success'] is True
    assert notice['resolution']['clue_id'] == 'notice_patrol_route'
    assert 'northwest mud track past the crates' in notice['resolution']['clue_text']
    assert prints['resolution']['success'] is True
    assert prints['resolution']['clue_id'] == 'milestone_mud_prints'
    assert 'number, origin, and direction stay unclear' in prints['resolution']['clue_text']


PROHIBITED = ('items_added', 'currency_gained', 'damage_taken', 'health_recovered',
    'conditions_applied', 'destination', 'revealed', 'objectives_completed', 'npc_changes',
    'scene_update', 'world_updates', 'remembered_contextual_leads', 'improvised_details')


@pytest.mark.parametrize('field', PROHIBITED)
@pytest.mark.parametrize('nested', [False, True])
def test_no_proposal_capabilities(field, nested):
    row = scenarios()[2]
    view = cr.authorize_investigation(row['resolution'], payload(row['scene']))
    before = copy.deepcopy((row, view))
    bad = {**STYLES['atmospheric'], field: {'text': 'Your wealth has increased by fifty gold coins.'}}
    if nested:
        bad = {**cr.DEFAULT_PLAN, 'tone': {field: {'scene_update': {'summary': SECRETS[1]}}}}
    stub = Stub(bad)
    output = cr.preview_investigation(view, stub, enabled=True)
    assert output.used_fallback and stub.calls == 1
    assert row['resolution']['clue_text'] in output.text
    assert field not in json.loads(output.to_json())
    assert 'wealth' not in output.to_json() and 'CANARY_' not in output.to_json()
    assert (row, view) == before
    with pytest.raises(ValueError): cr.render_investigation(view, bad)
    write('authority_'+field+('_nested' if nested else ''),
          {'input': bad, 'output': json.loads(output.to_json()), 'state_unchanged': True, 'calls': stub.calls})


INVALID = [None, {}, [], '', 'not json', '{', {'tone': 'spare'},
    {**cr.DEFAULT_PLAN, 'detail': 'unlimited'}, {**cr.DEFAULT_PLAN, 'structure': 'CANARY_DESTINATION'},
    {**cr.DEFAULT_PLAN, 'sensory_focus': ['visual']},
    {**cr.DEFAULT_PLAN, 'detail': True}, {**cr.DEFAULT_PLAN, 'prose': 'Your wounds have healed.'},
    ' '*2049, '{"tone":"spare","tone":"intent"}']


@pytest.mark.parametrize('bad', INVALID)
def test_invalid_plan_falls_back(bad):
    row = scenarios()[0]
    view = cr.authorize_investigation(row['resolution'], payload(row['scene']))
    stub = Stub(bad)
    out = cr.preview_investigation(view, stub, enabled=True)
    assert out.used_fallback and stub.calls == 1
    assert row['resolution']['clue_text'] in out.text
    assert out.text == cr.deterministic_fallback(view)
    write('invalid_'+str(INVALID.index(bad)), {'input': bad, 'output': json.loads(out.to_json()), 'calls': stub.calls})


def test_json_plan_and_mutation_sinks_not_called(monkeypatch):
    from game import api, storage
    calls = []
    def forbidden(*_a, **_kw):
        calls.append(True)
        raise AssertionError('A persistent adoption sink was reached')
    for name in ('remember_recent_contextual_leads', 'promote_accepted_bounded_improvisation',
                 '_validate_gm_scene_update_for_legacy_adoption',
                 '_validate_gm_world_updates_for_legacy_adoption', 'apply_normalized_world_updates'):
        monkeypatch.setattr(api, name, forbidden)
    for name in ('save_session', 'save_world', 'save_character', 'save_scene'):
        if hasattr(storage, name): monkeypatch.setattr(storage, name, forbidden)
    row = scenarios()[0]
    before = copy.deepcopy(row)
    view = cr.authorize_investigation(row['resolution'], payload(row['scene']))
    good = cr.preview_investigation(view, Stub(json.dumps(STYLES['atmospheric'])), enabled=True)
    bad = cr.preview_investigation(view, Stub({**cr.DEFAULT_PLAN, 'world_updates': {'secret': SECRETS[5]}}), enabled=True)
    assert not good.used_fallback and bad.used_fallback
    assert calls == [] and row == before
    assert set(json.loads(bad.to_json())) == {'preview_text', 'plan', 'diagnostic', 'used_fallback'}
    write('mutation_sinks', {'calls': calls, 'state_unchanged': row == before,
        'accepted': json.loads(good.to_json()), 'rejected': json.loads(bad.to_json()),
        'scope': 'No preview is wired into the API; legacy sinks instrumented to fail if called.'})


def test_empty_default_and_transport_failure(monkeypatch):
    row = scenarios()[0]
    view = cr.authorize_investigation(row['resolution'], payload(row['scene']))
    stub = Stub(cr.DEFAULT_PLAN)
    with pytest.raises(ValueError): cr.preview_investigation(view, stub)
    assert stub.calls == 0
    rows = []
    for error in (TimeoutError, RuntimeError, type('CANARY_EXCEPTION_CLASS', (RuntimeError,), {})):
        class Broken:
            calls = 0
            def select(self, _):
                self.calls += 1
                raise error('CANARY_PRIVATE_EXCEPTION')
        broken = Broken()
        out = cr.preview_investigation(view, broken, enabled=True)
        assert out.used_fallback and broken.calls == 1
        assert 'CANARY_' not in out.to_json()
        rows.append({'failure': error.__name__, 'output': json.loads(out.to_json()), 'calls': broken.calls})
    def fail(*_): raise RuntimeError('CANARY_RENDERER_EXCEPTION')
    monkeypatch.setattr(cr, 'render_investigation', fail)
    out = cr.preview_investigation(view, stub, enabled=True)
    assert out.used_fallback and view.revealed[0] in out.text
    rows.append({'failure': 'renderer_exception', 'output': json.loads(out.to_json()), 'calls': stub.calls})
    write('exception_fallbacks', rows)


def test_selector_detached_and_hidden_inputs_absent():
    row = scenarios()[3]
    original = copy.deepcopy(row)
    view = cr.authorize_investigation(row['resolution'], payload(row['scene']))
    class Mutating:
        def select(self, context):
            assert 'CANARY_' not in json.dumps(context)
            context['authorized_investigation']['revealed'] = ['Your wounds have healed.']
            return cr.DEFAULT_PLAN
    out = cr.preview_investigation(view, Mutating(), enabled=True)
    assert 'wounds' not in out.text and row == original
    assert view.revealed[0] in out.text
    # No hidden input even reaches the final renderer: only immutable view + enums.
    assert 'CANARY_' not in json.dumps(asdict(view))
    write('isolation', {'original_private_inputs': row, 'renderer_inputs': asdict(view),
                        'output': json.loads(out.to_json()), 'state_unchanged': True})


def test_actual_failed_and_repeat_resolvers(monkeypatch):
    import game.exploration as exploration
    scene = synthetic_scene('seal', 'CANARY_UNDISCOVERED opening sequence')
    monkeypatch.setattr(exploration, 'should_trigger_check', lambda *_a, **_kw:
                        {'requires_check': True, 'skill': 'investigation', 'difficulty': 18})
    monkeypatch.setattr(exploration, 'resolve_skill_check', lambda *_a, **_kw:
                        {'success': False, 'roll': 2, 'modifier': 0, 'total': 2, 'difficulty': 18})
    failed = resolve(scene, 'seal')
    assert failed['success'] is False
    view = cr.authorize_investigation(failed, payload(scene))
    assert view.revealed == () and view.status == 'failed'
    assert 'CANARY_' not in cr.preview_investigation(view, Stub(STYLES['investigative']), enabled=True).to_json()
    monkeypatch.setattr(exploration, 'should_trigger_check', lambda *_a, **_kw: {'requires_check': False})
    scene = synthetic_scene('seal', 'The wax bears a crescent stamp.')
    session = default_session()
    session['active_scene_id'] = 'unfamiliar_site'
    # Production runtime resolution marker, not a second knowledge store.
    from game.storage import mark_interactable_resolved
    mark_interactable_resolved(session, 'unfamiliar_site', 'seal')
    repeated = resolve_exploration_action(scene, session, default_world(),
        {'id': 'seal', 'type': 'investigate', 'target_id': 'seal', 'prompt': 'I examine the seal.'},
        character=default_character())
    assert repeated['kind'] == 'already_searched'
    known_view = cr.authorize_investigation(repeated, payload(scene, ['The wax bears a crescent stamp.']))
    assert known_view.status == 'known' and known_view.known
    write('actual_failed_repeat', {'failed_resolution': failed, 'failed_view': asdict(view),
                                  'repeat_resolution': repeated, 'repeat_view': asdict(known_view)})


def test_trusted_effects_are_rendered_once():
    row = scenarios()[2]
    r = row['resolution']
    r['state_changes']['damage_taken'] = 2
    before = copy.deepcopy(r)
    view = cr.authorize_investigation(r, payload(row['scene']))
    for plan in STYLES.values():
        out = cr.preview_investigation(view, Stub(plan), enabled=True)
        assert out.text.count('You suffer 2 damage.') == 1
        assert r == before
    # A resolved transition, if supplied by the authoritative investigation
    # result, remains an engine consequence rather than a selectable proposal.
    transitioned = {**r, 'resolved_transition': True, 'target_scene_id': 'courtyard'}
    moved_view = cr.authorize_investigation(transitioned, payload(row['scene']))
    assert 'You arrive at courtyard.' in cr.deterministic_fallback(moved_view)
    with pytest.raises(ValueError): cr.authorize_investigation({'kind': 'travel'}, {})


def test_no_legacy_wiring_or_capabilities():
    # Verify actual imports/references, not just a decorative permissions label.
    source = inspect.getsource(cr)
    import ast
    module = ast.parse(source)
    imports = [n.module for n in ast.walk(module) if isinstance(n, ast.ImportFrom)]
    assert not set(imports) & {'game.storage', 'game.api', 'game.world', 'game.gm', 'game.contextual_leads'}
    for path in (ROOT/'game').glob('*.py'):
        if path.name != 'controlled_investigation_renderer.py':
            assert 'controlled_investigation_renderer' not in path.read_text(encoding='utf-8')
    artifact = cr.InvestigationPreview('text', json.dumps(cr.DEFAULT_PLAN), 'accepted', False)
    serialized = json.loads(artifact.to_json())
    assert set(serialized) == {'preview_text', 'plan', 'diagnostic', 'used_fallback'}
    assert not set(serialized) & {'player_facing_text', 'metadata', 'scene_update', 'world_updates'}


def test_ten_plan_stress_and_performance():
    row = scenarios()[1]
    view = cr.authorize_investigation(row['resolution'], payload(row['scene']))
    plans = list(STYLES.values()) + [
        {**STYLES['atmospheric'], 'structure': 'action_first', 'pace': 'measured'},
        {**STYLES['investigative'], 'perspective': 'close_observation', 'tone': 'reflective'},
        {**STYLES['concise'], 'perspective': 'close_observation', 'detail': 'lean'},
        {**STYLES['atmospheric'], 'sensory_focus': 'listening', 'structure': 'evidence_first'},
        {**STYLES['investigative'], 'sensory_focus': 'visual', 'structure': 'setting_first'},
        {**STYLES['concise'], 'tone': 'intent', 'pace': 'measured', 'detail': 'extended'},
        {**STYLES['atmospheric'], 'perspective': 'second_person', 'transition': 'question', 'tone': 'intent'},
    ]
    assert len({json.dumps(p, sort_keys=True) for p in plans}) == 10
    outputs = [cr.render_investigation(view, p) for p in plans]
    assert len(set(outputs)) == 10
    assert all(view.revealed[0] in text for text in outputs)
    assert all(validate_generated_response(text, resolution=row['resolution'])['hard_valid'] for text in outputs)
    write('stress', [{'plan': p, 'narration': text} for p, text in zip(plans, outputs)])
    def timing(fn):
        samples = []
        for _ in range(500):
            start = time.perf_counter_ns(); fn(); samples.append((time.perf_counter_ns()-start)/1000)
        return {'median_us': statistics.median(samples), 'p95_us': sorted(samples)[474], 'iterations': 500}
    tracemalloc.start()
    start_current, _ = tracemalloc.get_traced_memory()
    for _ in range(100): cr.preview_investigation(view, Stub(plans[1]), enabled=True)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    sizes = {'schema_bytes': len(json.dumps(cr.PLAN_SCHEMA).encode()),
             'plan_bytes': len(json.dumps(plans[1]).encode()),
             'authorized_context_bytes': len(json.dumps(asdict(view)).encode()),
             'full_selection_payload_bytes': len(json.dumps(cr.selection_payload(view)).encode())}
    write('performance', {**sizes,
        'render': timing(lambda: cr.render_investigation(view, plans[1])),
        'validate': timing(lambda: cr.validate_plan(plans[1])),
        'fallback_end_to_end': timing(lambda: cr.preview_investigation(view, Stub({}), enabled=True)),
        'preview_end_to_end': timing(lambda: cr.preview_investigation(view, Stub(plans[1]), enabled=True)),
        'traced_peak_bytes': peak-start_current, 'traced_retained_bytes': current-start_current,
        'estimated_input_tokens_bytes_div_4': sizes['full_selection_payload_bytes']/4,
        'estimated_output_tokens_bytes_div_4': sizes['plan_bytes']/4,
        'cost_method': 'Rough UTF-8 bytes/4 estimate; not measured tokenizer usage or live billing.',
        'latency_method': 'Sequential local Python wall time, warm process; not a deployment guarantee.'})
    write('schema', cr.PLAN_SCHEMA)
