# PR-CR State/Emission Consistency

The patrol topic remains selected by the authoritative social resolver before finalization.

The emitted text matches the selected authored topic:

`Guard Captain mutters, "Word is, a patrol went missing near the old milestone."`

Rejected provider additions do not become state and do not appear in final text:

- trading crossroads;
- official orders;
- non-return;
- negative evidence;
- notice-board history beyond the authorized topic.

The projection does not add discoveries by itself. It only realizes a topic already selected by the social resolver. Immutable sealing still controls the accepted text, and later semantic mutators must preserve it.

Remaining commit-before-emission risk: the broader transaction system still commits resolver state before final emission validation in some paths. PR-CR does not redesign that transaction boundary.

