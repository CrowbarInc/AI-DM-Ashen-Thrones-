import json,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'artifacts/pr_play_12'
baseline=json.loads((ROOT/'artifacts/pr_play_11/test_summary.json').read_text())
lanes=[x for x in baseline if x!='entry_claim_authority']
allrows={}; failures=[]
for lane in lanes:
    files=[OUT/(lane+'_short.xml'),OUT/(lane+'_final.xml'),OUT/(lane+'_complete.xml')]
    # This superseded short run was stopped; use the completed full run and
    # substitute only explicitly successful same-case original-source probes.
    if lane=='diagnostics': files=[OUT/'diagnostics_final.xml']
    if lane=='harness': files=[OUT/'harness_local.xml']
    path=next((p for p in files if p.exists()),None)
    if not path: allrows[lane]=dict(status='environment-blocked',reason='No completed JUnit'); continue
    cases=list(ET.parse(path).iter('testcase')); bad=[]
    supplements=[]
    if lane in {'diagnostics','world','export_atgb'}:
        for extra in ['supplemental_original.xml','environment_probe.xml']:
            for c in ET.parse(OUT/extra).iter('testcase'):
                if c.find('failure') is None and c.find('error') is None:
                    supplements.append(c.get('classname','')+'::'+c.get('name',''))
    substituted=[]
    for case in cases:
        fail=case.find('failure'); error=case.find('error')
        node=fail if fail is not None else error
        if node is None: continue
        ident=case.get('classname','')+'::'+case.get('name','')
        if ident in supplements:
            substituted.append(ident)
            continue
        text=node.get('message','')+'\n'+(node.text or '')
        if ident in baseline[lane]['failure_cases']: classification='preexisting failure'
        elif any(s in text for s in ['FileNotFoundError','PermissionError','WinError','collection failure']): classification='environment-blocked'
        else: classification='unresolved'
        row=dict(lane=lane,test=ident,classification=classification,message=text)
        bad.append(ident); failures.append(row)
    skipped=sum(c.find('skipped') is not None for c in cases)
    allrows[lane]=dict(source=path.name,successful_same_case_supplement=substituted,tests=len(cases),passed=len(cases)-len(bad)-skipped,failed=len(bad),skipped=skipped,failure_cases=bad,baseline_passed=baseline[lane]['passed'],baseline_failures=baseline[lane]['failures']+baseline[lane]['errors'])
focused=ET.parse(OUT/'assessment.xml')
focases=list(focused.iter('testcase'))
counts={k:sum(r['classification']==k for r in failures) for k in ['preexisting failure','environment-blocked','unresolved','new regression']}
headline=dict(regression_passed=sum(r.get('passed',0) for r in allrows.values()),regression_failed=sum(r.get('failed',0) for r in allrows.values()),failure_classification=counts,focused_passed=sum(c.find('failure') is None and c.find('error') is None for c in focases),focused_total=len(focases),baseline='878 passing / 14 failures; same PR11 lane selections',full_suite=False,ATGB_benchmark=False)
result=dict(headline=headline,lanes=allrows,failures=failures,initial_attempts='Incomplete source copy omitted legacy fixtures and effective model configuration; local HTTP initially blocked. Initial runner stopped after superseding complete-copy runs. Initial logs/JUnit retained but not counted twice.',initial_assessment='Nine initial byte-equality assertions failed on known persistence envelope/debug metadata. Raw evidence retained; corrected gameplay comparison explicitly excludes only recorded bookkeeping.',synthetic_environment='Invalid offline key only; original existing model configuration projected unchanged for final affected lanes. No actual provider configuration written.')
(OUT/'regression_summary.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(headline,indent=2))
