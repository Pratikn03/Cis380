"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard" },
  { href: "/rag", label: "DSA (RAG)" },
  { href: "/jobs", label: "Jobs" },
  { href: "/risk", label: "Risk" },
  { href: "/models", label: "Models" },
  { href: "/datasets", label: "Datasets" },
  { href: "/settings", label: "Settings" },
  { href: "/login", label: "Login" },
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="min-h-screen bg-app">
      <div className="app-grid">
        <aside className="app-sidebar">
          <div className="brand-block">
            <div className="brand-pill">Sentifargo</div>
            <div className="brand-sub">Tier-6 Command Center</div>
          </div>
          <nav className="nav-stack">
            {NAV_ITEMS.map((item) => {
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`nav-link ${active ? "nav-link-active" : ""}`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
          <div className="sidebar-footer">
            <div className="status-dot" />
            <span>Observability online</span>
          </div>
        </aside>
        <main className="app-main">
          <div className="app-shell-card">
            <div className="app-shell-inner">{children}</div>
          </div>
        </main>
      </div>
    </div>
  );
}
