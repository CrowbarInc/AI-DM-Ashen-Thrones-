"""Run known failures against the saved, dirty entry production source."""
from pathlib import Path

def pytest_configure(config):
    import game.gm as gm
    import game.immutable_valid_response as immutable
    import game.provider_budget as budget
    import game.api as api
    for mod,path in [(budget,'provider_budget.py'),(gm,'gm.py'),(immutable,'immutable_valid_response.py'),(api,'api.py')]:
        p=Path('artifacts/pr_play_07/entry/game')/path
        exec(compile(p.read_text(encoding='utf-8-sig'),str(p),'exec'),mod.__dict__)
