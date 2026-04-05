"use client";

import Link from "next/link";

export type NavItem = {
  href: string;
  label: string;
  icon: string;
  group?: "core" | "ops";
};

const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Home", icon: "⌂", group: "core" },
  { href: "/rag", label: "Mission Chat", icon: "◈", group: "core" },
  { href: "/live-media", label: "Media Studio", icon: "◍", group: "core" },
  { href: "/risk", label: "Risk Lab", icon: "◰", group: "core" },
  { href: "/jobs", label: "Ops Center", icon: "◫", group: "ops" },
  { href: "/models", label: "Models", icon: "◎", group: "ops" },
  { href: "/datasets", label: "Datasets", icon: "◳", group: "ops" },
  { href: "/admin", label: "Admin", icon: "◉", group: "ops" },
  { href: "/settings", label: "Settings", icon: "◌", group: "ops" },
];

export function Sidebar({ pathname }: { pathname: string }) {
  return (
    <aside className="sf-sidebar">
      <div className="sf-brand">
        <span className="sf-brand-mark">✦</span>
        <span className="sf-brand-text">Sentifargo</span>
      </div>

      <div className="sf-nav-group-label">Command</div>
      <nav className="sf-nav">
        {NAV_ITEMS.filter((item) => item.group === "core").map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`sf-nav-item ${active ? "sf-nav-item-active" : ""}`}
            >
              <span className="sf-nav-icon">{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="sf-nav-group-label">Operations</div>
      <nav className="sf-nav">
        {NAV_ITEMS.filter((item) => item.group === "ops").map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`sf-nav-item ${active ? "sf-nav-item-active" : ""}`}
            >
              <span className="sf-nav-icon">{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
