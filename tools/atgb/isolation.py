"""Campaign-data isolation for benchmark runs.

Reset is refused until the resolved directory is a fresh benchmark store.
A warning is not the safeguard.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from tools.atgb.baseline import load_baseline, provenance, verify_files

MARKER_NAME = ".atgb-isolated"
RUNTIME_MARKERS = (
    "session.json",
    "session_log.jsonl",
    "combat.json",
    "snapshots",
)
BOOTSTRAP_FILES = (
    "campaign.json",
    "character.json",
    "conditions.json",
    "world.json",
)


class UnsafeBenchmarkDataDir(RuntimeError):
    """The resolved directory is not safe to reset or to use as a benchmark store."""


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def canonical_data_dir(root: Path | None = None) -> Path:
    return ((root or repo_root()) / "data").resolve()


def player_campaign_dir_from_env(root: Path | None = None) -> Path:
    """The campaign directory this process would use before a benchmark retargets it."""

    override = os.environ.get("ASHEN_DATA_DIR", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return canonical_data_dir(root)


def _same_or_nested(candidate: Path, protected: Path) -> bool:
    if candidate == protected:
        return True
    if protected in candidate.parents:
        return True
    if candidate in protected.parents:
        return True
    return False


def assert_safe_benchmark_data_dir(
    candidate: Path,
    *,
    repo: Path | None = None,
    player_campaign_dir: Path | None = None,
) -> Path:
    """Reject canonical data, the active player campaign, and directories that contain either."""

    root = (repo or repo_root()).resolve()
    resolved = Path(candidate).expanduser().resolve()
    canonical = canonical_data_dir(root)
    active = (player_campaign_dir or player_campaign_dir_from_env(root)).expanduser().resolve()

    if _same_or_nested(resolved, canonical):
        raise UnsafeBenchmarkDataDir(
            f"Refusing benchmark data directory {resolved}. "
            f"It is the repository canonical game-data directory or contains it ({canonical})."
        )
    if _same_or_nested(resolved, active):
        raise UnsafeBenchmarkDataDir(
            f"Refusing benchmark data directory {resolved}. "
            f"It is the active player campaign directory or contains it ({active})."
        )
    if resolved == root or resolved in root.parents:
        raise UnsafeBenchmarkDataDir(
            f"Refusing benchmark data directory {resolved}. It contains the repository."
        )
    try:
        resolved.relative_to(root)
        inside_repo = True
    except ValueError:
        inside_repo = False
    if inside_repo:
        artifacts = (root / "artifacts" / "atgb").resolve()
        tmp_root = (root / "development" / "tmp").resolve()
        allowed = _same_or_nested(resolved, artifacts) or _same_or_nested(resolved, tmp_root)
        if not allowed or resolved in {artifacts, tmp_root, root / "artifacts", root / "development"}:
            raise UnsafeBenchmarkDataDir(
                f"Refusing benchmark data directory {resolved}. Inside the repository, "
                "an isolated store must be a new directory under artifacts/atgb/ or development/tmp/."
            )
    return resolved


def assert_fresh_store(resolved: Path) -> None:
    """Refuse to reset a directory that already holds campaign runtime or a prior benchmark."""

    if not resolved.exists():
        return
    if not resolved.is_dir():
        raise UnsafeBenchmarkDataDir(f"Refusing benchmark data directory {resolved}. It is not a directory.")
    marker = resolved / MARKER_NAME
    if marker.exists():
        raise UnsafeBenchmarkDataDir(
            f"Refusing to reuse benchmark store {resolved}. "
            "Each scenario requires a new directory so earlier benchmark state cannot carry over."
        )
    occupied = [name for name in (*RUNTIME_MARKERS, *BOOTSTRAP_FILES) if (resolved / name).exists()]
    if occupied:
        raise UnsafeBenchmarkDataDir(
            f"Refusing to reset {resolved}. It already contains campaign files ({', '.join(occupied)}). "
            "Benchmark execution will not call the campaign reset on an existing campaign."
        )
    extras = [entry.name for entry in resolved.iterdir()]
    if extras:
        raise UnsafeBenchmarkDataDir(
            f"Refusing benchmark data directory {resolved}. It is not empty ({', '.join(extras)})."
        )


def prepare_isolated_store(
    candidate: Path,
    *,
    scenario_id: str,
    repo: Path | None = None,
    player_campaign_dir: Path | None = None,
    source_data_dir: Path | None = None,
) -> Path:
    """Create a fresh store and copy bootstrap files. Does not reset and does not import the game."""

    root = (repo or repo_root()).resolve()
    resolved = assert_safe_benchmark_data_dir(
        candidate,
        repo=root,
        player_campaign_dir=player_campaign_dir,
    )
    assert_fresh_store(resolved)
    source, baseline = load_baseline(root)
    if source_data_dir is not None and source_data_dir.resolve() != source.resolve():
        raise UnsafeBenchmarkDataDir(
            "Benchmark bootstrap accepts only the pinned baseline; alternate campaign data is refused."
        )
    resolved.mkdir(parents=True, exist_ok=True)
    marker_body = {
        "marker": "atgb-isolated-store",
        "scenario_id": scenario_id,
        "baseline": provenance(),
        "reset_allowed": False,
        "note": "Reset is allowed only in a process whose ASHEN_DATA_DIR resolves here after this marker exists.",
    }
    (resolved / MARKER_NAME).write_text(json.dumps(marker_body, indent=2) + "\n", encoding="utf-8")
    for name in BOOTSTRAP_FILES:
        source_path = source / name
        if not source_path.is_file():
            raise UnsafeBenchmarkDataDir(f"Missing bootstrap file {source_path}.")
        shutil.copy2(source_path, resolved / name)
    scenes = source / "scenes"
    if not scenes.is_dir():
        raise UnsafeBenchmarkDataDir(f"Missing bootstrap scene directory {scenes}.")
    shutil.copytree(scenes, resolved / "scenes")
    verify_files(resolved, baseline)
    for name in RUNTIME_MARKERS:
        if (resolved / name).exists():
            raise UnsafeBenchmarkDataDir(
                f"Bootstrap copy placed runtime file {name} into {resolved}. The canonical runtime was not an allowed source."
            )
    return resolved


def assert_imported_data_dir(imported_data_dir: Path, expected: Path, *, repo: Path | None = None, player_campaign_dir: Path | None = None) -> Path:
    """Confirm the game package bound the isolated directory. Call this before reset."""

    bound = Path(imported_data_dir).resolve()
    target = Path(expected).expanduser().resolve()
    if bound != target:
        raise UnsafeBenchmarkDataDir(
            f"Game DATA_DIR resolved to {bound}, not the isolated store {target}. Reset was not invoked."
        )
    assert_safe_benchmark_data_dir(bound, repo=repo, player_campaign_dir=player_campaign_dir)
    marker = bound / MARKER_NAME
    if not marker.is_file():
        raise UnsafeBenchmarkDataDir(f"Isolated store {bound} has no ATGB marker. Reset was not invoked.")
    return bound
