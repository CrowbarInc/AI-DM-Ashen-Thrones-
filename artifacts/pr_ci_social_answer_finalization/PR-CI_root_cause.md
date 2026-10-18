# PR-CI Root Cause

Root cause:

The immutable-response lifecycle ran before authored social answer preservation. Provider ignorance, evasion, or unrelated prose could be accepted as hard-valid NPC uncertainty, or rejected into safe nonresolution, and then sealed as immutable. Once sealed, downstream social realization correctly refused to mutate the text.

This made the immutable boundary internally consistent but ordered incorrectly for selected authored social answers.

Contributing issue:

The unauthorized social-fact detector treated `second bell` as a concrete time claim but did not treat `second horn` the same way. That let a provider-generated schedule claim survive as claim-only speech when no selected topic authorized it.

Repair:

Project only resolver-authorized social content before seal:

- selected authored topic -> existing authored realization
- no selected topic + unauthored concrete social fact -> existing safe strict-social fallback

Then run the normal immutable validation and sealing path.

