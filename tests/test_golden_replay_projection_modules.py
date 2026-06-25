from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

import tests.helpers.golden_replay_projection as facade
import tests.helpers.golden_replay_projection_extractors as extractors
import tests.helpers.golden_replay_projection_fallbacks as fallbacks
import tests.helpers.golden_replay_projection_fields as fields
import tests.helpers.golden_replay_projection_manifest as manifest
import tests.helpers.golden_replay_projection_speaker as speaker

BACKUP_PATH = Path(__file__).resolve().parents[1] / "tests" / "helpers" / "golden_replay_projection.py.bak"

PROJECTION_MODULES: tuple[str, ...] = (
    "tests.helpers.golden_replay_projection_fields",
    "tests.helpers.golden_replay_projection_manifest",
    "tests.helpers.golden_replay_projection_extractors",
    "tests.helpers.golden_replay_projection_fallbacks",
    "tests.helpers.golden_replay_projection_speaker",
    "tests.helpers.golden_replay_projection",
)

PUBLIC_FACADE_SYMBOLS: tuple[str, ...] = (
    "MISSING",
    "NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY",
    "PROTECTED_OBSERVATION_FIELDS",
    "PROTECTED_REPLAY_MANIFEST_FIELD_PATHS_BEGIN",
    "PROTECTED_REPLAY_MANIFEST_FIELD_PATHS_END",
    "REPLAY_FALLBACK_FAMILY_FEM_PRECEDENCE_KEYS",
    "SEMANTIC_DRIFT_FIELDS",
    "STRUCTURAL_DRIFT_FIELDS",
    "ProtectedObservationField",
    "SpeakerProjectionParityStatus",
    "dual_fallback_family_replay_precedence_surface",
    "extract_protected_observation_manifest_section",
    "final_text_has_scaffold_leakage",
    "golden_text_hash",
    "lookup_observation_path",
    "normalize_golden_text",
    "observed_projection_schema_defaults",
    "project_replay_fallback_family_from_fem",
    "project_semantic_mutation_summary",
    "project_speaker_projection_parity",
    "project_turn_observation",
    "protected_classifier_evidence_excluded_paths",
    "protected_classifier_evidence_field_paths",
    "protected_observation_default_row",
    "protected_observation_drift_bucket",
    "protected_observation_extraction_registry",
    "protected_observation_extraction_source_by_path",
    "protected_observation_field_paths",
    "protected_observation_field_registry",
    "protected_observation_flat_field_paths",
    "protected_observation_manifest_counts",
    "protected_observation_manifest_field_rows",
    "protected_observation_manifest_registry_parity_errors",
    "protected_observation_manifest_section_is_current",
    "protected_path_covered_by_unavailable",
    "protected_path_is_represented_in_observed_turn",
    "protected_path_representation_errors",
    "read_final_speaker_observation_for_replay",
    "render_protected_observation_manifest_section",
)


def _load_backup_module():
    import sys
    import types

    source = BACKUP_PATH.read_text(encoding="utf-8")
    mod = types.ModuleType("golden_replay_projection_backup")
    sys.modules[mod.__name__] = mod
    exec(compile(source, str(BACKUP_PATH), "exec"), mod.__dict__)
    return mod


@pytest.mark.parametrize("name", PUBLIC_FACADE_SYMBOLS)
def test_facade_reexports_public_projection_symbols(name: str) -> None:
    assert hasattr(facade, name), f"missing facade symbol {name!r}"


def test_protected_observation_fields_order_and_content_unchanged_from_backup() -> None:
    backup = _load_backup_module()
    backup_fields = backup.PROTECTED_OBSERVATION_FIELDS
    current_fields = facade.PROTECTED_OBSERVATION_FIELDS

    assert current_fields is not backup_fields
    assert len(current_fields) == len(backup_fields) == 41
    assert tuple(field.path for field in current_fields) == tuple(field.path for field in backup_fields)
    assert tuple((field.path, field.drift_bucket) for field in current_fields) == tuple(
        (field.path, field.drift_bucket) for field in backup_fields
    )


def test_render_protected_observation_manifest_section_unchanged_from_backup() -> None:
    backup = _load_backup_module()
    assert facade.render_protected_observation_manifest_section() == backup.render_protected_observation_manifest_section()


def test_projection_module_import_graph_has_no_cycles() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    helpers = repo_root / "tests" / "helpers"

    def module_imports(module_name: str) -> set[str]:
        rel = module_name.removeprefix("tests.helpers.") + ".py"
        path = helpers / rel
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith(
                "tests.helpers.golden_replay_projection"
            ):
                imports.add(node.module)
        return imports

    graph = {name: module_imports(name) for name in PROJECTION_MODULES}
    visiting: set[str] = set()
    visited: set[str] = set()

    def dfs(node: str) -> None:
        if node in visiting:
            raise AssertionError(f"import cycle detected at {node!r}; graph={graph!r}")
        if node in visited:
            return
        visiting.add(node)
        for dep in graph.get(node, ()):
            if dep in graph:
                dfs(dep)
        visiting.remove(node)
        visited.add(node)

    for module_name in PROJECTION_MODULES:
        dfs(module_name)


def test_focused_modules_do_not_import_facade() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    helpers = repo_root / "tests" / "helpers"
    for module_name in PROJECTION_MODULES[:-1]:
        rel = module_name.removeprefix("tests.helpers.") + ".py"
        tree = ast.parse((helpers / rel).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "tests.helpers.golden_replay_projection":
                raise AssertionError(f"{module_name} must not import facade")


def test_submodule_identity_matches_facade_for_registry_and_manifest() -> None:
    assert facade.PROTECTED_OBSERVATION_FIELDS is fields.PROTECTED_OBSERVATION_FIELDS
    assert facade.render_protected_observation_manifest_section is manifest.render_protected_observation_manifest_section
    assert facade.project_replay_fallback_family_from_fem is fallbacks.project_replay_fallback_family_from_fem
    assert facade.project_speaker_projection_parity is speaker.project_speaker_projection_parity
    assert facade.protected_observation_extraction_registry is extractors.protected_observation_extraction_registry
