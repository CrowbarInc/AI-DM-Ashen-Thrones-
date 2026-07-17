"""Shared lineage event selectors for fallback projection tests."""
from __future__ import annotations


def fallback_selected_event(observed: dict) -> dict:
    return next(
        event for event in observed["runtime_lineage_events"] if event.get("event_kind") == "fallback_selected"
    )


def mutation_event(observed: dict, mutation_kind: str) -> dict:
    return next(
        event
        for event in observed["runtime_lineage_events"]
        if event.get("event_kind") == "mutation" and event.get("mutation_kind") == mutation_kind
    )
