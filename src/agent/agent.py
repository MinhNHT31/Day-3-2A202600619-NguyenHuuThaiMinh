"""
Agent v1: Static Database Budget Advisor
Uses only the 'get_local_living_costs' tool to adjust advice based on city stats.
"""

import json
import re
import time
from typing import Any, Dict, List, Optional

from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker

class ReActAgent:
    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], tool_registry: Dict, max_steps: int = 8):
        self.llm = llm
        self.tools = tools
        self.tool_registry = tool_registry
        self.max_steps = max_steps
        self.history = []

    def get_system_prompt(self) -> str:
        return """You are a Personal Finance Agent V1.
Your task is to advise users on budgeting based on their location.

Available Tools:
- get_local_living_costs: Get average living costs for a specific city. Args: {"city": "Hà Nội"}

STRICT OUTPUT FORMAT:
Thought: <reasoning>
Action: {"tool": "<tool_name>", "args": {<arguments as JSON>}}

When you have enough info, output:
Final Answer: <your advice>

RULES:
1. ALWAYS call get_local_living_costs if the user provides a city.
2. Adjust your budget advice based on the living costs data returned by the tool rather than using rigid textbook formulas.
3. ALWAYS RESPOND IN VIETNAMESE.
"""

    def run(self, user_input: str) -> str:
        system_prompt = self.get_system_prompt()
        prompt_history = [f"User Query: {user_input}"]
        steps = 0
        self.history = []

        while steps < self.max_steps:
            current_prompt = "\n".join(prompt_history)
            t0 = time.time()
            try:
                result = self.llm.generate(current_prompt, system_prompt=system_prompt)
                response = result["content"]
            except Exception as exc:
                break

            if "Final Answer:" in response:
                return response.split("Final Answer:")[-1].strip()

            action = self._parse_action(response)
            if action is None:
                prompt_history.append(response)
                prompt_history.append('Observation: [PARSE ERROR] Use format Action: {"tool": "name", "args": {}}')
                steps += 1
                continue

            tool_name = action.get("tool", "")
            tool_args = action.get("args", {})
            observation = self._execute_tool(tool_name, tool_args)

            self.history.append({"step": steps, "tool_called": tool_name, "tool_args": tool_args, "observation": observation})
            prompt_history.append(response)
            prompt_history.append(f"Observation: {observation}")
            steps += 1

        return "Agent reached max steps."

    def _parse_action(self, response: str) -> Optional[Dict]:
        match = re.search(r"Action:\s*(\{.*?\})\s*(?:\n|$)", response, re.DOTALL)
        if match:
            try: return json.loads(match.group(1))
            except: pass
        return None

    def _execute_tool(self, tool_name: str, args: Dict) -> str:
        if tool_name not in self.tool_registry: return "Tool not found"
        try: return str(self.tool_registry[tool_name](**args))
        except Exception as e: return str(e)

    def get_trace(self) -> List[Dict]:
        return self.history
