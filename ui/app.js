const chatLog = document.getElementById("chat-log");
const input = document.getElementById("input");
const sendBtn = document.getElementById("send");
const statusEl = document.getElementById("status");

async function callAPI(message) {
  // Placeholder: point to FastAPI backend when available
  const resp = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  }).catch(() => null);
  if (!resp || !resp.ok) {
    return { reply: "Backend not connected yet. Please start FastAPI." };
  }
  return resp.json();
}

function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  div.textContent = text;
  chatLog.appendChild(div);
  chatLog.scrollTop = chatLog.scrollHeight;
}

sendBtn.onclick = async () => {
  const text = input.value.trim();
  if (!text) return;
  addMessage("user", text);
  input.value = "";
  const res = await callAPI(text);
  addMessage("bot", res.reply || JSON.stringify(res));
};

// Simple status ping
fetch("/health").then(
  (r) => (statusEl.textContent = r.ok ? "Connected" : "Backend unreachable"),
  () => (statusEl.textContent = "Backend unreachable")
);
