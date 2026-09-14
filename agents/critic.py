"""Critic agent: scores source credibility (deterministic) and judges
sufficiency / conflicts via GPT."""

from __future__ import annotations

from pydantic import BaseModel, Field

from llm import get_reasoning_llm
from state import ResearchState
from tools.credibility import score_source

SYSTEM_PROMPT = """You are a rigorous research critic. You are given a research \
query, its sub-questions, and the sources gathered so far (with summaries and \
credibility scores). Judge whether the research is sufficient to write a \
trustworthy report, note any gaps that still need dedicated research, and flag \
any conflicting information between sources. Be specific: gaps should be phrased \
as researchable sub-questions. Also identify, by their [n] index, any sources \
that are off-topic or irrelevant to the query - these will be dropped from the \
report entirely, so only flag ones a careful editor would actually cut."""


class CritiqueOutput(BaseModel):
    sufficient: bool = Field(description="True if the gathered sources adequately cover all sub-questions")
    gaps: list[str] = Field(default_factory=list, description="Specific sub-questions still needing research")
    conflicting_info: list[str] = Field(default_factory=list, description="Contradictions found between sources")
    irrelevant_indices: list[int] = Field(
        default_factory=list, description="1-based [n] indices of sources that are off-topic and should be dropped"
    )
    notes: str = Field(description="Short overall assessment of research quality")


def _dedupe_and_score(state: ResearchState) -> list[dict]:
    by_url: dict[str, dict] = {}
    for result in state.get("research_results", []):
        url = result.get("url")
        if not url or url in by_url:
            continue
        by_url[url] = score_source(result.get("subquestion", state.get("query", "")), result)
    return sorted(by_url.values(), key=lambda s: s.get("trust_score", 0), reverse=True)


def critic_node(state: ResearchState) -> dict:
    sources = _dedupe_and_score(state)

    if not sources:
        return {
            "sources": sources,
            "critique": {
                "sufficient": False,
                "gaps": state.get("plan", [state.get("query", "")]),
                "conflicting_info": [],
                "notes": "No sources were successfully gathered.",
            },
        }

    # `sources` is the same list, in the same order, that irrelevant_indices
    # is applied against below - don't resort or filter it between here and
    # the `drop` computation, or those indices will point at the wrong entries.
    digest_lines = []
    for i, s in enumerate(sources, start=1):
        digest_lines.append(
            f"[{i}] ({s.get('subquestion', '')}) {s.get('title', '')} "
            f"(trust={s.get('trust_score', 0)}): {s.get('summary', s.get('snippet', ''))}"
        )

    human_prompt = (
        f"Research query: {state.get('query', '')}\n"
        f"Sub-questions: {state.get('plan', [])}\n\n"
        "Sources gathered:\n" + "\n".join(digest_lines)
    )

    provider = state.get("reasoning_provider", "OpenAI GPT")
    llm = get_reasoning_llm(provider, temperature=0.1).with_structured_output(CritiqueOutput)
    try:
        result: CritiqueOutput = llm.invoke([("system", SYSTEM_PROMPT), ("human", human_prompt)])
        critique = result.model_dump()
    except Exception as exc:  # noqa: BLE001
        critique = {
            "sufficient": True,  # fail open so the run can still reach a report
            "gaps": [],
            "conflicting_info": [],
            "irrelevant_indices": [],
            "notes": f"Critic model unavailable ({exc}); proceeding with sources as gathered.",
        }
        return {"sources": sources, "critique": critique, "errors": [f"critic: {exc}"]}

    drop = {i - 1 for i in critique.get("irrelevant_indices", []) if 1 <= i <= len(sources)}
    filtered_sources = [s for idx, s in enumerate(sources) if idx not in drop]

    return {"sources": filtered_sources, "critique": critique}
