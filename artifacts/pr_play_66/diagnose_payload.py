"""Offline-only full-body leak diagnosis after critical experimental stop."""
import json,hashlib
from pathlib import Path
OUT=Path('artifacts/pr_play_66')
def read(n):return json.loads((OUT/n).read_text(encoding='utf-8'))
def save(n,v):(OUT/n).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
canaries=['CANARY_HIDDEN_DESTINATION','CANARY_UNDISCOVERED_CLUE','CANARY_GM_NOTE','CANARY_NPC_MOTIVE']
def paths(value,path=''):
    result=[]
    if isinstance(value,dict):
        for k,v in value.items():result+=paths(v,path+'/'+k)
    elif isinstance(value,list):
        for j,v in enumerate(value):result+=paths(v,path+'/'+str(j))
    elif isinstance(value,str):
        for c in canaries:
            if c in value:result.append(dict(path=path,canary=c,value=value if len(value)<200 else value[:200]))
    return result
matrix=read('publication_matrix.json');cases=[dict(name=r['name'],status=r['status'],leaks=paths(r.get('body',{}))) for r in matrix]
before=read('baseline_reproduction.json');disabled=next(r for r in matrix if r['name']=='flag_disabled');tcp=read('http_gameplay.json');controls=read('disabled_sequence_controls.json')
incident=dict(verdict='C — FAIL / CRITICAL DEFECT',classification='implementation',scope='Existing final HTTP payload visibility projection, separate from repaired mandatory-text selection',
    finding='Hidden canary values survive in server-serialized JSON outside gm_output.player_facing_text. Hidden information is therefore published even when the narration correctly excludes it.',
    paths=paths(next(r for r in matrix if r['name']=='accepted')['body']),baseline_before_repair=paths(before['body']),flag_disabled=paths(disabled['body']),
    source_evidence=dict(module='game/state_channels.py',functions=['_AUTHOR_EXACT_KEYS','is_author_key','_deep_project','deep_project_public_payload'],reason='Unknown keys are public. gm_notes, gm_only, private_notes and discoverable_clues are not removed by existing author-key rules. API projects the whole state-bearing response recursively by key without leaf visibility policy.'),
    baseline_leak_present=bool(paths(before['body'])),flag_disabled_leak_present=bool(paths(disabled['body'])),
    matrix_responses_with_hidden_canaries=sum(bool(r['leaks']) for r in cases),matrix_cases=cases,
    tcp_actions_with_hidden_canaries=sum(bool(paths(r['body'])) for r in tcp),disabled_controls_with_hidden_canaries=sum(bool(paths(r['body'])) for r in controls),
    stop=dict(experimental_execution='STOPPED',live_provider_requests=0,server='TCP server was already shut down after capture',flags='Default off, no persistent/global environment enablement; isolated test process interrupted',second_regression='Interrupted after discovery; no further HTTP/provider execution',followup='Safe offline diagnosis and evidence packaging only'),
    repair_scope='No post-holdout source change; do not silently expand mandatory-publication repair into a general state payload projection redesign.',
    next_step='Repair hidden-information leakage in the final gameplay HTTP payload projection before resuming experimental publication.')
save('critical_incident.json',incident)
reg=read('regression_summary_initial.json');reg['focused']['new_failures_status']={'static_assertion':'Updated for expressly authorized PR66 publication integration; targeted diagnostic passes','malformed_500':'Did not reproduce in 20-case diagnostic; initial cause unclassified. Full rerun interrupted on independently discovered hidden payload leakage.'};reg['followup_diagnostic']=dict(passed=20,deselected=105,source='regression_diagnosis.xml');reg['second_run']=dict(status='interrupted_on_critical_hidden_payload_leak',source='focused_final.txt',full_result_available=False);save('regression_summary_final.json',reg)
print({k:incident[k] for k in ['baseline_leak_present','flag_disabled_leak_present','matrix_responses_with_hidden_canaries','tcp_actions_with_hidden_canaries','disabled_controls_with_hidden_canaries']})
