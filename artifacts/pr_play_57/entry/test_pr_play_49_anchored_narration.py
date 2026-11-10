"""Offline authored examples, not recorded provider output; no gameplay wiring."""
import ast
import copy
from dataclasses import FrozenInstanceError, asdict
import inspect
import json
from pathlib import Path
import statistics
import time
import tracemalloc

import pytest

from game import anchored_investigation_narration as ar
from game import controlled_investigation_renderer as cr
from game.immutable_valid_response import validate_generated_response
from game.resolution_contract import contract_mapping_from_resolution
from tests.test_pr_play_47_controlled_renderer import (
    payload, resolve, synthetic_scene, scenarios, STYLES,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/pr_play_49'
SECRETS = ['UNSEEN_CLUE_K42', 'PRIVATE_GM_NOTE_K42', 'NPC_MOTIVE_K42',
           'HIDDEN_DESTINATION_K42', 'PRIVATE_WORLD_K42', 'QUEST_TWIST_K42']


def write(name, value):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / ('evidence_' + name + '.json')).write_text(
        json.dumps(value, indent=2) + '\n', encoding='utf-8')


class Stub:
    def __init__(self, text):
        self.text, self.calls, self.request = text, 0, None

    def generate(self, request):
        self.calls += 1
        self.request = copy.deepcopy(request)
        return copy.deepcopy(self.text)


def fixtures():
    rows = scenarios()[:2]
    specs = [
        ('ledger', 'success', 'The ledger records twelve ingots arriving, but only nine entered stock.'),
        ('bridge', 'partial', 'One support bears fresh scoring; its cause cannot be determined.'),
        ('chamber', 'failed', 'The concealed release lies behind the lintel.'),
        ('testimony', 'known', 'The testimony places the ferryman at the quay; the time is unknown.'),
        ('monument', 'mundane', None),
        ('campsite', 'multiple', 'The ashes contain fragments of blue cloth.'),
    ]
    for target, category, text in specs:
        scene = synthetic_scene(target, text)
        scene['scene'].update(hidden_facts=[SECRETS[3]], gm_notes=[SECRETS[1]],
                              npcs=[{'hidden_motivation': SECRETS[2]}])
        scene['scene']['discoverable_clues'].append({'id': SECRETS[0], 'text': SECRETS[0]})
        r = resolve(scene, target)
        known = []
        origin = 'actual resolver on synthetic scene'
        if category == 'failed':
            r = {**r, 'kind': 'investigate', 'success': False,
                 'discovered_clues': [], 'state_changes': {'skill_check_failed': True}}
            origin = 'explicit failed-check fixture; actual failed resolver independently tested'
        if category == 'known':
            known = [text]
            r = {**r, 'kind': 'already_searched', 'success': False,
                 'discovered_clues': [], 'state_changes': {'already_searched': True}}
            origin = 'explicit repeat fixture; actual repeat resolver independently tested'
        if category == 'multiple':
            r['discovered_clues'] = [text, 'A boot impression ends at the edge of the ash; its owner is unknown.']
            origin = 'actual single-clue resolver plus explicit multi-disclosure outcome fixture'
        rows.append({'id': target, 'category': category, 'scene': scene,
                     'resolution': r, 'known': known, 'origin': origin,
                     'player': f'I examine the {target}.'})
    return rows


def contract(row=None):
    row = row or fixtures()[0]
    p = payload(row['scene'], row['known'])
    p.update(world={'private': SECRETS[4]}, unexpected={
        'nested': {'public': {'summary': SECRETS[5]}}, SECRETS[0]: SECRETS[1]})
    return ar.authorize_anchored_investigation(row['resolution'], p)


# Distinct rhetorical structures; authored offline by the implementing agent.
# Family assignments are editorial judgments, not an automated uniqueness metric.
PRELUDES = [
    ('concise', 'single direct action', 'You lean closer to read the notice board.'),
    ('atmospheric', 'setting to focal narrowing',
     'Rain patters around the gate. Against that restless background, the posted notices hold your attention, one line at a time.'),
    ('tense', 'fragment then delayed release',
     'A crowded board. Too much to take in at once. You slow down and read.'),
    ('observational', 'parallel enumeration',
     'First the taxes, then the curfew rules, then the patrol warning: your gaze follows the notices across the board.'),
    ('methodical', 'procedural progression',
     'You work from the top of the board downward, reading each notice before moving to the next. At the patrol warning, you stop to read more carefully.'),
    ('character_focused', 'gesture framing attention',
     'You fold your arms, lean back, and then bend toward the writing again. This time you give the patrol notice your full attention.'),
    ('sensory', 'auditory contrast',
     'Behind you, the gate crowd murmurs and shifts. You let the sound recede as you attend to the words before you.'),
    ('reflective', 'reflection followed by action',
     'A hurried glance is easy; careful reading takes patience. You return to the patrol warning and read it slowly.'),
    ('fast_paced', 'staccato action sequence',
     'Taxes. Curfew. The patrol warning. You scan, stop, and read again.'),
    ('understated', 'negative emphasis then quiet turn',
     'There is no flourish to the examination. You simply take the time to read the patrol notice through.'),
]


@pytest.mark.parametrize('index', range(8))
def test_fixture_anchors(index):
    row = fixtures()[index]
    before = copy.deepcopy(row)
    c = contract(row)
    prelude = 'You look closely, taking time over the examination.'
    stub = Stub(prelude)
    out = ar.preview_anchored_investigation(c, stub, enabled=True)
    assert not out.used_fallback, out
    assert row == before and stub.calls == 1
    assert all(out.preview_text.count(a.text) == 1 for a in c.anchors)
    assert [out.preview_text.index(a.text) for a in c.anchors] == sorted(
        out.preview_text.index(a.text) for a in c.anchors)
    assert all(s not in json.dumps(stub.request) + out.to_json() for s in SECRETS)
    from game.api_turn_support import _authoritative_resolution_fact_text
    host, source = _authoritative_resolution_fact_text(
        resolution=row['resolution'], scene=row['scene'], world={})
    if not host:
        from game.immutable_valid_response import safe_nonresolution
        host = safe_nonresolution(contract_mapping_from_resolution(row['resolution']),
                                  resolution=row['resolution'], player_text=row['player'])
        source = 'existing safe_nonresolution'
    write('fixture_' + row['id'], {**row, 'hidden_information': SECRETS,
          'authoritative_projection': asdict(c), 'prelude_request': stub.request,
          'candidate_prelude': prelude, 'final_response': asdict(out),
          'fallback': ar.fallback(c), 'state_unchanged': row == before,
          'host': {'text': host, 'source': source},
          'controlled': cr.render_investigation(c.outcome, STYLES['atmospheric'])})


def test_canonical_source_and_uncertainty():
    notice, prints = fixtures()[:2]
    n, p = contract(notice), contract(prints)
    assert n.anchors[0].text == 'The missing patrol was last seen taking the northwest mud track past the crates.'
    assert 'number, origin, and direction stay unclear' in p.anchors[0].text
    # Saved PR43 engine results are the historical source; fresh resolver outputs
    # above verify that the current mechanics still authorize these same texts.
    live = json.loads((ROOT/'artifacts/pr_play_43/live_result.json').read_text())
    saved = []
    for turn in live['turns']:
        if turn['player_input'] in (notice['player'], prints['player']):
            assert turn['engine']['discovered_clues'][0] in (n.anchors[0].text, p.anchors[0].text)
            saved.append(turn)
    assert len(saved) == 2
    write('canonical_saved_resolvers', saved)
    for prelude in ['You crouch and examine the impressions carefully.',
                    'The mud holds your attention as you look more closely.',
                    'You pause before drawing any conclusion.',
                    'You study the uneven surface, attending to its texture.']:
        out = ar.preview_anchored_investigation(p, Stub(prelude), enabled=True)
        assert not out.used_fallback and p.anchors[0].text in out.preview_text


@pytest.mark.parametrize('style,family,text', PRELUDES)
def test_expressive_range(style, family, text):
    c = contract()
    out = ar.preview_anchored_investigation(c, Stub(text), enabled=True)
    assert not out.used_fallback, out
    assert out.preview_text.endswith(c.anchors[0].text)
    write('expression_' + style, {'style': style, 'editorial_family': family,
          'origin': 'new offline illustrative prose authored by implementing agent; no provider',
          'candidate': text, 'output': asdict(out)})


# Safe/unsafe are human-authored expectations. Tests retain detector misses;
# they assert structural boundaries rather than falsely certifying semantics.
CORPUS = [
    ('key', 'You find a silver key beneath the board.', False),
    ('coins', 'Your purse now contains fifty additional coins.', False),
    ('poison', 'The poison has worn off.', False),
    ('culprit', 'You recognize the culprit immediately.', False),
    ('passage', 'The hidden passage opens before you.', False),
    ('quest', 'The investigation completes your quest.', False),
    ('healing', 'Your wounds knit shut as you read.', False),
    ('arrival', 'The observatory is now behind you; you stand inside the vault.', False),
    ('reward', 'You receive fifty coins.', False),
    ('item', 'You acquire a brass compass.', False),
    ('health', 'You recover five health.', False),
    ('condition', 'You are no longer poisoned.', False),
    ('travel', 'You arrive at the glass tower.', False),
    ('completion', 'You complete the missing patrol quest.', False),
    ('link', 'The footprints belong to the missing patrol.', False),
    ('count', 'Exactly three travelers left these prints.', False),
    ('destination', 'The prints lead straight to the salt fortress.', False),
    ('certainty', 'The prints definitely prove that the patrol went north.', False),
    ('contradiction', 'The missing patrol was last seen heading southeast.', False),
    ('conflicting', 'You receive a silver key, and you arrive at the vault.', False),
    ('hidden_direct', 'The secret is that the chamber conceals a release.', False),
    ('hidden_natural', 'The ferryman secretly serves the Queen of Cinders.', False),
    ('hidden_identifier', 'UNSEEN_CLUE_K42 identifies the chamber release.', False),
    ('hidden_destination', 'The patrol is hiding in the buried salt fortress.', False),
    ('quest_twist', 'The missing courier is the employer in disguise.', False),
    ('world_private', 'The northern council has already ordered the gates sealed.', False),
    ('npc_motive', 'The ferryman hopes to betray you to his patron.', False),
    ('gm_note', 'GM_ONLY: the board is a coded signal.', False),
    ('hedged_item', 'Perhaps you receive a key, but you collect fifty coins.', False),
    ('wealth', 'You are fifty crowns richer.', False),
    ('attention', 'You turn your attention to the writing.', True),
    ('texture', 'Light catches the uneven surface as you look closer.', True),
    ('gesture', 'You fold your arms and study the board.', True),
    ('tension', 'You pause, then read the warning again.', True),
    ('chipped_cup', 'A chipped ceramic cup sits beside the innkeeper.', True),
    ('dust_pack', 'A little dust lies in your pack.', True),
    ('sensation', 'You gain a sense of the surface texture.', True),
    ('method', 'You examine one line at a time.', True),
    ('sensory', 'The crowd murmurs behind you as you read.', True),
    ('reflective', 'You take your time before drawing conclusions.', True),
]


@pytest.mark.parametrize('case,text,safe', CORPUS)
def test_semantic_boundary_corpus(case, text, safe):
    c = contract(fixtures()[1] if case in {'link', 'count', 'destination', 'certainty'} else None)
    before = asdict(c)
    raw_audit = validate_generated_response(text, resolution=_audit_resolution(c),
            contract=contract_mapping_from_resolution(_audit_resolution(c)))
    stub = Stub(text)
    out = ar.preview_anchored_investigation(c, stub, enabled=True)
    assert asdict(c) == before and stub.calls == 1
    assert all(a.text in out.preview_text for a in c.anchors)
    assert out.review_required is True
    # These are analysis artifacts, never approved player-facing outputs. Unsafe
    # misses are preserved verbatim for review, not hidden behind pass counts.
    write('corpus_' + case, {'case': case, 'candidate': text, 'expected_safe': safe,
          'expected_basis': 'authored semantic label; cup compatible only in separate inn scene',
          'raw_existing_validator': raw_audit, 'output': asdict(out),
          'false_accept': not safe and not out.used_fallback,
          'false_reject': safe and out.used_fallback, 'state_unchanged': True})


def _audit_resolution(c):
    return {'kind': 'investigate', 'success': c.outcome.success,
            'discovered_clues': list(c.outcome.revealed), 'state_changes': {}}


INVALID = [None, {}, [], True, 7, '', ' ', 'not a complete sentence',
           {'prelude': 'You look closely.', 'metadata': {'secret': SECRETS}},
           {'text': 'You look closely.', 'scene_update': {}},
           '{"prelude":"You look closely."}', 'x' * 1601, 'You look.\x00']


@pytest.mark.parametrize('raw', INVALID)
def test_malformed_and_oversized(raw):
    c = contract()
    stub = Stub(raw)
    out = ar.preview_anchored_investigation(c, stub, enabled=True)
    assert out.used_fallback and out.preview_text == ar.fallback(c)
    assert stub.calls == 1 and all(s not in out.to_json() for s in SECRETS)
    write('invalid_' + str(INVALID.index(raw)), {'input': raw, 'output': asdict(out)})


def test_opt_in_detachment_immutability_duplicate_and_sinks(monkeypatch):
    from game import api, gm, storage, world, bounded_improvisation
    c = contract()
    stub = Stub('You look closely.')
    with pytest.raises(ValueError): ar.preview_anchored_investigation(c, stub)
    assert stub.calls == 0
    with pytest.raises(FrozenInstanceError): c.anchors[0].text = 'Changed.'
    with pytest.raises(FrozenInstanceError): c.outcome.status = 'Changed'
    calls = []
    def forbidden(*args, **kwargs):
        calls.append(True)
        raise AssertionError('State adoption attempted')
    targets = {
        api: ['_apply_post_gm_updates', 'remember_recent_contextual_leads',
              'promote_accepted_bounded_improvisation',
              '_validate_gm_scene_update_for_legacy_adoption',
              '_validate_gm_world_updates_for_legacy_adoption', 'apply_normalized_world_updates'],
        gm: ['remember_recent_contextual_leads'],
        world: ['apply_resolution_world_updates', 'apply_normalized_world_updates'],
        storage: ['save_session', 'save_world', 'save_character', 'save_scene'],
        bounded_improvisation: ['promote_accepted_bounded_improvisation'],
    }
    patched = []
    for module, names in targets.items():
        for name in names:
            if hasattr(module, name):
                monkeypatch.setattr(module, name, forbidden)
                patched.append(module.__name__ + '.' + name)
    class Mutating:
        def generate(self, request):
            request['authorized_investigation']['newly_discovered'][:] = ['You receive a key.']
            request['public_scene']['observations'].append(SECRETS[0])
            return 'You look closely.'
    out = ar.preview_anchored_investigation(c, Mutating(), enabled=True)
    assert not out.used_fallback and 'key' not in out.preview_text
    dup = ar.preview_anchored_investigation(c, Stub(c.anchors[0].text), enabled=True)
    assert dup.used_fallback and dup.preview_text.count(c.anchors[0].text) == 1
    assert calls == [] and SECRETS[0] not in json.dumps(ar.prelude_request(c))
    write('isolation', {'patched_sinks': patched, 'sink_calls': calls,
          'detached_mutation_output': asdict(out), 'duplicate_output': asdict(dup),
          'no_state_handles_or_gameplay_adapter': True})


@pytest.mark.parametrize('error', [TimeoutError, RuntimeError, ValueError])
def test_failure_and_render_exception(error, monkeypatch):
    c = contract()
    class Broken:
        calls = 0
        def generate(self, request):
            self.calls += 1
            raise error(SECRETS[1])
    stub = Broken()
    out = ar.preview_anchored_investigation(c, stub, enabled=True)
    assert out.used_fallback and stub.calls == 1 and SECRETS[1] not in out.to_json()
    def fail(*args): raise RuntimeError(SECRETS[1])
    monkeypatch.setattr(ar, 'assemble', fail)
    rendered = ar.preview_anchored_investigation(c, Stub('You look closely.'), enabled=True)
    assert rendered.used_fallback and c.anchors[0].text in rendered.preview_text
    write('failure_' + error.__name__, {'generator': asdict(out), 'renderer': asdict(rendered), 'calls': stub.calls})


def test_no_gameplay_wiring_or_effects():
    source = inspect.getsource(ar)
    imports = [n.module for n in ast.walk(ast.parse(source)) if isinstance(n, ast.ImportFrom)]
    assert not set(imports) & {'game.api', 'game.gm', 'game.storage', 'game.world', 'openai'}
    # PR-PLAY-52 may name this module from the opt-in quarantine adapter only.
    # The player-facing pipeline still must not import it directly.
    allowed = {'anchored_investigation_narration.py', 'quarantined_investigation_narration.py'}
    for p in (ROOT/'game').glob('*.py'):
        if p.name not in allowed:
            assert 'anchored_investigation_narration' not in p.read_text(encoding='utf-8'), p.name
    api_source = (ROOT/'game'/'api.py').read_text(encoding='utf-8')
    assert 'anchored_investigation_narration' not in api_source
    assert 'ASHEN_QUARANTINE_INVESTIGATION_NARRATION' in api_source
    assert '= observe_completed_investigation' not in api_source
    assert '= _observe_quarantined_investigation_narration' not in api_source
    for field in ('items_added', 'currency_gained', 'damage_taken', 'health_recovered',
                  'conditions_applied', 'objectives_completed', 'npc_changes'):
        r = copy.deepcopy(fixtures()[0]['resolution'])
        r['state_changes'][field] = ['unsupported']
        with pytest.raises(ValueError): ar.authorize_anchored_investigation(r, {})
    # No unknown metadata or nested hidden identifiers survive the final allowlist.
    request = ar.prelude_request(contract())
    assert set(request) == {'authorized_investigation', 'public_scene',
                            'descriptive_constraints', 'max_output_utf8_bytes'}
    assert all(s not in json.dumps(request) for s in SECRETS)
    write('input_boundary', request)


def test_actual_failed_and_known_resolvers(monkeypatch):
    import game.exploration as exploration
    from game.defaults import default_session, default_world, default_character
    from game.storage import mark_interactable_resolved
    scene = synthetic_scene('chamber', 'UNSEEN_CLUE_K42')
    monkeypatch.setattr(exploration, 'should_trigger_check', lambda *a, **kw:
                        {'requires_check': True, 'skill': 'investigation', 'difficulty': 18})
    monkeypatch.setattr(exploration, 'resolve_skill_check', lambda *a, **kw:
                        {'success': False, 'roll': 2, 'total': 2, 'modifier': 0, 'difficulty': 18})
    failed = resolve(scene, 'chamber')
    c = ar.authorize_anchored_investigation(failed, payload(scene))
    assert c.outcome.status == 'failed' and not c.outcome.revealed
    assert 'UNSEEN' not in ar.fallback(c)
    monkeypatch.setattr(exploration, 'should_trigger_check', lambda *a, **kw: {'requires_check': False})
    scene = synthetic_scene('testimony', 'The signature is faded.')
    session = default_session()
    session['active_scene_id'] = 'unfamiliar_site'
    mark_interactable_resolved(session, 'unfamiliar_site', 'testimony')
    repeated = exploration.resolve_exploration_action(scene, session, default_world(),
        {'id': 'testimony', 'type': 'investigate', 'target_id': 'testimony',
         'prompt': 'I examine the testimony.'}, character=default_character())
    k = ar.authorize_anchored_investigation(repeated, payload(scene, ['The signature is faded.']))
    assert k.outcome.status == 'known' and not k.outcome.revealed
    assert 'The signature is faded.' in ar.fallback(k)
    write('actual_failed_known', {'failed': failed, 'failed_contract': asdict(c),
                                'repeated': repeated, 'known_contract': asdict(k)})


def test_performance_and_incidental_boundary():
    c = contract()
    text = PRELUDES[1][2]
    measures = {}
    for name, fn in [('validation', lambda: ar.validate_prelude(c, text)),
                     ('assembly', lambda: ar.assemble(c, text)),
                     ('fallback', lambda: ar.fallback(c)),
                     ('preview', lambda: ar.preview_anchored_investigation(c, Stub(text), enabled=True))]:
        fn()
        durations = []
        for _ in range(100):
            start = time.perf_counter_ns()
            fn()
            durations.append((time.perf_counter_ns() - start)/1e6)
        measures[name] = {'median_ms': statistics.median(durations), 'max_ms': max(durations), 'samples': 100}
    tracemalloc.start()
    for _ in range(10): ar.preview_anchored_investigation(c, Stub(text), enabled=True)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    request = json.dumps(ar.prelude_request(c))
    write('performance', {'latencies': measures, 'request_bytes': len(request.encode()),
          'authorized_context_bytes': len(json.dumps(asdict(c.outcome)).encode()),
          'prelude_input_bytes': len(request.encode()), 'prelude_output_bytes': len(text.encode()),
          'anchor_bytes': sum(len(a.text.encode()) for a in c.anchors),
          'traced_current_bytes': current, 'traced_peak_bytes': peak,
          'future_content_token_estimate_chars_div_4': len(request)/4 + len(text)/4,
          'estimate_not_provider_measurement': True})
    # A separate compatible inn scene: the cup remains just preview text.
    scene = synthetic_scene('receipt', 'The receipt bears a smudged date.')
    scene['scene']['visible_facts'] = ['The innkeeper stands beside a table.']
    view = ar.authorize_anchored_investigation(resolve(scene, 'receipt'), payload(scene))
    before = copy.deepcopy(scene)
    out = ar.preview_anchored_investigation(view,
        Stub('A chipped ceramic cup sits beside the innkeeper.'), enabled=True)
    assert not out.used_fallback and scene == before
    assert not any(k in json.loads(out.to_json()) for k in ('items_added', 'scene_update', 'world_updates', 'memory'))
    write('incidental', {'output': asdict(out), 'scene_unchanged': scene == before,
          'policy': 'A later interaction requires engine admission and an authorized mundane interaction or inventory resolver. Mention alone grants no object, ownership, properties or memory. No continuity machinery implemented.'})


def test_shared_projection_preserves_controlled_outputs_and_fixed_comparator():
    saved = json.loads((ROOT/'artifacts/pr_play_47/evidence_stress.json').read_text())
    notice, prints = contract(), contract(fixtures()[1])
    for row in saved:
        assert cr.render_investigation(prints.outcome, row['plan']) == row['narration']
    write('controlled_fixed_comparator', [{
        'plan': row['plan'], 'narration': cr.render_investigation(notice.outcome, row['plan']),
        'family': row['plan']['structure'],
    } for row in saved])
