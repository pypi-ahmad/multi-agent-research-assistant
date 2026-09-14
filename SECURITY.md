# Security Policy

## Supported versions

This is a single-branch personal project; there are no maintained release branches. Security fixes, if needed, are applied to `main` only. Please always run the latest commit on `main`.

## Reporting a vulnerability

If you find a security issue, please **do not open a public GitHub issue**. Instead:

1. Open a [private security advisory](https://github.com/pypi-ahmad/multi-agent-research-assistant/security/advisories/new) on GitHub, or
2. If that's not available to you, open a regular issue with minimal detail asking to be contacted privately, and the maintainer will follow up.

Please include:

- A description of the issue and its potential impact.
- Steps to reproduce it.
- Which file(s)/component(s) are involved, if known.

This is a best-effort, single-maintainer project, so please allow reasonable time for a response: there is no dedicated security team or SLA.

## Scope

This project is a **local-first application**: you run it on your own machine with your own API keys, and it has no hosted service, backend, or shared infrastructure of its own. Relevant security topics for this project include:

- Handling of API keys and credentials (`config.py`, `.env` loading via `python-dotenv`).
- Local data storage (`data/history.json`: plain JSON, no encryption, no access control beyond your OS filesystem permissions).
- Handling of untrusted input passed to the LLM (research queries, uploaded PDF text, web/arXiv search results).
- Dependencies with known CVEs (see `pyproject.toml` / `uv.lock`).

**Out of scope:** vulnerabilities in third-party services this project talks to (OpenAI's API, Agnes AI, DuckDuckGo, arXiv, or your own Ollama installation). Please report those to the relevant provider directly.

## Data handling reminder

This project does not collect, transmit, or have access to any user data. Everything stays on your machine except for the API calls you explicitly configure (to your chosen reasoning provider, and to DuckDuckGo/arXiv for search). See [DISCLAIMER.md](DISCLAIMER.md) for full details on data responsibility.
