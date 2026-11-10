# PR-PLAY-27 repair report

Confirmed root cause: a terminal to share is outside lexical coverage despite preserving the authorized offering. The expression contract was already bounded; extending its existing own_offerings branch is sufficient.

Production files modified in this pass:
- game/expressive_dialogue.py: replace global-in-sentence offering verb substitution with a scoped full-sentence grammar, preserve whole item phrases and seller identity, align offering prompt with allowed frames.
- tools/playtest/gameplay.py: derive four expression outcomes from existing audit/accepted response; validate published wording separately; exact host proposition counts as recovery even though generated exact repetition is intentionally rejected; require correct published speaker frame; generic uncertainty with answer material fails; missing/unauthorized response fails. evaluate retains state, confidentiality, parser, binding, hard-validation and overlay gates. Experiments can set requires_substantive_answer on an action to stop generic uncertainty when that experiment requires an answer. Legitimate uncertainty in other scenarios is unchanged.
- tools/playtest/runner.py: use can_start_interaction to reserve two remaining request slots (interpretation and possible expression) before submitting a turn. Existing ceilings, token admission, refusal, deadline and transport logic are unchanged.
- tests/test_pr_play_27_expression_recovery.py: matrix, recovery/failure controls, real-controller budget gate, mocked harness continuity and HTTP opening/conversation/state evidence.

Four derived outcomes: EXPRESSION_ACCEPTED; EXPRESSION_REJECTED_RECOVERED; EXPRESSION_REJECTED_UNRECOVERED; EXPRESSION_NOT_INVOKED. These are harness observations, not new persisted gameplay fields. Rejection reason, candidate, fallback and authority remain in the existing expression audit. Projection-only recovery requires an exact authorized proposition and native hard_valid=true; missing evidence fails closed.

A useful, authorized fallback permits continuation only if all existing semantic and integrity checks pass and a full next interaction fits the request budget. A parser/transport/binding/target/social failure, final hard-invalid response, missing answer, unauthorized mutation, disclosure, explicit substantive-answer dead end or exhausted budget still stops. No provider retry, regenerated turn or increased budget.

Important discovery: the historical shared classifier already permitted the exact PR-PLAY-26 fallback. The fatal rejection rule was in that experiment's manual continuation instructions, not a blanket production classifier branch. This pass makes the distinction explicit and testable in the shared harness; it does not rewrite archived evidence/controllers or override instructions in future experiments.

Compatibility: stricter offering frames intentionally exclude sell/for sale when the actual proposition only authorizes offer. This avoids the old broad replacement's ambiguity. Mandatory descriptors are retained. Other operations and authority selection are untouched. The workspace had substantial existing changes; per-pass before/after snapshots and diffs distinguish this repair from prior uncommitted work.

Remaining continuity: the exact rumors follow-up does not select patrol_rumor. An explicit patrol follow-up selects and publishes the existing authored answer without another expression call. The full evaluator still flags its discovered-clues overlay as authority unavailable. These are recorded limitations; neither topic selection nor overlay authority was redesigned. baseline_explicit_overlay_replay.json confirms the saved pre-pass evaluator flags the same overlay authority limitation.
