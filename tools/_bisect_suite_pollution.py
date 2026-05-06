"""Bisect suite-only pollution: find minimal prefix test that poisons a target."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PY = [sys.executable, "-m", "pytest"]


def collect_node_ids() -> list[str]:
    """Collect canonical node ids (in suite order). Parsing ``--collect-only`` stdout breaks on wrapped lines."""
    import pytest as pytest_mod

    ids: list[str] = []

    class Collector:
        def pytest_collection_finish(self, session: Any) -> None:
            ids.clear()
            ids.extend([i.nodeid.replace("\\", "/") for i in session.items])

    old = os.getcwd()
    os.chdir(ROOT)
    try:
        code = pytest_mod.main(["tests/", "--collect-only", "-q"], plugins=[Collector()])
        if code != 0:
            raise RuntimeError(f"pytest collect-only exited {code}")
    finally:
        os.chdir(old)
    return ids


def run_tests(node_ids: list[str]) -> bool:
    """Windows argv limits: pass node ids via pytest ``@argsfile``."""
    if not node_ids:
        return True
    fd, path = tempfile.mkstemp(suffix=".txt", prefix="pytest_nodes_", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write("\n".join(node_ids) + "\n")
        r = subprocess.run(
            PY + [f"@{path}", "-q", "--tb=no"],
            cwd=ROOT,
        )
        return r.returncode == 0
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def minimal_failing_prefix_tests(prefix: list[str], target: str) -> list[str]:
    """Return smallest list `prefix[:n]` such that `prefix[:n] + [target]` fails; empty if none."""
    if not prefix:
        return []
    if run_tests(prefix + [target]):
        return []
    lo, hi = 1, len(prefix)
    while lo < hi:
        mid = (lo + hi) // 2
        if not run_tests(prefix[:mid] + [target]):
            hi = mid
        else:
            lo = mid + 1
    return prefix[:lo]


def find_polluter(prefix: list[str], target: str) -> str | None:
    mp = minimal_failing_prefix_tests(prefix, target)
    if not mp:
        return None
    return mp[-1]


def report_target(target: str, all_ids: list[str]) -> None:
    if target not in all_ids:
        print(f"MISSING {target}")
        return
    idx = all_ids.index(target)
    prefix = all_ids[:idx]
    print(f"\n=== {target}\n    prefix_len={len(prefix)}")
    alone = run_tests([target])
    print(f"    target_alone_ok={alone}")
    if alone and prefix:
        full_pre = run_tests(prefix + [target])
        print(f"    full_prefix+target_ok={full_pre}")
    p = find_polluter(prefix, target)
    print(f"    polluter={p}")


def main() -> None:
    all_ids = collect_node_ids()
    targets = [
        "tests/test_final_emission_boundary_no_semantic_repair.py::test_awkward_but_legal_narration_not_polished",
        "tests/test_lead_npc_payoff_and_fallback.py::test_emission_gate_replaces_stock_global_fallback_for_failed_npc_pursuit_social",
        "tests/test_prompt_context.py::test_reintroduced_stale_entity_can_surface_selected_memory",
    ]
    for t in targets:
        report_target(t, all_ids)


if __name__ == "__main__":
    main()
