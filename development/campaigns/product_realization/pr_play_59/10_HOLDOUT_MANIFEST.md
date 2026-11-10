# HOLDOUT MANIFEST

{
  "sha256": "88b8e528d2ac31cb7be61da22444d0a7a9dc316494518dae703d0822a88cbf37",
  "cases": 50,
  "groups": {
    "attempted": 3,
    "unauthorized": 15,
    "authorized": 10,
    "negated": 4,
    "ambiguous": 5,
    "harmless": 10,
    "hypothetical": 3
  },
  "frozen_before_implementation": true,
  "independence": "Same-session author; frozen before edits. Not independent blind validation.",
  "entry_implementation_sha256": "c0bed820bb9d20b497b8f7a113e3222227e6809c78d30c174abbcfe3c0336a39"
}

Frozen before implementation edits; same-session author, not independent blind validation. Development and holdout files separate. implementation_frozen.json pins all four implementation files. holdout_started.json is created exclusively before execution to prevent repeated runs. The consequence pipeline was executed once; no post-holdout source tuning. No full integrated holdout claim.
