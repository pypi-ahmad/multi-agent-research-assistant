"""Web search tool backed by DuckDuckGo (no API key required)."""

from __future__ import annotations

from ddgs import DDGS


def web_search(query: str, max_results: int = 5) -> list[dict]:
    """Return web search results as plain dicts. Raises on failure."""
    with DDGS() as ddgs:
        raw = list(ddgs.text(query, max_results=max_results))

    results = []
    for item in raw:
        url = item.get("href") or item.get("url") or ""
        if not url:
            continue
        results.append(
            {
                "title": item.get("title", "Untitled"),
                "url": url,
                "snippet": item.get("body", ""),
                "source_type": "web",
                "published": None,
            }
        )
    return results
