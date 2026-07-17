"""Compatibility orchestration layer for failure classification sync (CG-2).

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
from tests.helpers.failure_classification_split_owner import *  # noqa: F403
from tests.helpers.failure_classification_dashboard_expectations import *  # noqa: F403

# Compatibility re-exports for import sites that predated CG-2 module split.
from tests.helpers.replay_observed_row_fixtures import (
    SyntheticObservedRowProfile,
    observed_dashboard_probe_row,
    observed_failure_row,
)

# High-level orchestration assertions (delegate to alignment module).
from tests.helpers.failure_classification_alignment import (
    assert_classifier_evidence_manifest_locked,
    assert_contract_classifier_alignment,
    assert_failure_classification_row_contract_locked,
)
