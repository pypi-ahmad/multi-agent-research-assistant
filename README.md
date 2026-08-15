# Multi-Agent Research Assistant

A LangGraph multi-agent system that researches any topic and produces a structured, cited report — with a Streamlit UI on top.

**Repository:** https://github.com/pypi-ahmad/multi-agent-research-assistant

## Features

- **Five-agent LangGraph pipeline**: Planner → Researcher (parallel) → Critic → Reflector → Writer, with a safety-bounded critique/re-research loop.
- **Hybrid model routing**: cheap local Ollama models do per-source summarization; a hosted reasoning model (OpenAI GPT or [Agnes 2.5 Flash](https://www.agnes-ai.com/en/docs/agnes-25-flash), user-selectable) handles planning, critique, and final synthesis.
- **Multi-source research**: DuckDuckGo web search, arXiv search, and optional PDF upload, all funneled through the same source pipeline.
- **Deterministic credibility scoring**: every source gets an authority / relevance / recency / trust score from heuristics (domain reputation, lexical overlap, publish date) — never asked of an LLM, so it can't be hallucinated.
- **Hallucination-resistant references**: the model cites sources by number from a fixed list; the References section itself is assembled from code, not generated text, so a link in the report always traces back to something actually retrieved.
- **Safety-bounded research loop**: depth preset caps both critic revisions and total researcher rounds, so the Critic → Researcher loop always terminates.
- **Persistent research memory**: every run is saved to a local JSON store; browse, reload, or continue past sessions from the sidebar.
- **Follow-up research**: ask a follow-up question that extends a prior report instead of starting from scratch.
- **Live agent progress**: the UI streams which agent is currently running as the graph executes.
- **Markdown / PDF export** of the final report.

## Tech Stack

| Layer | Choice |
|---|---|
| Agent orchestration | [LangGraph](https://github.com/langchain-ai/langgraph) (`StateGraph`, parallel `Send` fan-out) |
| Reasoning models | OpenAI-compatible API (OpenAI GPT or Agnes 2.5 Flash) via `langchain-openai` |
| Local models | [Ollama](https://ollama.com) (`llama3.1:8b`, `qwen2.5:7b`) via `langchain-ollama` |
| Web search | [`ddgs`](https://pypi.org/project/ddgs/) (DuckDuckGo, no API key) |
| Paper search | [`arxiv`](https://pypi.org/project/arxiv/) |
| PDF parsing | [`pypdf`](https://pypi.org/project/pypdf/) |
| PDF report export | [`fpdf2`](https://pypi.org/project/fpdf2/) |
| UI | [Streamlit](https://streamlit.io) |
| Package/env management | [uv](https://docs.astral.sh/uv/) |

## Project Structure

```
.
├── app.py                  # Streamlit UI
├── graph.py                # LangGraph wiring (nodes, edges, parallel fan-out)
├── state.py                # TypedDict graph state + reducers
├── config.py                # Environment-driven configuration
├── llm.py                  # Model constructors (GPT / Agnes / Ollama)
├── memory.py                # JSON-backed research history store
├── agents/
│   ├── planner.py           # Breaks the query into sub-questions (GPT/Agnes)
│   ├── researcher.py        # Gathers + summarizes sources per sub-question (Ollama), runs in parallel
│   ├── critic.py             # Scores source credibility, judges sufficiency/conflicts (GPT/Agnes)
│   ├── reflector.py          # Deterministic loop/stop decision (no LLM call)
│   └── writer.py             # Synthesizes the final report (GPT/Agnes)
├── tools/
│   ├── search.py             # DuckDuckGo web search
│   ├── arxiv.py               # arXiv paper search
│   ├── pdf_loader.py         # PDF text extraction
│   └── credibility.py        # Deterministic authority/relevance/recency/trust scoring
├── data/history.json         # Local research session history (created at runtime)
├── .streamlit/config.toml    # Serves the app on port 8521
├── launch.cmd                 # One-click setup + launch (Windows)
├── .env.example
└── pyproject.toml
```

## Installation & Setup

**Windows, one click:** double-click `launch.cmd`. It installs `uv` if missing, syncs dependencies, copies `.env.example` to `.env` on first run, and starts the app.

**Manual, any OS:**

```bash
uv sync
streamlit run app.py
```

Requires Python 3.11+ (managed automatically by `uv`) and a running [Ollama](https://ollama.com) instance for the local-model side of the pipeline:

```bash
ollama pull llama3.1:8b     # or qwen2.5:7b
```

## Environment Variables

Copy `.env.example` to `.env` and fill in what you need — or simply export these in your shell/OS if you already have them set, since `python-dotenv` never overrides variables that already exist in the environment.

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `OPENAI_API_KEY` | one of the two reasoning backends | — | OpenAI-compatible API key for planning/critique/synthesis |
| `OPENAI_BASE_URL` | no | `https://api.openai.com/v1` | OpenAI-compatible endpoint |
| `OPENAI_MODEL` | no | `gpt-4o-mini` | Model name for the OpenAI backend |
| `AGNES_API_KEY` | one of the two reasoning backends | — | API key for the Agnes 2.5 Flash backend |
| `AGNES_BASE_URL` | no | `https://apihub.agnes-ai.com/v1` | Agnes AI endpoint |
| `AGNES_MODEL` | no | `agnes-2.5-flash` | Agnes model name |
| `OLLAMA_BASE_URL` | no | `http://localhost:11434` | Local Ollama server used by the Researcher agent |

You need at least one of `OPENAI_API_KEY` / `AGNES_API_KEY` set; whichever is present becomes the default reasoning backend, and either can be picked in the UI at run time.

## Usage

1. Run `streamlit run app.py` (or `launch.cmd`) and open `http://localhost:8521`.
2. Enter a research query, pick a depth (Quick / Standard / Deep), a local Ollama model, and a reasoning backend.
3. Optionally upload a reference PDF.
4. Click **Start Research** and watch the agent feed (Planner → Researcher → Critic → Reflector → Writer).
5. Review the Plan, Sources (with credibility scores), Critic Feedback, and Final Report tabs.
6. Download the report as Markdown or PDF, ask a follow-up question, or revisit past runs from the sidebar.

## How It Works (Architecture)

```
START → Planner → [Researcher × N sub-questions, parallel] → Critic → Reflector ─┬─→ Writer → END
                          ▲                                                       │
                          └──────────────── (gap sub-questions) ─────────────────┘
```

1. **Planner** (reasoning model) turns the query into 2–6 sub-questions (count set by depth) and stores depth-derived limits (`max_revisions`, `max_steps`) in state.
2. **Researcher** runs once per sub-question via LangGraph's `Send` API — a true parallel fan-out, each branch searching the web and arXiv, then summarizing hits with the local Ollama model. Results merge back into state via an `operator.add` reducer.
3. **Critic** deduplicates and scores every source deterministically (`tools/credibility.py`), then asks the reasoning model whether the research is sufficient and whether sources conflict.
4. **Reflector** is plain Python, not an LLM call: it checks the critic's verdict against `max_revisions` / `max_steps` and decides to loop back to Researcher with the critic's gap sub-questions, or proceed to Writer. This guarantees the loop terminates regardless of model behavior.
5. **Writer** drafts the report body (Executive Summary → Key Findings → Detailed Analysis → Limitations → Conclusion) citing sources as `[n]`; the References section is then appended in code from the scored source list, so every citation is traceable to a real, retrieved source.

Follow-up questions reuse the same graph with the prior report as `previous_context`, so the Planner generates sub-questions that extend rather than repeat the earlier research.

## Configuration Options

Set in `config.py` / overridable via environment variables:

- `AVAILABLE_LOCAL_MODELS` — Ollama models offered in the UI (default `llama3.1:8b`, `qwen2.5:7b`)
- `DEPTH_PRESETS` — per-depth sub-question count, sources per sub-question, max critic revisions, and max researcher steps
- `MIN_TRUST_SCORE` — minimum credibility score for a source to be cited in the final report (default `3.0`)

## Future Improvements

- Streamed token-by-token report rendering instead of a single final write
- Mid-process plan editing (currently the Critic → Reflector loop is what expands the plan, rather than live user edits)
- Vector-store-backed retrieval for the persistent research memory

## License

[MIT](LICENSE)

<p align="center">Made with ❤️ by Ahmad Mujtaba</p>
