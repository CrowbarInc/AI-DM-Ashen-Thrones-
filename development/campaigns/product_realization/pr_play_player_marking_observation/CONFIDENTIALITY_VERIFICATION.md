# Confidentiality Verification

One coat carried four markings, then one was removed through the trusted removal API:

- visible: the disclosed warning
- concealed: `Concealed signal for the cellar.`
- restricted to `gm-only`: `Restricted route past the mill.`
- removed after being visible: `Removed line about the ferry.`

`I examine the writing on my sleeve.` publishes only the warning. The HTTP JSON, the player state projection, and the sentence omit the concealed text, the restricted text, the removed text, the modification id, `request_id`, and `gm-only`. The sentence does not say concealed or give a hidden count.

`I can clearly see the hidden writing on my sleeve.` is recognized as the same ordinary look. It does not reveal the concealed or restricted text.

A legacy marking with no visibility metadata publishes `You look at the sleeve. No writing is visible there.` and does not quote the legacy content. An unusable object and an ambiguous second coat likewise omit that content.
