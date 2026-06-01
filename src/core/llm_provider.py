from __future__ import annotations

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional, Generator

from dotenv import load_dotenv

# Project root = 2 levels up from src/core/
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"


def load_env_config(env_path: Path = DEFAULT_ENV_PATH) -> Dict[str, str]:
    """Load and validate environment configuration."""
    load_dotenv(dotenv_path=env_path, override=False)

    config = {
        "LLM_ENDPOINT": os.getenv("LLM_ENDPOINT", "").strip(),
        "API_KEY": os.getenv("API_KEY", "").strip(),
        "MODEL": os.getenv("MODEL", "").strip(),
    }

    missing = [key for key, value in config.items() if not value]
    if missing:
        raise ValueError(
            f"Missing required env values: {', '.join(missing)}. "
            f"Expected them in {env_path} or exported environment variables."
        )

    return config


class LLMProvider(ABC):
    """
    Abstract Base Class for LLM Providers.
    Supports OpenAI-compatible APIs, Gemini, and Local models.
    """

    def __init__(self, model_name: str, api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Produce a non-streaming completion.
        Returns:
            Dict containing:
            - content: The response text
            - usage: { 'prompt_tokens', 'completion_tokens', 'total_tokens' }
            - latency_ms: Response time in milliseconds
            - provider: Provider name string
        """
        pass

    @abstractmethod
    def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        """Produce a streaming completion, yielding tokens one by one."""
        pass
