# Sequential Execution

`commit_physical` re-reads authoritative state before each step. A successful earlier step can enable a later one. A failed or unsupported earlier step blocks dependents. A success can also invalidate a later assumption because the later step is checked against the new state.

Demonstrated order:

- Push the loose stone aside, then look where it was. Both steps ran. The stone is aside.
- Push the loose stone farther, climb the milestone, and look down the road. The push committed. The climb was unsupported. The look was not attempted.

Single travel wording still returns to the existing travel path. A multi-step sentence that contains a walk is not discarded as a whole.
