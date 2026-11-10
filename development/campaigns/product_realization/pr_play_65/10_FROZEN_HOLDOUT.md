# FROZEN HOLDOUT

Frozen before implementation: 40 inputs and expectations; SHA-256 `75b8cb081430d4e4a6ec54907c00c2081e2a1b0baf4d7b1f4d929fbb88a3c772`. Distribution: 10 delivery, 10 unauthorized, 5 contradiction, 5 historical, 5 provider, 5 continuity. Actual transition cases were explicitly deferred before freezing, replaced by continuity, because support was not yet proven.

One execution after source freeze: 32/40 complete expectation matches; eight false rejections (H09, H26, H29, H36, H37, H38, H39, H40). Zero unsafe acceptances, mandatory omissions or state changes offline. All assembled hook responses remain safe and covered. No tuning/rerun. This developer-authored holdout is not independent blind evaluation and does not include the complete HTTP publisher; HTTP results are separately red and override any offline success claim.
