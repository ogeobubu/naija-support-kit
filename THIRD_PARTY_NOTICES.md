# Third party software

The MIT license in this repository covers Naija Support Kit's original connector,
scripts and documentation. External software, container images and downloaded
model weights retain their respective licenses and notices. Their source code
is not vendored or relicensed by this repository.

| Dependency | Role | Upstream source and license information |
| --- | --- | --- |
| Chatwoot | Shared support inbox and channel integrations | [Chatwoot repository](https://github.com/chatwoot/chatwoot) |
| pgvector and PostgreSQL | Chatwoot database | [pgvector](https://github.com/pgvector/pgvector), [PostgreSQL](https://www.postgresql.org/about/licence/) |
| Redis | Chatwoot jobs and cache | [Redis repository](https://github.com/redis/redis); terms depend on the selected version |
| Mailpit | Local email capture | [Mailpit repository](https://github.com/axllent/mailpit) |
| Python container | Connector runtime | [Official Python image source](https://github.com/docker-library/python) |
| Ollama | Optional local model runtime | [Ollama repository](https://github.com/ollama/ollama) |
| Model weights | Optional question classification | Review the selected model's own license before use |

Naija Support Kit integrates with Chatwoot and WhatsApp. Those names and marks
belong to their respective owners; no affiliation or endorsement is claimed.
