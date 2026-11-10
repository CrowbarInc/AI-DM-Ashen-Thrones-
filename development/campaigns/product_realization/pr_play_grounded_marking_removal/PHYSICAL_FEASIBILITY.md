# Physical Feasibility

A visible marking is removable only when its recorded medium still carries an established `removal.methods` entry for the requested method. The method may also name the surface kinds it applies to. The surface may name allowed methods, or set `removal_environment` to `blocked`. None of those facts are inferred from the words mud, cloth, sleeve, charcoal, or ink.

Checked in order:

- The method is present on that medium and, when declared, on that surface kind.
- The surface is accessible and the character is not marked `ordinary_removal: unable`.
- A method with `mechanics: required` stays unresolved. No skill name or difficulty class is added.
- A method with `resource: none` needs no material. A named material that is not in inventory is not invented.
- A required resource such as `water` must already be one accessible inventory item. "I wash the warning off my sleeve" does not create water.
- `consumption: required` stays unresolved and does not decrement quantity. There is no consumption writer to waive that requirement.

Wiping succeeds for the sleeve warning only after the mud record lists wipe for cloth. Rubbing the name off the paper succeeds only after the charcoal record lists rub for paper. Wiping a metal plate with no such record does not succeed. Washing without water does not succeed. After water is present, washing removes the marking and leaves the water quantity unchanged.
