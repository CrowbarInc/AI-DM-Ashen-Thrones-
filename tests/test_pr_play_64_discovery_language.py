import json
import pytest
from tests.pr_play_64_development import cases, evaluate
from tests.test_pr_play_57_integrated_narration import hook, ROUTE
from game import integrated_investigation_narration as i
from game import quarantined_investigation_narration as q

@pytest.mark.parametrize('case',cases(),ids=lambda c:c['id']+'_'+c['name'])
def test_complete_pipeline(case,monkeypatch):
 monkeypatch.setenv(q.PUBLICATION_ENV,'1')
 row=evaluate(case)
 assert row['matches'],json.dumps(row['validation'])
 assert row['state_unchanged']
 assert row['fallback_validation']['decision']=='PASS'
 assert row['result']['used_fallback']==(case['expected']!='PASS')

@pytest.mark.parametrize('text',[
 'You take the key and examine it.',"You take the gate's key.",
 'You take a closer look and you acquire the key.',
 'You learn that the missing patrol was last seen taking the northwest mud track past the crates and the guard captain was killed.',
 'You read that the missing patrol was last seen taking the northwest mud track past the crates and a second route.',
 'You study the notice board and learn that the guard captain was last seen taking the northwest mud track past the crates.',
])
def test_expansions_stay_blocked(text):
 c,r=i.outcome_contract(hook());assert i.validate_integrated(c,r,ROUTE+' '+text)['decision']!='PASS'

def test_bare_careful_look_was_already_safe():
 # The historical failure needs the trailing "around ... examination" words.
 h=hook(kind='investigate',clues=[]);c,r=i.outcome_contract(h)
 assert i.validate_integrated(c,r,'You take a careful look; no new clue is established.')['decision']=='PASS'
