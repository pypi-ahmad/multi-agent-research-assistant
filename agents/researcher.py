"""Researcher agent: gathers sources per sub-question, summarizes via local Ollama model.

Runs as a LangGraph `Send` target, so it only ever sees the small payload
dict it was dispatched with (subquestion / local_model / sources_per_subquestion),
not the full graph state.
"""

from __future__ import annotations

import config
from llm import get_local
from tools.arxiv import arxiv_search
from tools.search import web_search

SUMMARY_PROMPT = (
    "Summarize the following source in 2-3 sentences, focused on how it relates to "
    "this research question: {subquestion}\n\nTitle: {title}\nContent: {snippet}"
)


def _summarize(llm, subquestion: str, title: str, snippet: str) -> str:
    prompt = SUMMARY_PROMPT.format(subquestion=subquestion, title=title, snippet=snippet[:2000])
    response = llm.invoke(prompt)
    return (response.content or "").strip()


def researcher_node(payload: dict) -> dict:
    subquestion = payload["subquestion"]
    local_model = payload.get("local_model") or config.DEFAULT_LOCAL_MODEL
    k = payload.get("sources_per_subquestion", 3)

    errors: list[str] = []
    raw_sources: list[dict] = []

    try:
        raw_sources.extend(web_search(subquestion, max_results=k))
    except Exception as exc:  # noqa: BLE001
        errors.append(f"web_search failed for '{subquestion}': {exc}")

    try:
        raw_sources.extend(arxiv_search(subquestion, max_results=max(1, k // 2)))
    except Exception as exc:  # noqa: BLE001
        errors.append(f"arxiv_search failed for '{subquestion}': {exc}")

    if not raw_sources:
        return {"research_results": [], "errors": errors, "step_count": 1}

    llm = get_local(local_model)
    local_model_down = False
    results = []
    for source in raw_sources:
        summary = source.get("snippet", "")
        if not local_model_down:
            try:
                summary = _summarize(llm, subquestion, source.get("title", ""), source.get("snippet", ""))
            except Exception as exc:  # noqa: BLE001
                local_model_down = True
                errors.append(
                    f"local model '{local_model}' unavailable ({exc}); using raw snippets for this round"
                )
        results.append({**source, "subquestion": subquestion, "summary": summary})

    return {"research_results": results, "errors": errors, "step_count": 1}
