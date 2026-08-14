"""Planner agent: breaks the query into a research plan. Uses GPT."""

from __future__ import annotations

from pydantic import BaseModel, Field

import config
from llm import get_reasoning_llm
from state import ResearchState

SYSTEM_PROMPT = """You are a meticulous research planner. Given a user's research \
query, break it into a small set of distinct, non-overlapping sub-questions that \
together give thorough coverage of the topic. Each sub-question must be answerable \
by web/arXiv search. Do not repeat the same angle twice."""


class PlanOutput(BaseModel):
    subquestions: list[str] = Field(description="Distinct research sub-questions")
    rationale: str = Field(description="One or two sentences on how these sub-questions cover the topic")


def planner_node(state: ResearchState) -> dict:
    depth = state.get("depth", "Standard")
    preset = config.DEPTH_PRESETS.get(depth, config.DEPTH_PRESETS["Standard"])

    context_parts = [f"Research query: {state['query']}"]
    if state.get("previous_context"):
        context_parts.append(
            "This is a follow-up on prior research. Prior findings summary:\n"
            f"{state['previous_context']}\n"
            "Generate sub-questions that extend or deepen this, not ones already answered."
        )
    if state.get("uploaded_pdf_text"):
        context_parts.append(
            "The user also uploaded a reference document. Excerpt:\n"
            f"{state['uploaded_pdf_text'][:3000]}"
        )
    context_parts.append(f"Produce exactly {preset['num_subquestions']} sub-questions.")

    provider = state.get("reasoning_provider", config.DEFAULT_REASONING_PROVIDER)
    llm = get_reasoning_llm(provider, temperature=0.2).with_structured_output(PlanOutput)
    try:
        result: PlanOutput = llm.invoke(
            [("system", SYSTEM_PROMPT), ("human", "\n\n".join(context_parts))]
        )
        plan = result.subquestions[: preset["num_subquestions"]] or [state["query"]]
        rationale = result.rationale
    except Exception as exc:  # noqa: BLE001 - surface to UI instead of crashing the run
        plan = [state["query"]]
        rationale = ""
        return {
            "plan": plan,
            "plan_rationale": rationale,
            "num_subquestions": preset["num_subquestions"],
            "sources_per_subquestion": preset["sources_per_subquestion"],
            "max_revisions": preset["max_revisions"],
            "max_steps": preset["max_steps"],
            "errors": [f"planner: {exc}"],
        }

    return {
        "plan": plan,
        "plan_rationale": rationale,
        "num_subquestions": preset["num_subquestions"],
        "sources_per_subquestion": preset["sources_per_subquestion"],
        "max_revisions": preset["max_revisions"],
        "max_steps": preset["max_steps"],
    }
