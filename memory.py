"""Persistent research history: a JSON file store under ./data.

No database needed for a single-user local app - plain JSON on disk is the
simplest correct thing here.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

import config


def _ensure_store() -> None:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not config.HISTORY_FILE.exists():
        config.HISTORY_FILE.write_text("[]", encoding="utf-8")


def load_all_sessions() -> list[dict]:
    _ensure_store()
    try:
        return json.loads(config.HISTORY_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def get_session(session_id: str) -> dict | None:
    return next((s for s in load_all_sessions() if s["id"] == session_id), None)


def save_session(
    query: str,
    depth: str,
    local_model: str,
    plan: list[str],
    sources: list[dict],
    report: str,
    session_id: str | None = None,
) -> str:
    """Create or replace a session (upsert by id) and return its id.

    Passing an existing session_id drops that entry and re-appends the
    updated version at the end of the list, so continuing a session (a
    follow-up) moves it to most-recent rather than duplicating it.
    """
    _ensure_store()
    sessions = [s for s in load_all_sessions() if s["id"] != session_id]
    sid = session_id or str(uuid.uuid4())
    sessions.append(
        {
            "id": sid,
            "timestamp": datetime.now(UTC).isoformat(),
            "query": query,
            "depth": depth,
            "local_model": local_model,
            "plan": plan,
            "sources": sources,
            "report": report,
        }
    )
    config.HISTORY_FILE.write_text(json.dumps(sessions, indent=2), encoding="utf-8")
    return sid


def delete_session(session_id: str) -> None:
    sessions = [s for s in load_all_sessions() if s["id"] != session_id]
    config.HISTORY_FILE.write_text(json.dumps(sessions, indent=2), encoding="utf-8")


def summarize_for_followup(session: dict, max_chars: int = 2000) -> str:
    """A short text blob planner can use as `previous_context` for a follow-up."""
    report = session.get("report", "")
    return report[:max_chars]
