# 09 SUPPORTED OPERATIONS

Projection/validation adapter supports items_added, items_removed and explicit counted deltas using existing field conventions. It does not add a gameplay mechanic. Inspection of game/exploration.py found investigation discovery/status transitions, not inventory acquisition/removal producers. Existing character defaults/imports contain inventory state, but no supported investigation consumption, transfer or equipment-change effect contract was found.

Thus acquisition/removal/quantity tests are synthetic resolver-adapter controls. No actual potion use, item transfer, source/destination inventory, equipment transition, arbitrary quantity setting or resulting inventory total is claimed supported. Unsupported recognized operations fail closed; unknown English/unknown effect vocabulary remains a heuristic limitation. No canonical fixture is rewritten to manufacture support.
