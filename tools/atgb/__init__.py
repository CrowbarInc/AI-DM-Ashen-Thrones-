"""Ashen Thrones Gameplay Benchmark infrastructure.

This package loads conversational fixtures, drives them through the existing
player chat boundary, and records evidence for a human rubric. It is not a
gameplay authority, a semantic interpreter, or a playability scorer.
"""

from __future__ import annotations

BENCHMARK_VERSION = "ATGB-02"
SCENARIO_VERSION = "ATGB-01"
RUBRIC_VERSION = "atgb-rubric-01"
PARTITION_REVISION = "ATGB-02-s07-held-out"
RESULT_SCHEMA_VERSION = 1

# Explicit missing-value markers. They are not measurements.
UNAVAILABLE = "unavailable"
UNSCORED = "unscored"
UNCONTROLLED = "uncontrolled"

EVIDENCE_INFRASTRUCTURE = "provider_disabled_infrastructure"
EVIDENCE_HOST = "host_deterministic"
EVIDENCE_LIVE = "live_provider_execution"
EVIDENCE_HUMAN = "human_reviewed_conversational"
