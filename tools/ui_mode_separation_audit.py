"""Heuristic audit helper for Objective #15 UI mode separation.

This is not a security scanner. It is a cheap "tripwire" that flags likely
regressions where code reintroduces mixed render-state consumption or cross-mode
leakage paths.

Usage:
  python tools/ui_mode_separation_audit.py
  python tools/ui_mode_separation_audit.py --root .
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_DEFAULT_IGNORES = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
    "data",
    "artifacts",
}


@dataclass(frozen=True, slots=True)
class Finding:
    kind: str
    path: Path
    line: int
    message: str


def iter_text_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dp = Path(dirpath)
        dirnames[:] = [d for d in dirnames if d not in REPO_DEFAULT_IGNORES and not d.startswith(".")]
        for fn in filenames:
            if fn.startswith("."):
                continue
            p = dp / fn
            if p.suffix.lower() in {".py", ".js", ".html", ".md"}:
                out.append(p)
    return sorted(out)


def read_lines(p: Path) -> list[str]:
    try:
        return p.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return p.read_text(encoding="utf-8", errors="replace").splitlines()


def _index_js_functions(lines: list[str]) -> dict[str, tuple[int, int]]:
    """Very small JS helper: map `function name(` blocks to (start_line, end_line).

    This is intentionally approximate; it exists only to suppress known-safe
    UI-mode separation references inside dedicated lane renderers.
    """
    starts: list[tuple[str, int]] = []
    for i, line in enumerate(lines, start=1):
        m = re.match(r"^\s*(?:async\s+)?function\s+([A-Za-z0-9_]+)\s*\(", line)
        if m:
            starts.append((m.group(1), i))
    out: dict[str, tuple[int, int]] = {}
    for idx, (name, start) in enumerate(starts):
        end = (starts[idx + 1][1] - 1) if (idx + 1) < len(starts) else len(lines)
        out[name] = (start, end)
    return out


def _line_in_fn(fn_index: dict[str, tuple[int, int]], fn_name: str, line_no: int) -> bool:
    rng = fn_index.get(fn_name)
    if not rng:
        return False
    start, end = rng
    return start <= line_no <= end


def _scan_frontend(lines: list[str], path: Path) -> list[Finding]:
    findings: list[Finding] = []
    fn_index = _index_js_functions(lines) if path.suffix == ".js" else {}
    for i, line in enumerate(lines, start=1):
        # Direct reads of hidden_facts or debug keys (outside expected render functions).
        if "hidden_facts" in line:
            # Known-safe: author-only editor and payload save path live in author-only functions.
            if _line_in_fn(fn_index, "renderAuthorState", i) or _line_in_fn(fn_index, "saveScene", i):
                continue
            findings.append(
                Finding(
                    "frontend.hidden_facts_read",
                    path,
                    i,
                    "Reference to hidden_facts (ensure author-only render path).",
                )
            )
        if re.search(r"\bdebug_traces\b|\b_final_emission_meta\b", line):
            # Known-safe: debug lane renderers.
            if _line_in_fn(fn_index, "renderDebugState", i) or _line_in_fn(fn_index, "renderEngineDebug", i):
                continue
            findings.append(
                Finding(
                    "frontend.debug_key_read",
                    path,
                    i,
                    "Reference to debug telemetry key (ensure debug-only render path).",
                )
            )

        # Rendering full JSON dumps should be debug-gated.
        if "JSON.stringify(" in line and ("debugBox" in line or "worldDebugBox" in line):
            if _line_in_fn(fn_index, "renderDebugState", i):
                continue
            findings.append(
                Finding(
                    "frontend.full_json_dump",
                    path,
                    i,
                    "JSON dump to a debug panel element (verify debug gating + clearing on mode exit).",
                )
            )

        # Mixed authoritative render state: suspicious use of /api/chat or /api/action payload as render source.
        if "renderStateEnvelope" in line and ("/chat" in "\n".join(lines[max(0, i - 20) : i + 5]) or "/action" in "\n".join(lines[max(0, i - 20) : i + 5])):
            findings.append(
                Finding(
                    "frontend.mixed_render_state",
                    path,
                    i,
                    "renderStateEnvelope appears near /api/chat or /api/action usage (render must come from /api/state).",
                )
            )
    return findings


def _scan_backend(lines: list[str], path: Path) -> list[Finding]:
    findings: list[Finding] = []
    # State projection is expected to mention lane keys.
    if path.name == "state_channels.py":
        return findings
    for i, line in enumerate(lines, start=1):
        # Endpoints should resolve ui_mode via shared helper.
        if re.search(r"@app\.(get|post)\(", line):
            window = "\n".join(lines[i - 1 : min(len(lines), i + 40)])
            if "/api/" in window and "resolve_requested_ui_mode" not in window:
                findings.append(
                    Finding(
                        "backend.endpoint_missing_ui_mode_resolution",
                        path,
                        i,
                        "Endpoint block does not reference resolve_requested_ui_mode nearby.",
                    )
                )
        # Guard usage for author/debug/runtime action
        if "/api/" in line and ("campaign" in line or "scene" in line or "world" in line):
            pass
        if "author_state" in line and "deep_project_author_payload" not in "\n".join(lines[max(0, i - 30) : i + 5]):
            findings.append(
                Finding(
                    "backend.author_state_manual_build",
                    path,
                    i,
                    "author_state referenced; verify it is produced only via state_channels projection.",
                )
            )
        if "debug_state" in line and "deep_project_debug_payload" not in "\n".join(lines[max(0, i - 30) : i + 5]):
            findings.append(
                Finding(
                    "backend.debug_state_manual_build",
                    path,
                    i,
                    "debug_state referenced; verify it is produced only via state_channels projection.",
                )
            )

        # Mixed object merge patterns that suggest recombining lanes.
        if re.search(r"public_state\s*\|\|\s*author_state|public_state\s*\|\|\s*debug_state", line):
            findings.append(
                Finding(
                    "backend.lane_merge_suspicious",
                    path,
                    i,
                    "Suspicious lane merge pattern; avoid recombining public/author/debug objects.",
                )
            )
    return findings


def scan(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for p in iter_text_files(root):
        rel = p.as_posix()
        lines = read_lines(p)

        if rel.endswith("static/app.js") or p.suffix == ".js":
            findings.extend(_scan_frontend(lines, p))
        if p.suffix == ".py" and "game/" in rel.replace("\\", "/"):
            findings.extend(_scan_backend(lines, p))
    return findings


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="repo root to scan (default: .)")
    ap.add_argument("--fail-on", default="", help="comma-separated finding kinds to treat as fatal")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    findings = scan(root)
    fail_on = {s.strip() for s in (args.fail_on or "").split(",") if s.strip()}

    if not findings:
        print("ui_mode_separation_audit: clean (no findings)")
        return 0

    # Group for readability: frontend/backend/other, then by kind.
    def group_key(f: Finding) -> tuple[str, str]:
        if f.kind.startswith("frontend."):
            return ("frontend", f.kind)
        if f.kind.startswith("backend."):
            return ("backend", f.kind)
        return ("other", f.kind)

    findings_sorted = sorted(findings, key=lambda f: (group_key(f), str(f.path), f.line))
    buckets: dict[tuple[str, str], list[Finding]] = {}
    for f in findings_sorted:
        buckets.setdefault(group_key(f), []).append(f)

    print("ui_mode_separation_audit: findings\n")
    for (area, kind), items in buckets.items():
        print(f"== {area} :: {kind} ({len(items)}) ==")
        for f in items:
            rel = f.path.relative_to(root) if f.path.is_relative_to(root) else f.path
            print(f"- {rel}:{f.line} {f.message}")
        print("")

    fatal = [f for f in findings if (not fail_on) or (f.kind in fail_on)]
    if fatal and fail_on:
        print(f"\nFATAL: {len(fatal)} findings matched --fail-on={sorted(fail_on)!r}")
        return 2
    print(f"Summary: {len(findings)} total findings across {len(buckets)} groups")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

