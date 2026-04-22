#!/usr/bin/env python3
"""Read-only presenter for canonical ContentLintReport JSON (report.as_dict()).

Does not run the lint engine; consumes JSON written by ``tools/run_content_lint.py --json-out``.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


MessageRow = Tuple[str, str, str, str]  # severity, code, message, scene_id ("" if absent)


def _die(msg: str, code: int = 1) -> None:
    sys.stderr.write(f"{msg}\n")
    raise SystemExit(code)


def _load_canonical(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        _die(f"Input not found or not a file: {path}")
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        _die(f"Failed to read {path}: {exc}")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        _die(f"Invalid JSON in {path}: {exc}")
    if not isinstance(data, dict):
        _die(f"Report root must be a JSON object: {path}")
    for key in ("ok", "error_count", "warning_count", "messages", "scene_ids_checked"):
        if key not in data:
            _die(f"Missing required key {key!r} in {path}")
    if not isinstance(data["messages"], list):
        _die(f"Expected 'messages' list in {path}")
    if not isinstance(data["scene_ids_checked"], list):
        _die(f"Expected 'scene_ids_checked' list in {path}")
    for i, m in enumerate(data["messages"]):
        if not isinstance(m, dict):
            _die(f"messages[{i}] must be an object in {path}")
        for req in ("severity", "code", "message"):
            if req not in m:
                _die(f"messages[{i}] missing {req!r} in {path}")
    return data


def _row(m: Mapping[str, Any]) -> MessageRow:
    sev = str(m.get("severity", ""))
    code = str(m.get("code", ""))
    msg = str(m.get("message", ""))
    sid = m.get("scene_id")
    sid_s = str(sid) if sid is not None else ""
    return (sev, code, msg, sid_s)


def _top_codes(messages: Sequence[Mapping[str, Any]], severity: str, top_n: int) -> List[Tuple[str, int]]:
    c: Counter[str] = Counter()
    for m in messages:
        if str(m.get("severity", "")) == severity:
            c[str(m.get("code", ""))] += 1
    ranked = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))
    return ranked[: max(0, top_n)]


def _by_scene_counts(messages: Sequence[Mapping[str, Any]]) -> Dict[str, Tuple[int, int]]:
    """scene key -> (errors, warnings). Use ``__global__`` for missing scene_id (printed as [global])."""
    out: Dict[str, List[int]] = defaultdict(lambda: [0, 0])
    for m in messages:
        sid = m.get("scene_id")
        key = "__global__" if sid is None or str(sid).strip() == "" else str(sid)
        sev = str(m.get("severity", ""))
        if sev == "error":
            out[key][0] += 1
        elif sev == "warning":
            out[key][1] += 1
    return {k: (v[0], v[1]) for k, v in out.items()}


def _format_top_codes(label: str, ranked: List[Tuple[str, int]]) -> List[str]:
    lines = [label]
    if not ranked:
        lines.append("  (none)")
    else:
        for code, n in ranked:
            lines.append(f"  {code}  x{n}")
    return lines


def _multiset_lines(title: str, ctr: Counter[MessageRow], top_n: int) -> List[str]:
    if not ctr:
        return [f"{title} (0)"]
    lines = [f"{title} ({sum(ctr.values())})"]
    # Deterministic: sort by (-count, severity, code, message, scene_id)
    items = sorted(ctr.items(), key=lambda kv: (-kv[1], kv[0][0], kv[0][1], kv[0][2], kv[0][3]))
    for (sev, code, msg, sid), n in items[: max(0, top_n)]:
        loc = f" scene_id={sid!r}" if sid else ""
        suffix = f"  x{n}" if n > 1 else ""
        lines.append(f"  [{sev}] {code}{loc}: {msg}{suffix}")
    if len(items) > top_n:
        lines.append(f"  ... ({len(items) - top_n} more)")
    return lines


def summarize_report(data: Dict[str, Any], *, input_label: str, top_n: int) -> str:
    scenes_n = len(data["scene_ids_checked"])
    err_n = int(data["error_count"])
    warn_n = int(data["warning_count"])
    messages: List[Mapping[str, Any]] = data["messages"]

    lines: List[str] = [
        f"content_lint summary ({input_label})",
        f"scenes_checked: {scenes_n}",
        f"errors: {err_n}   warnings: {warn_n}",
    ]
    lines.append("")
    lines.extend(_format_top_codes(f"top error codes (max {top_n}):", _top_codes(messages, "error", top_n)))
    lines.append("")
    lines.extend(_format_top_codes(f"top warning codes (max {top_n}):", _top_codes(messages, "warning", top_n)))

    by_scene = _by_scene_counts(messages)
    if by_scene:
        lines.append("")
        lines.append(f"by scene (errors / warnings, max {top_n} rows):")
        rows: List[Tuple[str, int, int]] = []
        for key, (e, w) in by_scene.items():
            if e or w:
                rows.append((key, e, w))
        # Deterministic: errors first, then volume, then id; [global] last among ties.
        rows.sort(key=lambda t: (0 if t[0] != "__global__" else 1, -t[1], -t[2], t[0]))
        shown = rows[: max(0, top_n)]
        for key, e, w in shown:
            label = "[global]" if key == "__global__" else f"[{key}]"
            lines.append(f"  {label} {e} / {w}")
        omitted = len(rows) - len(shown)
        if omitted > 0:
            noun = "scene" if omitted == 1 else "scenes"
            lines.append(f"  ... ({omitted} more {noun})")

    return "\n".join(lines) + "\n"


def compare_reports(
    old: Dict[str, Any],
    new: Dict[str, Any],
    *,
    old_label: str,
    new_label: str,
    top_n: int,
) -> str:
    old_msgs = old["messages"]
    new_msgs = new["messages"]
    c_old = Counter(_row(m) for m in old_msgs)
    c_new = Counter(_row(m) for m in new_msgs)

    d_err = int(new["error_count"]) - int(old["error_count"])
    d_warn = int(new["warning_count"]) - int(old["warning_count"])

    codes_old = {str(m.get("code", "")) for m in old_msgs}
    codes_new = {str(m.get("code", "")) for m in new_msgs}
    new_codes = sorted(codes_new - codes_old)
    resolved_codes = sorted(codes_old - codes_new)

    added = c_new - c_old
    removed = c_old - c_new

    lines: List[str] = [
        f"content_lint compare ({old_label} -> {new_label})",
        f"delta_error_count: {d_err:+d}",
        f"delta_warning_count: {d_warn:+d}",
        "",
        "new_codes:",
        "  " + (", ".join(new_codes) if new_codes else "(none)"),
        "",
        "resolved_codes:",
        "  " + (", ".join(resolved_codes) if resolved_codes else "(none)"),
        "",
    ]
    lines.extend(_multiset_lines("new_messages", added, top_n))
    lines.append("")
    lines.extend(_multiset_lines("resolved_messages", removed, top_n))
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Summarize canonical content-lint JSON (from run_content_lint.py --json-out).",
    )
    parser.add_argument("--input", type=Path, required=True, help="Path to canonical report JSON.")
    parser.add_argument(
        "--compare",
        type=Path,
        default=None,
        help="Optional second report; prints deltas vs --input (baseline -> compare).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=12,
        metavar="N",
        help="Max codes per severity, max by-scene rows, and max multiset rows in compare mode (default: 12).",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    top_n = int(args.top)
    if top_n < 0:
        _die("--top must be non-negative")

    base_path = args.input.resolve()
    data = _load_canonical(base_path)
    out = sys.stdout
    out.write(summarize_report(data, input_label=str(base_path), top_n=top_n))

    if args.compare is not None:
        other_path = args.compare.resolve()
        other = _load_canonical(other_path)
        out.write(
            compare_reports(
                data,
                other,
                old_label=str(base_path),
                new_label=str(other_path),
                top_n=top_n,
            )
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
