# 07 — Prototype Findings

PR-PLAY-12 · 2026-10-31 America/New_York. Offline investigation and isolated prototypes only.

The experiment code is `artifacts/pr_play_12/prototypes.py`. It is imported only in the disposable assessment environment. There are no runtime imports, provider requests, dependencies, canonical state writes or persistent schema additions. `test_assessment.py` retains the replay/corpus/prototype test code; prepare.py and run_regression.py document reproduction.

**A:** E1–E20 measure unchanged current production behavior. The two supported synonym/tense variants fail while several unauthorized outcomes pass. The latest historical single-word control commits once. These establish both lexical friction and incomplete detection, not a replacement validator.

**B lower-bound prototype:** validate declarations with the real source authority function, then publish arbitrary narration. All ordinary valid-declaration corpus variants pass, including unauthorized success, combat, movement, resource/quest and hidden-fact text; E19's forged declaration fails. This deliberately minimal prototype isolates what structured authority alone can guarantee. It is not an implementation of every possible enhanced B safeguard. A reference-linked arbitrary string has the same semantic hole; a reliable general deterministic semantic equivalence algorithm was not demonstrated.

**C/H finite prototype:** plan shape is exactly atoms + texture. Atoms contain only claim_id and variant; no supplied text is read. IDs must exist in the caller's public scene catalog; canonical text is engine-supplied. Three reviewed alternatives cover word order, rumor/gossip and missing-patrol tense. Required anchors are a three-fact experimental subset (notice/serjeant/runner), not a claimed extraction of production obligation semantics. One finite rain texture is allowed. Duplicate atoms and independent anchors are permitted. Required omissions, raw unsupported prose, unknown/hidden IDs, unreviewed variants, injected text fields and unknown sensory selectors fail closed.

Twenty comparative corpus plans and four hostile plan controls run deterministically. Supported/incidental cases accept reviewed realization choices; unsupported cases and E17 omission reject the new representation. Input-context equality and empty state_mutations are asserted. Results and rendered output are in prototype_results.json. This does **not** mean the original arbitrary E2/E3/E4 prose is semantically understood: the plan selects a renderer-owned variant. E16 renders supported anchors as separate sentences. C enforces its own explicit required-anchor policy, which differs from current E17 behavior.

Each candidate against the minimum objective:

| Candidate | Supported paraphrase | Unauthorized mechanics | Hidden information | Unsupported consequences | State authority |
| --- | --- | --- | --- | --- | --- |
| A | Some; E3/E4 false-positive candidates | E8/E9 delivered: incomplete | Exact E11 repaired downstream; paraphrases uncertain | Mixed: E6 rejected, E12/E20 delivered | Six domain checks pass; legacy adoption risk remains |
| B lower bound | Yes, arbitrary strings | Fails | Fails without downstream publication enforcement | Fails | No direct writes, but unsafe narrative premise exposure |
| C/H closed plan | Yes, three finite reviewed forms | Reject unrepresentable text/outcome | Unknown IDs/text injection rejected, conditional on public catalog | Reject unrepresented statements | Pure renderer; input unchanged; no state mutations |


Limitations: finite author-reviewed variants are not NLP entailment; publication filtering is a precondition, not fully integrated; runtime grammar, accessibility, attribution and ordinary-turn migration remain unimplemented; no latency or token-cost benchmark; no gameplay-quality score; no crash/restart transaction proof. A complete safe interface allowing arbitrary fresh prose is still unproved. The evidence supports a smaller constrained implementation, not a broad prose-validation relaxation.
