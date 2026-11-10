import sys,json,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
import pytest
from fastapi.testclient import TestClient
from tests.test_pr_play_71_lifecycle import configure,create
from game import api,storage
OUT=Path(__file__).resolve().parent
rows=[]
for label,raw in [('empty',{'player_facing_text':''}),('malformed',{})]:
 with pytest.MonkeyPatch.context() as mp:
  configure(OUT/'opening_diagnostics'/label,mp)
  mp.setattr(api,'call_gpt',lambda *a,**kw:copy.deepcopy(raw))
  with TestClient(api.app,raise_server_exceptions=False) as cl:
   identity=create(cl);before=storage.load_session();r=cl.post('/api/start_campaign')
   rows.append(dict(label=label,status=r.status_code,body=r.json(),before=before,after=storage.load_session(),identity=identity,classification='evaluation: frozen evaluator required error; existing deterministic recovery may validly succeed'))
(OUT/'opening_diagnostics.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
