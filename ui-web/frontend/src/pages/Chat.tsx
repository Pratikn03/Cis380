import { useState, useRef, useEffect } from "react";
import { api } from "../services/api";

interface RecommendationItem {
  title: string;
  reason: string;
}

interface MessageMeta {
  items?: RecommendationItem[];
  [key: string]: unknown;
}

interface Message {
  role: "user" | "assistant";
  content: string;
  meta?: MessageMeta;
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [backendUrl, setBackendUrl] = useState(
    localStorage.getItem("backendUrl") || "http://localhost:8000"
  );
  const [isConnected, setIsConnected] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Test connection on load
    checkConnection();
  }, [backendUrl]);

  const checkConnection = async () => {
    try {
      const response = await fetch(`${backendUrl}/health`, { method: "GET" });
      setIsConnected(response.ok);
    } catch {
      setIsConnected(false);
    }
  };

  const updateBackendUrl = (url: string) => {
    setBackendUrl(url);
    localStorage.setItem("backendUrl", url);
    api.defaults.baseURL = url;
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch(`${backendUrl}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: input, user_id: "web_user" }),
      });

      const data = await response.json();
      const assistantMessage: Message = {
        role: "assistant",
        content: data.answer || data.reply || "No response received",
        meta: data.meta,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        role: "assistant",
        content: `❌ Error: Could not connect to backend at ${backendUrl}. Make sure your server is running.`,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const suggestions = [
    "Recommend a movie",
    "Recommend action movies",
    "What is fraud detection?",
    "Help",
  ];

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-white">AI Chat</h1>
          <p className="text-slate-400 mt-1">Ask questions, get recommendations, analyze data</p>
        </div>

        {/* Backend URL Config */}
        <div className="mb-4 p-4 bg-slate-800/60 rounded-xl border border-slate-700">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <label className="text-sm text-slate-400 block mb-1">Backend URL</label>
              <input
                type="text"
                value={backendUrl}
                onChange={(e) => updateBackendUrl(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm focus:border-emerald-500 focus:outline-none"
                placeholder="http://localhost:8000"
              />
            </div>
            <div className="flex items-center gap-2 pt-5">
              <div
                className={`w-3 h-3 rounded-full ${
                  isConnected ? "bg-emerald-500" : "bg-red-500"
                }`}
              />
              <span className="text-sm text-slate-400">
                {isConnected ? "Connected" : "Disconnected"}
              </span>
              <button
                onClick={checkConnection}
                className="px-3 py-1 text-xs bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg"
              >
                Test
              </button>
            </div>
          </div>
        </div>

        {/* Chat Container */}
        <div className="bg-slate-800/60 rounded-2xl border border-slate-700 overflow-hidden">
          {/* Messages */}
          <div className="h-[500px] overflow-y-auto p-6 space-y-4">
            {messages.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-slate-400 mb-6">Start a conversation! Try one of these:</p>
                <div className="flex flex-wrap justify-center gap-2">
                  {suggestions.map((suggestion) => (
                    <button
                      key={suggestion}
                      onClick={() => setInput(suggestion)}
                      className="px-4 py-2 bg-slate-700 hover:bg-emerald-500/20 text-slate-300 hover:text-emerald-300 rounded-lg text-sm transition-all border border-slate-600 hover:border-emerald-500/50"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                      msg.role === "user"
                        ? "bg-emerald-500 text-slate-900"
                        : "bg-slate-700 text-slate-200"
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                    {msg.meta?.items && msg.meta.items.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-slate-600/50">
                        <p className="text-xs opacity-70 mb-2">Recommendations:</p>
                        {msg.meta.items.slice(0, 5).map((item, j) => (
                          <div key={j} className="text-sm py-1">
                            <span className="font-medium">{j + 1}. {item.title}</span>
                            {item.reason && (
                              <span className="opacity-70 text-xs block">{item.reason}</span>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-slate-700 text-slate-200 rounded-2xl px-4 py-3">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" />
                    <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce delay-100" />
                    <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce delay-200" />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t border-slate-700 p-4">
            <div className="flex gap-3">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message..."
                className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-slate-200 placeholder-slate-500 focus:border-emerald-500 focus:outline-none"
                disabled={isLoading}
              />
              <button
                onClick={sendMessage}
                disabled={isLoading || !input.trim()}
                className="px-6 py-3 bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-700 disabled:text-slate-500 text-slate-900 font-semibold rounded-xl transition-all"
              >
                Send
              </button>
            </div>
          </div>
        </div>

        {/* Help */}
        <div className="mt-4 text-center text-sm text-slate-500">
          <p>
            💡 To connect from GitHub Pages, run your backend with ngrok:{" "}
            <code className="bg-slate-800 px-2 py-1 rounded">ngrok http 8000</code>
          </p>
        </div>
      </div>
    </main>
  );
}
