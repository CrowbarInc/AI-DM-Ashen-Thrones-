# Intent Recognition

`recognize_removal` accepts a first-person wipe, rub, erase, clean, remove, or wash aimed at a marking word: writing, mark, note, message, warning, name, ink, letters, and the same family. The marking phrase and the object phrase are split on off, from, away from, or on. An optional with/using phrase is kept as a requested material. The proposal stores the utterance, operation `remove_marking`, method, target phrase, marking phrase, and resource phrase.

Recognized examples include "I wipe the warning off my sleeve", "I try to wipe the warning off the coat sleeve", "I rub the name off the paper", "I erase the message on the board", and "I remove the warning from my notes". The last two do not succeed unless an object and a compatible marking are established.

These do not enter the removal class:

- "I erase the memory from my mind."
- "I remove the coat."
- "I clean my sword."
- "I wipe my hands."
- "I wipe the dust off my sleeve."
- "I tell him to erase the writing."
- "I examine whether the writing was removed."
- "I inspect the erased writing."
- "I copy the warning onto my sleeve using the mud."

A question mark, a delegated command, or an examination verb at the start returns no proposal. "I rub away the charcoal writing" is recognized and then left unresolved because it names no object. Player wording is not stored as proof that a marking exists.
