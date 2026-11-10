# NEW CAMPAIGN BASELINE

Actual UI was attached early and New Campaign was visible/interactable. baseline_opening.png and browser_network.jsonl retain original normal creation/start evidence. No required setup fields exist: New Campaign silently resets runtime and displays Start Campaign with the existing character. Initial state/log reads complete after navigation; merely seeing the Start button before state load is insufficient evidence of readiness.

Repeated New Campaign now has a frontend busy guard and disabled control. New Campaign is disabled during opening. Cross-campaign demonstrations explicitly saved A before creating B, because current state auto-save represents only one active campaign. Creation timeout/network-loss UI injection was not executed; no broad reliability claim is made.
