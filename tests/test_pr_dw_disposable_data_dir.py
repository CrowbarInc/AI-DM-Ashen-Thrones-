from __future__ import annotations

from game import storage


def test_pr_dw_storage_data_dir_can_be_overridden_for_disposable_playtest(tmp_path, monkeypatch):
    data_dir = tmp_path / "pr_dw_data"
    monkeypatch.setenv("ASHEN_DATA_DIR", str(data_dir))

    assert storage._configured_data_dir() == data_dir.resolve()

