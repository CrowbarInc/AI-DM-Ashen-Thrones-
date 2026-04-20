"""Direct-owner contract suite for ``game.state_authority`` (registry, guards, read matrix).

Secondary integration coverage for runtime seams lives next to domain owners
(``test_interaction_context``, ``test_world_state``, ``test_validation_journal_affordances``,
``test_world_updates_and_clue_normalization``).
"""
from __future__ import annotations

import pytest

from game.state_authority import (
    HIDDEN_STATE,
    INTERACTION_STATE,
    PLAYER_VISIBLE_STATE,
    SCENE_STATE,
    WORLD_STATE,
    STATE_DOMAINS,
    StateAuthorityError,
    _CROSS_DOMAIN_WRITE_ALLOWLIST,
    _REGISTRY,
    all_state_domain_specs,
    assert_cross_domain_write_allowed,
    assert_owner_can_mutate_domain,
    build_state_mutation_trace,
    can_domain_read_domain,
    can_owner_mutate_domain,
    get_state_domain_spec,
)


pytestmark = pytest.mark.unit

_EXPECTED_DOMAINS = frozenset(
    {
        WORLD_STATE,
        SCENE_STATE,
        INTERACTION_STATE,
        PLAYER_VISIBLE_STATE,
        HIDDEN_STATE,
    }
)


def test_registry_exactly_five_domains_no_extras_deterministic_order():
    assert len(STATE_DOMAINS) == 5
    assert set(STATE_DOMAINS) == _EXPECTED_DOMAINS
    assert set(_REGISTRY.keys()) == _EXPECTED_DOMAINS
    specs = all_state_domain_specs()
    assert len(specs) == 5
    assert tuple(s.domain_id for s in specs) == STATE_DOMAINS
    for spec in specs:
        assert spec.domain_id == spec.domain_id.strip()
        assert spec.gpt_may_mutate is False


def test_unknown_domain_raises_state_authority_error():
    with pytest.raises(StateAuthorityError, match="Unknown state domain"):
        get_state_domain_spec("not_a_domain")


def test_player_visible_state_journal_publication_alignment():
    spec = get_state_domain_spec(PLAYER_VISIBLE_STATE)
    assert "game.journal" in spec.runtime_owner_modules
    assert "game.journal" in spec.mutable_by_modules
    assert spec.visibility_class == "derived"


def test_pseudo_mutation_owners_rejected(parametrize_owner):
    owner = parametrize_owner
    with pytest.raises(StateAuthorityError, match="Non-authoritative owner"):
        assert_owner_can_mutate_domain(owner, INTERACTION_STATE, operation="test_op")


@pytest.fixture(
    params=["gpt", "gpt_output", "llm", "model", "model_output", "openai"],
    ids=lambda x: x,
)
def parametrize_owner(request):
    return request.param


def test_pseudo_owners_fail_can_owner_mutate_domain():
    for bad in ("gpt", "model", "llm"):
        assert can_owner_mutate_domain(bad, WORLD_STATE) is False


def test_declared_module_owners_can_mutate_expected_domains():
    assert_owner_can_mutate_domain("game.interaction_context", INTERACTION_STATE)
    assert_owner_can_mutate_domain("game.world", WORLD_STATE)
    assert_owner_can_mutate_domain("game.api", SCENE_STATE)
    assert_owner_can_mutate_domain("game.api", WORLD_STATE)
    assert_owner_can_mutate_domain("game.journal", PLAYER_VISIBLE_STATE)


def test_wrong_module_cannot_mutate_domain():
    with pytest.raises(StateAuthorityError, match="not a declared mutator"):
        assert_owner_can_mutate_domain("game.interaction_context", WORLD_STATE)
    with pytest.raises(StateAuthorityError, match="not a declared mutator"):
        assert_owner_can_mutate_domain("game.world", INTERACTION_STATE)
    with pytest.raises(StateAuthorityError, match="not a declared mutator"):
        assert_owner_can_mutate_domain("game.journal", HIDDEN_STATE)


def test_read_matrix_concrete_pairs():
    assert can_domain_read_domain(WORLD_STATE, WORLD_STATE) is True
    assert can_domain_read_domain(WORLD_STATE, SCENE_STATE) is True
    assert can_domain_read_domain(WORLD_STATE, INTERACTION_STATE) is False
    assert can_domain_read_domain(WORLD_STATE, PLAYER_VISIBLE_STATE) is False
    assert can_domain_read_domain(WORLD_STATE, HIDDEN_STATE) is False

    assert can_domain_read_domain(SCENE_STATE, HIDDEN_STATE) is True
    assert can_domain_read_domain(SCENE_STATE, PLAYER_VISIBLE_STATE) is False

    assert can_domain_read_domain(INTERACTION_STATE, WORLD_STATE) is True
    assert can_domain_read_domain(INTERACTION_STATE, SCENE_STATE) is True
    assert can_domain_read_domain(INTERACTION_STATE, HIDDEN_STATE) is False

    assert can_domain_read_domain(PLAYER_VISIBLE_STATE, HIDDEN_STATE) is True
    assert can_domain_read_domain(HIDDEN_STATE, PLAYER_VISIBLE_STATE) is False
    assert can_domain_read_domain(HIDDEN_STATE, HIDDEN_STATE) is True


def test_cross_domain_implicit_denial():
    with pytest.raises(StateAuthorityError, match="Cross-domain write not allow-listed"):
        assert_cross_domain_write_allowed(
            INTERACTION_STATE,
            WORLD_STATE,
            operation="shadow_world_write",
        )
    with pytest.raises(StateAuthorityError, match="Cross-domain write not allow-listed"):
        assert_cross_domain_write_allowed(
            PLAYER_VISIBLE_STATE,
            WORLD_STATE,
            operation="narration_back_write",
        )


def test_cross_domain_same_domain_is_noop():
    assert_cross_domain_write_allowed(INTERACTION_STATE, INTERACTION_STATE, operation="ignored_for_same_domain")


def test_cross_domain_operation_mismatch_fails():
    with pytest.raises(StateAuthorityError, match="Cross-domain write not allow-listed"):
        assert_cross_domain_write_allowed(
            INTERACTION_STATE,
            SCENE_STATE,
            operation="exchange_interruption_tracker_slot_typo",
        )
    with pytest.raises(StateAuthorityError, match="Cross-domain write not allow-listed"):
        assert_cross_domain_write_allowed(
            HIDDEN_STATE,
            PLAYER_VISIBLE_STATE,
            operation="journal_merge_revealed_hidden_facts_typo",
        )


def test_cross_domain_block_b_operations_allow_listed():
    assert_cross_domain_write_allowed(
        INTERACTION_STATE,
        SCENE_STATE,
        operation="exchange_interruption_tracker_slot",
    )
    assert_cross_domain_write_allowed(
        HIDDEN_STATE,
        PLAYER_VISIBLE_STATE,
        operation="journal_merge_revealed_hidden_facts",
    )


def test_cross_domain_allowlist_nonempty_and_json_friendly_ops():
    assert _CROSS_DOMAIN_WRITE_ALLOWLIST
    for edge in _CROSS_DOMAIN_WRITE_ALLOWLIST:
        assert edge.source in _EXPECTED_DOMAINS
        assert edge.target in _EXPECTED_DOMAINS
        for op in edge.operations:
            assert isinstance(op, str) and op.strip() == op


def test_cross_domain_empty_operation_rejected():
    with pytest.raises(StateAuthorityError, match="non-empty operation"):
        assert_cross_domain_write_allowed(INTERACTION_STATE, SCENE_STATE, operation="")


def test_publication_view_specs_player_visible_and_hidden():
    pvs = get_state_domain_spec(PLAYER_VISIBLE_STATE)
    assert pvs.forbidden_write_targets == frozenset(
        {WORLD_STATE, SCENE_STATE, INTERACTION_STATE, HIDDEN_STATE}
    )
    hid = get_state_domain_spec(HIDDEN_STATE)
    assert PLAYER_VISIBLE_STATE in hid.forbidden_write_targets
    assert PLAYER_VISIBLE_STATE not in hid.reads_allowed_from


def test_build_state_mutation_trace_compact_shape():
    t = build_state_mutation_trace(
        domain=SCENE_STATE,
        owner_module=" game.api ",
        operation="authoritative_scene_transition",
        cross_domain=(INTERACTION_STATE, SCENE_STATE, "interlocutor_binding"),
        extra={"changed_area": "scene_state.active_scene_id"},
    )
    assert t == {
        "kind": "state_mutation",
        "domain": SCENE_STATE,
        "owner_module": "game.api",
        "operation": "authoritative_scene_transition",
        "cross_domain": {
            "source": INTERACTION_STATE,
            "target": SCENE_STATE,
            "operation": "interlocutor_binding",
        },
        "changed_area": "scene_state.active_scene_id",
    }

    minimal = build_state_mutation_trace(domain=WORLD_STATE, owner_module="game.world")
    assert minimal == {
        "kind": "state_mutation",
        "domain": WORLD_STATE,
        "owner_module": "game.world",
    }


def test_prompt_context_is_not_player_visible_state_mutator():
    """Prompt assembly stays read-side for this domain; registry excludes it from mutators."""
    assert can_owner_mutate_domain("game.prompt_context", PLAYER_VISIBLE_STATE) is False


def test_prompt_context_is_not_runtime_truth_mutator_for_authoritative_domains():
    """Narration/prompt packaging must not be treated as alternate owners of engine truth."""
    assert can_owner_mutate_domain("game.prompt_context", WORLD_STATE) is False
    assert can_owner_mutate_domain("game.prompt_context", HIDDEN_STATE) is False


def test_storage_is_not_interaction_state_mutator():
    """Lazy session helpers are not promoted to interaction_state policy owners."""
    assert can_owner_mutate_domain("game.storage", INTERACTION_STATE) is False


def test_scene_state_lazy_init_remains_outside_direct_owner_suite():
    """``interaction_context._scene_state`` intentionally skips guards on lazy first touch."""
    from game.interaction_context import _scene_state

    session: dict = {}
    st = _scene_state(session)
    assert isinstance(st, dict)
    assert session.get("scene_state") is st


def test_storage_get_interaction_context_first_touch_not_guarded():
    """Deferred seam: lazy ``interaction_context`` root init in storage without guard coupling."""
    from game.storage import get_interaction_context

    session: dict = {}
    ctx = get_interaction_context(session)
    assert isinstance(ctx, dict)
    assert session.get("interaction_context") is ctx
