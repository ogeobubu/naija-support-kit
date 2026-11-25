# Contributing to Naija Support Kit

Contributions should make customer support easier to operate and keep human
handoff dependable. Oge Obubu, [@ogeobubu](https://github.com/ogeobubu), maintains
the project and reviews changes before merging them.

## Start a contribution

Open an issue for a substantial change before implementing it. Describe the
customer or operator problem, the proposed behavior and any effect on handoff,
account isolation, credentials or operating costs. Fork the repository and use
a branch for your change.

Keep pull requests focused. Explain the problem, resulting behavior and checks
you ran. Update documentation when configuration or behavior changes.

## Run checks

The offline checks use Python's standard library. Docker and a paid API account
are not needed for these checks:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/check_scenarios.py
for script in scripts/*.sh; do bash -n "$script"; done
ruby -c scripts/create_local_demo.rb
```

Before committing, stage only intended files and inspect the exact public set:

```sh
git diff --cached --stat
python3 scripts/check_public_files.py
git diff --cached --check
```

Only run `scripts/check_live_demo.py` against the configured fictional local
inbox. It creates synthetic conversations; CI does not run it against a real
Chatwoot installation.

## Protect local and customer information

Use fictional stores and synthetic messages in examples and tests. Do not commit
`.env`, credentials, database files, runtime logs, customer conversations or sales
records. `.env.example` contains placeholders only. Report vulnerabilities using
[the private security process](SECURITY.md), not a public issue.

## Contribution terms and conduct

Submit only work you have permission to contribute. Contributions are distributed
under this repository's MIT license. Preserve notices for any third-party work.
Follow the [community code of conduct](CODE_OF_CONDUCT.md). Be respectful, explain
technical disagreements and keep personal or confidential information out of
public discussion.
