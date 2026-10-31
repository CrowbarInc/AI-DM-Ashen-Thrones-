from pathlib import Path
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from tools.validation_evidence import build_packet, write_packet
out=Path('artifacts/atgb/atgb_r1_02')
t=json.loads((out/'s08_2_trace.json').read_text())
examples=[]
for i,row in enumerate(t['rows']):
 examples.append({'example_id':f's08_2_{row["stub_purpose"].lower()}', 'scenario_run_id':f'S08.2-{row["stub_purpose"]}-stub',
 'turn_index':2,'player_input':t['historical_input'],'player_input_classification':['representative_player_behavior','boundary_case'],
 'simulated_player_rationale':'Frozen related variation replayed at the interpretation-to-orchestration seam; no simulated model output.',
 'prior_player_context':t['prior_input'],'prior_gm_context':t['prior_response'],
 'exact_gm_output':row['after']['player_facing_text'],'historical_result':'Original trial interpretation FAIL / response FAIL / authority PASS (provisional AI assessment, not authenticated human review).',
 'semantic_result':'FAIL','mandatory_gates':{'routing':{'status':'PASS'},'conversational_adequacy':{'status':'FAIL'}},
 'diagnostic_result':{'routing_correctness':'PASS','production_adequacy':'NOT EVALUABLE'},
 'automated_evaluation':{'method':'Exact deterministic route/fallback assertions; no playability evaluator or ATGB scorer invoked.'},
 'runtime_validity':'VALID deterministic response-plan execution; not live API replay',
 'final_emission_metadata':{'boundary':'response plan','live_provider':False},'continuation_action':'Stop at downstream fallback; no additional repair.',
 'source_artifact_path':'artifacts/atgb/atgb_r1_02/s08_2_trace.json',
 'human_review':{'status':'UNREVIEWED','rationale':'External review pending; no authenticated human judgment.'},
 'evaluator_disagreement_history':[], 'calibration_reference':None})
packet=build_packet(campaign={'campaign_id':'atgb_r1_02','what_was_tested':'Mechanical revision entry and downstream S08.2 response plan under two explicit empty-evidence stubs.',
 'runtime_path':'decision_from_interpretation_record -> _communication_decision -> revision gate -> ordinary public-evidence answering',
 'gm_boundary':'Host response plan; interpretation stubbed, no live provider, no expression.',
 'player_input_mode':'Preserved ATGB related-variation sentence; purposes DESCRIPTION and CORRECTION are controlled stubs.',
 'run_count':2,'turn_count':2,'automated_conclusion':'Routing PASS; stub response adequacy FAIL; production adequacy NOT EVALUABLE.'},
 claim_types=['structural_evidence','runtime_evidence'],examples=examples,missing_concepts=[{'name':'Downstream contextual response sufficiency','evidence':'Two empty-evidence stubs return the established-information fallback.','status':'Observed empty-evidence fallback; deferred outside scope.'}],
 limitations=['Raw historical interpretation/evidence refs unavailable.','These are related variations, not unseen generalization.','No ATGB performance result or broad semantic success claim.','Both fallback outputs fail the people-description request; no successful response is fabricated.'],evidence_scope='deterministic_response_plan')
write_packet(Path('artifacts/validation_evidence/atgb_r1_02'),packet)
print('Evidence packet written and schema validated.')

