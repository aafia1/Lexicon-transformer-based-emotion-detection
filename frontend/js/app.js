(() => {
  "use strict";

  const API_BASE = ""; // same-origin (Flask serves frontend + API)
  const HISTORY_KEY = "lexicon_history_v1";
  const THEME_KEY = "lexicon_theme_v1";
  const MAX_HISTORY = 12;

  // ---- Elements ----
  const els = {
    textInput: document.getElementById("textInput"),
    charCount: document.getElementById("charCount"),
    analyzeBtn: document.getElementById("analyzeBtn"),
    analyzeLabel: document.getElementById("analyzeLabel"),
    spinner: document.getElementById("spinner"),
    clearBtn: document.getElementById("clearBtn"),
    errorMsg: document.getElementById("errorMsg"),
    resultPanel: document.getElementById("resultPanel"),
    resultCard: document.getElementById("resultCard"),
    resultEmoji: document.getElementById("resultEmoji"),
    resultLabel: document.getElementById("resultLabel"),
    resultMessage: document.getElementById("resultMessage"),
    gaugeFill: document.getElementById("gaugeFill"),
    confidenceValue: document.getElementById("confidenceValue"),
    bars: document.getElementById("bars"),
    metaWords: document.getElementById("metaWords"),
    metaLatency: document.getElementById("metaLatency"),
    statusChip: document.getElementById("statusChip"),
    themeToggle: document.getElementById("themeToggle"),
    spectrometer: document.getElementById("spectrometer"),
    sampleChips: document.getElementById("sampleChips"),
    historyList: document.getElementById("historyList"),
    clearHistoryBtn: document.getElementById("clearHistoryBtn"),
    bgWash: document.getElementById("bgWash"),
  };

  // ---- Theme ----
  function initTheme() {
    const saved = localStorage.getItem(THEME_KEY) ||
      (window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
    document.documentElement.setAttribute("data-theme", saved);
  }
  els.themeToggle.addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme");
    const next = current === "light" ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem(THEME_KEY, next);
  });
  initTheme();

  // ---- Character counter ----
  els.textInput.addEventListener("input", () => {
    els.charCount.textContent = `${els.textInput.value.length} / 2000`;
  });

  // ---- Sample chips ----
  els.sampleChips.addEventListener("click", (e) => {
    const chip = e.target.closest(".chip");
    if (!chip) return;
    els.textInput.value = chip.dataset.text;
    els.charCount.textContent = `${els.textInput.value.length} / 2000`;
    els.textInput.focus();
  });

  // ---- Clear ----
  els.clearBtn.addEventListener("click", () => {
    els.textInput.value = "";
    els.charCount.textContent = "0 / 2000";
    els.resultPanel.hidden = true;
    els.errorMsg.hidden = true;
    resetSpectrometer();
  });

  // ---- Health check ----
  async function checkHealth() {
    try {
      const res = await fetch(`${API_BASE}/api/health`);
      const data = await res.json();
      if (data.model_loaded) {
        setStatus(true, "API online");
      } else {
        setStatus(false, "Model not trained yet");
      }
    } catch {
      setStatus(false, "API offline");
    }
  }
  function setStatus(online, label) {
    els.statusChip.classList.toggle("online", online);
    els.statusChip.classList.toggle("offline", !online);
    els.statusChip.innerHTML = `<span class="dot"></span> ${label}`;
  }
  checkHealth();

  // ---- Spectrometer ----
  function resetSpectrometer() {
    els.spectrometer.querySelectorAll(".spectrometer-segment").forEach((seg) => {
      seg.classList.remove("active");
      seg.style.background = "";
    });
  }
  function lightSpectrometer(emotion, colors) {
    resetSpectrometer();
    const seg = els.spectrometer.querySelector(`[data-emotion="${emotion}"]`);
    if (seg) {
      seg.classList.add("active");
      seg.style.background = `linear-gradient(135deg, ${colors[0]}, ${colors[1]})`;
    }
  }

  // ---- Analyze ----
  els.analyzeBtn.addEventListener("click", analyze);
  els.textInput.addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") analyze();
  });

  async function analyze() {
    const text = els.textInput.value.trim();
    els.errorMsg.hidden = true;

    if (!text) {
      showError("Please enter some text to analyze.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      const data = await res.json();
      if (!res.ok) {
        showError(data.error || "Something went wrong.");
        return;
      }
      renderResult(text, data);
      saveHistory(text, data);
    } catch (err) {
      showError("Could not reach the API. Is the Flask server running?");
    } finally {
      setLoading(false);
    }
  }

  function setLoading(isLoading) {
    els.analyzeBtn.disabled = isLoading;
    els.spinner.hidden = !isLoading;
    els.analyzeLabel.textContent = isLoading ? "Analyzing…" : "Analyze emotion";
  }

  function showError(msg) {
    els.errorMsg.textContent = msg;
    els.errorMsg.hidden = false;
  }

  function renderResult(text, data) {
    const { emotion, confidence, distribution, meta, word_count, latency_ms } = data;
    const gradient = meta.gradient || ["#8B7CF6", "#5B4FE0"];

    document.documentElement.style.setProperty("--emotion-color", gradient[0]);
    els.resultCard.style.setProperty("--emotion-color-1", gradient[0]);
    els.resultCard.style.setProperty("--emotion-color-2", gradient[1]);
    els.gaugeFill.style.setProperty("--emotion-color-1", gradient[0]);

    els.resultEmoji.textContent = meta.emoji || "🙂";
    els.resultLabel.textContent = meta.label || emotion;
    els.resultMessage.textContent = meta.message || "";

    const circumference = 157; // matches path length approximation
    const offset = circumference - (confidence / 100) * circumference;
    requestAnimationFrame(() => {
      els.gaugeFill.style.strokeDashoffset = offset;
    });
    animateNumber(els.confidenceValue, confidence);

    // Distribution bars, sorted descending
    const sorted = Object.entries(distribution).sort((a, b) => b[1] - a[1]);
    els.bars.innerHTML = sorted.map(([emo, pct]) => {
      const emoMeta = EMOTION_COLORS[emo] || gradient;
      return `
        <div class="bar-row">
          <span class="bar-name">${emo}</span>
          <div class="bar-track"><div class="bar-fill" style="width:0%;background:linear-gradient(90deg, ${emoMeta[0]}, ${emoMeta[1]})" data-pct="${pct}"></div></div>
          <span class="bar-pct">${pct}%</span>
        </div>`;
    }).join("");
    requestAnimationFrame(() => {
      els.bars.querySelectorAll(".bar-fill").forEach((el) => {
        el.style.width = `${el.dataset.pct}%`;
      });
    });

    els.metaWords.textContent = word_count;
    els.metaLatency.textContent = `${Math.round(latency_ms)}ms`;

    lightSpectrometer(emotion, gradient);
    els.resultPanel.hidden = false;
    els.resultPanel.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  function animateNumber(el, target) {
    const start = 0;
    const duration = 700;
    const startTime = performance.now();
    function tick(now) {
      const progress = Math.min((now - startTime) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.round(start + (target - start) * eased);
      if (progress < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }

  // Fallback local color map (also used for bars, mirrors backend EMOTION_META)
  const EMOTION_COLORS = {
    happiness: ["#F5A524", "#FFD166"],
    sadness: ["#3B82F6", "#60A5FA"],
    anger: ["#EF4444", "#F97316"],
    love: ["#EC4899", "#F472B6"],
    hate: ["#78716C", "#A8A29E"],
    surprise: ["#8B5CF6", "#C084FC"],
  };

  // ---- History (persisted in localStorage) ----
  function loadHistory() {
    try {
      return JSON.parse(localStorage.getItem(HISTORY_KEY)) || [];
    } catch {
      return [];
    }
  }
  function saveHistory(text, data) {
    const history = loadHistory();
    history.unshift({
      text,
      emotion: data.emotion,
      emoji: data.meta.emoji,
      color: (data.meta.gradient || EMOTION_COLORS[data.emotion])[0],
      confidence: data.confidence,
      time: Date.now(),
    });
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(0, MAX_HISTORY)));
    renderHistory();
  }
  function renderHistory() {
    const history = loadHistory();
    if (!history.length) {
      els.historyList.innerHTML = `<p class="empty-state">Your analyzed lines will appear here.</p>`;
      return;
    }
    els.historyList.innerHTML = history.map((h) => `
      <div class="history-item">
        <span class="history-emoji">${h.emoji}</span>
        <span class="history-text">${escapeHtml(h.text)}</span>
        <span class="history-tag" style="background:${h.color}">${h.emotion}</span>
        <span class="history-time">${timeAgo(h.time)}</span>
      </div>
    `).join("");
  }
  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }
  function timeAgo(ts) {
    const s = Math.floor((Date.now() - ts) / 1000);
    if (s < 60) return "just now";
    if (s < 3600) return `${Math.floor(s / 60)}m ago`;
    return `${Math.floor(s / 3600)}h ago`;
  }
  els.clearHistoryBtn.addEventListener("click", () => {
    localStorage.removeItem(HISTORY_KEY);
    renderHistory();
  });

  renderHistory();
})();
