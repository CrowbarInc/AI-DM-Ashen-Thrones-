# Concurrency tests

Development tests in `tests/test_pr_play_78_integrated.py` passed:

- Two overlapping reads, writers ordered.
- A write waits for a write. A read waits for a write.
- Duplicate request runs once.
- A failed write releases the lane.
- Independent campaigns do not block each other.

Frozen holdout: 10 concurrency cases, included in the 120/120 pass. Patterns cover reads, writes, a duplicate, a timeout, and two campaigns. The fixture was not edited after the harness key fix.

Not separately executed as live HTTP storms: save during an in-flight provider mutation, and a network retry against the browser host. Provider timeout behavior is covered by the holdout pattern and by the lane-release test. No lost update, duplicate consequence, or cross-campaign block was observed in the tests that ran.

Browser double-submit: the control is disabled for the duration of `sendChat`. Backend ordering still applies to a direct second POST.
