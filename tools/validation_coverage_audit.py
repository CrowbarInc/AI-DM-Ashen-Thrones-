#!/usr/bin/env python3
"""Objective #12 — validation coverage registry audit (governance-only, registry-driven).

Reads ``tests/validation_coverage_registry`` (typed pointers + allowlists). No ``game/``
imports, no scoring, no evaluator logic — only ``validate_entries`` and reporting.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from io import StringIO
from pathlib import Path
from typing import Sequence, TextIO

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.validation_coverage_registry import (  # noqa: E402
    REGISTRY,
    ALLOWED_BEHAVIORAL_GAUNTLET_AXES,
    CoverageEntry,
    CoverageStatus,
    RequiredSurface,
    validate_entries,
)

# Declarative bridge: registry stores pytest smoke function names; the playability runner
# uses ``tools/run_playability_validation.py`` scenario keys (see SCENARIOS there).
_PLAYABILITY_SMOKE_ID_TO_RUNNER_SCENARIO: dict[str, str] = {
    "test_playability_smoke_direct_answer_pressure": "p1_direct_answer",
    "test_playability_smoke_narrowing_player_intent": "p2_respect_intent",
    "test_playability_smoke_escalation_under_pressure": "p3_logical_escalation",
    "test_playability_smoke_immersion_guard_adversarial_upstream": "p4_immersion",
}

_SURFACE_ORDER: tuple[RequiredSurface, ...] = (
    RequiredSurface.TRANSCRIPT,
    RequiredSurface.BEHAVIORAL_GAUNTLET,
    RequiredSurface.MANUAL_GAUNTLET,
    RequiredSurface.PLAYABILITY,
    RequiredSurface.UNIT_CONTRACT,
    RequiredSurface.INTEGRATION_SMOKE,
)


def _parse_surface(raw: str) -> RequiredSurface:
    key = raw.strip().lower().replace("-", "_")
    for s in RequiredSurface:
        if s.value == key:
            return s
    allowed = ", ".join(sorted(x.value for x in RequiredSurface))
    raise argparse.ArgumentTypeError(f"unknown surface {raw!r}; expected one of: {allowed}")


def _rows(registry_override: Sequence[CoverageEntry] | None) -> tuple[CoverageEntry, ...]:
    if registry_override is not None:
        return tuple(registry_override)
    return REGISTRY


def _active_missing_surface(rows: tuple[CoverageEntry, ...], surface: RequiredSurface) -> list[str]:
    out: list[str] = []
    for e in rows:
        if e.status is not CoverageStatus.ACTIVE:
            continue
        if surface not in e.required_surfaces:
            out.append(e.feature_id)
    return sorted(out)


def _print_command_hints(entry: CoverageEntry, out: TextIO) -> None:
    out.write("\n--- Likely commands (from typed pointers only; declarative) ---\n")
    lines: list[str] = []

    for mod in entry.transcript_modules:
        m = mod.strip()
        if m:
            lines.append(f"  transcript: pytest {m}")

    if entry.behavioral_gauntlet_axes:
        lines.append(
            "  behavioral_gauntlet: pytest tests/test_behavioral_gauntlet_smoke.py "
            f"(axes in registry: {', '.join(a.strip() for a in entry.behavioral_gauntlet_axes)})",
        )
        lines.append(
            f"  behavioral_gauntlet: allowed axis ids (canonical): "
            f"{', '.join(sorted(ALLOWED_BEHAVIORAL_GAUNTLET_AXES))}",
        )

    for gid in entry.manual_gauntlets:
        g = gid.strip().lower()
        if g:
            lines.append(f"  manual_gauntlet: python tools/run_manual_gauntlet.py --gauntlet {g}")

    for scen in entry.playability_scenarios:
        s = scen.strip()
        if not s:
            continue
        lines.append(f"  playability (pytest smoke id): pytest tests/test_playability_smoke.py::{s}")
        runner = _PLAYABILITY_SMOKE_ID_TO_RUNNER_SCENARIO.get(s)
        if runner:
            lines.append(
                "  playability (runner scenario id, tools/run_playability_validation.py): "
                f"python tools/run_playability_validation.py --scenario {runner}",
            )

    for mod in entry.unit_contract_modules:
        m = mod.strip()
        if m:
            lines.append(f"  unit_contract: pytest {m}")

    for mod in entry.integration_smoke_modules:
        m = mod.strip()
        if not m:
            continue
        if m.startswith("tests/") and m.endswith(".py"):
            lines.append(f"  integration_smoke: pytest {m}")
        elif m.startswith("tools/") and m.endswith(".py"):
            lines.append(f"  integration_smoke: python {m}")
        else:
            lines.append(f"  integration_smoke: (unclassified path) {m}")

    if not lines:
        out.write("  (no pointer-derived commands)\n")
    else:
        out.write("\n".join(lines) + "\n")


def _print_summary(rows: tuple[CoverageEntry, ...], errors: list[str], out: TextIO) -> None:
    out.write("=== Objective #12 - validation coverage summary ===\n\n")
    out.write(f"Total entries: {len(rows)}\n")
    by_status = Counter(e.status.value for e in rows)
    out.write(
        "By status: "
        + ", ".join(f"{k}={by_status[k]}" for k in sorted(by_status))
        + "\n\n",
    )

    by_owner = Counter(e.owner_domain for e in rows)
    out.write("Features by owner_domain:\n")
    for dom, n in sorted(by_owner.items(), key=lambda x: (-x[1], x[0])):
        out.write(f"  {dom}: {n}\n")
    out.write("\n")

    out.write("Active features missing required surface (surface not listed in required_surfaces):\n")
    for surf in _SURFACE_ORDER:
        missing = _active_missing_surface(rows, surf)
        label = surf.value
        if missing:
            out.write(f"  missing {label}: {', '.join(missing)}\n")
        else:
            out.write(f"  missing {label}: (none)\n")
    out.write("\n")

    if errors:
        out.write(f"Registry validation: FAILED ({len(errors)} issue(s))\n")
        for err in errors:
            out.write(f"  - {err}\n")
    else:
        out.write("Registry validation: OK (no invalid references / schema issues)\n")


def _print_feature(entry: CoverageEntry, out: TextIO) -> None:
    out.write("=== Feature inspection ===\n\n")
    out.write(f"feature_id: {entry.feature_id}\n")
    out.write(f"title: {entry.title}\n")
    out.write(f"owner_domain: {entry.owner_domain}\n")
    out.write(f"status: {entry.status.value}\n")
    out.write(
        "required_surfaces: "
        + ", ".join(sorted(s.value for s in entry.required_surfaces))
        + "\n\n",
    )
    out.write("transcript_modules:\n")
    for x in entry.transcript_modules:
        out.write(f"  - {x}\n")
    if not entry.transcript_modules:
        out.write("  (empty)\n")
    out.write("behavioral_gauntlet_axes:\n")
    for x in entry.behavioral_gauntlet_axes:
        out.write(f"  - {x}\n")
    if not entry.behavioral_gauntlet_axes:
        out.write("  (empty)\n")
    out.write("manual_gauntlets:\n")
    for x in entry.manual_gauntlets:
        out.write(f"  - {x}\n")
    if not entry.manual_gauntlets:
        out.write("  (empty)\n")
    out.write("playability_scenarios:\n")
    for x in entry.playability_scenarios:
        out.write(f"  - {x}\n")
    if not entry.playability_scenarios:
        out.write("  (empty)\n")
    out.write("unit_contract_modules:\n")
    for x in entry.unit_contract_modules:
        out.write(f"  - {x}\n")
    if not entry.unit_contract_modules:
        out.write("  (empty)\n")
    out.write("integration_smoke_modules:\n")
    for x in entry.integration_smoke_modules:
        out.write(f"  - {x}\n")
    if not entry.integration_smoke_modules:
        out.write("  (empty)\n")
    out.write("\noptional_smoke_overlap:\n")
    for x in entry.optional_smoke_overlap:
        out.write(f"  - {x}\n")
    if not entry.optional_smoke_overlap:
        out.write("  (empty)\n")
    out.write("\nnotes:\n")
    if entry.notes.strip():
        out.write(entry.notes.rstrip() + "\n")
    else:
        out.write("(empty)\n")

    _print_command_hints(entry, out)


def _print_surface_filter(rows: tuple[CoverageEntry, ...], surface: RequiredSurface, out: TextIO) -> None:
    out.write(f"=== Entries declaring required surface {surface.value!r} ===\n\n")
    hits = [e for e in rows if surface in e.required_surfaces]
    if not hits:
        out.write("(none)\n")
        return
    for e in sorted(hits, key=lambda x: x.feature_id):
        out.write(f"{e.feature_id}\t{e.status.value}\t{e.owner_domain}\t{e.title}\n")


def _print_missing_filter(rows: tuple[CoverageEntry, ...], surface: RequiredSurface, out: TextIO) -> None:
    out.write(
        f"=== Active entries NOT declaring required surface {surface.value!r} "
        "(coverage gap vs that surface) ===\n\n",
    )
    miss = _active_missing_surface(rows, surface)
    if not miss:
        out.write("(none)\n")
        return
    for fid in miss:
        out.write(f"{fid}\n")


def run(
    argv: list[str] | None,
    *,
    registry_override: Sequence[CoverageEntry] | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """CLI entry for tests: optional ``registry_override`` replaces committed :data:`REGISTRY`."""

    out = stdout or sys.stdout
    err = stderr or sys.stderr

    p = argparse.ArgumentParser(
        description="Audit Objective #12 validation coverage registry (governance-only).",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help="Exit with status 2 if validate_entries reports any issues.",
    )
    mx = p.add_mutually_exclusive_group()
    mx.add_argument("--feature", metavar="FEATURE_ID", help="Inspect one feature (validation owed).")
    mx.add_argument(
        "--surface",
        metavar="SURFACE",
        type=_parse_surface,
        help="List registry rows that require this surface.",
    )
    mx.add_argument(
        "--missing",
        metavar="SURFACE",
        type=_parse_surface,
        help="List active feature_ids that do not require this surface.",
    )
    args = p.parse_args(argv)

    rows = _rows(registry_override)
    errors = validate_entries(rows)

    if args.feature:
        if args.strict and errors:
            for line in errors:
                err.write(f"{line}\n")
            return 2
        hit = next((e for e in rows if e.feature_id == args.feature), None)
        if hit is None:
            err.write(f"Unknown feature_id: {args.feature!r}\n")
            return 1
        _print_feature(hit, out)
        return 0

    if args.surface is not None:
        if args.strict and errors:
            for line in errors:
                err.write(f"{line}\n")
            return 2
        _print_surface_filter(rows, args.surface, out)
        return 0

    if args.missing is not None:
        if args.strict and errors:
            for line in errors:
                err.write(f"{line}\n")
            return 2
        _print_missing_filter(rows, args.missing, out)
        return 0

    _print_summary(rows, errors, out)
    if args.strict and errors:
        return 2
    return 0


def main(argv: list[str] | None = None) -> int:
    return run(argv, registry_override=None)


if __name__ == "__main__":
    raise SystemExit(main())
