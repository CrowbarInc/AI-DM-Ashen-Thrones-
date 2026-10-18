# PR-BR Regression Harness Recovery

Date: 2026-10-03

Deterministic diagnosis of the raw-chat/client-path stall reported after Claim Control Slice 2. No claim-control semantics were changed.

## 1. Executive conclusion

The previously blocked raw-chat and client-path nodes are not waiting on this tree. They return. Isolated and whole-file reruns finish in seconds. The silent-stall report matches the first `TestClient` test in each file, but that test now completes.

One of those nodes completes and fails: `test_raw_chat_stub_authority_and_contracts`. The live decision audit rejects the grounded third-bell narration, so the stub is called again with `retry_reason=hard_invalid`, and the test forbids that retry. Claim-control adversarial tests stay green. Production authority behavior was not changed to make the node pass.

An unstubbed `/api/chat` call does wait on the OpenAI client. A probe placed outside `tests/` did not load `tests/conftest.py`, so the new guard was not installed, and that probe performed two real model calls before this was stopped. Those calls are counted below. The regression suites did not repeat them.

## 2. Exact blocker reproduced

Reproduced node: `tests/test_pr_br_continuation18_immutable_boundary.py::test_raw_chat_stub_preserves_valid_and_contains_invalid`.

Result: PASS in 0.95s alone, and the whole C18 file (20 tests) passed in 0.84s. The same pattern holds for the other previously blocked files: they run to completion. C19's raw-chat node completes and fails an assertion. It does not stall.

The prior "N dots then silence" positions match the first test that constructs `TestClient` and posts `/api/chat`:

| Suite | Prior observation | First client test | This cycle |
| --- | --- | --- | --- |
| C18 | 15 dots | `test_raw_chat_stub_preserves_valid_and_contains_invalid` | PASS |
| C19 | 10 dots | `test_raw_chat_stub_authority_and_contracts` | FAIL (completes) |
| C20 | 13 dots | `test_raw_chat_stub_covers_incidental_binding_and_authority` | PASS |
| C21 | 9 dots | `test_raw_chat_stub_covers_the_ten_boundaries` | PASS |
| C21b | 17 dots | `test_raw_chat_stub_rejects_nonpersons_and_keeps_people` | PASS |
| C21c | grouped with C21b | `test_raw_chat_stub_covers_referential_heads` | PASS |
| C22 | 26 dots | `test_raw_chat_stub_covers_commitment_and_addressee` | PASS |
| C24 | 5 dots | `test_p1_c22_after_runner_keeps_contract_and_runner` | PASS |

## 3. Blocking call stack/path

There is no waiting stack on the stubbed tests. The request returns to the test.

C19's completed failure shows the path that the retry takes:

`TestClient.post("/api/chat")` → `api_chat` → `chat` → `run_preserve_if_valid` → `_regenerate_once` → `_bounded_call_gpt(..., retry_reason="hard_invalid")` → the test's `game.api.call_gpt` stub.

The stub then raises `AssertionError` at `tests/test_pr_br_continuation19_hard_authority.py:435` because `retry_reason == "hard_invalid"`.

What the unstubbed production function waits on, observed once and then stopped:

`game.gm.call_gpt` → `resolve_model_route` → `openai.OpenAI(...)` → `client.responses.create(...)`.

That path logged `[MODEL ROUTE] purpose=strict_social` and `[MODEL ROUTE] purpose=retry_escalation` and returned HTTP 200 in 7.8s in this environment. If `responses.create` cannot finish, the OpenAI client waits out its HTTP timeout and pytest has no assertion to print. Captured stdout, including the route log, stays hidden until the test ends, so an interrupt looks like a silent block.

## 4. Root cause

Two separate facts:

1. The reported stall does not reproduce for the stubbed client tests. Their monkeypatch of `game.api.call_gpt` is the call site `chat` uses, and the stub returns.

2. `game.gm.call_gpt` catches `Exception` around the OpenAI call and, on failure, returns a fallback. A missed stub therefore either waits on `responses.create` or, if the client raises a normal exception, turns that into GM fallback text instead of a test error. That is why a live attempt can look like a hang rather than a failure.

The C19 assertion failure is not that wait. The initial line is rejected by the decision audit, so regeneration is invoked once, as designed.

## 5. Harness vs production

The stubbed tests that were reported as blocked are harness paths, and they return.

The unstubbed generation function is production code that waits on the model client. Deterministic tests are supposed to replace `game.api.call_gpt` before posting. The new guard makes a missed replacement fail the test before that wait.

## 6. Regression timeline

E. Cannot be temporally isolated.

Claim Control Slices 1 and 2 are uncommitted working-tree changes. `git log` on `game/gm_resolution_decision.py` does not contain those slices as commits, so they cannot be bisected without rewriting history. The stall described in the Slice 2 report does not reproduce on this same tree. The C19 live-path rejection is visible now, on the current claim-control tree. The sibling unit test `test_grounded_third_bell_is_authoritative_and_kept` still passes because it never supplies a `GMResolutionDecision`.

## 7. Minimum reproduction

Smallest path that was reported to hang, and that now returns:

- seeded frontier-gate session
- `TestClient(app)`
- `POST /api/chat`
- `game.api.call_gpt` stub

It does not require a prior turn, narration-audit fixtures, or a live model. C18's first post is enough, and it passes.

Smallest path that fails:

1. Same seed.
2. First chat turn (the ungrounded schedule is rejected and replaced).
3. Append visible fact `The city gate closes when the watch changes at the third bell.`
4. Second chat: "I ask the guard what hour the gate closes."
5. Stub returns `THIRD_BELL` on every call.

The second turn's first generation is rejected. The retry call arrives with `retry_reason=hard_invalid`. Rejection reasons on that retry prompt:

- `unauthorized_resolution_decision_fact`
- violations with `reason_codes: ["proposition_authority"]` for both sentences:
  - "Travelers can still pass, but only until the watch changes at the third bell."
  - "After that, the gates close until morning."

The schedule sentence is present in the generation prompt. It does not cover either narration sentence under decision-row matching.

## 8. Model-call safety audit

| Question | Finding |
| --- | --- |
| What replaces real generation? | The test's `game.api.call_gpt` monkeypatch. |
| Is it still patched? | Yes. C18 and the other passing raw-chat nodes receive the stub. C19's failure is raised inside the stub. |
| Correct import location? | Yes for `/api/chat`. `game.api` binds `call_gpt` at import and the route calls that global. |
| Did architecture changes move the call site? | The route still calls `game.api.call_gpt`. A direct `game.gm.call_gpt` call would bypass a patch that only targets `game.api`. |
| Can a test bypass the stub? | Yes, if it posts `/api/chat` without replacing `game.api.call_gpt`, or if it calls `game.gm.call_gpt` after only patching `game.api`. |
| Is a client constructed with no request? | Not by the stubbed tests. The unstubbed function constructs `OpenAI` and then calls `responses.create`. |
| Retry waiting on a stale stub? | No unbounded retry. Regeneration is one `hard_invalid` attempt, then the targeted-retry loop is capped. C19 fails on that single retry. |
| Separate unpatched interpretation call? | `ASHEN_DISABLE_LIVE_INTERPRETATION=1` in `tests/conftest.py`. Interpretation returns skipped and does not call the model. |
| Preflight? | Lifespan calls `log_upstream_api_preflight_at_startup`. Pytest sets `ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT=1`, so startup does not probe. |

## 9. TestClient / ASGI lifecycle

`TestClient(app)` enters the FastAPI lifespan. Lifespan ensures data files, logs the skipped preflight, and prints the upstream-gate summary. That returns. The request is synchronous `chat`, not a streaming response. Persistence uses an `RLock` that is released before the request. No portal deadlock was observed. Whole-file client suites exited.

## 10. Claim-control interaction

Claim control does not cause the reported stall. The stubbed requests return.

It does cause the C19 failure. `audit_narrated_claims` marks consequential proposition rows with `proposition_authority` unless a decision row covers the sentence. The visible schedule fact is stored as an authorized row with an empty semantic identity. Empty identity does not match by itself. Token overlap also fails:

- the fact is "The city gate closes when the watch changes at the third bell."
- the narration adds "travelers can still pass" and "until morning"
- neither sentence is a token subset of the fact, nor the reverse

`validate_generated_response` maps a failed decision audit to `unauthorized_resolution_decision_fact` only when a decision is present. The older unit test omits the decision, so corpus grounding still accepts the same text. The live path always has a decision.

No unbounded iteration, lock, or serialization recursion was involved. The retry happens once.

## 11. Regex performance

Slice 2 detectors were timed on short narration, a long repeated narration, `"bell " * 2000`, a long quotation, and adversarial punctuation (`"...?!," * 500` plus 200 quotes).

Single-pattern searches on the punctuation string, including the new actor, cause, history, causal, evidential, and certainty patterns, each finished in well under 0.05s.

Full audits:

- short, long, repeated-token, and quoted narration: each under 0.25s
- punctuation split into 500 fragments: about 7.1s to 8.9s

That punctuation cost is linear in fragment count. Each fragment re-runs the audit, including proposition classification of the whole text. It is not an exponential backtracking hang, and it is not where the raw-chat tests spend their time. Those tests use ordinary sentences and finish in about a second. The bound is locked by `tests/test_pr_br_claim_control_regex_bound.py`. Production detectors were not edited.

## 12. Repair implemented

No production authority change.

Harness repair:

- `tests/helpers/live_model_guard.py`
- autouse fixture `_forbid_live_model_calls` in `tests/conftest.py`
- `tests/test_live_model_guard.py`
- `tests/test_pr_br_claim_control_regex_bound.py`

`LiveModelCallForbidden` subclasses `BaseException` so `call_gpt`'s `except Exception` cannot turn the attempt into a fallback or a network wait.

## 13. Fail-fast API guard

For every test under `tests/`, the fixture replaces:

- `openai.OpenAI` and `openai.AsyncOpenAI`
- `game.gm.call_gpt`
- `game.api.call_gpt`
- `game.semantic_interpreter._invoke_interpretation_model`
- `game.api_upstream_preflight._default_openai_client_factory`

A test stub that assigns `game.api.call_gpt` replaces the generation wrapper. The constructor block stays. The exception message includes the site name and the call stack.

Confirmed: `openai.OpenAI(api_key="not-a-live-call")` and `game.gm.call_gpt(...)` raise `LiveModelCallForbidden` immediately. No transport.

The guard does not apply to a pytest file outside `tests/`, because pytest does not load `tests/conftest.py` for those paths. That is how the probe below escaped it.

## 14. Previously blocked node results

| Node | Result |
| --- | --- |
| `test_raw_chat_stub_preserves_valid_and_contains_invalid` | PASS |
| `test_raw_chat_stub_authority_and_contracts` | FAIL |
| `test_raw_chat_stub_covers_incidental_binding_and_authority` | PASS |
| `test_raw_chat_stub_covers_the_ten_boundaries` | PASS |
| `test_raw_chat_stub_rejects_nonpersons_and_keeps_people` | PASS |
| `test_raw_chat_stub_covers_referential_heads` | PASS |
| `test_raw_chat_stub_covers_commitment_and_addressee` (C22) | PASS |
| C24 client posts, including `test_p1_c22_after_runner_keeps_contract_and_runner` | PASS |

None were skipped, xfailed, or left as "interrupted."

## 15. Broad deterministic regression

One pytest session, fail-fast guard installed, 29.1s, exit code 1:

| Suite | Tests | Result |
| --- | ---: | --- |
| live model guard | 2 | PASS |
| regex bound | 1 | PASS |
| Claim Control Slice 1 | 6 | PASS |
| Claim Control Slice 2 | 10 | PASS |
| GMResolutionDecision | 9 | PASS |
| Decision Ownership Slice 2 | 7 | PASS |
| Semantic Fidelity Slice 3 | 7 | PASS |
| Qualifier / movement / mixed intent | 9 | PASS |
| C18 | 20 | PASS |
| C19 | 11 | 10 PASS, 1 FAIL |
| C20 | 14 | PASS |
| C21 | 10 | PASS |
| C21b | 18 | PASS |
| C21c | 17 | PASS |
| C22 | 27 | PASS |
| C23 | 3 | PASS |
| C24 | 9 | PASS |
| C25 | 9 | PASS |
| C26 | 8 | PASS |
| C27 | 13 | PASS |
| **Total** | **210** | **209 PASS, 1 FAIL** |

Movement/state coverage is the qualifier suite plus C22's commitment/movement nodes, all passed. NPC epistemic coverage is Slice 2, Semantic Fidelity Slice 3, Decision Ownership Slice 2, and C19's non-chat epistemic tests, all passed except the one C19 client node above.

## 16. Newly exposed failures and classifications

`test_raw_chat_stub_authority_and_contracts`

Classification: D. The live architecture now audits narration against `GMResolutionDecision`. The test still expects the older corpus-grounding rule to keep `THIRD_BELL` on the first generation once the schedule is a visible fact.

The visible fact does not cover the two sentences. Those sentences also add "travelers can still pass" and "until morning," which the fact does not state. The unit test without a decision still accepts the text. This was not patched. Claim control was not weakened. It is not a harness defect, and it is not widespread: it is the only failure in the 210-test run.

## 17. Claim-control adversarial recheck

Slice 1 and Slice 2 ran in the same session as the harness repair: 16 passed. That includes actor attribution, cause attribution, event time, history assertions, cue-less residuals, epistemic certainty, player presupposition, NPC repetition, false-positive controls, positive authority, and temporal provenance.

## 18. Files changed

- `tests/conftest.py`
- `tests/helpers/live_model_guard.py`
- `tests/test_live_model_guard.py`
- `tests/test_pr_br_claim_control_regex_bound.py`
- `artifacts/pr_br_regression_harness/diagnostic_report.md`
- `handoff/CURRENT_REVIEW.md`
- `handoff/REVIEW_MANIFEST.json`
- `handoff/CURRENT_REVIEW.zip`

No production semantic files were edited.

## 19. Known limitations

- The original silent stall was not reproduced, so its exact waiting frame on the prior run cannot be dumped.
- The fail-fast guard applies to tests collected with `tests/conftest.py`. A pytest file outside `tests/` does not get it.
- Authored visible facts with empty semantic identity still do not license partial paraphrases that add extra consequential claims. Whether they should is a product decision, not a harness fix.
- Punctuation-fragment audits are linear and can take several seconds on hundreds of fragments. Ordinary narration does not.

## 20. Exact gameplay/model API call count

2.

Both were `responses.create` calls from one accidental probe, `development/tmp/test_guard_probe.py::test_unstubbed_chat_fails_closed`, which lived outside `tests/` and therefore did not load the guard. Route log: `strict_social`, then `retry_escalation`. The probe was deleted and not repeated.

Regression suites, guard tests, regex timing, and the stubbed raw-chat reruns: 0.

## 21. Recommendation

Do not start live validation on the strength of this harness pass alone. The client suites are usable again, and claim control's adversarial tests are still green. The one completed failure is a real authority mismatch between corpus grounding and the live decision audit. Decide that case in a targeted follow-up. Do not loosen the audit to satisfy the old assertion.

B.
HARNESS RESTORED BUT DETERMINISTIC REGRESSIONS EXPOSED LOCALIZED PRODUCTION DEFECTS;
RETURN TO TARGETED IMPLEMENTATION
