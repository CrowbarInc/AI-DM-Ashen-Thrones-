from __future__ import annotations

from typing import Any, Dict


DEFAULT_CLOCKS = {
    "suspicion": 0,
    "unrest": 0,
    "danger": 0,
    "occult_instability": 0,
    "time_pressure": 0,
}


def get_or_init_clocks(session: Dict[str, Any]) -> Dict[str, int]:
    """Ensure session has a clocks dict with default keys."""
    clocks = session.get("clocks")
    if not isinstance(clocks, dict):
        clocks = {}
        session["clocks"] = clocks
    for name, value in DEFAULT_CLOCKS.items():
        clocks.setdefault(name, value)
    return clocks


def _clamp(value: int, min_value: int, max_value: int) -> int:
    return max(min_value, min(max_value, value))


def advance_clock(
    session: Dict[str, Any],
    name: str,
    delta: int = 1,
    min_value: int = 0,
    max_value: int = 10,
) -> int:
    """Advance a named clock by delta and return the new value."""
    clocks = get_or_init_clocks(session)
    current = int(clocks.get(name, 0))
    new_val = _clamp(current + int(delta), min_value, max_value)
    clocks[name] = new_val
    return new_val


def set_clock(
    session: Dict[str, Any],
    name: str,
    value: int,
    min_value: int = 0,
    max_value: int = 10,
) -> int:
    """Set a named clock to a specific value."""
    clocks = get_or_init_clocks(session)
    new_val = _clamp(int(value), min_value, max_value)
    clocks[name] = new_val
    return new_val

