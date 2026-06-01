"""
Agent v2: Real-time Hyper-Personalized Budget Advisor
Uses a chain of tools: gross-to-net, rent scraper, and commute calculator.
"""

import json
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker

class ReActAgentV2:
    MAX_RETRY = 2

    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], tool_registry: Dict, max_steps: int = 10):
        self.llm = llm
        self.tools = tools
        self.tool_registry = tool_registry
        self.max_steps = max_steps
        self.history = []

    def get_system_prompt(self) -> str:
        tool_block = "\n".join(f"  - {t['name']}: {t['description']}" for t in self.tools)
        return f"""You are an advanced Personal Finance Agent (V2).
Your task is to provide highly personalized budgeting advice by chaining real-time tools.

AVAILABLE TOOLS:
{tool_block}

FORMAT:
Thought: <reasoning>
Action: {{"tool": "<name>", "args": {{...}}}}

When ready:
Final Answer: <your advice>

MANDATORY WORKFLOW:
1. If the user provides a Gross salary, call `calculate_net_salary` first.
2. If the user mentions a living district, call `get_rent_prices`.
3. If the user mentions a commute (from -> to), call `calculate_commute_cost`.
4. Synthesize all observations into a detailed budget plan (Final Answer). Include specific amounts and warnings about high fixed costs.

RULES:
- Always use double quotes for JSON in Action.
- Do not make up numbers; use the exact numbers returned by the tools.
- ALWAYS RESPOND IN VIETNAMESE.
"""

    def run(self, user_input: str) -> str:
        system_prompt = self.get_system_prompt()
        prompt_history = [f"User Query: {user_input}"]
        steps = 0
        self.history = []
        errors = 0

        while steps < self.max_steps:
            current_prompt = "\n".join(prompt_history)
            try:
                result = self.llm.generate(current_prompt, system_prompt=system_prompt)
                response = result["content"]
            except Exception as exc:
                break

            if "Final Answer:" in response:
                return response.split("Final Answer:")[-1].strip()

            action, err = self._parse_action_v2(response)
            if action is None:
                errors += 1
                if errors >= self.MAX_RETRY:
                    prompt_history.append(response)
                    prompt_history.append("Observation: [SYSTEM] Please provide Final Answer now.")
                    errors = 0
                else:
                    prompt_history.append(response)
                    prompt_history.append(f"Observation: [PARSE ERROR] {err}")
                steps += 1
                continue

            errors = 0
            tool_name = action.get("tool", "")
            tool_args = action.get("args", {})
            observation = self._execute_tool(tool_name, tool_args)

            self.history.append({"step": steps, "tool_called": tool_name, "tool_args": tool_args, "observation": observation})
            prompt_history.append(response)
            prompt_history.append(f"Observation: {observation}")
            steps += 1

        return "Agent V2 reached max steps."

    def _parse_action_v2(self, response: str) -> Tuple[Optional[Dict], str]:
        match = re.search(r"Action:\s*(\{.*?\})\s*(?:\n|$)", response, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(1))
                return parsed, ""
            except Exception as e:
                return None, str(e)
        return None, "No Action JSON found"

    def _execute_tool(self, tool_name: str, args: Dict) -> str:
        if tool_name not in self.tool_registry: return "Tool not found"
        try: return str(self.tool_registry[tool_name](**args))
        except Exception as e: return str(e)

    def get_trace(self) -> List[Dict]:
        return self.history
