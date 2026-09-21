# Development Evidence

This directory is the non-runtime development-history owner. It is not part of
the minimum runnable product.

Do not load this tree recursively. Start from `docs/DEVELOPMENT_CONSTITUTION.md`
and `docs/NEXT_SESSION.md`, then open only the paths those documents name.

## Layout

| Path | Owner |
|---|---|
| `campaigns/reconciliation/` | Architecture Reconciliation (`AR-*`) reports |
| `campaigns/product_realization/` | Product Realization (`PR-*`) reports |
| `campaigns/foundation/` | Earlier foundation campaign reports (`CD`–`CX`) |
| `reports/` | Repository-organization and other housekeeping reports |
| `archive/` | Stray historical root output that is not a campaign report |
| `tmp/` | Disposable Cursor/Codex/pytest scratch (Git-ignored) |

## Placement

- Write new AR/PR campaign reports directly under the matching `campaigns/` era.
- Write generated replay/audit evidence under `artifacts/<topic>/`, not here.
- Write disposable test output under `tmp/`.
- Leave runtime code in `game/`, `data/`, and `static/`.
- Leave standing governance in `docs/`.
