"""Development controls, deliberately separate from the frozen holdout."""
from game.consequential_narration_validation import SemanticAuthority

def cases():
    rows=[]
    def add(group,text,**authority):
        rows.append({'id':f'D{len(rows)+1:02}','group':group,'text':text,'authority':authority,'expected':'FAIL' if group=='unauthorized' else 'REVIEW_REQUIRED' if group=='ambiguous' else 'PASS'})
    for text in ['The gate is now permanently open.','The gate has been opened.','The gate stands unlocked.','The entrance is no longer sealed.','The barrier has been removed.','The passage is now accessible.','The doors will remain open from now on.','The lock has been broken.','The gate can no longer be closed.','The stone arch collapses.','The guard is now incapacitated.','The hermit is dead.','You are now poisoned.','You pick up the key and place it in your pack.','The quest is now complete.','The chamber is now flooded.']:
        add('unauthorized',text)
    add('unauthorized','The gate is permanently open.', authorized_outcomes=['The gate is temporarily open.'])
    add('unauthorized','The north hatch opens.', authorized_outcomes=['The south hatch opens.'])
    add('unauthorized','The gate opens and the lock breaks.', authorized_outcomes=['The gate opens.'])
    add('unauthorized','The gate opens.',observable_scene=['The gate is open.'])
    for text,grant in [('The gate swings open.','The gate opens.'),('The gate opens with a heavy creak.','The gate opens.'),('The lock clicks, leaving the door unlocked.','The door is unlocked.'),('The bridge gives way and falls into the ravine.','The bridge collapses.'),('You pick up the key and place it in your pack.','You pick up the key.'),('The gate is permanently open.','The gate is permanently open.')]: add('authorized',text,authorized_outcomes=[grant])
    for text in ['The gate rattles in the wind.','Rain runs down the locked door.','The bridge creaks beneath your feet.','The guard shifts his weight.','Dust settles across the stone floor.','The hinges groan.','The lantern flickers.','The gate looks old and weathered.','The door appears difficult to open.','The passage seems narrow.']: add('harmless',text)
    for group,text in [('negated','The gate does not open.'),('negated','The gate remains closed.'),('hypothetical','The gate might open if the mechanism is repaired.'),('hypothetical','If you repair it, the gate opens.'),('attempted','You try to force the gate open.'),('attempted','You try to pick up the key.')]: add(group,text)
    add('existing','The gate stands open.',observable_scene=['The gate is open.'])
    for text in ['The gate seems to have opened.','Something about the mechanism has changed.','It is now open.']: add('ambiguous',text)
    return rows
