"""LangGraph wiring: planner -> researcher (parallel) -> critic -> reflector
-> {researcher again | writer}."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from agents.critic import critic_node
from agents.planner import planner_node
from agents.reflector import reflector_node
from agents.researcher import researcher_node
from agents.writer import writer_node
from config import DEFAULT_REASONING_PROVIDER
from state import ResearchState


def _dispatch_research(state: ResearchState) -> list[Send]:
    """Fan out one parallel `researcher` run per sub-question."""
    local_model = state.get("local_model")
    sources_per_subquestion = state.get("sources_per_subquestion", 3)
    return [
        Send(
            "researcher",
            {
                "subquestion": subquestion,
                "local_model": local_model,
                "sources_per_subquestion": sources_per_subquestion,
            },
        )
        for subquestion in state.get("plan", [])
    ]


def _reflect_router(state: ResearchState) -> str | list[Send]:
    if not state.get("needs_more_research"):
        return "writer"

    local_model = state.get("local_model")
    sources_per_subquestion = state.get("sources_per_subquestion", 3)
    return [
        Send(
            "researcher",
            {
                "subquestion": gap,
                "local_model": local_model,
                "sources_per_subquestion": sources_per_subquestion,
            },
        )
        for gap in state.get("pending_gaps", [])
    ]


def build_graph():
    graph = StateGraph(ResearchState)

    graph.add_node("planner", planner_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("critic", critic_node)
    graph.add_node("reflector", reflector_node)
    graph.add_node("writer", writer_node)

    graph.add_edge(START, "planner")
    graph.add_conditional_edges("planner", _dispatch_research, ["researcher"])
    graph.add_edge("researcher", "critic")
    graph.add_edge("critic", "reflector")
    graph.add_conditional_edges("reflector", _reflect_router, ["researcher", "writer"])
    graph.add_edge("writer", END)

    return graph.compile()


research_graph = build_graph()


def initial_state(
    query: str,
    depth: str,
    local_model: str,
    reasoning_provider: str = DEFAULT_REASONING_PROVIDER,
    uploaded_pdf_text: str = "",
    previous_context: str = "",
) -> ResearchState:
    """Build a fully-seeded state dict so every reducer channel starts from a known value."""
    return {
        "query": query,
        "depth": depth,
        "local_model": local_model,
        "reasoning_provider": reasoning_provider,
        "uploaded_pdf_text": uploaded_pdf_text,
        "previous_context": previous_context,
        "plan": [],
        "plan_rationale": "",
        "research_results": [],
        "step_count": 0,
        "errors": [],
        "sources": [],
        "critique": {},
        "revision_count": 0,
        "needs_more_research": False,
        "pending_gaps": [],
        "final_report": "",
    }
