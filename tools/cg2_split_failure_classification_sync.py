"""One-shot CG-2 extraction: split failure_classification_sync into focused modules.

Historical / non-runtime: retained for audit archaeology only; do not run against current helpers.
References removed CK Block 3–5 alias and compat-local token paths.
"""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "tests/helpers/failure_classification_sync.py"
lines = SRC.read_text(encoding="utf-8").splitlines(keepends=True)

# Original import block (lines 11-100, 0-indexed 10-100)
IMPORT_BLOCK = "".join(lines[10:100])

BUILDERS_IMPORTS = """from game.attribution_read_views import (
    OPENING_FALLBACK_SELECTION_OWNER,
    SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_FALLBACK_SELECTION_OWNER,
    SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
    SANITIZER_STRICT_SOCIAL_PROSE_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_STRICT_SOCIAL_SELECTION_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_TRACE_SELECTION_OWNER_SHORT,
    SANITIZER_TRACE_STRICT_SOCIAL_PROSE_OWNER_SHORT,
    SEALED_FALLBACK_MODULE_CONTENT_OWNER,
    SEALED_FALLBACK_OWNER_SEALED_GATE,
    SEALED_FALLBACK_SELECTION_OWNER,
    UPSTREAM_FAST_FALLBACK_CONTENT_OWNER,
    UPSTREAM_FAST_FALLBACK_SELECTION_OWNER,
    VISIBILITY_FALLBACK_SELECTION_OWNER,
)
from game.final_emission_replay_projection import (
    FIRST_MENTION_HARD_REPLACEMENT,
    REFERENTIAL_CLARITY_HARD_REPLACEMENT,
    VISIBILITY_HARD_REPLACEMENT,
)
from game.runtime_lineage_telemetry import make_runtime_lineage_event
from tests.helpers.failure_classifier import classify_replay_failure
from tests.helpers.opening_fallback_evidence import (
    OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL,
    OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED,
    OPENING_FALLBACK_FAMILY,
    OPENING_SUCCESS_REPAIR_KIND,
    fail_closed_opening_observed_fields,
    successful_opening_observed_fields,
)
from tests.helpers.replay_observed_row_fixtures import (
    SyntheticObservedRowProfile,
    observed_dashboard_probe_row,
    observed_failure_row,
)
"""

SPLIT_OWNER_IMPORTS = """from game.attribution_read_views import (
    OPENING_FAIL_CLOSED_CONTENT_OWNER,
    OPENING_FALLBACK_CONTENT_OWNER,
    OPENING_FALLBACK_OWNER_SEALED_GATE,
    OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
    OPENING_FALLBACK_SELECTION_OWNER,
    SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_FALLBACK_SELECTION_OWNER,
    SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
    SANITIZER_STRICT_SOCIAL_PROSE_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_STRICT_SOCIAL_SELECTION_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_TRACE_SELECTION_OWNER_SHORT,
    SANITIZER_TRACE_STRICT_SOCIAL_PROSE_OWNER_SHORT,
    SEALED_FALLBACK_MODULE_CONTENT_OWNER,
    SEALED_FALLBACK_OWNER_SEALED_GATE,
    SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED,
    SEALED_FALLBACK_OWNER_UNKNOWN_NONE,
    SEALED_FALLBACK_SELECTION_OWNER,
    SEALED_FALLBACK_UNKNOWN_CONTENT_OWNER,
    STRICT_SOCIAL_FALLBACK_CONTENT_OWNER,
    UPSTREAM_FAST_FALLBACK_CONTENT_OWNER,
    UPSTREAM_FAST_FALLBACK_SELECTION_OWNER,
    VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY,
    VISIBILITY_FALLBACK_SELECTION_OWNER,
)
from game.final_emission_replay_projection import (
    FIRST_MENTION_HARD_REPLACEMENT,
    REFERENTIAL_CLARITY_HARD_REPLACEMENT,
    VISIBILITY_HARD_REPLACEMENT,
)
from game.runtime_lineage_telemetry import make_runtime_lineage_event
from tests.helpers.opening_fallback_evidence import OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED
from tests.helpers.replay_observed_row_fixtures import SyntheticObservedRowProfile
from tests.helpers.failure_classification_builders import (
    exact_value_drift_row,
    observed_opening_family_split_owner_row,
    observed_referential_local_substitution_classifier_row,
    observed_sanitizer_split_owner_row,
    observed_sealed_family_split_owner_row,
    observed_upstream_fast_split_owner_row,
    observed_visibility_family_hard_replacement_row,
    opening_family_fallback_selected_lineage_event,
    sanitizer_fallback_selected_lineage_event,
    sealed_family_fallback_selected_lineage_event,
    upstream_fast_fallback_selected_lineage_event,
    visibility_family_fallback_selected_lineage_event,
)
"""

DASHBOARD_IMPORTS = """from typing import Any, Mapping

from game.attribution_read_views import (
    SANITIZER_FALLBACK_SELECTION_OWNER,
    SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
)
from tests.helpers.failure_classifier import validate_failure_classification_row
from tests.helpers.failure_classification_split_owner import (
    SPLIT_OWNER_ACCEPTANCE_MATRIX,
    SplitOwnerAcceptanceRow,
    split_owner_matrix_classifier_drift_row,
    split_owner_matrix_legacy,
    split_owner_observed_row_from_matrix_row,
)
from tests.helpers.failure_classification_alignment import (
    failure_classification_row_contract_fields,
)
"""

ALIGNMENT_IMPORTS = """from pathlib import Path
from typing import Any, Mapping, Sequence, get_origin, get_type_hints

from tests.failure_classification_contract import (
    ALLOWED_CLASSIFICATION_ROW_FIELDS,
    ALLOWED_FAILURE_CATEGORIES,
    ALLOWED_OPENING_FALLBACK_OWNER_BUCKETS,
    ALLOWED_PRIMARY_OWNERS,
    ALLOWED_RUNTIME_RESPONSE_TYPE_REPAIR_KINDS,
    ALLOWED_SEALED_FALLBACK_OWNER_BUCKETS,
    ALLOWED_SECONDARY_OWNERS,
    ALLOWED_SOURCE_FAMILY_TAGS,
    ALLOWED_VISIBILITY_FALLBACK_OWNER_BUCKETS,
    CLASSIFIER_EVIDENCE_EXTENSION_FIELDS,
    CLASSIFIER_EVIDENCE_FIELDS,
    LEGACY_RESPONSE_TYPE_REPAIR_KINDS,
    MAJOR_OWNER_INVESTIGATION_TARGETS,
    OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS,
    PROTECTED_CLASSIFIER_EVIDENCE_FIELDS,
    REQUIRED_CLASSIFICATION_FIELDS,
)
from tests.helpers.failure_classifier import (
    CATEGORY_RULES,
    FailureClassification,
    INVESTIGATION_TARGETS,
    PRIMARY_OWNER_RULES,
    SECONDARY_OWNER_RULES,
    validate_failure_classification_row,
)
from tests.helpers.golden_replay_projection import (
    protected_classifier_evidence_excluded_paths,
    protected_classifier_evidence_field_paths,
    protected_observation_drift_bucket,
    protected_observation_field_paths,
    protected_observation_field_registry,
)
from tests.helpers.failure_classification_dashboard_expectations import (
    failure_dashboard_row_shape_errors,
    failure_classification_row_contract_misalignments,
)
"""


def slice_lines(start: int, end: int) -> str:
    return "".join(lines[start - 1 : end])


def write_module(path: Path, docstring: str, imports: str, body: str) -> None:
    content = f'"""{docstring}"""\nfrom __future__ import annotations\n\n{imports}\n{body}'
    path.write_text(content, encoding="utf-8")
    print(f"wrote {path.name}: {len(content.splitlines())} lines")


def main() -> None:
    helpers = REPO / "tests/helpers"

    write_module(
        helpers / "failure_classification_builders.py",
        "Synthetic observed rows, drift row builders, and replay probe helpers (CG-2).\n\n"
        "**Authority:** derives test data only; does not own taxonomy vocabulary.\n"
        "Registry: ``docs/audits/CG_failure_classification_authority_registry.md``",
        BUILDERS_IMPORTS,
        slice_lines(103, 514) + slice_lines(1605, 1866),
    )

    split_body = slice_lines(515, 1018) + slice_lines(1105, 1293) + slice_lines(1366, 1604)
    write_module(
        helpers / "failure_classification_split_owner.py",
        "Split-owner acceptance matrix, FEM projection, and matrix assertions (CG-2).\n\n"
        "**Authority:** owns matrix row definitions and projection helpers only.\n"
        "Registry: ``docs/audits/CG_failure_classification_authority_registry.md``",
        SPLIT_OWNER_IMPORTS,
        split_body,
    )

    dashboard_body = (
        slice_lines(1019, 1083)
        + slice_lines(1085, 1103)
        + slice_lines(1294, 1364)
        + slice_lines(2017, 2037)
    )
    write_module(
        helpers / "failure_classification_dashboard_expectations.py",
        "Expected dashboard rows and presentation-structure helpers (CG-2).\n\n"
        "**Authority:** owns expected presentation structures only; does not define taxonomy.\n"
        "Registry: ``docs/audits/CG_failure_classification_authority_registry.md``",
        DASHBOARD_IMPORTS,
        dashboard_body,
    )

    # Patch split_owner contract misalignments to import dashboard case-id checks
    split_path = helpers / "failure_classification_split_owner.py"
    split_text = split_path.read_text(encoding="utf-8")
    split_text = split_text.replace(
        "    misalignments.extend(split_owner_matrix_dashboard_case_id_misalignments())\n",
        "    from tests.helpers.failure_classification_dashboard_expectations import (\n"
        "        split_owner_matrix_dashboard_case_id_misalignments,\n"
        "    )\n\n"
        "    misalignments.extend(split_owner_matrix_dashboard_case_id_misalignments())\n",
    )
    split_path.write_text(split_text, encoding="utf-8")

    alignment_body = slice_lines(1867, 2016) + slice_lines(2040, 2287)
    write_module(
        helpers / "failure_classification_alignment.py",
        "Contract/classifier parity, schema validation, and authority checks (CG-2).\n\n"
        "**Authority:** validates upstream authorities; does not own taxonomy values.\n"
        "Registry: ``docs/audits/CG_failure_classification_authority_registry.md``",
        ALIGNMENT_IMPORTS,
        alignment_body,
    )

    # Fix alignment: failure_classification_row_contract_misalignments should stay in alignment, not dashboard
    # Re-read original and fix dashboard - remove contract misalignments from dashboard imports
    dash_path = helpers / "failure_classification_dashboard_expectations.py"
    dash_text = dash_path.read_text(encoding="utf-8")
    dash_text = dash_text.replace(
        "from tests.helpers.failure_classification_alignment import (\n"
        "    failure_classification_row_contract_fields,\n)\n",
        "from tests.helpers.failure_classification_alignment import failure_classification_row_contract_fields\n",
    )
    dash_path.write_text(dash_text, encoding="utf-8")

    # alignment imports dashboard row shape - need to fix circular import
    # failure_dashboard_row_shape_errors is in dashboard - alignment's classifier_evidence_manifest_misalignments
    # calls failure_classification_row_contract_misalignments which should be in alignment module

    # Rewrite alignment to include failure_classification_row_contract_misalignments locally
    align_path = helpers / "failure_classification_alignment.py"
    align_text = align_path.read_text(encoding="utf-8")
    align_text = align_text.replace(
        "from tests.helpers.failure_classification_dashboard_expectations import (\n"
        "    failure_dashboard_row_shape_errors,\n"
        "    failure_classification_row_contract_misalignments,\n)\n",
        "",
    )
    # Insert row contract misalignments from original (lines 1940-1995 area) - it's in alignment_body already
    # failure_dashboard_row_shape_errors was in dashboard_body slice 2027-2037
    align_path.write_text(align_text, encoding="utf-8")

    sync_content = '''"""Compatibility orchestration layer for failure classification sync (CG-2).

Re-exports focused modules so existing import sites remain stable:
- ``failure_classification_alignment`` — contract/classifier parity and schema validation
- ``failure_classification_builders`` — synthetic rows and drift helpers
- ``failure_classification_split_owner`` — split-owner acceptance matrix
- ``failure_classification_dashboard_expectations`` — expected dashboard structures

Registry: ``docs/audits/CG_failure_classification_authority_registry.md``
"""
from __future__ import annotations

from tests.helpers.failure_classification_alignment import *  # noqa: F403
from tests.helpers.failure_classification_builders import *  # noqa: F403
from tests.helpers.failure_classification_dashboard_expectations import *  # noqa: F403
from tests.helpers.failure_classification_split_owner import *  # noqa: F403

# High-level orchestration assertions (delegate to alignment module).
from tests.helpers.failure_classification_alignment import (
    assert_classifier_evidence_manifest_locked,
    assert_contract_classifier_alignment,
    assert_failure_classification_row_contract_locked,
)
'''
    (helpers / "failure_classification_sync.py").write_text(sync_content, encoding="utf-8")
    print(f"wrote failure_classification_sync.py: {len(sync_content.splitlines())} lines")


if __name__ == "__main__":
    main()
