# 02 — Environment Leakage Root Cause

R1-03 execute_trial.py imports production API first. Its L4 branch then imports
tests.test_pr_ef_gm_authority.seed_scene and
tests.test_pr_ef_r4_authorization._prepare. The former imports
tests.test_pr_du_player_pipeline, whose module-level experiments.pr_dq.world import
initializes experiments/pr_dq/__init__.py:11. That initializer unconditionally sets
ASHEN_DISABLE_LIVE_INTERPRETATION='1'. The latter fixture module also depends on
the same pipeline. It is unrelated to invoking a pytest fixture function.

game.semantic_interpreter.live_interpretation_enabled reads the environment on
each call, accepting 1/true/yes/on as disabled. Production combines it with the
provider-disable flag in production_live_interpretation_enabled, then checks at
interpret_production_turn entry. The flag is not cached. Python caches imported
modules, making the side effect order-dependent. The experimental initializer
does not restore its caller's value. L4's unused MonkeyPatch instance never scopes
that initializer; no later flag assertion catches it.

Production _contract caches schema/adapter/model, not the live-enable predicate.
It already saves/restores this flag around its own experimental imports. That
restoration does not cover a later independent fixture import. tests/conftest.py
also intentionally disables live calls during pytest collection; it is a separate
test-runner default, not the demonstrated R1-03 direct-script import chain.

Classification: intentional experimental safety workaround, improperly scoped
when reused as a live-validation fixture. Existing PR-DQ/DU/EF tests rely on the
disabled default; some explicitly enable interpretation inside monkeypatch scope.
Deleting the assignment would alter that experimental contract and frozen files.
Repair replaces the validation dependency, preserving those legitimate defaults.
Fresh subprocess tests demonstrate both the old leak's detection/restoration and
new module import safety with unset, enabled and disabled values in both orders.
