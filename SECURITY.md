# Security policy

Naija Support Kit is an experimental starter for supervised, single-business
pilots. The Compose configuration is intended for local development. It does
not establish production readiness or provide a security service-level agreement.

## Report a vulnerability privately

Use [GitHub private vulnerability reporting](https://github.com/ogeobubu/naija-support-kit/security/advisories/new).
Include affected versions, reproduction steps and the expected impact. Use
synthetic data and redact credentials. Avoid public issues for unpatched
vulnerabilities or customer data.

The maintainer reviews reports as availability permits. No response-time
commitment is currently offered. Fixes target the current main branch.

## Deployment boundaries

- Keep the local ports bound to loopback. Put a production deployment behind
  properly configured HTTPS and access controls.
- The local Sidekiq worker allows private-network fetches so it can reach the
  bot container. Review this permission and network isolation before hosting
  untrusted accounts or accepting arbitrary webhook destinations.
- The connector accepts only the configured account and inbox. Use a separate
  deployment for each business until stronger tenant isolation is implemented.
- The webhook URL includes a shared secret. Do not publish that URL or log it.
- Keep `.env`, backups, logs, conversation records and the `data/` directory out
  of public repositories. Rotate any credential that has been exposed.
- The connector checks conversation status before sending, but that check and
  the send are not atomic. Supervise handoffs during pilots.

Model runtimes, model weights, Chatwoot and other containers have their own
security updates and reporting processes. See [third-party notices](THIRD_PARTY_NOTICES.md).
