# START CAMPAIGN RELIABILITY

Existing frontend startCampaignBusy suppresses duplicate clicks; server _OpeningScope serializes opening against reset/snapshot persistence. Duplicate start returns 409 without another committed turn. Start now disables New Campaign and has a 90-second AbortController deadline. Timeout/network failure says the result could not be confirmed and requests state refresh rather than asserting rollback; the server can have committed after client abort. No automatic retry/polling was added.

Observed loading is Preparing opening… with a disabled Start button; valid opening removes Start and renders actions. Failed opening/provider exception checks and existing startup suites were run offline. The new client deadline and interrupted/slow frontend cases were not all browser-injected. Current frontend had to be reloaded in a new application context because the first tab cached the old asset.
