import json
from pathlib import Path
from tests.test_pr_play_63_disclosure import assess
from tests.test_pr_play_57_integrated_narration import hook,ROUTE
h=hook(kind='investigate',clues=[],known=())
c,r,a=assess(h,'No new clue is established. '+ROUTE)
Path('artifacts/pr_play_63/preexisting_route_gap.json').write_text(json.dumps({'hook':h,'request':r,'validation':a,'published':False,'scope':'offline synthetic negative control; no provider or publication'},indent=2))
