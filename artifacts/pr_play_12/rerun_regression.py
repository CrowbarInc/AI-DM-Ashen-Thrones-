"""Completed-copy PR11 lane rerun; synthetic clients and localhost only."""
import json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'artifacts/pr_play_12'
lanes=json.loads((ROOT/'artifacts/pr_play_11/regression_runs.json').read_text())
results={}
for name,row in lanes.items():
    if name in {'entry_claim_authority','harness'}: continue
    files=[x for x in row['command'] if x.startswith('tests/')]
    cmd=[sys.executable,'-m','pytest',*files,'-q','--tb=short','--basetemp='+str(OUT/('tmp_complete_'+name)),'--junitxml='+str(OUT/(name+'_complete.xml'))]
    started=time.monotonic()
    # A deliberately invalid synthetic key satisfies legacy get-key aliases.
    # Test conftest blocks real clients; owned worker transport blocks external sockets.
    env={**os.environ,'OPENAI_API_KEY':'offline-placeholder','ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT':'1','ASHEN_DISABLE_PROVIDER_RETRIES':'1','ASHEN_PLAYTEST_DISABLE_SDK_RETRIES':'1'}
    with (OUT/(name+'_complete.txt')).open('wb') as log:
        try:
            p=subprocess.run(cmd,cwd=OUT/'sandbox',stdout=log,stderr=subprocess.STDOUT,timeout=100,env=env)
            results[name]=dict(command=cmd,exit=p.returncode,seconds=round(time.monotonic()-started,2))
        except subprocess.TimeoutExpired:
            results[name]=dict(command=cmd,timeout=True,seconds=100)
    (OUT/'regression_complete_runs.json').write_text(json.dumps(results,indent=2))
    print(name,results[name].get('exit','timeout'),flush=True)
