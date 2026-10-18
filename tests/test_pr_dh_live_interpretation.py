from tools.run_pr_dh_live_interpretation import (
    OUTPUT_TOKEN_CAP,
    Budget,
    _planner_schema,
    _tool_schema,
)


def _assert_no_open_additional_properties(schema):
    if isinstance(schema, dict):
        if schema.get("type") == "object":
            assert schema.get("additionalProperties") is False
        for value in schema.values():
            _assert_no_open_additional_properties(value)
    elif isinstance(schema, list):
        for item in schema:
            _assert_no_open_additional_properties(item)


def test_pr_dh_strict_response_schemas_are_closed():
    _assert_no_open_additional_properties(_planner_schema())
    _assert_no_open_additional_properties(_tool_schema())


def test_pr_dh_budget_preflight_reserves_output_cap():
    budget = Budget(requests=23, input_tokens=59_000, output_tokens=5_500)
    assert budget.can_send(100, OUTPUT_TOKEN_CAP) is False

    budget = Budget(requests=0, input_tokens=100, output_tokens=100)
    assert budget.can_send(100, 100) is True
