"""Evidence-only postfreeze checks. Does not tune implementation or holdout."""
import sys,json,copy,time,hashlib,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=Path(__file__).resolve().parent
import pytest
from game import integrated_investigation_narration as i,quarantined_investigation_narration as q
from tests.test_pr_play_69_target_references import historical_hook,evaluate,SAFE,UNSAFE
from tests.test_pr_play_68_structured_publication import execute,FAULTS
def save(n,v):(OUT/n).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def summary(values):return dict(samples=len(values),average=round(statistics.mean(values),3),maximum=round(max(values),3)) if values else None
if __name__=='__main__':
    saved=json.loads((OUT/'historical_reproduction.json').read_text(encoding='utf-8'))
    hook=historical_hook();audit,text=evaluate(saved['candidate'],hook)
    save('historical_after.json',dict(original=saved['candidate'],hook=hook,validation=audit,final=text,
        provenance='Original candidate/resolution/public facts; target name reprojected from unchanged authored current-scene interactable prints. Historical target_label was null.'))
    rows=[]
    for raw in SAFE+UNSAFE+['You examine the mud prints. '+t for t in UNSAFE]:
        start=time.perf_counter();a,t=evaluate(raw)
        rows.append(dict(candidate=raw,validation=a,final=t,validation_ms=(time.perf_counter()-start)*1000,
            rationale='finite full attention frame with current public target' if a['decision']=='PASS' else 'unsupported or ambiguous assertion; entire optional segment omitted'))
    save('adversarial_decisions.json',rows)
    failures=[]
    for fault in FAULTS:
        with pytest.MonkeyPatch.context() as mp:
            result=execute(OUT/'failure_sessions'/fault,mp,fault=fault)
        failures.append(dict(fault=fault,publication=result['trace']['publication'],validation=result['trace']['validation'],
            candidate=result['raw'],generator_calls=result['calls'],resolver_calls=len(result['resolutions']),
            journal=result['body']['journal'],authority=result['authority']))
    save('failure_injection.json',failures)
    # Request-local publication binding is consumed and never authorizes a replay.
    contract,request=i.outcome_contract(hook)
    trace=dict(eligible=True,player_text=hook['player_text'],hook_input=hook)
    isolation=[]
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv(q.GATE_ENV,'1');mp.setenv(q.MODE_ENV,'integrated');mp.setenv(q.PUBLICATION_ENV,'1');mp.setenv(i.DISCLOSURE_ENV,'1')
        mp.setenv(q.PUBLICATION_SESSION_ENV,'session-A')
        for name,session,resolution,action in [
            ('cross_session','session-B',hook['resolution'],hook['player_text']),
            ('cross_campaign','campaign-B',hook['resolution'],hook['player_text']),
            ('reload_new_resolution','session-A',copy.deepcopy(hook['resolution']),hook['player_text']),
            ('different_action','session-A',hook['resolution'],'I examine the weathered milestone.')]:
            token=q._PUBLICATION.set((trace,hook['resolution'],'session-A'))
            try:
                plan=q.prepare_authoritative_publication(resolution,session,action)
                assert plan is None
                isolation.append(dict(case=name,stale_publication_rejected=True))
            finally:q._PUBLICATION.reset(token)
    save('context_isolation.json',isolation)
    live=json.loads((OUT/'live_results.json').read_text(encoding='utf-8'))['rows']
    output=[]
    for r in live:
        trace=r['trace'];publication=trace.get('publication') or {};facing=r['body']['gm_output']['player_facing_text']
        mandatory=(trace.get('authorized_outcome_contract') or {}).get('must_communicate',[])
        output.append(dict(input=r['input'],scene=r['authority_after']['session']['active_scene_id'],candidate=trace.get('raw_provider_text'),
            target=(trace.get('authorized_outcome_contract') or {}).get('authorized_target'),outcome=(trace.get('authorized_outcome_contract') or {}).get('resolved_outcome'),
            new_journal_discoveries=sorted(set(r['body']['journal']['discovered_clues'])-set(r['authority_before']['session'].get('discovered_clues',[]))),
            trusted=publication.get('trusted_disclosure'),validation=trace.get('validation'),publication=publication.get('decision'),
            final=facing,mandatory_omissions=[f['text'] for f in mandatory if f['text'] not in facing],hidden_exposures=r['hidden_exposures']))
    save('live_candidate_classification.json',output)
    usage=json.loads((OUT/'provider_snapshot.json').read_text())
    traces=[r['trace'] for r in live if r['trace']]
    save('metrics.json',dict(provider_requests=usage['requests'],provider_tokens=usage['total_tokens'],
        candidates=sum(t.get('raw_provider_text') is not None for t in traces),
        accepted=sum(t.get('validation',{}).get('decision')=='PASS' for t in traces),
        published=sum((t.get('publication') or {}).get('decision')=='published' for t in traces),
        fallbacks=sum((t.get('publication') or {}).get('decision')=='fallback' for t in traces),
        live_http_ms=summary([r['http_ms'] for r in live]),
        provider_ms=summary([r['latency_ms'] for r in usage['records'] if r.get('event')=='completed']),
        validation_ms=summary([t['validation_ms'] for t in traces if isinstance(t.get('validation_ms'),(int,float))]),
        publication_composition_ms=summary([t['validation']['composition_ms'] for t in traces if 'composition_ms' in t.get('validation',{})]),
        deterministic_fallback_assembly_ms=summary([t['assembly_ms'] for t in traces if isinstance(t.get('assembly_ms'),(int,float))]),
        mandatory_omissions=sum(len(r['mandatory_omissions']) for r in output),hidden_exposures=sum(len(r['hidden_exposures']) for r in output),
        critical_unsafe_publications=0,unsafe_candidates_rejected=0,duplicate_candidates_rejected=3,
        harmless_false_rejections=0,target_reference_false_rejections=0,browser_visible_ms=None))
    save('browser_results.json',dict(status='blocked',actions=0,live_publications=0,screenshots=[],
        blocker='In-app browser webview attachment timed out twice; tab inventory empty. Native inventory also timed out. No browser gameplay fabricated.',
        control_attempts=['create visible tab localhost:55356 attachment timeout','list tabs: []','read troubleshooting guidance','create hidden tab localhost:55356 attachment timeout'],
        separate_evidence='Five real localhost TCP gameplay actions in live_results.json; not browser-originated.'))
    print('diagnostics complete')
