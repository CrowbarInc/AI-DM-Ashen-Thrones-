# PR-DI Remaining Risks

- The PR-DH live set contains only six scenarios, so route-specific conclusions are provisional.
- Candidate C's final natural-language responses are not separately captured; utility is inferred from model intent fields and tool results.
- PR-DH did not measure full turn/narration costs, so cost normalization is interpretation/tool-only.
- Candidate B's useful clarification currently lives in plans that may fail schema; a future experiment needs a distinct clarification contract.
- Engine-enforced authority preservation can mask model noncompliance; future scoring should mark pre-validation model proposals separately.
- Compound-action transaction semantics are unresolved: the evidence does not show whether partial supported steps should commit when later steps are unsupported.
- Existing dirty worktree state means PR-DI can preserve but not certify unrelated modifications.
