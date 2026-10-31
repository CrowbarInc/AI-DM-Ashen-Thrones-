"""Optional rendered-UI adapter. No browser dependency is installed by this tool."""
from typing import Protocol


class BrowserAdapter(Protocol):
    def campaign_opening(self, base_url: str, screenshot_dir: str, timeout: float) -> dict:
        """Own New Campaign and a SINGLE Start click; return narration/error and evidence paths.

        An adapter replaces API mutation steps, never repeats them. It must compare
        rendered outcome to API state and stop/close on timeout. No implementation
        is registered until repository browser tooling exists.
        """
        ...


def observation() -> dict:
    return {"status": "NOT_TESTED", "reason": "No repository browser runner/dependency; API evidence does not establish rendered UI behavior."}
