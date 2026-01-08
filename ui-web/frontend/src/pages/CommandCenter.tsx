import { useState } from "react";

export default function CommandCenter() {
  const [activeEngine, setActiveEngine] = useState("fraud");
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const engines = [
    { id: "fraud", name: "Fraud Detection", icon: "🛡️" },
    { id: "vision", name: "Vision Analysis", icon: "👁️" },
    { id: "cyber", name: "Cyber Security", icon: "🔐" },
    { id: "nlp", name: "NLP Processing", icon: "📝" },
    { id: "behavior", name: "Behavior Analytics", icon: "📊" },
  ];

  const results = [
    { type: "Transaction Pattern", confidence: 94, status: "normal", details: "Standard purchasing behavior detected" },
    { type: "Location Anomaly", confidence: 67, status: "warning", details: "Unusual geographic access pattern" },
    { type: "Velocity Check", confidence: 99, status: "normal", details: "Transaction frequency within normal range" },
  ];

  const stats = [
    { label: "System Status", value: "Online", color: "emerald" },
    { label: "Active Engines", value: "5/5", color: "emerald" },
    { label: "Avg Response", value: "45ms", color: "slate" },
    { label: "Alerts Today", value: "3", color: "amber" },
  ];

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">Command Center</h1>
          <p className="text-slate-400 mt-2">Real-time anomaly detection and monitoring</p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
          {engines.map((engine) => (
            <button
              key={engine.id}
              onClick={() => setActiveEngine(engine.id)}
              className={activeEngine === engine.id 
                ? "p-4 rounded-xl border bg-emerald-500/20 border-emerald-500 text-emerald-300 transition-all"
                : "p-4 rounded-xl border bg-slate-800/50 border-slate-700 text-slate-400 hover:border-slate-600 transition-all"
              }
            >
              <span className="text-2xl">{engine.icon}</span>
              <p className="mt-2 text-sm font-medium">{engine.name}</p>
            </button>
          ))}
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-slate-800/60 rounded-2xl border border-slate-700 p-6">
            <h2 className="text-xl font-semibold text-white mb-4">Analysis Input</h2>
            <div className="space-y-4">
              <textarea
                className="w-full h-40 bg-slate-900 border border-slate-700 rounded-xl p-4 text-slate-200 placeholder-slate-500 focus:border-emerald-500 focus:outline-none resize-none"
                placeholder="Enter data for analysis..."
              />
              <div className="flex gap-4">
                <button
                  onClick={() => setIsAnalyzing(!isAnalyzing)}
                  className="flex-1 py-3 bg-emerald-500 hover:bg-emerald-400 text-slate-900 font-semibold rounded-xl transition-all"
                >
                  {isAnalyzing ? "Analyzing..." : "Run Analysis"}
                </button>
                <button className="px-6 py-3 border border-slate-600 text-slate-300 rounded-xl hover:border-emerald-400 transition-all">
                  Upload
                </button>
              </div>
            </div>
          </div>

          <div className="bg-slate-800/60 rounded-2xl border border-slate-700 p-6">
            <h2 className="text-xl font-semibold text-white mb-4">Detection Results</h2>
            <div className="space-y-4">
              {results.map((result, i) => (
                <div key={i} className="p-4 bg-slate-900/50 rounded-xl border border-slate-700">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-white">{result.type}</span>
                    <span className={result.status === "normal" ? "px-3 py-1 rounded-full text-xs font-medium text-emerald-400 bg-emerald-400/10" : "px-3 py-1 rounded-full text-xs font-medium text-amber-400 bg-amber-400/10"}>
                      {result.status.toUpperCase()}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 mb-2">
                    <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
                      <div className="h-full bg-emerald-500 rounded-full" style={{ width: result.confidence + "%" }} />
                    </div>
                    <span className="text-sm text-slate-400">{result.confidence}%</span>
                  </div>
                  <p className="text-sm text-slate-400">{result.details}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-4">
          {stats.map((stat, i) => (
            <div key={i} className="bg-slate-800/40 rounded-xl p-4 border border-slate-700">
              <p className="text-sm text-slate-400">{stat.label}</p>
              <p className={stat.color === "emerald" ? "text-2xl font-bold text-emerald-400" : stat.color === "amber" ? "text-2xl font-bold text-amber-400" : "text-2xl font-bold text-slate-300"}>{stat.value}</p>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
