import json,time
from pathlib import Path
from tools.playtest import runner
original=runner.request
attempts=[]
def probe(base, method, path, timeout, body=None):
    start=time.monotonic()
    try:
        status,value=original(base,method,path,timeout,body)
        attempts.append(dict(url=base+path,status=status,seconds=time.monotonic()-start))
        if status==200: raise KeyboardInterrupt
        return status,value
    except Exception as exc:
        attempts.append(dict(url=base+path,error=type(exc).__name__,detail=str(exc),seconds=time.monotonic()-start))
        raise
runner.request=probe
run,result=runner.run_playtest(output_root=Path('artifacts/atgb/pr_play_15/initial'),startup_timeout=30)
runner.write(Path('artifacts/pr_play_15/initial_reproduction.json'),dict(run=str(run),attempts=attempts,result=result))
print(run,result.get('failure'),result['process_cleanup'])

