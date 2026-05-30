#!/usr/bin/env python3
"""Refresh or verify the generated protected-field-paths section in the replay manifest.

Report-only governance helper: reads ``protected_field_paths()`` from golden replay
projection and keeps ``docs/testing/protected_replay_manifest.md`` aligned.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.helpers.golden_replay_projection import (  # noqa: E402
    SEMANTIC_DRIFT_FIELDS,
    STRUCTURAL_DRIFT_FIELDS,
    protected_field_paths,
)

MANIFEST_PATH = ROOT / "docs" / "testing" / "protected_replay_manifest.md"
BEGIN_MARKER = "<!-- BEGIN GENERATED: protected_field_paths -->"
END_MARKER = "<!-- END GENERATED: protected_field_paths -->"
INSERT_BEFORE_HEADING = "## Cycle S Drift Policy Addendum"


def _drift_bucket(path: str) -> str:
    if path in SEMANTIC_DRIFT_FIELDS:
        return "semantic_drift"
    return "structural_drift"


def render_generated_section() -> str:
    """Return the bounded manifest section for protected observation field paths."""
    paths = protected_field_paths()
    lines = [
        BEGIN_MARKER,
        "",
        "## Protected Observation Field Paths (Generated)",
        "",
        "Bounded registry of golden replay observation paths locked by protected replay.",
        "Source: `tests/helpers/golden_replay_projection.py::protected_field_paths()`.",
        "",
        "Refresh this section:",
        "",
        "```bash",
        "python tools/refresh_protected_replay_manifest.py --write",
        "```",
        "",
        "Verify without writing:",
        "",
        "```bash",
        "python tools/refresh_protected_replay_manifest.py --check",
        "```",
        "",
        f"- **Path count:** {len(paths)}",
        f"- **Structural drift fields:** {len(STRUCTURAL_DRIFT_FIELDS)}",
        f"- **Semantic drift fields:** {len(SEMANTIC_DRIFT_FIELDS)}",
        "",
        "| Field path | Drift bucket |",
        "|---|---|",
    ]
    for path in paths:
        lines.append(f"| `{path}` | `{_drift_bucket(path)}` |")
    lines.extend(["", END_MARKER])
    return "\n".join(lines)


def extract_generated_section(manifest_text: str) -> str | None:
    begin = manifest_text.find(BEGIN_MARKER)
    end = manifest_text.find(END_MARKER)
    if begin == -1 or end == -1 or end < begin:
        return None
    return manifest_text[begin : end + len(END_MARKER)]


def manifest_section_is_current(manifest_text: str | None = None) -> bool:
    text = manifest_text if manifest_text is not None else MANIFEST_PATH.read_text(encoding="utf-8")
    current = extract_generated_section(text)
    expected = render_generated_section()
    return current is not None and current == expected


def refresh_manifest(*, write: bool) -> int:
    manifest = MANIFEST_PATH.read_text(encoding="utf-8")
    expected = render_generated_section()
    current = extract_generated_section(manifest)

    if current == expected:
        if write:
            print(f"{MANIFEST_PATH}: generated protected_field_paths section already current")
        return 0

    if current is None:
        anchor = manifest.find(INSERT_BEFORE_HEADING)
        if anchor == -1:
            print(f"Missing insertion anchor {INSERT_BEFORE_HEADING!r}", file=sys.stderr)
            return 1
        updated = manifest[:anchor] + expected + "\n\n" + manifest[anchor:]
    else:
        updated = manifest.replace(current, expected)

    if write:
        MANIFEST_PATH.write_text(updated, encoding="utf-8")
        print(f"Wrote generated protected_field_paths section to {MANIFEST_PATH}")
        return 0

    print(
        "Protected replay manifest generated section is out of date. "
        "Run: python tools/refresh_protected_replay_manifest.py --write",
        file=sys.stderr,
    )
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Verify the generated section matches projection.")
    mode.add_argument("--write", action="store_true", help="Rewrite the generated section in the manifest.")
    args = parser.parse_args(argv)
    return refresh_manifest(write=args.write)


if __name__ == "__main__":
    raise SystemExit(main())
