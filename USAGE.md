# Usage Guide

A step-by-step walkthrough of the Streamlit app, grounded in the actual UI
code in `app.py`. For what the app is and how it's built, see
[ARCHITECTURE.md](ARCHITECTURE.md).

## 1. First-time setup

**Windows, one click:**

```powershell
launch.cmd
```

This installs `uv` if it's missing, runs `uv sync`, creates `.env` from
`.env.example` on first run, and launches the app at
`http://localhost:8521`.

**Manual, any OS:**

```bash
uv sync
cp .env.example .env    # then edit .env with your keys
uv run streamlit run app.py
```

You need:
- At least one reasoning-provider key: `OPENAI_API_KEY` (OpenAI-compatible)
  or `AGNES_API_KEY` (Agnes 2.5 Flash). Whichever is set becomes the
  default; you can still pick either one in the UI at run time.
- A running [Ollama](https://ollama.com) instance with at least one model
  pulled, used for cheap per-source summarization:
  ```bash
  ollama pull llama3.1:8b     # or qwen2.5:7b
  ```

## 2. Start a research run

1. Open `http://localhost:8521`.
2. Type your research query into the text box.
3. Pick a **depth**:

   | Depth | Sub-questions | Sources per sub-question | Max critic revisions | Max researcher rounds |
   |---|---|---|---|---|
   | Quick | 2 | 2 | 0 | 4 |
   | Standard (default) | 4 | 3 | 1 | 8 |
   | Deep | 6 | 4 | 2 | 14 |

   Higher depth means more thorough coverage, but more search calls, more
   local-model summarization calls, and longer wall-clock time.
4. Pick a **local model** (from your pulled Ollama models) and a
   **reasoning model** (OpenAI GPT or Agnes 2.5 Flash), whichever backend
   you pick needs its API key set (a warning banner appears if it's
   missing).
5. Optionally upload a reference PDF; its text is extracted and folded
   into both the Planner's context and the source pool for the report.
6. Click **Start Research**. A live status panel shows which agent
   (Planner → Researcher → Critic → Reflector → Writer) is currently
   running as the graph executes; the Critic → Reflector step may loop
   back to Researcher one or more times (up to the depth's revision limit)
   before reaching the Writer.

## 3. Review the results

Once the run completes, four tabs appear:

- **Plan**: the Planner's rationale and the sub-questions it generated.
- **Sources**: every source that survived deduplication and critic
  filtering, sorted by trust score, each expandable to show its summary,
  authority/relevance/recency breakdown, and link. Sources below
  `MIN_TRUST_SCORE` are marked "below threshold" and excluded from the
  final report, but still shown here for transparency.
- **Critic Feedback**: the critic's overall notes, any remaining gaps,
  any conflicting information found between sources, and any warnings
  logged during the run (e.g. a failed search call or an unavailable
  model that caused a graceful fallback).
- **Final Report**: the generated Markdown report (Executive Summary →
  Key Findings → Detailed Analysis → Limitations → Conclusion → References),
  with **Download as Markdown** and **Download as PDF** buttons.

Every run is automatically saved to local history; no explicit save step
is needed.

## 4. Ask a follow-up question

Below the results, type a question in **"Ask a follow-up to dig deeper on
the same topic"** and click **Continue Research**. This re-runs the full
five-agent pipeline with the prior report as context, so the Planner
generates sub-questions that extend the earlier research rather than
repeating it. The follow-up reuses the same depth, local model, and
reasoning provider as the original run, and updates the same saved session
rather than creating a new one.

## 5. Revisit past research

The sidebar's **"Past Research"** section lists your last 20 sessions
(newest first), each showing its query, depth, and local model. Expand a
session and click:

- **Load**: restores that session's plan, sources, and report into the
  main view (its critic feedback isn't persisted, so that tab will be
  empty for a loaded session).
- **Delete**: permanently removes it from `data/history.json`.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Yellow warning banner about a missing API key | Neither `OPENAI_API_KEY` nor `AGNES_API_KEY` is set for the reasoning provider you picked | Set the relevant key in `.env`, or switch providers in the dropdown |
| "Start Research" button is disabled | The query box is empty | Type a query; it's required |
| Sources tab is empty / report says "no sources met the credibility threshold" | Web/arXiv search failed for every sub-question, or every result scored below `MIN_TRUST_SCORE` | Check the Critic Feedback tab's warnings for the underlying search error; try a broader query |
| Report body says "Report generation failed because the GPT model was unavailable" | The reasoning provider's API call failed (bad key, network issue, rate limit, timeout) | Check your API key and network; requests time out after `REASONING_TIMEOUT_SECONDS` (60s by default) |
| Source summaries look like raw snippets instead of 2 or 3 sentence summaries | The local Ollama model was unreachable or timed out mid-run; the app falls back to raw snippets rather than failing the run | Confirm Ollama is running and the selected model is pulled; requests time out after `OLLAMA_TIMEOUT_SECONDS` (90s by default) |
| PDF download button shows "PDF export unavailable" | `fpdf2` failed to render the report (rare) | Use the Markdown download instead |
| PDF export shows `?` in place of em dashes/curly quotes | `fpdf2`'s core fonts are Latin-1 only; this is a known, accepted limitation | Use the Markdown download for exact text, or ignore; it's cosmetic |
| Loaded past session shows no critic feedback | Critic feedback (gaps/conflicts/notes) is not persisted to `data/history.json`; only plan, sources, and the final report are | Expected behavior; re-run the query if you need fresh critic feedback |

## Resetting

All state lives in `data/history.json`. Delete it (or delete individual
sessions via the sidebar) to clear history. Delete `.venv` and re-run
`launch.cmd` / `uv sync` to reset the Python environment.
