"""Multipart import and initialization/error response boundary coverage."""
import sys,json,time,urllib.request,urllib.error,inspect
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from artifacts.pr_play_67.http_harness import *
from artifacts.pr_play_67.integration import checked
rows=[]
for enabled in [False,True]:
    with seed('supplemental_'+str(enabled),enabled),server() as request:
        port=inspect.getclosurevars(request).nonlocals['port']
        for valid in [True,False]:
            boundary='PR67MultipartBoundary'
            document=storage.load_character();document['gm_notes']='IMPORT_SECRET_SENTINEL'
            data=(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="sheet.json"\r\nContent-Type: application/json\r\n\r\n'+(json.dumps(document) if valid else '{malformed SECRET_SENTINEL_INPUT')+f'\r\n--{boundary}--\r\n').encode()
            req=urllib.request.Request(f'http://127.0.0.1:{port}/api/import_sheet',data=data,headers={'Content-Type':f'multipart/form-data; boundary={boundary}'})
            start=time.perf_counter()
            try:response=urllib.request.urlopen(req,timeout=60)
            except urllib.error.HTTPError as error:response=error
            raw=response.read().decode()
            row=dict(enabled=enabled,valid_sheet=valid,request={'method':'POST','path':'/api/import_sheet','fixture':'default player sheet with internal annotation' if valid else 'malformed synthetic JSON'},status=response.status,body=json.loads(raw),serialized_body=raw,bytes=len(raw.encode()),http_ms=(time.perf_counter()-start)*1000,hidden_exposures=scan(raw))
            checked(row);assert 'SECRET_SENTINEL' not in raw
            if valid:assert row['status']==200
            else:assert row['status']==500
            rows.append(row)
        for path,body in [('/api/new_campaign',{}),('/api/start_campaign',{})]:
            def fail(*a,**k):raise RuntimeError('INITIALIZATION_SECRET_SENTINEL')
            with pytest.MonkeyPatch.context() as mp:
                mp.setattr(api,'apply_new_campaign_hard_reset' if path.endswith('new_campaign') else 'load_campaign',fail)
                row=checked(request(path,body));assert 'SECRET_SENTINEL' not in row['serialized_body'];rows.append(row)
save('supplemental_http.json',redact(rows))
print('Supplemental TCP requests:',len(rows))
