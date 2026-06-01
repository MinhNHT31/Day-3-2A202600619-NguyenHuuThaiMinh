/* ================================================================
   Intermarket Analysis Agent — Frontend Logic
   ================================================================ */
(function () {
  "use strict";

  // ---- DOM refs ----
  const $          = (s) => document.querySelector(s);
  const $$         = (s) => document.querySelectorAll(s);

  const chatMessages   = $("#chatMessages");
  const messageInput   = $("#messageInput");
  const sendBtn        = $("#sendBtn");
  const modeBtns       = $$(".mode-btn");
  const modeIndicator  = $("#modeIndicator");
  const currentBadge   = $("#currentModeBadge");
  const charCounter    = $("#charCounter");
  const statusBadge    = $("#statusBadge");
  const metricsPanel   = $("#metricsPanel");
  const metricsBody    = $("#metricsBody");
  const tracePanel     = $("#tracePanel");
  const traceBody      = $("#traceBody");
  const overlay        = $("#overlay");
  const welcomeCard    = $("#welcomeCard");

  // ---- State ----
  let currentMode = "chatbot"; // "chatbot" | "v1" | "v2"
  let isBusy = false;

  // ---- Init ----
  function init() {
    positionIndicator();
    bindEvents();
    
    // Initial bot message asking for info
    addMessage("bot", "👋 Chào bạn! Để tôi có thể tư vấn kế hoạch chi tiêu chính xác nhất, bạn vui lòng cho tôi biết:\n- **Tuổi**\n- **Mức lương hiện tại**\n- **Nơi bạn đang sống / làm việc** nhé!", {mode: currentMode});
    
    messageInput.focus();
  }

  // ---- Mode switcher ----
  function setMode(mode) {
    currentMode = mode;
    modeBtns.forEach((b) => b.classList.toggle("active", b.dataset.mode === mode));
    positionIndicator();

    const labels = { chatbot: "Chatbot", v1: "Agent v1", v2: "Agent v2" };
    const classes = { chatbot: "chatbot", v1: "agent-v1", v2: "agent-v2" };
    currentBadge.textContent = labels[mode];
    currentBadge.className = "mode-badge " + classes[mode];
  }

  function positionIndicator() {
    const active = $(".mode-btn.active");
    if (!active || !modeIndicator) return;
    const parent = active.parentElement;
    const pRect = parent.getBoundingClientRect();
    const aRect = active.getBoundingClientRect();
    modeIndicator.style.left   = (aRect.left - pRect.left) + "px";
    modeIndicator.style.width  = aRect.width + "px";
  }

  // ---- Events ----
  function bindEvents() {
    modeBtns.forEach((btn) => {
      btn.addEventListener("click", () => setMode(btn.dataset.mode));
    });

    messageInput.addEventListener("input", () => {
      autoResize();
      const len = messageInput.value.trim().length;
      sendBtn.disabled = len === 0;
      charCounter.textContent = messageInput.value.length + " / 2000";
    });

    messageInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        if (!sendBtn.disabled && !isBusy) sendMessage();
      }
    });

    sendBtn.addEventListener("click", () => {
      if (!isBusy) sendMessage();
    });

    // Suggestion chips
    $$(".suggestion-chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        messageInput.value = chip.dataset.query;
        messageInput.dispatchEvent(new Event("input"));
        sendMessage();
      });
    });

    // Panels
    $("#metricsBtn").addEventListener("click", openMetrics);
    $("#closeMetrics").addEventListener("click", closePanels);
    $("#closeTrace").addEventListener("click", closePanels);
    overlay.addEventListener("click", closePanels);

    window.addEventListener("resize", positionIndicator);
  }

  function autoResize() {
    messageInput.style.height = "auto";
    messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + "px";
  }

  // ---- Send message ----
  async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text || isBusy) return;

    // Hide welcome
    if (welcomeCard) welcomeCard.style.display = "none";

    // Add user message
    addMessage("user", text);
    messageInput.value = "";
    messageInput.style.height = "auto";
    sendBtn.disabled = true;
    charCounter.textContent = "0 / 2000";

    setStatus("busy", currentMode === "chatbot" ? "Thinking..." : "Running agent...");
    isBusy = true;

    // Show thinking
    const thinkingEl = addThinking();

    const startTime = performance.now();

    try {
      let data;
      if (currentMode === "chatbot") {
        data = await apiChat(text);
      } else {
        data = await apiAgent(text, currentMode);
      }
      const elapsed = Math.round(performance.now() - startTime);

      // Remove thinking
      thinkingEl.remove();

      // Build meta
      const meta = buildMeta(data, elapsed);
      addMessage("bot", data.answer || data.error || "No response", meta, data.trace);

    } catch (err) {
      thinkingEl.remove();
      addMessage("bot", "Error: " + err.message, { error: true });
      setStatus("error", "Error");
    } finally {
      isBusy = false;
      setStatus("ready", "Ready");
    }
  }

  // ---- API calls ----
  async function apiChat(message) {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    if (!res.ok) throw new Error("HTTP " + res.status);
    return res.json();
  }

  async function apiAgent(message, version) {
    const res = await fetch("/api/agent", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, version }),
    });
    if (!res.ok) throw new Error("HTTP " + res.status);
    return res.json();
  }

  // ---- Render messages ----
  function addMessage(role, text, meta, trace) {
    const row = document.createElement("div");
    row.className = "msg-row " + role;

    if (role === "bot") {
      row.innerHTML = `
        <div class="msg-avatar bot">AI</div>
        <div>
          <div class="msg-bubble bot-bubble">${formatText(text)}</div>
          ${meta ? renderMeta(meta, trace) : ""}
        </div>`;
    } else {
      row.innerHTML = `
        <div>
          <div class="msg-bubble user-bubble">${escapeHtml(text)}</div>
        </div>
        <div class="msg-avatar user-av">U</div>`;
    }

    chatMessages.appendChild(row);
    scrollToBottom();
  }

  function addThinking() {
    const row = document.createElement("div");
    row.className = "msg-row thinking-row";
    row.innerHTML = `
      <div class="msg-avatar bot">AI</div>
      <div class="thinking">
        <div class="thinking-dots"><span></span><span></span><span></span></div>
        <span class="thinking-text">${currentMode === "chatbot" ? "Generating response..." : "Running ReAct loop..."}</span>
      </div>`;
    chatMessages.appendChild(row);
    scrollToBottom();
    return row;
  }

  function renderMeta(meta, trace) {
    // Extract unique tools called
    let toolsUsed = [];
    if (trace && trace.length > 0) {
      trace.forEach(step => {
        if (step.tool_called && !toolsUsed.includes(step.tool_called)) {
          toolsUsed.push(step.tool_called);
        }
      });
    }
    
    let html = '<div class="stats-card">';
    
    // Latency
    html += `
      <div class="stat-item">
        <span class="stat-label">Thời gian</span>
        <span class="stat-val" style="color: var(--emerald)">${(meta.latency / 1000).toFixed(1)}s</span>
      </div>`;
      
    // Tokens
    if (meta.tokens) {
      html += `
        <div class="stat-item">
          <span class="stat-label">Tokens</span>
          <span class="stat-val">${meta.tokens}</span>
        </div>`;
    }
    
    // Tools count
    html += `
      <div class="stat-item">
        <span class="stat-label">Số Tools</span>
        <span class="stat-val" style="color: var(--sky)">${toolsUsed.length}</span>
      </div>`;
      
    // View Trace link
    if (trace && trace.length > 0) {
      const traceId = "trace-" + Date.now();
      html += `<span class="trace-link" data-trace-id="${traceId}" onclick="window.__showTrace('${traceId}')">Xem Lịch sử Tư duy &rarr;</span>`;
      window.__traceData = window.__traceData || {};
      window.__traceData[traceId] = trace;
    }
    
    // Tools List (full width)
    if (toolsUsed.length > 0) {
      html += `<div class="tools-list">Gợi ý Tools: [${toolsUsed.join(", ")}]</div>`;
    }
    
    html += "</div>";
    return html;
  }

  function buildMeta(data, elapsed) {
    const m = {};
    const modeLabels = { chatbot: "Chatbot", agent_v1: "Agent v1", agent_v2: "Agent v2" };
    m.mode = modeLabels[data.mode] || data.mode || "";
    m.latency = data.latency_ms || elapsed;
    if (data.tokens) m.tokens = data.tokens.total_tokens || "";
    if (data.steps !== undefined) m.steps = data.steps;
    return m;
  }

  // ---- Trace viewer ----
  window.__showTrace = function (traceId) {
    const trace = (window.__traceData || {})[traceId];
    if (!trace) return;

    traceBody.innerHTML = "";
    trace.forEach((step, i) => {
      const el = document.createElement("div");
      el.className = "trace-step";

      let argsStr = "";
      try { argsStr = JSON.stringify(step.tool_args, null, 2); } catch { argsStr = String(step.tool_args); }

      let obsStr = String(step.observation || "");
      try {
        const parsed = JSON.parse(obsStr);
        obsStr = JSON.stringify(parsed, null, 2);
      } catch {}

      // Truncate long observations
      if (obsStr.length > 800) obsStr = obsStr.substring(0, 800) + "\n... (truncated)";

      el.innerHTML = `
        <div class="trace-step-header">
          <span class="trace-step-num">${step.step}</span>
          <span class="trace-step-tool">${escapeHtml(step.tool_called || "N/A")}</span>
        </div>
        <div class="trace-step-args">Args: ${escapeHtml(argsStr)}</div>
        <div class="trace-step-obs">Obs: ${escapeHtml(obsStr)}</div>`;
      traceBody.appendChild(el);
    });

    tracePanel.classList.add("open");
    overlay.classList.add("show");
  };

  // ---- Metrics panel ----
  async function openMetrics() {
    try {
      const res = await fetch("/api/metrics");
      const data = await res.json();
      metricsBody.innerHTML = renderMetrics(data);
    } catch {
      metricsBody.innerHTML = '<p class="metrics-empty">Failed to load metrics.</p>';
    }
    metricsPanel.classList.add("open");
    overlay.classList.add("show");
  }

  function renderMetrics(d) {
    if (d.message) return `<p class="metrics-empty">${escapeHtml(d.message)}</p>`;

    return `
      <div class="metric-card">
        <div class="mc-label">Total Requests</div>
        <div class="mc-value gold">${d.total_requests || 0}</div>
      </div>
      <div class="metric-card">
        <div class="mc-label">Total Tokens</div>
        <div class="mc-value">${(d.total_tokens || 0).toLocaleString()}</div>
      </div>
      <div class="metric-card">
        <div class="mc-label">Estimated Cost</div>
        <div class="mc-value emerald">$${(d.total_cost_usd || 0).toFixed(4)}</div>
      </div>
      <div class="metric-card">
        <div class="mc-label">Avg Latency</div>
        <div class="mc-value">${(d.avg_latency_ms || 0).toFixed(0)} ms</div>
      </div>
      <div class="metric-card">
        <div class="mc-label">Token Efficiency</div>
        <div class="mc-value">${(d.avg_token_efficiency || 0).toFixed(2)} (prompt/completion ratio)</div>
      </div>
      <div class="metric-card">
        <div class="mc-label">Models Used</div>
        <div class="mc-value" style="font-size:0.9rem">${(d.models_used || []).join(", ") || "N/A"}</div>
      </div>`;
  }

  function closePanels() {
    metricsPanel.classList.remove("open");
    tracePanel.classList.remove("open");
    overlay.classList.remove("show");
  }

  // ---- Status ----
  function setStatus(state, text) {
    statusBadge.className = "status-badge " + (state === "ready" ? "" : state);
    statusBadge.querySelector(".status-text").textContent = text;
  }

  // ---- Helpers ----
  function scrollToBottom() {
    const container = $(".chat-container");
    requestAnimationFrame(() => { container.scrollTop = container.scrollHeight; });
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function formatText(text) {
    // Simple markdown-ish formatting
    let html = escapeHtml(text);
    // Bold
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    // Line breaks -> paragraphs
    html = html.split(/\n\n+/).map(p => `<p>${p.replace(/\n/g, "<br>")}</p>`).join("");
    // Bullet points
    html = html.replace(/^[-*] (.+)/gm, '<span style="display:block;padding-left:14px;position:relative"><span style="position:absolute;left:0;color:var(--gold)">&#x2022;</span>$1</span>');
    return html;
  }

  // ---- Go ----
  init();
})();
