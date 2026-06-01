"""
Chatbot Baseline: Simple LLM Chatbot (no tools, no ReAct loop).
Used to demonstrate textbook advice without context.
"""

import argparse
import time
from src.core.openai_provider import OpenAIProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker

CHATBOT_SYSTEM_PROMPT = """You are a basic financial advisor. 
When asked about budgeting or personal finance, you give general, safe advice based on common sense. Do NOT use rigid formulas like the 50/30/20 rule, as they are often unrealistic.
You do NOT have access to real-time data, cost of living stats, or tools.
Always structure your responses clearly.
ALWAYS RESPOND IN VIETNAMESE."""

def run_chatbot_once(question: str, llm: OpenAIProvider) -> str:
    logger.log_event("CHATBOT_QUERY", {"question": question})

    t0     = time.time()
    result = llm.generate(question, system_prompt=CHATBOT_SYSTEM_PROMPT)
    answer = result["content"]
    usage  = result.get("usage", {})
    latency = result.get("latency_ms", int((time.time() - t0) * 1000))

    tracker.track_request(
        provider   = result.get("provider", "chatbot"),
        model      = llm.model_name,
        usage      = usage,
        latency_ms = latency,
    )

    return answer

if __name__ == "__main__":
    llm = OpenAIProvider()
    print(run_chatbot_once("Tôi có thu nhập 10 triệu/tháng, hãy gợi ý cách chi tiêu.", llm))
