#!/usr/bin/env python3
"""Author-time CLI: run :func:`game.content_lint.lint_all_content` on scene JSON envelopes.

Loads envelopes from disk (same layout as runtime: ``data/scenes/<id>.json`` by default),
without touching gameplay or startup paths. Subset mode keeps strict cross-scene checks
against the full on-disk registry while **scoping graph reachability to loaded scenes
only** (see module comment near the ``lint_all_content`` call).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from game.content_lint import ContentLintMessage, ContentLintReport, lint_all_content  # noqa: E402
from game.storage import SCENES_DIR  # noqa: E402


def _list_scene_ids_on_disk(scenes_dir: Path) -> List[str]:
    if not scenes_dir.is_dir():
        return []
    return sorted(p.stem for p in scenes_dir.glob("*.json"))


def _load_scene_envelope_raw(scenes_dir: Path, scene_id: str) -> Dict[str, Any]:
    path = scenes_dir / f"{scene_id}.json"
    if not path.is_file():
        raise FileNotFoundError(f"No scene file for id {scene_id!r}: {path}")
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"Empty scene file: {path}")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Scene root must be a JSON object: {path}")
    return data


def _try_load_world_dict(root: Path) -> Optional[Dict[str, Any]]:
    path = root / "data" / "world.json"
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return None
    try:
        w = json.loads(text)
    except json.JSONDecodeError:
        return None
    return w if isinstance(w, dict) else None


def _parse_scene_id_args(values: Optional[Sequence[str]]) -> Optional[List[str]]:
    """Flatten ``--scene-id`` values; split comma-separated tokens; preserve first-seen order."""
    if not values:
        return None
    out: List[str] = []
    seen: Set[str] = set()
    for raw in values:
        for part in str(raw).split(","):
            sid = part.strip()
            if not sid or sid in seen:
                continue
            seen.add(sid)
            out.append(sid)
    return out or None


def _render_cli_report(report: ContentLintReport, *, quiet: bool) -> None:
    out = sys.stdout
    out.write(
        f"scenes_checked={len(report.scene_ids_checked)} "
        f"errors={report.error_count} warnings={report.warning_count}\n"
    )
    if quiet:
        return
    by_scene: Dict[str, List[ContentLintMessage]] = defaultdict(list)
    unscoped: List[ContentLintMessage] = []
    for m in report.messages:
        sid = m.scene_id
        if sid:
            by_scene[sid].append(m)
        else:
            unscoped.append(m)
    for sid in sorted(by_scene.keys()):
        out.write(f"\n[{sid}]\n")
        for m in by_scene[sid]:
            out.write(f"  {m.severity}: {m.code}: {m.message}\n")
    if unscoped:
        out.write("\n[global]\n")
        for m in unscoped:
            out.write(f"  {m.severity}: {m.code}: {m.message}\n")


def _exit_code(report: ContentLintReport, fail_on_warnings: bool) -> int:
    if report.error_count > 0:
        return 1
    if fail_on_warnings and report.warning_count > 0:
        return 2
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run author-time content lint on scene JSON files.")
    parser.add_argument(
        "--scenes-dir",
        type=Path,
        default=None,
        help=f"Directory of <scene_id>.json envelopes (default: {SCENES_DIR})",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Write the canonical ContentLintReport JSON (report.as_dict()) to this path.",
    )
    parser.add_argument("--quiet", action="store_true", help="Print only the one-line summary.")
    parser.add_argument(
        "--fail-on-warnings",
        action="store_true",
        help="Exit non-zero when there are warnings but no errors (exit code 2).",
    )
    parser.add_argument(
        "--scene-id",
        action="append",
        default=None,
        metavar="ID",
        help="Lint only these scene ids (repeatable; comma-separated lists allowed). "
        "Unknown ids are rejected. Full-disk ids are still the reference registry.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    scenes_dir = (args.scenes_dir or SCENES_DIR).resolve()
    all_ids = _list_scene_ids_on_disk(scenes_dir)
    reference_known: Set[str] = set(all_ids)

    wanted = _parse_scene_id_args(args.scene_id)
    if wanted is not None:
        unknown = sorted(set(wanted) - reference_known)
        if unknown:
            sys.stderr.write("Unknown scene id(s) (no JSON on disk): " + ", ".join(unknown) + "\n")
            return 1
        load_order = sorted(wanted)
    else:
        load_order = list(all_ids)

    scenes: Dict[str, Dict[str, Any]] = {}
    for sid in load_order:
        try:
            scenes[sid] = _load_scene_envelope_raw(scenes_dir, sid)
        except (OSError, ValueError, FileNotFoundError) as exc:
            sys.stderr.write(f"{exc}\n")
            return 1

    world = _try_load_world_dict(ROOT)

    # Subset mode: graph reachability is scoped to loaded scenes only so we do not emit
    # graph.unreachable_scene for authors' not-yet-loaded neighbors (full strict refs still
    # use reference_known / on-disk id list).
    subset = wanted is not None
    report = lint_all_content(
        scenes,
        world=world,
        graph_seed_scene_ids=None,
        reference_known_scene_ids=reference_known if subset else None,
        graph_known_scene_ids=set(scenes.keys()) if subset else None,
    )

    if args.json_out is not None:
        path = args.json_out.resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report.as_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    _render_cli_report(report, quiet=args.quiet)
    return _exit_code(report, args.fail_on_warnings)


if __name__ == "__main__":
    raise SystemExit(main())
