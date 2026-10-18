"""PR-DN experiment harness tests. No provider calls."""
from __future__ import annotations

from experiments.pr_dn.runner import STAGE_1, prepare, scenarios
from experiments.pr_dl.prompt import interpretation_schema, schema_is_non_authoritative


def test_pr_dn_scenarios_are_preregistered_and_balanced() -> None:
    rows = scenarios()
    assert len(rows) == 12
    categories = [row.category for row in rows]
    assert sum(category == "novel_compound" for category in categories) == 2
    assert sum(category.startswith("ambiguous_reference") for category in categories) == 2
    assert sum(category == "unauthorized_world_fact" for category in categories) == 2
    assert sum(category == "direct_mechanical_override" for category in categories) == 2
    assert sum(category == "unsupported_mechanic" for category in categories) == 2
    assert sum(category.startswith("ordinary_control") for category in categories) == 2
    assert any("and" in row.utterance.lower() and row.category == "ordinary_control" for row in rows)
    assert any("OOC:" in row.utterance for row in rows)
    assert tuple(STAGE_1) == ("DN01", "DN03", "DN05", "DN11")


def test_pr_dn_schema_remains_non_authoritative() -> None:
    assert schema_is_non_authoritative(interpretation_schema())


def test_pr_dn_preparation_is_isolated_and_routes_expected_rows() -> None:
    prepared = prepare()
    rows = {row["scenario_id"]: row for row in prepared["rows"]}
    assert prepared["isolation"]["save_guard_verified"] is True
    assert prepared["isolation"]["provider_tripwire_hits"] == []
    assert all(not row["state_changed"] for row in rows.values())
    assert rows["DN01"]["refined_routed"] is True
    assert rows["DN03"]["refined_routed"] is True
    assert rows["DN11"]["deterministic_quality"] == "PASS"
