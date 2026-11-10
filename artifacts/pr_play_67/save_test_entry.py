from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent/'entry_source'
for name in ['test_pr_play_61_player_facing.py','test_pr_play_52_quarantined_integration.py','test_pr_play_42_evidence_boundaries.py','test_pr_play_44_information_delivery.py','test_ui_mode_regression_matrix_objective15.py']:
    assert not (OUT/name).exists()
    (OUT/name).write_bytes((ROOT/'tests'/name).read_bytes())
