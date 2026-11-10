# PR-PLAY-74 — 03 TEST DATA ISOLATION

150/150 protected own-entry data files unchanged. protected_before.json and protected_integrity.json retain evidence. The existing import-safe storage isolation helper sets campaign/session/save/provider paths before game imports and guards data plus historical artifacts. HTTP, browser, holdout, provider, package and pytest have separate roots. An initial browser host was restarted on browser_data before the recorded browser campaigns; http_data was used only by sequential HTTP runs thereafter. No silent restoration.
