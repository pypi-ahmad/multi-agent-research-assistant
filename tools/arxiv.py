"""arXiv search tool."""

from __future__ import annotations

import arxiv


def arxiv_search(query: str, max_results: int = 5) -> list[dict]:
    """Return arXiv paper results as plain dicts. Raises on failure."""
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    results = []
    for paper in client.results(search):
        results.append(
            {
                "title": paper.title,
                "url": paper.entry_id,
                "snippet": (paper.summary or "").replace("\n", " ").strip()[:600],
                "source_type": "arxiv",
                "published": paper.published.date().isoformat() if paper.published else None,
            }
        )
    return results
