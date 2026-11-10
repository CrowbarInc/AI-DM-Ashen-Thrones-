"""Frozen benchmark bootstrap only; never reads a player's campaign as a seed."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

BASELINE_VERSION = "frontier-gate-v1"
MANIFEST_SHA256 = "9c390c78f3fcf7507793e1037eb0add59e5e373050d1996f29f0c26f3b7bf0ea"
FILES = frozenset({"campaign.json", "character.json", "conditions.json", "world.json",
                   "scenes/frontier_gate.json", "scenes/market_quarter.json", "scenes/old_milestone.json"})


class BaselineError(ValueError):
    """Missing, modified or incompatible benchmark baseline. No fallback is allowed."""


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_baseline(repo: Path) -> tuple[Path, dict]:
    source = repo / "data/validation/atgb/baselines" / BASELINE_VERSION
    try:
        manifest_path = source / "manifest.json"
        if digest(manifest_path) != MANIFEST_SHA256:
            raise BaselineError("Baseline manifest differs from the pinned version.")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if (manifest["baseline_version"] != BASELINE_VERSION or manifest["schema_version"] != 1
                or set(manifest["files"]) != FILES):
            raise BaselineError("Incompatible baseline version, schema or file inventory.")
        verify_files(source, manifest)
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        raise BaselineError(f"Baseline unavailable or invalid: {exc}") from exc
    return source, manifest


def verify_files(directory: Path, manifest: dict) -> None:
    for name in sorted(FILES):
        path = directory / name
        if not path.is_file() or digest(path) != manifest["files"][name]:
            raise BaselineError(f"Missing or incompatible baseline file: {name}")


def provenance() -> dict:
    return {"version": BASELINE_VERSION, "manifest_sha256": MANIFEST_SHA256,
            "source": f"data/validation/atgb/baselines/{BASELINE_VERSION}"}
