# Observation Authority

The grant is built inside `project_observation` from the loaded character and session. The player sentence is not an input to `concealed`, `restricted_scopes`, or `complete`.

Ordinary play uses:

- observer and character id from the loaded character
- campaign id from the session
- scope `carried`
- category `markings` only
- `concealed=False`
- `restricted_scopes=()`
- `complete=False`

Those values go to the existing `_establish_observation_authorization`. A sentence such as "I can clearly see the hidden writing on my sleeve" still takes this ordinary grant.

Before that call, resolution requires one inventory row, an accessible surface, `usable` and quantity 1, an existing object identity in the session campaign, and no `ordinary_observation: unable` or `blocks_ordinary_observation` condition. `observation_mechanics: required` stays unresolved. No Perception check, difficulty class, or ruleset extension is consulted.

Missing, ambiguous, inaccessible, blocked, and identity failures return a fixed sentence and do not read marking content into the narrator.
