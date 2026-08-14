"""Writer agent: synthesizes the final report. Uses GPT for the prose;
the References section is assembled from code, never from the model, so a
citation can never be hallucinated."""

from __future__ import annotations

import config
from llm import get_reasoning_llm
from state import ResearchState

SYSTEM_PROMPT = """You are a senior research analyst writing a structured report. \
Use only the numbered sources provided; cite them inline as [n] matching their \
number. Never invent a source, url, or fact not present in the provided sources. \
If evidence is thin or contradictory, say so plainly in the Limitations section \
rather than glossing over it.

Write markdown with exactly these level-2 headers, in this order:
## Executive Summary
## Key Findings
## Detailed Analysis
## Limitations / Conflicting Information
## Conclusion

Do not include a title heading or a references section yourself - those are added separately."""


def _build_source_digest(sources: list[dict]) -> tuple[str, list[dict]]:
    included = [s for s in sources if s.get("trust_score", 0) >= config.MIN_TRUST_SCORE]
    lines = []
    for i, s in enumerate(included, start=1):
        lines.append(
            f"[{i}] {s.get('title', 'Untitled')} (trust={s.get('trust_score', 0)}/10, "
            f"{s.get('source_type', 'web')}): {s.get('summary', s.get('snippet', ''))}"
        )
    return "\n".join(lines), included


def _build_references(included: list[dict]) -> str:
    if not included:
        return "\n\n## References\nNo sources met the minimum credibility threshold.\n"
    lines = ["\n\n## References"]
    for i, s in enumerate(included, start=1):
        lines.append(
            f"{i}. [{s.get('title', 'Untitled')}]({s.get('url', '')}) "
            f"- trust {s.get('trust_score', 0)}/10 ({s.get('source_type', 'web')})"
        )
    return "\n".join(lines) + "\n"


def writer_node(state: ResearchState) -> dict:
    sources = state.get("sources", [])
    digest, included = _build_source_digest(sources)
    critique = state.get("critique", {})

    human_prompt = (
        f"Research query: {state.get('query', '')}\n"
        f"Sub-questions researched: {state.get('plan', [])}\n\n"
        f"Sources:\n{digest or 'No sources met the credibility threshold.'}\n\n"
        f"Critic notes: {critique.get('notes', '')}\n"
        f"Known conflicting information: {critique.get('conflicting_info', [])}\n"
        f"Known gaps not fully resolved: {critique.get('pending_gaps', critique.get('gaps', []))}\n"
    )

    title = f"# Research Report: {state.get('query', 'Untitled')}"

    try:
        provider = state.get("reasoning_provider", "OpenAI GPT")
        llm = get_reasoning_llm(provider, temperature=0.3)
        response = llm.invoke([("system", SYSTEM_PROMPT), ("human", human_prompt)])
        body = (response.content or "").strip()
    except Exception as exc:  # noqa: BLE001
        body = (
            "## Executive Summary\nReport generation failed because the GPT model "
            f"was unavailable: {exc}\n\n## Key Findings\nSee raw sources below.\n\n"
            "## Detailed Analysis\nNot generated.\n\n"
            "## Limitations / Conflicting Information\nReport could not be synthesized.\n\n"
            "## Conclusion\nRetry once the model endpoint is reachable."
        )
        report = title + "\n\n" + body + _build_references(included)
        return {"final_report": report, "errors": [f"writer: {exc}"]}

    report = title + "\n\n" + body + _build_references(included)
    return {"final_report": report}
