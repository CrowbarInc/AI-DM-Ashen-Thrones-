# PR-DS Remaining Risks

- The compatibility gate is experimental. Production chat does not call `experiments.pr_dr` or `experiments.pr_dq`.
- DR01's stored class is still INSPECT. The predeclared expected class is still PERCEIVE. A later scorer that treats execution as class accuracy would be wrong.
- The gate accepts an INSPECT only when the utterance classification and the resolver metadata both point at a description that is already a visible fact. A future scene with a visible fact that duplicates another object's description would need a new check. This courtyard has one such fact.
- PERCEIVE of a `perceive_target` still returns that interactable's description through the existing observe adapter. This change does not widen that path, and it also does not narrow it.
- DR02 and DR06 remain operation-class misses. They did not execute. The model can still describe the wrong class on out-of-character speech.
- The stale DR09 harness note is still in the PR-DR artifacts. Readers who trust the note and skip the usage rows will under-count the live run by one request.
- Empty scene-runtime initialization on an accepted inspection changes the full snapshot without changing clues, scene, or clock. Callers that treat every snapshot difference as a world event will over-count DR01.
- The disposable world has one lantern, one gate, and one notice. Other scenes were not replayed.
- Nine production-path exploration tests and twenty-four turn-pipeline tests failed in this run. They do not import this adapter. They were not fixed here.
- There is no conversation rollback. A committed IC action stays committed in the disposable history.
