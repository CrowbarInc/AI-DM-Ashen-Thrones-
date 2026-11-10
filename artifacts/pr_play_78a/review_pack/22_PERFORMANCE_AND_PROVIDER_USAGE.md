# Performance and provider usage

HTTP chat samples, both campaigns, excluding nothing but the turns recorded in `http_campaigns.json`: mean 206.1 ms, median 210.0 ms, p95 300.6 ms, max 545.5 ms, n 13

Survey campaign: {'mean': 137.6, 'median': 132.1, 'p95': 211.8, 'max': 211.8, 'n': 7}
Report campaign: {'mean': 244.2, 'median': 233.2, 'p95': 545.5, 'max': 545.5, 'n': 8}

Adaptive chat: {'mean': 314.2, 'median': 242.6, 'p95': 661.4, 'max': 687.4, 'n': 28}

Browser-visible `ASHEN_UI_READY` chat samples (survey raced pass plus completed survey pass, and the report pass): mean 581.9 ms, median 465.5 ms, p95 1490.1 ms, max 1623.2 ms, n 16

PR-PLAY-78 browser mean 598 ms, p95 989 ms, max 1,077 ms. Those were mostly deterministic. This cycle's browser maximum on the report mixed turn was 1,490 ms. The provider-assisted match is separate: 3828.4 ms.

Provider requests: 1
Provider tokens: 158
Accepted live matches: 1
Rejected live matches: 0
Retries on the live call: 0
Adaptive expression generation was off, so that session sent no provider requests.
