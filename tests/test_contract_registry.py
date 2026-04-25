import importlib
import sys


def test_registry_exports_frozenset_and_expected_keys_present() -> None:
    reg = importlib.import_module("game.contract_registry")

    keys = reg.PUBLIC_NARRATIVE_PLAN_PROMPT_TOP_KEYS
    assert isinstance(keys, frozenset)

    expected = {
        "version",
        "narrative_mode",
        "role_allocation",
        "scene_anchors",
        "active_pressures",
        "required_new_information",
        "allowable_entity_references",
        "narrative_roles",
        "narrative_mode_contract",
        "scene_opening",
        "action_outcome",
        "transition_node",
        "answer_exposition_plan",
    }
    assert expected.issubset(keys)
    assert "" not in keys
    assert all(isinstance(k, str) and k.strip() == k and k for k in keys)


def test_helper_returns_same_set_object() -> None:
    reg = importlib.import_module("game.contract_registry")
    assert reg.public_narrative_plan_prompt_top_keys() is reg.PUBLIC_NARRATIVE_PLAN_PROMPT_TOP_KEYS


def test_contract_registry_does_not_import_runtime_heavy_owners() -> None:
    # Ensure a clean import snapshot for the modules we care about.
    forbidden = (
        "game.prompt_context",
        "game.final_emission_gate",
        "game.social_exchange_emission",
        "game.narration_plan_bundle",
        "tools.planner_convergence_audit",
        "tests.test_planner_convergence_static_audit",
    )
    for name in forbidden:
        sys.modules.pop(name, None)

    importlib.invalidate_caches()
    importlib.import_module("game.contract_registry")

    # Import-light guarantee: importing the registry must not pull these in.
    for name in forbidden:
        assert name not in sys.modules


def test_emergency_fallback_registry_constants_and_helpers() -> None:
    reg = importlib.import_module("game.contract_registry")

    src = reg.EMERGENCY_FALLBACK_SOURCE_IDS
    kinds = reg.EMERGENCY_FALLBACK_KIND_IDS
    assert isinstance(src, frozenset)
    assert isinstance(kinds, frozenset)
    assert reg.emergency_fallback_source_ids() is src
    assert reg.emergency_fallback_kind_ids() is kinds
    assert "" not in src
    assert "" not in kinds
    assert all(isinstance(x, str) and x.strip() == x and x for x in src)
    assert all(isinstance(x, str) and x.strip() == x and x for x in kinds)

    assert {
        "minimal_social_emergency_fallback",
        "deterministic_social_fallback",
        "social_interlocutor_minimal_fallback",
    }.issubset(src)
    assert {
        "emergency_social_minimal",
        "response_type_contract_social_emergency",
        "visibility_minimal_social_fallback",
        "social_interlocutor_fallback",
        "direct_answer_hint",
        "interruption",
        "pressure_refusal",
        "refusal_evasion",
        "explicit_ignorance",
    }.issubset(kinds)

