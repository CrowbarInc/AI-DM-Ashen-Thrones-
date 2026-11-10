import copy
import pytest

from game import integrated_investigation_narration as integrated
from tests.pr_play_58_development import cases


@pytest.mark.parametrize('case', cases(), ids=lambda c:c['id'])
def test_development_coverage_safety(case):
    before = copy.deepcopy(case['hook'])
    contract, request = integrated.outcome_contract(case['hook'])
    result = integrated.validate_integrated(contract, request, case['text'])
    assert case['hook'] == before
    if case['expected']=='PASS':
        assert result['coverage']['decision']=='PASS'
    else:
        assert result['decision']!='PASS'


def test_coverage_does_not_override_semantic_or_legacy(monkeypatch):
    case=cases()[0]
    contract,request=integrated.outcome_contract(case['hook'])
    for decision in ['FAIL','REVIEW_REQUIRED','VALIDATION_ERROR']:
        monkeypatch.setattr(integrated.semantic,'validate_consequential_narration',
            lambda *args, d=decision: {'decision':d,'reasons':['injected'],'claims':[]})
        result=integrated.validate_integrated(contract,request,case['text'])
        assert result['coverage']['decision']=='PASS'
        assert result['decision']==decision
