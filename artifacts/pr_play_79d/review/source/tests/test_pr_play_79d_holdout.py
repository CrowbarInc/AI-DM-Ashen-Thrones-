"""Run frozen developer-authored recall holdout once, retaining original results."""
import json
from pathlib import Path
import pytest
from tests.test_pr_play_79d_closeout import exercise_recall

ROOT = Path(__file__).resolve().parents[1]
ROWS = json.loads((ROOT/'artifacts/pr_play_79d/holdout.json').read_text())

@pytest.mark.parametrize('row', ROWS, ids=[r['id'] for r in ROWS])
def test_frozen(row, tmp_path, monkeypatch):
    recalled = exercise_recall(row['source'], row['fact'], row['condition'])
    assert recalled == ((row['fact'],) if row['expected_recall'] else ())
    from game.exploration import _repeat_publication
    from game.publication_contract import record_completed_publication
    text = _repeat_publication({}, True, row['input'], recalled=recalled)['engine_publication']
    monkeypatch.setenv('ASHEN_PUBLICATION_TRACE_PATH', str(tmp_path/'publication.jsonl'))
    trace = record_completed_publication({'gm_output': {'player_facing_text':text}}, source_handler='holdout')
    assert trace['final_player_facing_response'] == text
    assert 'nothing new' in text and 'CANARY_' not in text
