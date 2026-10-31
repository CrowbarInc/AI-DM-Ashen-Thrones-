# 03 — Harness Repair

tools/atgb/readiness.py is a validation-only replacement foundation. It imports no
test modules or experiments at module load. execution_mode uses the repository's
MonkeyPatch.context convention for explicit live/disabled scopes and restores the
original value, including absence, on normal exit or failure. Sequential tests
cover both modes and original unset/0/1 states. Process-global configuration is
for sequential use; concurrent trials must use independent processes.

import_fixture compares environment before/after an import, rejects any import
mutation, and restores all changed entries even if the import itself raises.
It does not declare a legacy module safe after detection; discard that trial
process because Python module caches and other side effects cannot be undone by
environment restoration. Never reuse the R1-03 runner or import test_*.py for live
setup. Explicit disabled-interpretation tests and all experimental source remain
unchanged. Production _contract's existing import-restoration owner is reused.

seed_control copies only the preserved R1-03 pre-execution world, character, combat,
scene and initial session into an exclusive disposable store. Its context is
cleared, then production chat generates the actual pending ask under stubbed
interpretation. No pending record is fabricated for the positive control.
Storage paths are patched with scoped repository conventions and restored by
fixture teardown; the disposable store is discarded from active use.

guarded_trial writes a nonsecret preflight result before invoking its callback;
failed setup returns a validation_setup_failure without entering gameplay or
provider dispatch. It also catches setup inspection exceptions by type only.
No provider runner or live request was executed or authorized by this pass.
