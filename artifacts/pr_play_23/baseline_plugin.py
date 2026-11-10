"""Pytest-only switch to the pre-PR-PLAY-23 behavior for paired comparisons."""
import pytest


@pytest.fixture(autouse=True)
def pre_repair(monkeypatch):
    monkeypatch.setattr('game.local_interaction.normalize_local_approach', lambda record, **kw: record)
