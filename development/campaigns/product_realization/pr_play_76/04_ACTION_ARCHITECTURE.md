# Action Architecture

```
player text
  -> plan_physical
  -> intent / operation
  -> target grounding
  -> current ledger and scene objects
  -> category A-F
  -> preconditions
  -> mechanical requirement, only from an authored skill_check
  -> commit_physical
  -> ledger consequence
  -> engine_publication
```

The provider is not on this path for routine wording. `interpret_with_provider` can propose an operation and a target reference. It cannot roll, set a DC, declare success, or write the ledger. The host re-parses the player text at commit time and refuses a plan whose id does not match.

Read-only questions use the existing ledger and do not create ledger keys. Writes go through the existing session save. A failed session write in the HTTP rollback test left the prior bytes unchanged.
