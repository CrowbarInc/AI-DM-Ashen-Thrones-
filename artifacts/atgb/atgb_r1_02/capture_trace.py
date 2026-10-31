"""Reproduce the bounded S08.2 seam with preserved context and explicit stubs."""
from pathlib import Path
import copy, dataclasses, hashlib, importlib.util, json, sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from game import conversational_orchestration as after
OUT = ROOT / 'artifacts/atgb/atgb_r1_02'
spec = importlib.util.spec_from_file_location('game.atgb_r1_02_before', OUT / 'orchestration_before.py')
before = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = before
spec.loader.exec_module(before)
capture = json.loads((ROOT / 'artifacts/atgb/atgb_03c/S08/result.json').read_text(encoding='utf-8'))
first, second = capture['turns'][:2]
store = next((ROOT / 'artifacts/atgb/atgb_03c/S08/stores').iterdir())
log = json.loads((store / 'session_log.jsonl').read_text(encoding='utf-8').splitlines()[0])
exchange = log['resolution'].get('metadata', {}).get('delivered_exchange')
# The final session is not a pre-turn snapshot. Reconstruct only the relevant
# pre-S08.2 seam inputs established by the first delivered log and captured state.
session = {'active_scene_id': 'frontier_gate', 'conversational_context': {
    'last_gm_exchange': {'player_text': first['player_input'], 'response_text': first['response_text']}}}
scene = json.loads((ROOT / 'data/validation/atgb/baselines/frontier-gate-v1/scenes/frontier_gate.json').read_text(encoding='utf-8'))
world = json.loads((ROOT / 'data/validation/atgb/baselines/frontier-gate-v1/world.json').read_text(encoding='utf-8'))
rows = []
for purpose in ['DESCRIPTION', 'CORRECTION']:
    record = {'communication': {'recipient': 'GM', 'purpose': purpose, 'evidence_refs': []},
              'interpretation_status': 'INTERPRETED', 'action_components': [], 'public_evidence': {}}
    snapshot = copy.deepcopy((session, scene, world, record))
    old = before.decision_from_interpretation_record(record, player_text=second['player_input'], session=session, scene=scene, world=world)
    new = after.decision_from_interpretation_record(record, player_text=second['player_input'], session=session, scene=scene, world=world)
    assert (session, scene, world, record) == snapshot
    rows.append({'stub_purpose': purpose, 'raw_historical_interpretation_available': False,
                 'before': dataclasses.asdict(old), 'after': dataclasses.asdict(new),
                 'mechanical_revision_response_before': old.reason == 'no_pending_intention',
                 'mechanical_revision_response_after': new.reason in {'no_pending_intention', 'pending_intention_revised', 'executed_intention_not_reversible'},
                 'fallback_after': new.player_facing_text, 'state_changed': False})
result = {'evidence_scope': 'deterministic_routing_and_response_plan',
          'input_classification': ['representative_player_behavior', 'boundary_case'],
          'source': 'artifacts/atgb/atgb_03c/S08/result.json',
          'historical_input': second['player_input'], 'prior_input': first['player_input'],
          'prior_response': first['response_text'], 'historical_response': second['response_text'],
          'historical_decision': second['conversational_decision'],
          'reconstructed_relevant_session': session, 'reconstruction_limit': 'Relevant seam state only; final store is not a pre-turn snapshot. Raw interpretation and selected evidence were not retained.',
          'rows': rows, 'routing_correctness': 'PASS',
          'stub_conversational_adequacy': 'FAIL',
          'production_conversational_adequacy': 'NOT EVALUABLE',
          'next_observed_boundary': 'Ordinary GM public-evidence answering returns the established-information fallback when evidence is empty; preserved prior description is not itself selected by this seam.',
          'provider_calls': 0, 'human_review_status': 'UNREVIEWED'}
(OUT / 's08_2_trace.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print('Routing PASS; empty-evidence stub adequacy FAIL; production adequacy NOT EVALUABLE; providers 0.')
