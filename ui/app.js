const API_URL = "/api/chat";
const chatLog = document.getElementById("chat-log");
const input = document.getElementById("input");
const sendBtn = document.getElementById("send");
const statusEl = document.getElementById("status");
const statusDot = document.getElementById("status-dot");
const quickUser = document.getElementById("form-user");
const quickMovie = document.getElementById("form-movie");
const btnQuick = document.getElementById("btn-form-send");
const banner = document.getElementById("banner");
const authToken = document.getElementById("auth-token");
const btnStream = document.getElementById("btn-stream");
let activeStream = null;
let activeStreamDiv = null;

function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  // crude detection of "Top features" to render badges
  const shapIdx = text.indexOf("Top features:");
  if (shapIdx >= 0) {
    const main = text.slice(0, shapIdx).trim();
    const shap = text.slice(shapIdx + "Top features:".length).trim();
    const badges = shap.split(";").map((s) => s.trim()).filter(Boolean);
    const badgeHtml = badges.map((b) => `<span class="badge">${b}</span>`).join(" ");
    div.innerHTML = `<div>${main}</div><div id="shap-container"><span class="label">Top features</span>${badgeHtml}</div>`;
  } else {
    div.textContent = text;
  }
  chatLog.appendChild(div);
  chatLog.scrollTop = chatLog.scrollHeight;
}

function setBanner(text, muted = false) {
  if (!banner) return;
  banner.textContent = text;
  banner.className = muted ? "banner muted" : "banner";
}

async function sendMessage() {
  const text = input.value.trim();
  if (!text) return;
  addMessage("user", text);
  input.value = "";
  try {
    const headers = { "Content-Type": "application/json" };
    if (authToken && authToken.value) headers["Authorization"] = `Bearer ${authToken.value}`;
    const resp = await fetch(API_URL, {
      method: "POST",
      headers,
      body: JSON.stringify({ message: text }),
    });
    const data = await resp.json();
    addMessage("bot", data.reply || "[no reply]");
    setBanner("Ready.", true);
  } catch (err) {
    addMessage("bot", "Error: cannot reach backend.");
    setBanner("Error reaching backend", false);
  }
}

sendBtn.onclick = sendMessage;
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// Simple status ping
fetch("/health").then(
  (r) => {
    const ok = r.ok;
    statusEl.textContent = ok ? "Connected" : "Backend unreachable";
    if (statusDot) statusDot.style.background = ok ? "#22c55e" : "#f97316";
  },
  () => {
    statusEl.textContent = "Backend unreachable";
    if (statusDot) statusDot.style.background = "#f97316";
  }
);

// Quick MovieLens form
async function sendQuick() {
  const uid = parseInt(quickUser.value || "0", 10);
  const mid = parseInt(quickMovie.value || "0", 10);
  if (!uid || !mid) {
    addMessage("bot", "Enter user_id and movie_id.");
    return;
  }
  try {
    const headers = { "Content-Type": "application/json" };
    if (authToken && authToken.value) headers["Authorization"] = `Bearer ${authToken.value}`;
    const resp = await fetch("/api/recommend", {
      method: "POST",
      headers,
      body: JSON.stringify({ user_id: uid, movie_id: mid }),
    });
    const data = await resp.json();
    addMessage("user", `recommend ${uid} ${mid}`);
    addMessage("bot", JSON.stringify(data, null, 2));
    setBanner("Ready.", true);
  } catch (err) {
    addMessage("bot", "Error calling recommend endpoint.");
    setBanner("Error on recommend call", false);
  }
}
if (btnQuick) btnQuick.onclick = sendQuick;

// Streaming via SSE
function startStream(text) {
  if (!text) return;
  if (activeStream) activeStream.close();
  addMessage("user", text);
  activeStreamDiv = document.createElement("div");
  activeStreamDiv.className = "msg bot";
  activeStreamDiv.textContent = "";
  chatLog.appendChild(activeStreamDiv);
  chatLog.scrollTop = chatLog.scrollHeight;

  const tokenParam = authToken && authToken.value ? `&token=${encodeURIComponent(authToken.value)}` : "";
  const url = `/api/chat/stream?message=${encodeURIComponent(text)}${tokenParam}`;
  const es = new EventSource(url);
  activeStream = es;
  setBanner("Streaming...", true);

  es.onmessage = (ev) => {
    if (ev.data === "[DONE]") {
      es.close();
      activeStream = null;
      setBanner("Ready.", true);
      return;
    }
    if (activeStreamDiv) {
      activeStreamDiv.textContent += (activeStreamDiv.textContent ? " " : "") + ev.data;
      chatLog.scrollTop = chatLog.scrollHeight;
    }
  };
  es.onerror = () => {
    setBanner("Stream error", false);
    es.close();
    activeStream = null;
  };
}
if (btnStream) btnStream.onclick = () => startStream(input.value.trim());

// Example clicks
document.querySelectorAll(".examples li").forEach((li) => {
  li.addEventListener("click", () => {
    input.value = li.dataset.example || "";
    input.focus();
  });
});
