import { NavLink } from "react-router-dom";
import clsx from "clsx";
import { navigation } from "../data/navigation";

export default function Sidebar() {
  const backendUrl = import.meta.env.VITE_API_BASE || "http://localhost:8000";
  const environment = backendUrl.includes("localhost") ? "Local" : "Remote";

  return (
    <aside className="w-full border-b border-line bg-white/80 px-6 py-6 md:w-72 md:border-b-0 md:border-r lg:w-80">
      <div className="flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-900 text-sm font-semibold text-white">
          SF
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-moss">SentinelForge</p>
          <p className="text-lg font-display font-semibold">Command Center</p>
        </div>
      </div>

      <nav className="mt-8 space-y-2">
        {navigation.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === "/"}
            className={({ isActive }) =>
              clsx(
                "flex items-center justify-between rounded-2xl px-4 py-3 text-sm font-semibold transition",
                isActive
                  ? "bg-moss text-white shadow-lift"
                  : "border border-line text-fog hover:border-moss"
              )
            }
          >
            <span>{item.label}</span>
            <span className="text-xs opacity-70">/</span>
          </NavLink>
        ))}
      </nav>

      <div className="mt-8 space-y-4">
        <div className="card-panel px-4 py-4">
          <p className="text-xs uppercase tracking-[0.3em] text-fog">Settings</p>
          <div className="mt-3 text-xs text-fog">Backend URL</div>
          <p className="mt-1 break-all text-sm font-semibold text-ink">{backendUrl}</p>
          <div className="mt-3 text-xs text-fog">Environment</div>
          <p className="mt-1 text-sm font-semibold text-ink">{environment}</p>
        </div>

        <div className="card-panel px-4 py-4">
          <p className="text-xs uppercase tracking-[0.3em] text-fog">Modules</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {[
              "Chat",
              "Risk",
              "Fraud",
              "Cyber",
              "Behavior",
              "Brand",
              "Vision",
              "Video",
              "Voice",
              "Recommender",
              "RAG",
            ].map((item) => (
              <span key={item} className="tag text-fog">
                {item}
              </span>
            ))}
          </div>
        </div>

        <div className="card-panel px-4 py-4 text-sm text-fog">
          <p className="text-xs uppercase tracking-[0.3em] text-fog">Quick Tips</p>
          <ul className="mt-3 space-y-2">
            <li>Ask for movies, cars, or outfits to test recommendations.</li>
            <li>Capture a photo, then press Analyze Media in the chat.</li>
            <li>Try cyber/behavior vectors if model files are present.</li>
            <li>Upload docs to RAG and query your knowledge base.</li>
          </ul>
        </div>
      </div>
    </aside>
  );
}
