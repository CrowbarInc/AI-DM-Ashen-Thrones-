"""Run unchanged PR11 selections against isolated current-source copies."""
import json, os, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'artifacts/pr_play_12'
lanes=json.loads((ROOT/'artifacts/pr_play_11/regression_runs.json').read_text())
results={}
for name,row in lanes.items():
    if name=='entry_claim_authority': continue
    files=[x for x in row['command'] if x.startswith('tests/')]
    cmd=[sys.executable,'-m','pytest',*files,'-q','--tb=short','--basetemp='+str(OUT/('tmp_reg_'+name)),'--junitxml='+str(OUT/(name+'.xml'))]
    started=time.monotonic()
    try:
        p=subprocess.run(cmd,cwd=OUT/'sandbox',capture_output=True,timeout=240,env={**os.environ,'ASHEN_DISABLE_PROVIDER_RETRIES':'1','ASHEN_PLAYTEST_DISABLE_SDK_RETRIES':'1'})
        (OUT/(name+'.txt')).write_bytes(p.stdout+p.stderr)
        results[name]=dict(command=cmd,exit=p.returncode,seconds=round(time.monotonic()-started,2))
    except subprocess.TimeoutExpired as e:
        (OUT/(name+'.txt')).write_bytes((e.stdout or b'')+(e.stderr or b''))
        results[name]=dict(command=cmd,timeout=True,seconds=240)
    (OUT/'regression_runs.json').write_text(json.dumps(results,indent=2))
    print(name,results[name].get('exit','timeout'),flush=True)
