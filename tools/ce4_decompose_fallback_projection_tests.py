"""CE4 test decomposition for test_golden_replay_fallback_projection.py."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "tests" / "test_golden_replay_fallback_projection.py"
BACKUP = ROOT / "tests" / "test_golden_replay_fallback_projection_monolith.py.bak"
TESTS = ROOT / "tests"
HELPERS = ROOT / "tests" / "helpers"

IMPORT_BLOCK_END = 71
HELPER_START = 353
HELPER_END = 364

MODULES: list[tuple[str, str, list[tuple[int, int]]]] = [
    (
        "test_golden_replay_fallback_opening_projection",
        "Opening and sealed-gate opening fallback projection coverage.",
        [(81, 247)],
    ),
    (
        "test_golden_replay_fallback_sealed_projection",
        "Sealed and strict-social sealed fallback projection coverage.",
        [(250, 277), (887, 993)],
    ),
    (
        "test_golden_replay_fallback_visibility_projection",
        "Visibility, referential, and hard-replacement fallback projection coverage.",
        [(280, 351), (367, 493)],
    ),
    (
        "test_golden_replay_fallback_upstream_projection",
        "Upstream prepared emission telemetry and drift classification coverage.",
        [(496, 652)],
    ),
    (
        "test_golden_replay_fallback_sanitizer_projection",
        "Sanitizer empty and strict-social fallback projection coverage.",
        [(655, 781), (809, 851)],
    ),
    (
        "test_golden_replay_fallback_upstream_fast_projection",
        "Upstream-fast fallback split-owner and classifier alignment coverage.",
        [(784, 807), (854, 884)],
    ),
    (
        "test_golden_replay_fallback_long_session_summary",
        "Long-session fallback lineage and escalation summary coverage.",
        [(996, 1228)],
    ),
    (
        "test_golden_replay_fallback_acceptance_matrix",
        "Split-owner acceptance matrix golden-replay alignment coverage.",
        [(1231, 1251)],
    ),
]

HELPER_BODY = '''"""Shared lineage event selectors for fallback projection tests."""
from __future__ import annotations


def fallback_selected_event(observed: dict) -> dict:
    return next(
        event for event in observed["runtime_lineage_events"] if event.get("event_kind") == "fallback_selected"
    )


def mutation_event(observed: dict, mutation_kind: str) -> dict:
    return next(
        event
        for event in observed["runtime_lineage_events"]
        if event.get("event_kind") == "mutation" and event.get("mutation_kind") == mutation_kind
    )
'''

HELPER_IMPORT = (
    "from tests.helpers.golden_replay_fallback_projection_helpers import (\n"
    "    fallback_selected_event as _fallback_selected_event,\n"
    "    mutation_event as _mutation_event,\n"
    ")\n"
)

BOUNDARY_COMMENT = """
# Opening fallback owner-bucket boundary:
# this suite owns transport from FEM/runtime-lineage metadata into replay
# observations and debug output. Gate behavior/selection remains in
# test_final_emission_gate.py; FEM owner-bucket/lineage construction remains in
# test_final_emission_meta.py; classifier diagnostics remain in
# test_failure_classifier.py.
"""

STUB = '''"""Historical redirect: fallback projection tests decomposed into focused owner files.

Practical direct-owner coverage now lives in:

- ``tests/test_golden_replay_fallback_opening_projection.py`` — opening/sealed-gate opening projection
- ``tests/test_golden_replay_fallback_sealed_projection.py`` — sealed and strict-social sealed projection
- ``tests/test_golden_replay_fallback_visibility_projection.py`` — visibility/referential hard-replacement projection
- ``tests/test_golden_replay_fallback_upstream_projection.py`` — upstream prepared emission telemetry
- ``tests/test_golden_replay_fallback_sanitizer_projection.py`` — sanitizer empty/strict-social projection
- ``tests/test_golden_replay_fallback_upstream_fast_projection.py`` — upstream-fast split-owner projection
- ``tests/test_golden_replay_fallback_long_session_summary.py`` — long-session lineage/escalation summaries
- ``tests/test_golden_replay_fallback_acceptance_matrix.py`` — split-owner acceptance matrix alignment

Run the focused files above (or ``pytest tests/test_golden_replay_fallback_*.py``) instead of this stub.
"""


def test_golden_replay_fallback_projection_decomposed_redirect_stub() -> None:
    import tests.test_golden_replay_fallback_projection as stub

    assert stub.__doc__
'''


def slice_lines(lines: list[str], start: int, end: int) -> str:
    return "".join(lines[start - 1 : end])


def uses_lineage_helpers(body: str) -> bool:
    return "_fallback_selected_event" in body or "_mutation_event" in body


def main() -> None:
    source_path = BACKUP if BACKUP.is_file() else SRC
    if not BACKUP.is_file():
        BACKUP.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")

    lines = source_path.read_text(encoding="utf-8").splitlines(keepends=True)
    import_block = slice_lines(lines, 1, IMPORT_BLOCK_END)

    (HELPERS / "golden_replay_fallback_projection_helpers.py").write_text(HELPER_BODY, encoding="utf-8")

    stats: list[tuple[str, int, int]] = []
    moved_tests: list[tuple[str, list[str]]] = []

    for module_name, description, ranges in MODULES:
        body_parts = [slice_lines(lines, start, end) for start, end in ranges]
        body = "".join(body_parts)
        helper_import = HELPER_IMPORT if uses_lineage_helpers(body) else ""
        opening_comment = BOUNDARY_COMMENT if module_name.endswith("opening_projection") else ""
        content = (
            f'"""{description}"""\n'
            f"{import_block}\n"
            f"{helper_import}\n"
            f"{opening_comment}\n"
            f"{body}"
        )
        out = TESTS / f"{module_name}.py"
        out.write_text(content, encoding="utf-8")
        loc = len(content.splitlines())
        test_count = content.count("\ndef test_")
        stats.append((module_name, loc, test_count))
        test_names = [
            line.strip().split("(")[0].replace("def ", "")
            for line in content.splitlines()
            if line.startswith("def test_")
        ]
        moved_tests.append((module_name, test_names))

    SRC.write_text(STUB, encoding="utf-8")
    stub_loc = len(STUB.splitlines())

    print("CE4 fallback projection test decomposition complete.")
    print(f"  monolith backup: {len(lines)} LOC")
    print(f"  stub: {stub_loc} LOC")
    for module_name, loc, test_count in stats:
        print(f"  {module_name}: {loc} LOC, {test_count} tests")
    print(f"  golden_replay_fallback_projection_helpers.py: {len(HELPER_BODY.splitlines())} LOC")


if __name__ == "__main__":
    main()
