# Naija Support Kit

[![CI](https://github.com/ogeobubu/naija-support-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/ogeobubu/naija-support-kit/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Self-hosted customer support for Nigerian businesses, built with Chatwoot,
approved FAQ answers and human handoff.

Maintained by **[Oge Obubu · @ogeobubu](https://github.com/ogeobubu)**.
Naija Support Kit is an independent open-source product for teams and service
providers who want to configure and operate customer support for small businesses.

**Status: experimental, supervised pilots.** The local Website inbox workflow has
been exercised end to end. Official WhatsApp connectivity is supplied through
Chatwoot and requires separate setup and verification. Ollama classification is
optional. The default bot uses FAQ matching and does not require an AI service.

## What you can build

- Answer approved questions about opening hours, delivery and business policies.
- Escalate unknown questions, complaints, payment issues and requests for a person.
- Let staff take over conversations in Chatwoot's shared inbox.
- Run the fictional retailer demo before configuring a real business.
- Offer setup, training, hosting and maintenance as separately agreed services.

The connector is scoped to one account and inbox. Start with a separate
deployment per business. This repository does not provide automated multi-tenant
onboarding, billing or production usage enforcement.

## How it works

```text
Customer → Chatwoot Website or configured WhatsApp channel
                    ↓
               AgentBot webhook
                    ↓
         Python FAQ connector → approved answer
                    ↓
          Chatwoot reply or staff handoff
```

| Component | Responsibility |
| --- | --- |
| Chatwoot | Conversations, staff interface and channel connections |
| Python connector | FAQ selection, replies, handoff checks and event deduplication |
| PostgreSQL and Redis | Chatwoot persistence, cache and background jobs |
| Mailpit | Capture development emails locally |
| Ollama, optional | Select an approved FAQ ID using a local model |

## Try it without Docker

The connector and offline tests use Python's standard library; no dependency
installation or paid API key is required for this demonstration.

```sh
git clone https://github.com/ogeobubu/naija-support-kit.git
cd naija-support-kit
python3 scripts/setup.py
python3 bot/app.py --ask 'How much is delivery to Lekki?'
python3 bot/app.py --ask 'I want to speak to a human'
python3 scripts/check_scenarios.py
```

The sample store and prices in `knowledge/business.json` are fictional. Use
owner-approved information before serving a real business.

## Start Chatwoot locally

### macOS with Colima

Use Homebrew to install the local runtime tools:

```sh
brew install colima docker docker-compose docker-buildx
```

Verify `docker buildx version`. Homebrew's Docker plugins are installed under
`$(brew --prefix)/lib/docker/cli-plugins`; add that directory to Docker's
`cliPluginsExtraDirs` configuration if needed. A stale Docker Desktop plugin
symlink may need to be backed up and replaced when switching to Colima.

```sh
bash scripts/check-install.sh
bash scripts/start.sh
```

The start script initializes local secrets once, starts Colima if required,
pulls images sequentially with retries, builds the bot and prepares Chatwoot's
database. Initial downloads can be large. Completed images are reused on retry.

### Other Docker hosts

With Docker Engine and the Compose plugin already installed:

```sh
python3 scripts/setup.py
docker compose --parallel 1 pull postgres redis mailpit rails
docker compose build bot
docker compose run --rm rails bundle exec rails db:chatwoot_prepare
docker compose up -d
```

The convenience shell and local-demo creation helpers currently use the
standalone `docker-compose` command. Adapt them or install that command when
using these helpers on another host.

### Local services

| Service | Address |
| --- | --- |
| Chatwoot | http://localhost:3000 |
| Captured development emails | http://localhost:8025 |
| Connector health | http://localhost:8080/health |

Complete Chatwoot's initial admin setup in the browser. If initial signup is
unavailable, temporarily enable `ENABLE_ACCOUNT_SIGNUP` in your local `.env`,
recreate Rails, and disable it after creating your account.

## Connect the fictional demo

Find your account ID in Chatwoot and replace `YOUR_ACCOUNT_ID` below:

```sh
python3 scripts/create_local_demo.py --account YOUR_ACCOUNT_ID
docker-compose up -d --force-recreate bot
python3 scripts/check_live_demo.py
```

The helper creates or reuses a clearly named fictional Website inbox, attaches
a dedicated AgentBot and saves its token privately in `.env`. It prints the
public widget URL and records local IDs in `data/local-demo.json`.

See [the demonstration guide](docs/local-demo.md) for browser testing and the
scope of the live verification. For an existing inbox, use
`scripts/connect_bot.py`; it prompts privately for your administrator token.

## Configure a business

Use [the onboarding checklist](docs/pilot-onboarding.md) to collect and approve
business information, then edit `knowledge/business.json`. Each FAQ has an ID,
matching keywords and an approved answer. Changes are read on the next message.

The default `BOT_MODE=faq` uses conservative keyword matching. Unknown or
ambiguous questions escalate. Staff handle payments, refunds, stock confirmation,
complaints and order-specific questions. Attachments also go to staff.

The bot answers only pending conversations. Opening a conversation hands it to
staff. Stop all automation with `docker-compose stop bot`; start it again with
`docker-compose start bot`.

## Optional local AI

Install Ollama from its official distribution, then run:

```sh
ollama serve
# In another terminal:
ollama pull qwen2.5:1.5b
```

Set `BOT_MODE=ollama` and the appropriate `OLLAMA_URL` in `.env`, then recreate
the connector. The model selects an FAQ ID; the final business answer still
comes from approved text. Model selection can be wrong, so evaluate it with real
questions before a pilot. The runtime and model weights have separate licenses.

## Official WhatsApp connection

Connect a business-owned number and Meta account through
[Chatwoot's official WhatsApp setup](https://www.chatwoot.com/hc/user-guide/en/categories/whatsapp).
This needs appropriate account access and a reachable HTTPS deployment. Verify
incoming messages, replies and staff takeover on the actual number before launch.

The toolkit has no license fee. Hosting, electricity, internet, optional model
inference and applicable messaging charges still need budgeting.

## Tests and contribution

```sh
python3 -m unittest discover -s tests -v
python3 scripts/check_scenarios.py
```

CI runs unit tests, local HTTP contract checks, customer scenarios, syntax checks
and Compose validation. Live Chatwoot and WhatsApp tests are separate. Read
[CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

## Deployment boundaries

The Compose services bind published ports to loopback. The Sidekiq worker allows
private-network fetches so it can call the local bot. Review that setting, HTTPS,
access controls, backups, retention, monitoring and network isolation before
production hosting.

Events are deduplicated in `data/events.sqlite3`. A crash or uncertain send can
leave an event needing manual review. Processing is synchronous; staff ownership
checks and message sends are not atomic. See [SECURITY.md](SECURITY.md) for these
boundaries and private vulnerability reporting.

Keep `.env`, runtime files, customer data and sales records private. The public
repository intentionally excludes them. `scripts/check_public_files.py` checks
the Git index for forbidden files and some credential patterns before publishing.

## Project ownership and license

Naija Support Kit is maintained under the `ogeobubu` personal account with a
product roadmap, contribution process, code ownership and automated checks.
See [governance](GOVERNANCE.md), [roadmap](docs/roadmap.md) and
[changelog](CHANGELOG.md).

Original repository code and documentation are [MIT licensed](LICENSE).
Chatwoot and other external dependencies retain their own licenses and marks;
see [third-party notices](THIRD_PARTY_NOTICES.md).
