"""Reflector: deterministic loop/stop decision.

Deliberately not an LLM call: whether to keep researching must never depend
on a model choosing to obey a step limit. The critic's structured judgement
plus hard counters are enough, and staying rule-based guarantees the loop
always terminates.
"""

from __future__ import annotations

from state import ResearchState


def reflector_node(state: ResearchState) -> dict:
    critique = state.get("critique", {})
    revision_count = state.get("revision_count", 0)
    max_revisions = state.get("max_revisions", 0)
    step_count = state.get("step_count", 0)
    max_steps = state.get("max_steps", 8)

    gaps = critique.get("gaps", [])
    hit_safety_limit = revision_count >= max_revisions or step_count >= max_steps
    sufficient = critique.get("sufficient", True)

    if sufficient or hit_safety_limit or not gaps:
        return {"needs_more_research": False, "pending_gaps": []}

    return {
        "needs_more_research": True,
        "pending_gaps": gaps,
        "revision_count": revision_count + 1,
    }
