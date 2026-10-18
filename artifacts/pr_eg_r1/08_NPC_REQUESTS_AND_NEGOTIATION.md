# 08 — NPC Requests and Negotiation

A request that promises a reward, asks the NPC to promise something, or offers to carry a message is a social request.

The NPC line is: "I can't promise you a reward for that."

That line is stored as a withheld, non-canonical commitment. It does not create a quest, a payment, an inventory change, or a faction change.

"Swear you'll pay me ten silver" uses the same decline. The response does not contain "ten silver" as an agreement.

"If I take a message to the gate for you, will you promise me something" used to fall through to an unknown-fact ask because "take" looked like a world action. A negotiation phrase is no longer discarded for that reason. The second live conversation declines it with no provider call.

The engine does not generate a counter-offer. An authorized offer would require world authority that this courtyard does not grant. No general negotiation or quest system was added.

The unsupported-command template is not on this path.
