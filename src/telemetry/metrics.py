import time
from typing import Dict, Any, List
from src.telemetry.logger import logger


# Real pricing per 1K tokens (approximate, June 2025)
MODEL_PRICING = {
    # OpenAI
    "gpt-4o":                {"input": 0.005,  "output": 0.015},
    "gpt-4o-mini":           {"input": 0.00015, "output": 0.0006},
    "gpt-4-turbo":           {"input": 0.01,   "output": 0.03},
    "gpt-3.5-turbo":         {"input": 0.0005,  "output": 0.0015},
    # DeepSeek (opencode.ai compatible)
    "deepseek-v4-flash":     {"input": 0.001,  "output": 0.002},
    "deepseek-chat":         {"input": 0.0014,  "output": 0.0028},
    # Gemini
    "gemini-1.5-flash":      {"input": 0.00035, "output": 0.00105},
    "gemini-1.5-pro":        {"input": 0.0035,  "output": 0.0105},
    # Default fallback
    "_default":              {"input": 0.002,  "output": 0.004},
}


class PerformanceTracker:
    """
    Industry-standard LLM performance & cost tracker.
    Logs all requests to telemetry and accumulates session-level stats.
    """

    def __init__(self):
        self.session_metrics: List[Dict[str, Any]] = []

    def track_request(
        self,
        provider: str,
        model: str,
        usage: Dict[str, int],
        latency_ms: int,
    ) -> Dict[str, Any]:
        """
        Log a single LLM request with real cost estimation.

        Args:
            provider:   Provider name (e.g., "openai_compatible", "google")
            model:      Model identifier string
            usage:      Dict with prompt_tokens, completion_tokens, total_tokens
            latency_ms: End-to-end latency in milliseconds

        Returns:
            The metric dict that was logged.
        """
        cost = self._calculate_cost(model, usage)

        metric = {
            "provider":          provider,
            "model":             model,
            "prompt_tokens":     usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens":      usage.get("total_tokens", 0),
            "latency_ms":        latency_ms,
            "cost_usd":          round(cost, 6),
            "token_efficiency":  self._token_efficiency(usage),
        }

        self.session_metrics.append(metric)
        logger.log_event("LLM_METRIC", metric)
        return metric

    def _calculate_cost(self, model: str, usage: Dict[str, int]) -> float:
        """Calculate request cost using real pricing per 1K tokens."""
        pricing = MODEL_PRICING.get(model, MODEL_PRICING["_default"])
        prompt_cost  = (usage.get("prompt_tokens", 0)     / 1000) * pricing["input"]
        output_cost  = (usage.get("completion_tokens", 0) / 1000) * pricing["output"]
        return prompt_cost + output_cost

    def _token_efficiency(self, usage: Dict[str, int]) -> float:
        """
        Compute prompt-to-completion ratio.
        A ratio > 10 indicates verbose prompts with short completions (inefficient).
        """
        prompt     = usage.get("prompt_tokens", 1)
        completion = usage.get("completion_tokens", 1)
        return round(prompt / max(completion, 1), 2)

    def get_session_summary(self) -> Dict[str, Any]:
        """Return aggregate statistics for the current session."""
        if not self.session_metrics:
            return {"message": "No requests tracked yet."}

        total_cost     = sum(m["cost_usd"] for m in self.session_metrics)
        total_tokens   = sum(m["total_tokens"] for m in self.session_metrics)
        avg_latency    = sum(m["latency_ms"] for m in self.session_metrics) / len(self.session_metrics)
        avg_efficiency = sum(m["token_efficiency"] for m in self.session_metrics) / len(self.session_metrics)

        return {
            "total_requests":     len(self.session_metrics),
            "total_tokens":       total_tokens,
            "total_cost_usd":     round(total_cost, 6),
            "avg_latency_ms":     round(avg_latency, 1),
            "avg_token_efficiency": round(avg_efficiency, 2),
            "models_used":        list({m["model"] for m in self.session_metrics}),
        }

    def print_summary(self) -> None:
        """Print a formatted session summary to stdout."""
        s = self.get_session_summary()
        print("\n--- Session Telemetry Summary ---")
        for k, v in s.items():
            print(f"  {k}: {v}")
        print("-" * 35)


# Global tracker instance
tracker = PerformanceTracker()
