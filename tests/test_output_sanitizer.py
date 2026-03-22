from __future__ import annotations

from game.output_sanitizer import sanitize_player_facing_output


def test_sanitizer_rewrites_procedural_engine_text():
    text = "I need a more concrete action or target to resolve that procedurally."
    out = sanitize_player_facing_output(text, {})
    low = out.lower()
    assert "resolve that procedurally" not in low
    assert "more concrete action" not in low
    assert "state exactly what you do" not in low
    assert "scene offers no clear answer" in low


def test_sanitizer_strips_internal_role_prefixes():
    text = (
        "Planner: Move to branch A.\n"
        "Router: choose dialogue route.\n"
        "Validator: based on established state, uncertain."
    )
    out = sanitize_player_facing_output(text, {})
    low = out.lower()
    assert "planner:" not in low
    assert "router:" not in low
    assert "validator:" not in low


def test_sanitizer_cleans_malformed_concatenation_splice():
    text = "there's no solid evidence... you might start leaves by speaking to the runner."
    out = sanitize_player_facing_output(text, {})
    low = out.lower()
    assert "start leaves by speaking" not in low
    assert "start by speaking" not in low
    assert "state exactly what you do" not in low


def test_sanitizer_blocks_router_planner_validator_scaffold_terms():
    text = "internal validator state says router planner instructions are unresolved."
    out = sanitize_player_facing_output(text, {})
    low = out.lower()
    assert "validator state" not in low
    assert "router" not in low
    assert "planner" not in low


def test_sanitizer_preserves_valid_atmospheric_narration():
    text = "Rain needles across the checkpoint as lanternlight wavers on wet stone."
    out = sanitize_player_facing_output(text, {})
    assert out == text


def test_sanitizer_rewrites_fragmented_scaffold_start_with():
    text = "Start with man in tattered clothes appears to be waiting by the gate."
    out = sanitize_player_facing_output(text, {})
    low = out.lower()
    assert "start with" not in low
    assert "man in tattered clothes" in low
    assert "lingers nearby" in low


def test_sanitizer_removes_instructional_prompt_sentence():
    text = "The moment hangs unresolved; state exactly what you do."
    out = sanitize_player_facing_output(text, {})
    low = out.lower()
    assert "state exactly what you do" not in low
    assert "moment hangs unresolved" not in low


def test_sanitizer_removes_duplicate_and_spliced_fragments():
    text = (
        "A man in tattered clothes lingers nearby, watching the crowd. "
        "A man in tattered clothes lingers nearby, watching the crowd. "
        "Stay with many want it."
    )
    out = sanitize_player_facing_output(text, {})
    low = out.lower()
    assert low.count("a man in tattered clothes lingers nearby, watching the crowd.") == 1
    assert "stay with many want it" not in low
