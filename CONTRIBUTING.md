# Contributing

Thanks for considering a contribution — this project is free, open, and community-driven, and improvements from anyone are genuinely welcome, whether that's a one-line typo fix or a new agent capability.

## Ways to contribute

- **Report a bug** — see [SUPPORT.md](SUPPORT.md) and the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md).
- **Suggest a feature** — use the [feature request template](.github/ISSUE_TEMPLATE/feature_request.md).
- **Improve the docs** — README clarity, missing setup steps, and typo fixes are all valuable and welcome as small PRs.
- **Submit code** — bug fixes, new tools (search providers, credibility heuristics), new reasoning/local model backends, or UI improvements.

No contribution is too small. If you're unsure whether something is worth a PR, open an issue first and ask.

## Getting set up

```bash
git clone https://github.com/pypi-ahmad/multi-agent-research-assistant.git
cd multi-agent-research-assistant
uv sync
copy .env.example .env    # then add your own API keys
```

You'll need at least one of `OPENAI_API_KEY` / `AGNES_API_KEY` set, and a local [Ollama](https://ollama.com) server running with a pulled model (`ollama pull llama3.1:8b`) for the researcher-side summarization. See the README's [Environment Variables](README.md#environment-variables) section for the full list.

Run the app locally to test your changes:

```bash
uv run streamlit run app.py
```

Lint before committing (the project uses `ruff`, listed as a dev dependency):

```bash
uv run ruff check .
```

## Development workflow

1. Fork the repo and create a branch from `main`.
2. Make your change. Keep it focused — a PR that does one thing is much easier to review than one that mixes a bug fix with a refactor.
3. Test it manually against the running app (there is currently no automated test suite — see below).
4. Update the README or other docs if your change affects setup, configuration, or user-facing behavior.
5. Open a PR using the [pull request template](.github/PULL_REQUEST_TEMPLATE.md), describing what changed and why.

## Project structure

See the [README's Project Structure section](README.md#project-structure) for a map of `agents/`, `tools/`, and the core `app.py` / `graph.py` / `state.py` / `config.py` / `llm.py` / `memory.py` files. Understanding the LangGraph flow in `graph.py` (Planner → parallel Researcher → Critic → Reflector → Writer) is the fastest way to orient yourself.

## Testing

There is no automated test suite in this repository today. If you're adding non-trivial logic (a new scoring heuristic, a new tool, a state-machine change), please:

- Test it manually by running a real research query end-to-end.
- Consider adding a small `pytest` test alongside your change if it's a pure function (e.g. something in `tools/credibility.py`) — this is welcomed but not required.

## Code style

- Match the existing style in the file you're editing.
- Keep functions small and single-purpose, consistent with the existing `agents/` and `tools/` modules.
- Run `uv run ruff check .` before opening a PR.
- Avoid adding new dependencies unless there's a clear need — this project intentionally keeps its dependency list small.

## Reporting security issues

Please do **not** open a public issue for a security vulnerability. See [SECURITY.md](SECURITY.md) for how to report it privately.

## A note on scope

This is a personal, local-first project maintained on a best-effort basis. Response times to issues and PRs will vary — please be patient. See [SUPPORT.md](SUPPORT.md) for what to expect.
