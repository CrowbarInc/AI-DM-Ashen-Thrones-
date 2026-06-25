"""One-shot CE5 splitter: move golden_replay_projection.py into focused modules."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "tests" / "helpers" / "golden_replay_projection.py"
BACKUP = ROOT / "tests" / "helpers" / "golden_replay_projection.py.bak"
HELPERS = ROOT / "tests" / "helpers"


def _lines(start: int, end: int) -> str:
    text = SRC.read_text(encoding="utf-8").splitlines(keepends=True)
    return "".join(text[start - 1 : end])


def _write(name: str, body: str) -> None:
    path = HELPERS / name
    path.write_text(body, encoding="utf-8")
    print(f"wrote {path} ({len(body.splitlines())} lines)")


def main() -> None:
    if not BACKUP.exists():
        BACKUP.write_text(SRC.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"backup -> {BACKUP}")

    fields_header = '''"""Protected observation field registry and drift bucket classification (CE5)."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any, Mapping

from game.output_sanitizer import resembles_serialized_response_payload

'''
    fields_body = (
        _lines(87, 95)
        + _lines(217, 282)
        + _lines(533, 543)
        + _lines(586, 635)
        + _lines(780, 809)
        + _lines(848, 863)
        + _lines(990, 995)
    )
    _write("golden_replay_projection_fields.py", fields_header + fields_body)

    manifest_header = '''"""Protected replay manifest rendering for observation field paths (CE5)."""
from __future__ import annotations

from tests.helpers.golden_replay_projection_fields import (
    PROTECTED_OBSERVATION_FIELDS,
    protected_observation_drift_bucket,
    protected_observation_field_paths,
    protected_observation_field_registry,
)

'''
    _write("golden_replay_projection_manifest.py", manifest_header + _lines(637, 777))

    fallbacks_header = '''"""Golden replay fallback-family read-side projection (CE5)."""
from __future__ import annotations

from typing import Any, Mapping

from game.final_emission_replay_projection import is_sealed_replacement_lineage_kind
from game.realization_provenance import REALIZATION_FALLBACK_FAMILY_FIELD

from tests.helpers.golden_replay_projection_fields import _first_present

'''
    fallbacks_body = _lines(78, 85) + _lines(1072, 1121) + _lines(1277, 1284)
    _write("golden_replay_projection_fallbacks.py", fallbacks_header + fallbacks_body)

    speaker_header = '''"""Golden replay speaker projection parity (CE5)."""
from __future__ import annotations

from typing import Any, Literal, Mapping

from game.final_emission_speaker_observation import read_final_speaker_observation

from tests.helpers.golden_replay_projection_fields import _first_present
from tests.helpers.transcript_runner import latest_target_id, latest_target_source

'''
    speaker_body = _lines(49, 55) + _lines(1138, 1274)
    _write("golden_replay_projection_speaker.py", speaker_header + speaker_body)

    extractors_header = '''"""Payload extraction and protected observation projection helpers (CE5)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from game.final_emission_replay_projection import (
    build_fem_runtime_lineage_events,
    read_opening_fallback_owner_bucket_for_replay,
)
from game.runtime_lineage_telemetry import normalize_runtime_lineage_events

from tests.debug_trace_utils import latest_compact_debug_trace_entry
from tests.helpers.golden_replay_projection_fallbacks import (
    _fem_dual_fallback_family_present,
    _fem_has_any_key,
)
from tests.helpers.golden_replay_projection_fields import (
    MISSING,
    PROTECTED_OBSERVATION_FIELDS,
    _EXPECTED_PROTECTED_CLASSIFIER_EVIDENCE_COUNT,
    _PROTECTED_CLASSIFIER_EVIDENCE_EXCLUDED_PATHS,
    _first_present,
    final_text_has_scaffold_leakage,
    protected_observation_extraction_registry as _unused_registry_import_guard,
    protected_observation_field_paths,
    protected_observation_field_registry,
    protected_classifier_evidence_excluded_paths,
    protected_classifier_evidence_field_paths,
)

'''
    # Remove bogus import line from header - fix below
    extractors_header = extractors_header.replace(
        "    protected_observation_extraction_registry as _unused_registry_import_guard,\n", ""
    )
    extractors_body = (
        _lines(98, 215)
        + _lines(284, 531)
        + _lines(545, 584)
        + _lines(811, 846)
        + _lines(865, 1063)
        + _lines(1065, 1070)
        + _lines(1124, 1136)
        + _lines(1287, 1574)
    )
    _write("golden_replay_projection_extractors.py", extractors_header + extractors_body)

    facade_header = '''"""Golden replay turn-observation projection adapter (Cycle T1).

Centralizes payload/snapshot → observation dict projection and protected
field-path enumeration. Test-only; no runtime behavior changes.

**Cycle AO5 boundary — acceptance observation only (do not merge with runtime lineage):**

This **test-only acceptance** module owns the canonical protected observation paths
(``PROTECTED_OBSERVATION_FIELDS``), ``project_turn_observation``, drift buckets, and
classifier/dashboard overlap derivation. It is CI acceptance authority.

Runtime FEM lineage projection (``fem_runtime_lineage_events``, sealed sub-kinds,
selection/content owner splits on lineage events) is owned by
:mod:`game.final_emission_replay_projection`. Golden replay may consume lineage events
for diagnostics and prefer payload-stamped events when present, but lineage event
**owner** semantics are excluded from protected drift classification unless explicitly
promoted later (see ``test_golden_drift_classification_ignores_runtime_lineage_diagnostics``).

These modules must **not** be merged.

**Dual fallback-family contract (Cycle AB):**

Runtime FEM may carry two independent fallback-family vocabularies:

- ``fallback_family_used`` — diegetic/template taxonomy from
  :mod:`game.diegetic_fallback_narration` (e.g. ``scene_opening``, ``observe``,
  ``social``).
- ``realization_fallback_family`` — governed provenance taxonomy from
  :mod:`game.realization_provenance` / :mod:`game.realization_authority`
  (e.g. ``legacy_diegetic_fallback``, ``upstream_prepared_emission``,
  ``gate_terminal_repair``).

Golden replay exposes a single observed ``fallback_family`` for protected
structural drift checks. :func:`project_replay_fallback_family_from_fem`
implements the read-side precedence rule documented by
:func:`dual_fallback_family_replay_precedence_surface` — diegetic
``fallback_family_used`` first, governed ``realization_fallback_family`` only
when diegetic is absent. That preference is a **read-side compatibility
projection**; runtime code must not rewrite either FEM field to force one
taxonomy into the other, and the two fields must not be collapsed at write time.

CE5 splits implementation into focused modules; this file remains the public facade.
"""
from __future__ import annotations

from typing import Any, Mapping

from game.final_emission_replay_projection import (
    normalize_fem_for_replay_acceptance,
    read_emission_debug_lane_for_replay,
    read_fem_from_turn_for_replay,
)

from tests.helpers.transcript_runner import compact_snapshot_summary

from tests.helpers.golden_replay_projection_extractors import (
    MISSING,
    ProtectedObservationField,
    _ProtectedExtractionSpec,
    _build_projection_status,
    _echo_overlap_band,
    _extract_fem_flat_observed_fields,
    _extract_sanitizer_lineage_observed_fields,
    _extract_sanitizer_trace_flat_observed_fields,
    _find_nested_list,
    _find_nested_mapping,
    _first_present,
    _project_flat_protected_observed_fields,
    _resolve_route_kind,
    _runtime_lineage_events_from_payload,
    _sanitizer_debug_change_counts,
    _trace_from_payload_or_snapshot,
    final_text_has_scaffold_leakage,
    golden_text_hash,
    lookup_observation_path,
    normalize_golden_text,
    project_semantic_mutation_summary,
    protected_classifier_evidence_excluded_paths,
    protected_classifier_evidence_field_paths,
    protected_observation_extraction_registry,
    protected_observation_extraction_source_by_path,
    protected_path_covered_by_unavailable,
    protected_path_is_represented_in_observed_turn,
    protected_path_representation_errors,
)
from tests.helpers.golden_replay_projection_fallbacks import (
    NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
    REPLAY_FALLBACK_FAMILY_FEM_PRECEDENCE_KEYS,
    _resolve_fallback_family,
    dual_fallback_family_replay_precedence_surface,
    project_replay_fallback_family_from_fem,
)
from tests.helpers.golden_replay_projection_fields import (
    PROTECTED_OBSERVATION_FIELDS,
    SEMANTIC_DRIFT_FIELDS,
    STRUCTURAL_DRIFT_FIELDS,
    observed_projection_schema_defaults,
    protected_observation_default_row,
    protected_observation_drift_bucket,
    protected_observation_field_paths,
    protected_observation_field_registry,
    protected_observation_flat_field_paths,
)
from tests.helpers.golden_replay_projection_manifest import (
    PROTECTED_REPLAY_MANIFEST_FIELD_PATHS_BEGIN,
    PROTECTED_REPLAY_MANIFEST_FIELD_PATHS_END,
    extract_protected_observation_manifest_section,
    protected_observation_manifest_counts,
    protected_observation_manifest_field_rows,
    protected_observation_manifest_registry_parity_errors,
    protected_observation_manifest_section_is_current,
    render_protected_observation_manifest_section,
)
from tests.helpers.golden_replay_projection_speaker import (
    SpeakerProjectionParityStatus,
    project_speaker_projection_parity,
    read_final_speaker_observation_for_replay,
    _resolve_selected_speaker_id,
)

'''
    facade_body = _lines(1576, 1756)
    _write("golden_replay_projection.py", facade_header + facade_body)


if __name__ == "__main__":
    main()
