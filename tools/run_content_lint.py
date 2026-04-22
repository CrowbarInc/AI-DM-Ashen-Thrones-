#!/usr/bin/env python3
"""Author-time CLI: run :func:`game.content_lint.lint_all_content` on scene JSON envelopes.

Loads envelopes from disk (same layout as runtime: ``data/scenes/<id>.json`` by default),
without touching gameplay or startup paths. World data is loaded only from predictable
locations (see ``--world-json``, ``--no-world``, and default adjacent ``world.json`` under
``<parent of --scenes-dir>/``). Subset mode keeps strict cross-scene checks against the full
on-disk registry while **scoping graph reachability to loaded scenes only** (see
``lint_all_content`` call site).
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


def _try_load_world_adjacent_to_scenes_dir(scenes_dir: Path) -> Optional[Dict[str, Any]]:
    """Load ``world.json`` next to the scenes package (``<parent>/world.json``).

    Default layout: ``data/world.json`` beside ``data/scenes``. Ephemeral test dirs without
    that file simply omit world context (avoids coupling a temp ``--scenes-dir`` to the
    repository's shipped ``data/world.json``).
    """
    path = scenes_dir.resolve().parent / "world.json"
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


def _load_world_json_strict(path: Path) -> Dict[str, Any]:
    """Load ``world.json`` from an explicit path; fail closed on missing/invalid content."""
    rp = path.resolve()
    if not rp.is_file():
        raise FileNotFoundError(f"--world-json path is not a file: {rp}")
    text = rp.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"Empty world file: {rp}")
    try:
        w = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in world file {rp}: {exc}") from exc
    if not isinstance(w, dict):
        raise ValueError(f"World root must be a JSON object: {rp}")
    return w


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


def _message_code_family(code: str) -> str:
    """First dot-separated segment of a stable lint code (used for CLI grouping only)."""
    return code.split(".", 1)[0] if code else "other"


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
            fam = _message_code_family(m.code)
            out.write(f"  {m.severity} [{fam}]: {m.code}: {m.message}\n")
    if unscoped:
        out.write("\n[global]\n")
        for m in unscoped:
            fam = _message_code_family(m.code)
            out.write(f"  {m.severity} [{fam}]: {m.code}: {m.message}\n")


def _exit_code(report: ContentLintReport, fail_on_warnings: bool) -> int:
    if report.error_count > 0:
        return 1
    if fail_on_warnings and report.warning_count > 0:
        return 2
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Author-time content lint: loads scene JSON envelopes from disk and runs the same "
            "deterministic engine as in-process lint_all_content (scene rules + graph + bundle/N2 governance). "
            "Does not start the game or touch runtime hot paths."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Modes:\n"
            "  Full (default) - load every <id>.json under --scenes-dir; graph and strict refs use the full set.\n"
            "  Subset - pass --scene-id one or more times: only those envelopes load, but strict cross-scene refs\n"
            "    and the bundle world<->scene registry still treat every *.json stem on disk as known targets\n"
            "    (reference registry). Graph reachability (e.g. graph.unreachable_scene) is scoped to loaded ids only.\n"
            "\n"
            "World bundle:\n"
            "  Default - if <parent of --scenes-dir>/world.json exists and parses, it is loaded; else no world.\n"
            "  --world-json PATH - load exactly that file (must exist, non-empty object JSON); errors exit 1.\n"
            "  --no-world - never load world (skips adjacent file even when present). Mutually exclusive with --world-json.\n"
            "\n"
            "Exit codes (unchanged):\n"
            "  0 - report has zero errors (warnings allowed unless --fail-on-warnings).\n"
            "  1 - one or more error-severity messages, or CLI/load failure (unknown --scene-id, invalid JSON, I/O).\n"
            "  2 - --fail-on-warnings and warning_count > 0 while error_count == 0."
        ),
    )
    parser.add_argument(
        "--scenes-dir",
        type=Path,
        default=None,
        help=f"Directory of <scene_id>.json envelopes (default: {SCENES_DIR}).",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Write canonical ContentLintReport JSON (report.as_dict()) to PATH (parents created).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Print only the one-line summary (scenes_checked / errors / warnings).",
    )
    parser.add_argument(
        "--fail-on-warnings",
        action="store_true",
        help="If the report has warnings but zero errors, exit 2 instead of 0.",
    )
    parser.add_argument(
        "--scene-id",
        action="append",
        default=None,
        metavar="ID",
        help=(
            "Subset mode: lint only these scene ids (repeatable; comma-separated lists allowed). "
            "Unknown ids (no matching .json on disk) exit 1. Strict refs + bundle registry still use all stems on disk."
        ),
    )
    parser.add_argument(
        "--world-json",
        type=Path,
        default=None,
        help="Load world.json from this path only (must be a readable file with a JSON object root).",
    )
    parser.add_argument(
        "--no-world",
        action="store_true",
        help="Do not load world.json (no bundle/world context from disk for this run).",
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

    if args.no_world and args.world_json is not None:
        sys.stderr.write("Cannot combine --no-world with --world-json.\n")
        return 1

    world: Optional[Dict[str, Any]] = None
    if args.no_world:
        world = None
    elif args.world_json is not None:
        try:
            world = _load_world_json_strict(args.world_json)
        except (OSError, ValueError, FileNotFoundError) as exc:
            sys.stderr.write(f"{exc}\n")
            return 1
    else:
        world = _try_load_world_adjacent_to_scenes_dir(scenes_dir)

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
