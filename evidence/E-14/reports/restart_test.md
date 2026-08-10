# Restart Test - E-14

Commit: `44e6cb32`
Generated: `2026-08-10T04:03:41+00:00`

- Before simulated backend restart: `/api/v1/alerts/recent` count `1`.
- After fresh Backend app instance: `/api/v1/alerts/recent` count `0`.

Current recent-alert state is process memory (`request.app.state.decision_alerts`), so a backend process restart loses recent alerts unless a durable store/outbox is added.
