"""Verify journal and inventory idempotency from actual retained HTTP states."""
from pathlib import Path
import sys,json,copy
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R));O=Path(__file__).resolve().parent
from tests.helpers.storage_isolation import install
install(O/'analysis_data')
from game.journal import build_player_journal
checks=[]
for name in ['http_traces.json','pre_holdout_http_traces.json']:
 if not (O/name).exists():continue
 for row in json.loads((O/name).read_text()):
  res=row.get('authoritative_log',{}).get('resolution',{})
  if res.get('kind')!='already_searched':continue
  a=row['authority_before'];b=row['authority_after'];sid=a['session']['active_scene_id'];scene=json.loads((O/'http_data/scenes'/f'{sid}.json').read_text())
  ja=build_player_journal(copy.deepcopy(a['session']),copy.deepcopy(a['world']),scene);jb=build_player_journal(copy.deepcopy(b['session']),copy.deepcopy(b['world']),scene)
  checks.append(dict(source=name,text=row['request']['json']['text'],journal_equal=all(ja[k]==jb[k] for k in ['known_facts','discovered_clues','lead_counts']),unique_clues=len(jb['discovered_clues'])==len(set(jb['discovered_clues'])),inventory_equal=a['character']==b['character'],flags_equal=a['world']['world_state']['flags']==b['world']['world_state']['flags'],before_journal=ja,after_journal=jb))
(O/'repeat_journal_audit.json').write_text(json.dumps(checks,indent=2));print('Actual repeat journal/inventory checks:',len(checks),'failures:',sum(not all(r[k] for k in ['journal_equal','unique_clues','inventory_equal','flags_equal']) for r in checks))
