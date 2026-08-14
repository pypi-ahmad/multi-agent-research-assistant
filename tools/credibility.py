"""Deterministic source credibility scoring.

Scores are computed heuristically (domain reputation, recency, lexical
overlap) rather than asked of an LLM, so a score can never be hallucinated
and stays stable across reruns.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from urllib.parse import urlparse

HIGH_AUTHORITY_DOMAINS = {
    "nature.com": 9.5,
    "science.org": 9.5,
    "arxiv.org": 8.5,
    "ieee.org": 9.0,
    "acm.org": 9.0,
    "nih.gov": 9.5,
    "who.int": 9.0,
    "reuters.com": 8.5,
    "apnews.com": 8.5,
    "bbc.com": 8.0,
    "nytimes.com": 7.5,
    "wikipedia.org": 6.0,
}
TLD_SCORES = {".gov": 9.0, ".edu": 8.5, ".org": 6.5}
DEFAULT_AUTHORITY = 5.0

_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> set[str]:
    return set(_WORD_RE.findall(text.lower()))


def score_authority(url: str, source_type: str) -> float:
    if source_type == "arxiv":
        return HIGH_AUTHORITY_DOMAINS["arxiv.org"]
    domain = urlparse(url).netloc.lower().removeprefix("www.")
    for known_domain, score in HIGH_AUTHORITY_DOMAINS.items():
        if domain == known_domain or domain.endswith("." + known_domain):
            return score
    for tld, score in TLD_SCORES.items():
        if domain.endswith(tld):
            return score
    return DEFAULT_AUTHORITY


def score_recency(published: str | None) -> float:
    if not published:
        return 5.0
    try:
        published_date = datetime.fromisoformat(published).date()
    except ValueError:
        return 5.0
    age_years = (datetime.now(UTC).date() - published_date).days / 365.25
    if age_years <= 1:
        return 9.0
    if age_years <= 3:
        return 7.0
    if age_years <= 7:
        return 5.0
    return 3.0


def score_relevance(query: str, text: str) -> float:
    query_tokens = _tokenize(query)
    text_tokens = _tokenize(text)
    if not query_tokens or not text_tokens:
        return 5.0
    overlap = len(query_tokens & text_tokens) / len(query_tokens)
    return round(min(overlap, 1.0) * 10, 1)


def score_source(subquestion: str, source: dict) -> dict:
    """Return a copy of source with authority/relevance/recency/trust_score filled in."""
    authority = score_authority(source.get("url", ""), source.get("source_type", "web"))
    relevance = score_relevance(subquestion, source.get("snippet", "") + " " + source.get("title", ""))
    recency = score_recency(source.get("published"))
    trust = round(authority * 0.4 + relevance * 0.35 + recency * 0.25, 1)

    scored = dict(source)
    scored.update(authority=authority, relevance=relevance, recency=recency, trust_score=trust)
    return scored
