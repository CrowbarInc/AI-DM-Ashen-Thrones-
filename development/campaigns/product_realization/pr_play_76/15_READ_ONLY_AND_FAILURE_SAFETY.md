# Read-Only and Failure Safety

"Is the door open?", "Can I move the crate?", and "Am I beside the notice board?" do not commit the corresponding action. They do not change posture, position, open state, or inventory.

Failed or refused actions leave no successful consequence:

- missing target
- ambiguous target
- inaccessible target
- locked or obstructed door
- immovable target
- missing mechanic
- failed authored check
- invalid destination, including through a wall
- deferred take, drop, and place-from-inventory
- consequential break or steal

The HTTP test that injects a session-write failure returns HTTP 500, does not publish the success sentence, and leaves the prior session bytes unchanged.
