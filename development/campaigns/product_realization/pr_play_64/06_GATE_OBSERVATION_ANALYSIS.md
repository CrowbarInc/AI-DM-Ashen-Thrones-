# 06 GATE OBSERVATION ANALYSIS

The bare phrase “You take a careful look.” already avoids acquisition rejection at entry: `_head` ends in “look”, a surface noun. The real historical extended candidate fails because the greedy captured object continues past “look” through the trailing examination words, so its final head is not “look”.

Exact recovered candidate:

> You take a careful look around the gate but find no new clues from your examination. The scene remains as before, with the notice board listing taxes, curfew rules, and a warning about the missing patrol, while the serjeant keeps watch and the crowd lingers in the muddy line.

This candidate reproduces FAIL → PASS. The acquisition regex now excludes the finite idioms “take a careful look” and “take a closer look” at the verb-object boundary, before greedy capture. `take note` was already uncaptured. Physical “take the iron key”, “take the key and examine it”, “take the gate's key”, and observation plus a separate item acquisition remain rejected. No broad take-prefix exemption.
