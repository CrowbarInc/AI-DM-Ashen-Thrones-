# PR-BT Regression Completion Gate

Date: 2026-10-05. MODE: DETERMINISTIC REGRESSION COMPLETION. MODEL/API CALLS: ZERO.
No commit, push, or live gameplay was performed.

## A. Executive result

FAIL. Decision: **C - BOUNDED PR-BT REPAIR NEEDED**.
The final relevant regression completed normally: **913 passed, 1 failed,
0 skipped/xfailed**, with one guard-incompatible test deselected. Runtime: 36.251
seconds (JUnit suite time). The remaining failure is the unchanged PR-BT size
assertion. Integrity and prompt regressions pass after the bounded prompt repair.

One smallest remaining repair: revise only the restored prompt guidance so that
it preserves the tested guidance while meeting the existing 12,000-character
savings floor on P2 and P3. P3 needs 535 characters of additional savings and P2
needs 415. This is an unresolved repair requirement, not permission to start
another context-reduction slice. No further optimization was performed on resume.

## B. Prior nontermination diagnosis

**C - TEST HARNESS / PROCESS EXIT ISSUE**, localized to the sandbox environment.
Independent C13, C14, and C18 route tests stalled before request execution in
Starlette TestClient / AnyIO blocking-portal startup. Faulthandler stacks pointed
to Windows asyncio `_make_self_pipe`, `socket.socketpair`, and `socket.accept`.
The same C18 test passed outside the sandbox in 1.501 seconds; the complete
regression then terminated in 36.251 seconds outside the sandbox. C13 and C14
route cases also pass in that run. No production deadlock or provider wait was
demonstrated. Earlier aggregate teardown-stall observations lacked an independent
teardown stack; their precise mechanism remains unproven.

A separate temporary-file PermissionError was resolved by pointing TMP/TEMP to
the workspace. The adversarial regex case is legitimately slower (5.34 seconds
in the final run), but does not explain the long stalls.

## C. Test matrix

Counts below describe complete runs only. Repeated runs are not added to the
final unique-test total. Historical JUnit times take precedence over estimates
in earlier progress messages. Every run used zero live model/API calls.
Commands and diagnostic details are in
`artifacts/pr_bt_regression_completion_gate/command_ledger.md`; the final command
is preserved in `final_command.ps1`.

| Evidence filename (all under gate artifacts) | Passed | Failed | Time seconds | Normal exit |
|---|---:|---:|---:|---|
| stage1_pr_bt.xml | 3 | 0 | 1.995 | yes |
| stage2_pr_bs.xml | 9 | 0 | 1.660 | yes |
| stage3_pr_br_pre_c13.xml | 44 | 0 | 12.954 | yes |
| stage3_pr_br_non_testclient.xml | 173 | 1 | 12.800 | yes |
| stage3_pr_br_temp_permission_rerun.xml | 1 | 0 | 1.878 | yes |
| stage4_prompt_files.xml | 198 | 14 | 4.757 | yes |
| stage4_prompt_files_after_repair.xml | 210 | 2 | 4.335 | yes |
| stage4_prompt_files_after_repair2.xml | 212 | 0 | 3.953 | yes |
| stage4_prompt_files_after_compact_repair.xml | 212 | 0 | 4.510 | yes |
| stage4_prompt_files_after_tight_repair.xml | 212 | 0 | 4.555 | yes |
| stage1_pr_bt_after_repair.xml | 2 | 1 | 2.580 | yes |
| stage1_pr_bt_after_compact_repair.xml | 2 | 1 | 2.808 | yes |
| stage1_pr_bt_after_tight_repair.xml | 2 | 1 | 2.831 | yes |
| stage4_realization_authority_provenance.xml | 31 | 1 | 3.535 | yes |
| c18_outside_sandbox.xml | 1 | 0 | 1.501 | yes |
| final_regression.xml | **913** | **1** | **36.251** | **yes** |

All complete runs have zero skipped/xfailed cases. The final run deselected one
test; earlier runs did not. Interrupted batches and timeout diagnostics are
listed separately in the command ledger and are never counted as passed suites.

## D. PR-BT direct validation

Final: 2 passed, 1 failed. Rule-presence and policy/recipe visibility pass.
`test_pr_bt_provider_requests_remove_at_least_12000_chars_each` fails at P2:
`121438 - 109853 = 11585`, below 12000. P3 also misses the floor independently
in the measurements, though the assertion stops at P2.

## E. PR-BS regression

All 9 Decision-Facing Answer Recipe tests pass in the final run, including
provider construction and representative interpretation, NPC, and hypothesis
behavior. The recipe remains guidance rather than authority.

## F. PR-BR integrity regression

All 35 existing `test_pr_br_*.py` files ran to completion in the final run.
The JUnit file contains per-test evidence for authority, provenance, epistemic
ceilings, premises, declaration/narration validation, player hypotheses,
incidental improvisation, NPC handling, structured envelopes, immutable accepted
responses, and raw-chat integration. No integrity failure was observed.

## G. Prompt / realization regression

All 212 prompt tests pass after repair. All selected realization, response-policy,
fallback, final-emission, schema, and trace cases pass in the final run.
One provenance test is incompatible with the repository's live-call guard:
`test_call_gpt_provider_failure_metadata_has_provider_family`. It installs a
fake OpenAI constructor that raises, but invokes the guarded `gm.call_gpt`
wrapper directly. The guard rejects it before the fake can execute. It was
deselected in the final run, not counted as passed, and no guard was bypassed.
This test is intended to be deterministic; it is not evidence of a required live
dependency. A future harness adjustment can exercise that fake without removing
the global live-call boundary.

## H. Broader relevant regression

The final combined 914-case run is the broader relevant gate. It covers every
PR-BR file plus PR-BS, PR-BT, prompt construction, response policy, fallback,
output/schema, and turn trace. It completes with the single size failure.
No claim is made about an unrelated repository-wide suite.

## I. Failures

Initial PR-BT deduplication removed prompt/system guidance required by 14 existing
tests. The missing families were response delta, typed uncertainty and grounding,
anti-railroading distinctions and explicit commitment, context separation,
diegetic narration purity/order, spoiler/exploration guidance, scene momentum,
and active-NPC refusal guidance. Exact failed IDs are in the original prompt
JUnit file. Two remained after the first repair and passed after its correction.

The current remaining defect is the size floor described in D and K. The temporary
file permission failure and direct-call guard failure were harness issues; both
are preserved as historical failures and are not relabeled as successful runs.

## J. Repairs

PRODUCTION CHANGES: YES, limited to `game/gm.py` and `game/prompt_context.py`.
Compact references/guidance were restored for the missing prompt contracts.
The system prompt regained exploration, declaration style, validator voice,
spoiler, direct-answer, and momentum anchors. Prompt instructions regained policy
references and the explicit active-NPC answer/refusal obligation. No validator,
assertion, expected result, authority object, or turn packet was weakened.

The repaired state restores the prompt tests but does not satisfy the size test.
The addition-only policy-anchor diff and exact changed-line inventory accompany
the handoff. A clean pre-gate source snapshot was not captured; a full git diff
would include unrelated pre-existing changes and is deliberately not presented
as this repair's diff. Full current files are included for independent review.

## K. Provider-size confirmation

Reconstructed once more after final regression with the repository measurement
tool and zero calls. Full requests, measurements, and rule-presence JSON are
included in the bundle.

| Probe | Before | Initial PR-BT | Final | Added by repair | Savings |
|---|---:|---:|---:|---:|---:|
| P1 | 110450 | 96178 | 97260 | 1082 | 13190 (11.94%) |
| P2 | 121438 | 109095 | 109853 | 758 | 11585 (9.54%) |
| P3 | 110665 | 98118 | 99200 | 1082 | 11465 (10.36%) |

Common minimum savings: 11465, down from 12343. System prompt: 9012 characters.
Turn packets remain 10676/10640/10910; recipes remain 2356/1876/1691.
The variation is caused by restored guidance and its conditional prompt layout,
not stochastic measurement. It is not accepted as a green size result.

## L. Semantic-presence confirmation

PASS in all three actual reconstructed provider requests: authority, inference,
player hypotheses, bounded NPC/incidental realization, structured consequential
declarations, unknown/fallback handling, and structured output. All 12 existing
presence checks per probe are true. Full response-policy objects, recipe, and
turn packet remain provider-visible. Presence evidence establishes guidance
visibility, not empirical live-model behavior.

## M. C18 status

**PASS. ACCEPTED RESPONSE == SEALED RESPONSE == EMITTED RESPONSE.**
The dedicated raw-chat authorized-fact/seal test passes independently outside
the sandbox and again in the full run. All 21 immutable-boundary tests and all
11 structured-chat-path tests pass in the final run. Earlier timeout observations
are environment diagnostics and do not constitute C18 behavioral failures.

## N. Architecture status

**A - PR-BR REMAINS CLOSED.** No authority/provenance/state-integrity contradiction
was found. Runtime ownership of claims, validation, epistemic ceilings, premise
links, immutable acceptance, and emission remains intact in the tested paths.

## O. Micro-live readiness

**NOT READY.** The remaining PR-BT size assertion must pass before advancing.
Decision taxonomy: **C - BOUNDED PR-BT REPAIR NEEDED**. No micro-live was run.
