# PR-BR Continuation 4 focused live transcript

## T1 claim_attempt_runner — PASS

Player: I stop beside the tavern runner and ask what rumor they have been calling out to the yard.

GM: Tavern Runner shakes their head. "I have heard talk, but I cannot verify it."

op=ask kind=inquiry dim=None dims=[] prov=inherited_discourse calls=1 fallback=['minimal_social_emergency', 'ownership_terminal']

## T2 claim_attempt_serjeant — FAIL

Player: I leave the runner and ask the gate serjeant what travelers have been repeating as they come through.

GM: Gate Serjeant mutters, "Word is, the runner heard the patrol vanished near muddy footprints northwest of the crates."

op=perceive kind=clarification dim=use dims=['use', 'wear'] prov=unresolved calls=1 fallback=[]

## T3 indirect_source — FAIL

Player: Who did he hear that from?

GM: Gate Serjeant mutters, "Word is, the patrol route changed after the Ash Compact census choke worsened."

op=ask kind=inquiry dim=source dims=['source'] prov=inherited_discourse calls=1 fallback=[]

## T4 indirect_confidence — PASS

Player: Does he trust the story?

GM: Gate Serjeant shrugs, eyes narrowing slightly. "I can't say for sure if I trust it," they mutter. "It's just word that the patrol route changed once the Ash Compact census choke tightened. Nothing confirmed beyond the rumor." "If you want certainty, you might need to follow up where those muddy footprints lead."

op=ask kind=inquiry dim=confidence dims=['confidence'] prov=inherited_discourse calls=2 fallback=[]

## T5 inspect_object — FAIL

Player: I stop at the posted sheet and look it over.

GM: Gate Serjeant says, "I couldn't tell you the requested information; you will need another source."

op=ask kind=inquiry dim=None dims=[] prov=explicit_player calls=1 fallback=[]

## T6 wear_use — PASS

Player: Does it look like people have handled it recently?

GM: Gate Serjeant says, "Which do you mean? I cannot tell which one that refers to."

op=perceive kind=clarification dim=wear dims=['wear', 'use', 'appearance'] prov=unresolved calls=1 fallback=['minimal_social_emergency', 'lawful_strict_social_emergency', 'ownership_terminal']
