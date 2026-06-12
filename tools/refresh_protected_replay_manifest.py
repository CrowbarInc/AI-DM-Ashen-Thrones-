#!/usr/bin/env python3
"""Refresh or verify the generated protected-field-paths section in the replay manifest.

Report-only governance helper: reads the canonical protected observation registry
(``PROTECTED_OBSERVATION_FIELDS``) from golden replay projection and keeps
``docs/testing/protected_replay_manifest.md`` aligned.
"""

from __future__ import annotations

import argparse
import sys
from difflib import unified_diff
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.helpers.golden_replay_projection import (  # noqa: E402
    PROTECTED_OBSERVATION_FIELDS,
    PROTECTED_REPLAY_MANIFEST_FIELD_PATHS_BEGIN,
    PROTECTED_REPLAY_MANIFEST_FIELD_PATHS_END,
    extract_protected_observation_manifest_section,
    protected_observation_drift_bucket,
    protected_observation_field_paths,
    protected_observation_field_registry,
    protected_observation_manifest_registry_parity_errors,
    protected_observation_manifest_section_is_current,
    protected_observation_manifest_field_rows,
    render_protected_observation_manifest_section,
)

MANIFEST_PATH = ROOT / "docs" / "testing" / "protected_replay_manifest.md"
BEGIN_MARKER = PROTECTED_REPLAY_MANIFEST_FIELD_PATHS_BEGIN
END_MARKER = PROTECTED_REPLAY_MANIFEST_FIELD_PATHS_END
INSERT_BEFORE_HEADING = "## Cycle S Drift Policy Addendum"


def _registry_fields_by_path() -> dict[str, str]:
    """Return registry path -> drift bucket via canonical registry accessors."""
    return {
        path: protected_observation_drift_bucket(path)
        for path in protected_observation_field_paths()
    }


def render_generated_section() -> str:
    """Return the bounded manifest section for protected observation field paths."""
    return render_protected_observation_manifest_section()


def extract_generated_section(manifest_text: str) -> str | None:
    return extract_protected_observation_manifest_section(manifest_text)


def manifest_section_is_current(manifest_text: str | None = None) -> bool:
    text = manifest_text if manifest_text is not None else MANIFEST_PATH.read_text(encoding="utf-8")
    return protected_observation_manifest_section_is_current(text)


def _validate_registry_invariants() -> str | None:
    paths = protected_observation_field_paths()
    if len(paths) != len(set(paths)):
        from collections import Counter

        duplicates = sorted(path for path, count in Counter(paths).items() if count > 1)
        return f"Protected observation registry has duplicate paths: {duplicates!r}"
    if len(protected_observation_field_registry()) != len(PROTECTED_OBSERVATION_FIELDS):
        return (
            "protected_observation_field_registry() must mirror PROTECTED_OBSERVATION_FIELDS: "
            f"registry={len(protected_observation_field_registry())!r} "
            f"fields={len(PROTECTED_OBSERVATION_FIELDS)!r}"
        )
    rows = protected_observation_manifest_field_rows()
    if len(rows) != len(paths):
        return (
            "Protected observation manifest rows disagree with registry path count: "
            f"rows={len(rows)!r} paths={len(paths)!r}"
        )
    for field in protected_observation_field_registry():
        bucket = protected_observation_drift_bucket(field.path)
        if bucket != field.drift_bucket:
            return (
                f"protected_observation_drift_bucket({field.path!r})={bucket!r} "
                f"but registry declares {field.drift_bucket!r}"
            )
    return None


def _manifest_drift_message(manifest_text: str, expected: str, current: str | None) -> str:
    if current is None:
        return (
            f"Missing generated section markers {BEGIN_MARKER!r} / {END_MARKER!r} in {MANIFEST_PATH}."
        )
    diff_lines = list(
        unified_diff(
            current.splitlines(),
            expected.splitlines(),
            fromfile="manifest (current)",
            tofile="registry (expected)",
            lineterm="",
        )
    )
    preview = "\n".join(diff_lines[:40])
    if len(diff_lines) > 40:
        preview += f"\n... ({len(diff_lines) - 40} more diff lines)"
    return (
        "Protected replay manifest generated section is out of date.\n"
        "Run: python tools/refresh_protected_replay_manifest.py --write\n"
        f"{preview}"
    )


def refresh_manifest(*, write: bool) -> int:
    invariant_error = _validate_registry_invariants()
    if invariant_error is not None:
        print(invariant_error, file=sys.stderr)
        return 1

    manifest = MANIFEST_PATH.read_text(encoding="utf-8")
    parity_errors = protected_observation_manifest_registry_parity_errors(manifest)
    if parity_errors and not write:
        print("\n".join(parity_errors), file=sys.stderr)
        return 1

    expected = render_generated_section()
    current = extract_generated_section(manifest)

    if current == expected:
        if write:
            print(f"{MANIFEST_PATH}: generated protected_field_paths section already current")
        return 0

    if not write:
        print(_manifest_drift_message(manifest, expected, current), file=sys.stderr)
        return 1

    if current is None:
        anchor = manifest.find(INSERT_BEFORE_HEADING)
        if anchor == -1:
            print(f"Missing insertion anchor {INSERT_BEFORE_HEADING!r}", file=sys.stderr)
            return 1
        updated = manifest[:anchor] + expected + "\n\n" + manifest[anchor:]
    else:
        updated = manifest.replace(current, expected)

    MANIFEST_PATH.write_text(updated, encoding="utf-8")
    print(f"Wrote generated protected_field_paths section to {MANIFEST_PATH}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--check",
        action="store_true",
        help="Verify the generated section matches PROTECTED_OBSERVATION_FIELDS.",
    )
    mode.add_argument("--write", action="store_true", help="Rewrite the generated section in the manifest.")
    args = parser.parse_args(argv)
    return refresh_manifest(write=args.write)


if __name__ == "__main__":
    raise SystemExit(main())
