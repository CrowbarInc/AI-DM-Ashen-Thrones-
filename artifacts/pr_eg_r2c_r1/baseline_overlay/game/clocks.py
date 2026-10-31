from __future__ import annotations

from typing import Any, Dict

from game.schema_contracts import adapt_legacy_clock, normalize_clock, validate_clock


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
    """Advance a named clock by delta and return the new value.

    Session pressure clocks remain stored as plain ints for persistence size; coercion
    uses :func:`game.schema_contracts.normalize_clock` / ``validate_clock`` for bounds.
    """
    clocks = get_or_init_clocks(session)
    current = int(clocks.get(name, 0))
    work = adapt_legacy_clock(
        {
            "id": name,
            "value": current,
            "min_value": min_value,
            "max_value": max_value,
            "scope": "session",
            "metadata": {},
        }
    )
    canon = normalize_clock(work)
    validate_clock(canon)
    new_val = _clamp(int(canon["value"]) + int(delta), int(canon["min_value"]), int(canon["max_value"]))
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
    work = adapt_legacy_clock(
        {
            "id": name,
            "value": int(value),
            "min_value": min_value,
            "max_value": max_value,
            "scope": "session",
            "metadata": {},
        }
    )
    canon = normalize_clock(work)
    validate_clock(canon)
    new_val = _clamp(int(value), int(canon["min_value"]), int(canon["max_value"]))
    clocks[name] = new_val
    return new_val

