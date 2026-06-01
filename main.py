"""
Main entry point: Intermarket Analysis Agent
Supports both Agent v1 and Agent v2.

Usage:
    python main.py                          # Interactive session with Agent v2
    python main.py --version v1             # Use Agent v1
    python main.py --query "Phân tích thị trường hôm nay"
    python main.py --demo                   # Run pre-defined demo scenarios
"""

import argparse
import json
import sys

from src.core.openai_provider import OpenAIProvider
from src.tools import TOOL_REGISTRY, TOOL_DEFINITIONS
from src.telemetry.logger import logger


DEMO_QUERIES = [
    "Phân tích mối quan hệ hiện tại giữa DXY, Vàng và Dầu hôm nay. Phát hiện bất thường và đề xuất danh mục đầu tư.",
    "Giá Dầu đang ở mức $85. Dự báo tác động lên lạm phát và Vàng trong 3 tháng tới.",
    "Hãy chạy phân tích liên thị trường đầy đủ và tạo báo cáo tổng hợp.",
]


def create_agent(version: str, llm: OpenAIProvider, max_steps: int):
    """Factory: create the requested agent version."""
    if version == "v1":
        from src.agent.agent import ReActAgent
        return ReActAgent(
            llm=llm,
            tools=TOOL_DEFINITIONS,
            tool_registry=TOOL_REGISTRY,
            max_steps=max_steps,
        )
    else:
        from src.agent.agent_v2 import ReActAgentV2
        return ReActAgentV2(
            llm=llm,
            tools=TOOL_DEFINITIONS,
            tool_registry=TOOL_REGISTRY,
            max_steps=max_steps,
        )


def run_query(agent, query: str, show_trace: bool = False) -> str:
    """Run a single query and optionally show the trace."""
    print(f"\n{'='*65}")
    print(f"  [AGENT QUERY]")
    print(f"{'='*65}")
    print(f"  {query}")
    print(f"{'='*65}\n")

    answer = agent.run(query)

    print(f"\n{'='*65}")
    print("  [FINAL ANSWER]")
    print(f"{'='*65}")
    print(answer)
    print(f"{'='*65}\n")

    if show_trace and hasattr(agent, "get_trace"):
        trace = agent.get_trace()
        if trace:
            print(f"\n[TRACE] {len(trace)} steps executed:")
            for step in trace:
                print(f"  Step {step['step']}: called {step['tool_called']}({step['tool_args']})")

    return answer


def run_demo(agent) -> None:
    """Run all pre-defined demo scenarios."""
    print("\n" + "=" * 60)
    print("  INTERMARKET ANALYSIS AGENT --- DEMO MODE")
    print("=" * 60)

    for i, query in enumerate(DEMO_QUERIES, 1):
        print(f"\n\n--- Demo Scenario {i}/{len(DEMO_QUERIES)} ---")
        run_query(agent, query, show_trace=(i == 1))
        if i < len(DEMO_QUERIES):
            input("\n[Press Enter to continue to next scenario...]\n")


def run_interactive(agent) -> None:
    """Interactive REPL session."""
    print("\n" + "="*65)
    print("  [Intermarket Analysis Agent] Interactive Mode")
    print("  Type 'quit' to exit, 'trace' to toggle trace display.")
    print("="*65 + "\n")

    show_trace = False

    while True:
        try:
            query = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[Session ended]")
            break

        if query.lower() in ("quit", "exit", "q"):
            print("[Session ended]")
            break
        if query.lower() == "trace":
            show_trace = not show_trace
            print(f"[Trace display: {'ON' if show_trace else 'OFF'}]")
            continue
        if not query:
            continue

        run_query(agent, query, show_trace=show_trace)


def main():
    parser = argparse.ArgumentParser(
        description="Intermarket Analysis Agent (Gold-Oil-Dollar)"
    )
    parser.add_argument(
        "--version", choices=["v1", "v2"], default="v2",
        help="Agent version: v1 (basic) or v2 (improved). Default: v2",
    )
    parser.add_argument(
        "--query", "-q", type=str, default=None,
        help="Run a single query in non-interactive mode.",
    )
    parser.add_argument(
        "--demo", action="store_true",
        help="Run pre-defined demo scenarios.",
    )
    parser.add_argument(
        "--max-steps", type=int, default=10,
        help="Maximum ReAct loop steps. Default: 10",
    )
    parser.add_argument(
        "--trace", action="store_true",
        help="Print the step trace after each query.",
    )
    args = parser.parse_args()

    # Initialise LLM
    llm = OpenAIProvider()
    print(f"[Agent {args.version.upper()}] Model: {llm.model_name}")

    # Create agent
    agent = create_agent(args.version, llm, args.max_steps)

    # Run mode
    if args.demo:
        run_demo(agent)
    elif args.query:
        run_query(agent, args.query, show_trace=args.trace)
    else:
        run_interactive(agent)


if __name__ == "__main__":
    main()
