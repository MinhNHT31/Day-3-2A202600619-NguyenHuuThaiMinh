"""
Web Application: Personal Finance Agent Dashboard
Flask backend with REST API for Chatbot, Agent v1, and Agent v2.

Run:
    python web_app.py
    Then open http://localhost:5000
"""

import json
import sys
import os
import time
import threading
import queue
from datetime import datetime

from flask import Flask, request, jsonify, send_from_directory, Response

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.openai_provider import OpenAIProvider
from src.tools import TOOL_REGISTRY, TOOL_DEFINITIONS
from src.telemetry.metrics import tracker

app = Flask(__name__, static_folder="web", static_url_path="")

# ---------------------------------------------------------------------------
#  LLM + Agents (lazy-initialised on first request)
# ---------------------------------------------------------------------------
_llm = None
_agents = {}

def _get_llm():
    global _llm
    if _llm is None:
        _llm = OpenAIProvider()
    return _llm

def _get_agent(version: str):
    global _agents
    if version not in _agents:
        llm = _get_llm()
        if version == "v1":
            from src.agent.agent import ReActAgent
            _agents["v1"] = ReActAgent(
                llm=llm, tools=TOOL_DEFINITIONS,
                tool_registry=TOOL_REGISTRY, max_steps=10,
            )
        else:
            from src.agent.agent_v2 import ReActAgentV2
            _agents["v2"] = ReActAgentV2(
                llm=llm, tools=TOOL_DEFINITIONS,
                tool_registry=TOOL_REGISTRY, max_steps=10,
            )
    return _agents[version]

# ---------------------------------------------------------------------------
#  Chatbot system prompt
# ---------------------------------------------------------------------------
CHATBOT_SYSTEM_PROMPT = """You are a textbook financial advisor. 
When asked about budgeting or personal finance, you ALWAYS apply standard textbook rules like the 50/30/20 rule, regardless of the user's specific location or circumstances.
You do NOT have access to real-time data, cost of living stats, or tools.
Always structure your responses strictly according to textbook formulas."""

# ---------------------------------------------------------------------------
#  Routes: static frontend
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return send_from_directory("web", "index.html")

# ---------------------------------------------------------------------------
#  API: /api/chat  (Chatbot baseline)
# ---------------------------------------------------------------------------
@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(force=True)
    user_msg = data.get("message", "").strip()
    if not user_msg:
        return jsonify({"error": "Empty message"}), 400

    llm = _get_llm()
    t0 = time.time()
    try:
        result = llm.generate(user_msg, system_prompt=CHATBOT_SYSTEM_PROMPT)
        latency = int((time.time() - t0) * 1000)
        return jsonify({
            "answer":     result["content"],
            "latency_ms": latency,
            "tokens":     result.get("usage", {}),
            "provider":   result.get("provider", "unknown"),
            "model":      llm.model_name,
            "mode":       "chatbot",
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------------------------------------------------------------
#  API: /api/agent  (Agent v1 or v2)
# ---------------------------------------------------------------------------
@app.route("/api/agent", methods=["POST"])
def api_agent():
    data = request.get_json(force=True)
    user_msg = data.get("message", "").strip()
    version  = data.get("version", "v2").strip().lower()
    if not user_msg:
        return jsonify({"error": "Empty message"}), 400
    if version not in ("v1", "v2"):
        return jsonify({"error": "version must be 'v1' or 'v2'"}), 400

    agent = _get_agent(version)
    t0 = time.time()
    try:
        answer  = agent.run(user_msg)
        latency = int((time.time() - t0) * 1000)
        trace   = agent.get_trace() if hasattr(agent, "get_trace") else []
        return jsonify({
            "answer":     answer,
            "latency_ms": latency,
            "steps":      len(trace),
            "trace":      trace,
            "model":      _get_llm().model_name,
            "mode":       f"agent_{version}",
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------------------------------------------------------------
#  API: /api/metrics  (Session telemetry)
# ---------------------------------------------------------------------------
@app.route("/api/metrics", methods=["GET"])
def api_metrics():
    return jsonify(tracker.get_session_summary())

# ---------------------------------------------------------------------------
#  Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("  Personal Finance Agent - Web Dashboard")
    print("  Open http://localhost:5000 in your browser")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=False)
