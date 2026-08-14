"""Shared model constructors: GPT for reasoning, local Ollama for bulk drafting."""

from __future__ import annotations

from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

import config


def get_reasoning_llm(provider: str = "OpenAI GPT", temperature: float = 0.2) -> ChatOpenAI:
    """Planner / critic / writer model. Both backends are OpenAI-compatible APIs."""
    if provider == "Agnes 2.5 Flash":
        if not config.AGNES_API_KEY:
            raise RuntimeError(
                "AGNES_API_KEY is not set. Export it or add it to a .env file (see .env.example)."
            )
        return ChatOpenAI(
            model=config.AGNES_MODEL,
            base_url=config.AGNES_BASE_URL,
            api_key=config.AGNES_API_KEY,
            temperature=temperature,
            timeout=config.REASONING_TIMEOUT_SECONDS,
        )

    if not config.OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Export it or add it to a .env file (see .env.example)."
        )
    return ChatOpenAI(
        model=config.OPENAI_MODEL,
        base_url=config.OPENAI_BASE_URL,
        api_key=config.OPENAI_API_KEY,
        temperature=temperature,
        timeout=config.REASONING_TIMEOUT_SECONDS,
    )


def get_local(model_name: str, temperature: float = 0.3) -> ChatOllama:
    """Researcher model: cheap local summarization/drafting via Ollama.

    A stuck or overloaded local model must not hang the whole research run,
    so requests are bounded and the caller (researcher_node) falls back to
    the raw snippet on any failure, including a timeout.
    """
    return ChatOllama(
        model=model_name,
        base_url=config.OLLAMA_BASE_URL,
        temperature=temperature,
        client_kwargs={"timeout": config.OLLAMA_TIMEOUT_SECONDS},
    )
