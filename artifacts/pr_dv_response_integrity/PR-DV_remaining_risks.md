PR-DV Remaining Risks

- Broad shared turn-pipeline tests remain red in this dirty checkout.
- Persistence failure and exception rollback behavior were not fully injected.
- HTTP transport/browser-level behavior remains inconclusive.
- The worktree already contained many unrelated modifications, including production save files; PR-DV used disposable test storage only.
