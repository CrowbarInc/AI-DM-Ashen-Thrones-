from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from game.contract_registry import emergency_fallback_kind_ids, emergency_fallback_source_ids


@dataclass(frozen=True)
class _FoundTelemetry:
    sources: frozenset[str]
    kinds: frozenset[str]


def _collect_string_literal_assignments(py_path: Path) -> dict[str, set[str]]:
    """Return string-literal assignments by variable name.

    Only captures direct assignments like: `name = "literal"` (including annotated assigns).
    """

    tree = ast.parse(py_path.read_text(encoding="utf-8"), filename=str(py_path))
    out: dict[str, set[str]] = {"final_emitted_source": set(), "fallback_kind": set()}

    def _maybe_add(name: str, value: ast.AST) -> None:
        if name not in out:
            return
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            out[name].add(value.value)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name):
                    _maybe_add(tgt.id, node.value)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.value is not None:
                _maybe_add(node.target.id, node.value)

    return out


def _narrow_emergency_literals_for_social_exchange_emission(py_path: Path) -> _FoundTelemetry:
    """Narrow to strict-social deterministic/minimal emergency telemetry in social emission.

    Guard must remain focused:
    - Only the deterministic->minimal emergency branch assigns these literals.
    - Do not require normal non-emergency sources to enter the registry.
    """

    by_var = _collect_string_literal_assignments(py_path)
    sources = {
        s
        for s in by_var["final_emitted_source"]
        if (s == "deterministic_social_fallback" or "emergency" in s)
    }
    kinds = {k for k in by_var["fallback_kind"] if k.startswith("emergency_social_")}
    return _FoundTelemetry(sources=frozenset(sources), kinds=frozenset(kinds))


def _narrow_emergency_literals_for_final_emission_gate(py_path: Path) -> _FoundTelemetry:
    """Narrow to strict-social minimal emergency telemetry in final gate replace path."""

    by_var = _collect_string_literal_assignments(py_path)
    sources = {s for s in by_var["final_emitted_source"] if s.startswith("social_interlocutor_")}
    kinds = {k for k in by_var["fallback_kind"] if k == "social_interlocutor_fallback"}
    return _FoundTelemetry(sources=frozenset(sources), kinds=frozenset(kinds))


def test_emergency_fallback_registry_static_drift_guard() -> None:
    root = Path(__file__).resolve().parents[1]

    social_path = root / "game" / "social_exchange_emission.py"
    gate_path = root / "game" / "final_emission_gate.py"
    assert social_path.exists()
    assert gate_path.exists()

    found_social = _narrow_emergency_literals_for_social_exchange_emission(social_path)
    found_gate = _narrow_emergency_literals_for_final_emission_gate(gate_path)

    found_sources = set(found_social.sources) | set(found_gate.sources)
    found_kinds = set(found_social.kinds) | set(found_gate.kinds)

    assert found_sources, "Drift guard found no emergency final_emitted_source literals."
    assert found_kinds, "Drift guard found no emergency fallback_kind literals."

    reg_sources = emergency_fallback_source_ids()
    reg_kinds = emergency_fallback_kind_ids()

    missing_sources = sorted(s for s in found_sources if s not in reg_sources)
    missing_kinds = sorted(k for k in found_kinds if k not in reg_kinds)

    assert missing_sources == []
    assert missing_kinds == []

