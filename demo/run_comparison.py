"""
Demo: Chatbot vs Agent Comparison
Runs the same question through both Chatbot (baseline) and ReAct Agent (v2)
to demonstrate the difference in reasoning depth and data quality.

Usage:
    python demo/run_comparison.py
"""

import sys
import os
import time
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.openai_provider import OpenAIProvider
from src.tools import TOOL_REGISTRY, TOOL_DEFINITIONS
from src.agent.agent_v2 import ReActAgentV2
from chatbot import run_chatbot_once


TEST_CASES = [
    {
        "id": "TC01",
        "type": "Simple Q&A",
        "question": "Mối quan hệ giữa giá Dầu và lạm phát là gì?",
        "expected_winner": "DRAW",
        "reason": "Conceptual question — chatbot handles well",
    },
    {
        "id": "TC02",
        "type": "Real-time Data",
        "question": "Giá Vàng, Dầu và DXY hiện tại là bao nhiêu?",
        "expected_winner": "AGENT",
        "reason": "Requires real-time data fetching",
    },
    {
        "id": "TC03",
        "type": "Multi-step Analysis",
        "question": "Phân tích tương quan DXY-Vàng-Dầu, phát hiện bất thường và đề xuất danh mục đầu tư.",
        "expected_winner": "AGENT",
        "reason": "Multi-step reasoning + tool calls required",
    },
    {
        "id": "TC04",
        "type": "Risk Scenario",
        "question": "Nếu Dầu duy trì ở $95, tác động lên lạm phát và Vàng ra sao?",
        "expected_winner": "AGENT",
        "reason": "Requires quantitative calculation",
    },
]


def run_comparison():
    print("\n" + "═"*70)
    print("  📊 INTERMARKET ANALYSIS: CHATBOT vs AGENT COMPARISON")
    print("═"*70)

    llm   = OpenAIProvider()
    agent = ReActAgentV2(
        llm=llm,
        tools=TOOL_DEFINITIONS,
        tool_registry=TOOL_REGISTRY,
        max_steps=10,
    )

    results = []

    for tc in TEST_CASES:
        print(f"\n\n{'─'*70}")
        print(f"  Test Case {tc['id']}: {tc['type']}")
        print(f"  Question: {tc['question']}")
        print(f"{'─'*70}")

        # --- Chatbot ---
        print("\n[CHATBOT] Thinking...")
        t0 = time.time()
        chatbot_answer = run_chatbot_once(tc["question"], llm)
        chatbot_time   = round(time.time() - t0, 2)
        print(f"Chatbot ({chatbot_time}s): {chatbot_answer[:300]}...")

        # --- Agent ---
        print(f"\n[AGENT v2] Running ReAct loop...")
        t0 = time.time()
        agent_answer = agent.run(tc["question"])
        agent_time   = round(time.time() - t0, 2)
        agent_steps  = len(agent.get_trace())
        print(f"Agent ({agent_time}s, {agent_steps} steps): {agent_answer[:300]}...")

        result = {
            "test_case":    tc["id"],
            "type":         tc["type"],
            "question":     tc["question"],
            "chatbot": {
                "answer_preview": chatbot_answer[:200],
                "latency_s":      chatbot_time,
                "has_real_data":  False,
            },
            "agent": {
                "answer_preview": agent_answer[:200],
                "latency_s":      agent_time,
                "steps":          agent_steps,
                "has_real_data":  True,
            },
            "expected_winner": tc["expected_winner"],
        }
        results.append(result)

        input("\n[Press Enter to continue...]\n")

    # --- Summary Table ---
    print("\n" + "═"*70)
    print("  📈 COMPARISON SUMMARY")
    print("═"*70)
    print(f"{'Case':<8} {'Type':<20} {'Chatbot (s)':<14} {'Agent (s)':<12} {'Steps':<8} {'Expected'}")
    print("─"*70)
    for r in results:
        print(
            f"{r['test_case']:<8} {r['type']:<20} "
            f"{r['chatbot']['latency_s']:<14} {r['agent']['latency_s']:<12} "
            f"{r['agent']['steps']:<8} {r['expected_winner']}"
        )

    # Save results
    os.makedirs("reports", exist_ok=True)
    out_path = os.path.join("reports", "comparison_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Full results saved to: {out_path}")


if __name__ == "__main__":
    run_comparison()
