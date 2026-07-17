"""Protected replay manifest rendering for observation field paths (CE5)."""
from __future__ import annotations

from tests.helpers.golden_replay_projection_fields import (
    PROTECTED_OBSERVATION_FIELDS,
    protected_observation_drift_bucket,
    protected_observation_field_paths,
    protected_observation_field_registry,
)

PROTECTED_REPLAY_MANIFEST_FIELD_PATHS_BEGIN = "<!-- BEGIN GENERATED: protected_field_paths -->"
PROTECTED_REPLAY_MANIFEST_FIELD_PATHS_END = "<!-- END GENERATED: protected_field_paths -->"


def protected_observation_manifest_field_rows() -> tuple[tuple[str, str], ...]:
    """Return sorted ``(path, drift_bucket)`` rows derived from ``PROTECTED_OBSERVATION_FIELDS``."""
    buckets_by_path: dict[str, str] = {}
    for field in PROTECTED_OBSERVATION_FIELDS:
        previous = buckets_by_path.setdefault(field.path, field.drift_bucket)
        if previous != field.drift_bucket:
            raise ValueError(
                f"Protected observation field {field.path!r} has conflicting drift buckets: "
                f"{previous!r} and {field.drift_bucket!r}"
            )
    return tuple((path, buckets_by_path[path]) for path in sorted(buckets_by_path))


def protected_observation_manifest_counts() -> dict[str, int]:
    """Return structural/semantic/total counts for manifest generation."""
    rows = protected_observation_manifest_field_rows()
    structural_count = sum(bucket == "structural_drift" for _path, bucket in rows)
    semantic_count = sum(bucket == "semantic_drift" for _path, bucket in rows)
    return {
        "total": len(rows),
        "structural_drift": structural_count,
        "semantic_drift": semantic_count,
    }


def render_protected_observation_manifest_section(
    *,
    begin_marker: str = PROTECTED_REPLAY_MANIFEST_FIELD_PATHS_BEGIN,
    end_marker: str = PROTECTED_REPLAY_MANIFEST_FIELD_PATHS_END,
    refresh_command: str = "python tools/refresh_protected_replay_manifest.py --write",
    check_command: str = "python tools/refresh_protected_replay_manifest.py --check",
) -> str:
    """Render the bounded protected-field-paths section for ``protected_replay_manifest.md``."""
    rows = protected_observation_manifest_field_rows()
    counts = protected_observation_manifest_counts()
    lines = [
        begin_marker,
        "",
        "## Protected Observation Field Paths (Generated)",
        "",
        "Bounded registry of golden replay observation paths locked by protected replay.",
        "Source: `tests/helpers/golden_replay_projection.py::PROTECTED_OBSERVATION_FIELDS`.",
        "",
        "Refresh this section:",
        "",
        "```bash",
        refresh_command,
        "```",
        "",
        "Verify without writing:",
        "",
        "```bash",
        check_command,
        "```",
        "",
        f"- **Path count:** {counts['total']}",
        f"- **Structural drift fields:** {counts['structural_drift']}",
        f"- **Semantic drift fields:** {counts['semantic_drift']}",
        "",
        "| Field path | Drift bucket |",
        "|---|---|",
    ]
    for path, bucket in rows:
        lines.append(f"| `{path}` | `{bucket}` |")
    lines.extend(["", end_marker])
    return "\n".join(lines)


def extract_protected_observation_manifest_section(
    manifest_text: str,
    *,
    begin_marker: str = PROTECTED_REPLAY_MANIFEST_FIELD_PATHS_BEGIN,
    end_marker: str = PROTECTED_REPLAY_MANIFEST_FIELD_PATHS_END,
) -> str | None:
    """Extract the generated protected-field-paths section from manifest markdown."""
    begin = manifest_text.find(begin_marker)
    end = manifest_text.find(end_marker)
    if begin == -1 or end == -1 or end < begin:
        return None
    return manifest_text[begin : end + len(end_marker)]


def protected_observation_manifest_section_is_current(manifest_text: str) -> bool:
    """Return True when the manifest generated section matches ``PROTECTED_OBSERVATION_FIELDS``."""
    current = extract_protected_observation_manifest_section(manifest_text)
    expected = render_protected_observation_manifest_section()
    return current is not None and current == expected


def protected_observation_manifest_registry_parity_errors(
    manifest_text: str,
) -> list[str]:
    """Return parity drift messages when manifest docs diverge from the protected observation registry."""
    errors: list[str] = []

    if extract_protected_observation_manifest_section(manifest_text) is None:
        errors.append(
            "missing generated manifest section markers "
            f"{PROTECTED_REPLAY_MANIFEST_FIELD_PATHS_BEGIN!r} / "
            f"{PROTECTED_REPLAY_MANIFEST_FIELD_PATHS_END!r}"
        )
        return errors

    if not protected_observation_manifest_section_is_current(manifest_text):
        errors.append(
            "generated manifest section is stale; "
            "run: python tools/refresh_protected_replay_manifest.py --write"
        )

    manifest_rows = dict(protected_observation_manifest_field_rows())
    registry_paths = protected_observation_field_paths()
    manifest_paths = tuple(manifest_rows)

    if manifest_paths != registry_paths:
        extra = sorted(set(manifest_paths) - set(registry_paths))
        missing = sorted(set(registry_paths) - set(manifest_paths))
        if extra:
            errors.append(f"manifest has paths not in registry: {extra!r}")
        if missing:
            errors.append(f"manifest missing registry paths: {missing!r}")

    for field in protected_observation_field_registry():
        registry_bucket = field.drift_bucket
        drift_bucket = protected_observation_drift_bucket(field.path)
        if drift_bucket != registry_bucket:
            errors.append(
                f"protected_observation_drift_bucket({field.path!r})={drift_bucket!r} "
                f"but registry declares {registry_bucket!r}"
            )
        manifest_bucket = manifest_rows.get(field.path)
        if manifest_bucket is not None and manifest_bucket != registry_bucket:
            errors.append(
                f"manifest drift bucket for {field.path!r} is {manifest_bucket!r}, "
                f"registry declares {registry_bucket!r}"
            )

    return errors
