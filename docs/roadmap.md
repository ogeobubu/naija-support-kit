# Product roadmap

The current milestone is a supervised, local customer-support demonstration.
The following priorities are direction, not promised dates or service guarantees.

## Available now

- Self-hosted Chatwoot, PostgreSQL, Redis and local email capture.
- A standard-library Python bot with approved FAQ replies.
- Human-request and unknown-question handoff.
- Account and inbox checks, duplicate-event suppression and failure records.
- Optional Ollama classification that selects approved FAQ answers.
- Synthetic customer scenarios and a live fictional-inbox verification helper.

## Next milestone

- Repeatable setup on Linux servers and more deployment documentation.
- Durable asynchronous webhook processing and bounded retries.
- Stronger coordination between staff takeover and bot replies.
- Better monitoring, rate limits and usage controls.
- A documented end-to-end official WhatsApp pilot.
- Evaluation of local models with Nigerian phrasing and supported languages.

## Later work

- Audited multi-business isolation and permission boundaries.
- Customer onboarding and knowledge approval workflows.
- Reporting that separates automation quality, staff effort and operating costs.

Discuss priorities in GitHub issues. Commercial customizations should not bypass
the handoff and isolation requirements of the core product.
