"""Shared LangGraph state definitions."""

from __future__ import annotations

import operator
from typing import Annotated, Literal, TypedDict

Depth = Literal["Quick", "Standard", "Deep"]


class Source(TypedDict, total=False):
    """A single piece of evidence gathered by the researcher."""

    subquestion: str
    title: str
    url: str
    snippet: str
    summary: str
    source_type: str  # "web" | "arxiv" | "pdf"
    published: str | None
    authority: float
    relevance: float
    recency: float
    trust_score: float


class Critique(TypedDict, total=False):
    sufficient: bool
    gaps: list[str]
    notes: str
    conflicting_info: list[str]


class ResearchState(TypedDict, total=False):
    # --- inputs ---
    query: str
    depth: Depth
    local_model: str
    reasoning_provider: str  # "OpenAI GPT" | "Agnes 2.5 Flash"
    uploaded_pdf_text: str
    previous_context: str  # summary of a prior session, for follow-ups

    # --- depth-derived config ---
    num_subquestions: int
    sources_per_subquestion: int
    max_revisions: int
    max_steps: int

    # --- planner output ---
    plan: list[str]
    plan_rationale: str

    # --- researcher output (parallel writers -> must accumulate) ---
    research_results: Annotated[list[Source], operator.add]
    step_count: Annotated[int, operator.add]
    errors: Annotated[list[str], operator.add]

    # --- critic output (single writer -> plain overwrite) ---
    sources: list[Source]
    critique: Critique

    # --- reflector output ---
    revision_count: int
    needs_more_research: bool
    pending_gaps: list[str]

    # --- writer output ---
    final_report: str
