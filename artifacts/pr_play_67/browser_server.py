"""Disposable browser target, isolated from the user's campaign."""
import sys,time,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from artifacts.pr_play_67.http_harness import *
with seed('browser_session',True),server() as request:
    url=request('/api/state')['request']['path']
    # URL comes from the server request closure, not a production port.
    import inspect
    port=inspect.getclosurevars(request).nonlocals['port']
    save('browser_target.json',{'url':f'http://127.0.0.1:{port}/'})
    print(f'Browser target: http://127.0.0.1:{port}/',flush=True)
    for _ in range(6000):
        if (OUT/'browser_stop').exists(): break
        time.sleep(.1)
