"""Environment-driven configuration for the research assistant."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# load_dotenv() never overrides variables already present in the OS
# environment, so a machine that already exports OPENAI_API_KEY /
# OPENAI_BASE_URL keeps using those values untouched.
load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

AGNES_API_KEY = os.environ.get("AGNES_API_KEY", "")
AGNES_BASE_URL = os.environ.get("AGNES_BASE_URL", "https://apihub.agnes-ai.com/v1")
AGNES_MODEL = os.environ.get("AGNES_MODEL", "agnes-2.5-flash")

# Both reasoning backends are OpenAI-compatible; the UI lets the user pick
# which one drives planner/critic/writer.
REASONING_PROVIDERS = ["OpenAI GPT", "Agnes 2.5 Flash"]
DEFAULT_REASONING_PROVIDER = "Agnes 2.5 Flash" if AGNES_API_KEY else "OpenAI GPT"

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
AVAILABLE_LOCAL_MODELS = ["llama3.1:8b", "qwen2.5:7b"]
DEFAULT_LOCAL_MODEL = AVAILABLE_LOCAL_MODELS[0]

# a stuck local model or a hung API call must never freeze the whole run
REASONING_TIMEOUT_SECONDS = 60
OLLAMA_TIMEOUT_SECONDS = 90

# depth -> (# sub-questions, sources fetched per sub-question, max critic
# revision loops, hard ceiling on total researcher rounds)
DEPTH_PRESETS: dict[str, dict[str, int]] = {
    "Quick": {"num_subquestions": 2, "sources_per_subquestion": 2, "max_revisions": 0, "max_steps": 4},
    "Standard": {"num_subquestions": 4, "sources_per_subquestion": 3, "max_revisions": 1, "max_steps": 8},
    "Deep": {"num_subquestions": 6, "sources_per_subquestion": 4, "max_revisions": 2, "max_steps": 14},
}

# sources scoring below this trust score are dropped from the report entirely
MIN_TRUST_SCORE = 3.0

DATA_DIR = Path(__file__).parent / "data"
HISTORY_FILE = DATA_DIR / "history.json"

PROJECT_ROOT = Path(__file__).parent
