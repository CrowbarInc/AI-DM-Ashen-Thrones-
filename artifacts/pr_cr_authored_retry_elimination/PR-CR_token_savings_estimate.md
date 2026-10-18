# PR-CR Token Savings Estimate

Measured historical PR-CQ patrol retry consumption:

- input tokens: 42,960;
- output tokens: 83;
- total retry tokens: 43,043.

Deterministically eliminated request under PR-CR:

- the PR-CQ patrol retry generation is skipped when early projection validates;
- equivalent avoided retry requests: 1.

Projected savings under equivalent conditions:

- 43,043 tokens avoided per matching patrol-style turn.

Not claimed:

- no live PR-CR savings were measured;
- no first-generation prompt size improvement is claimed;
- no provider pricing improvement is claimed.

