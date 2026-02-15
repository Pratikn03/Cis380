"use client";

import { useMemo } from "react";
import { usePathname } from "next/navigation";
import { Sidebar } from "@/components/shell/Sidebar";
import { StatusRail } from "@/components/shell/StatusRail";
import { TopCommandBar } from "@/components/shell/TopCommandBar";

const PAGE_LABELS: Record<string, string> = {
  "/": "Command Center",
  "/rag": "Mission Chat",
  "/live-media": "Media Studio",
  "/risk": "Risk Lab",
  "/jobs": "Ops Center",
  "/models": "Models",
  "/datasets": "Datasets",
  "/admin": "Admin",
  "/settings": "Settings",
};

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  const activeLabel = useMemo(() => PAGE_LABELS[pathname] ?? "Command Center", [pathname]);

  return (
    <div className="sf-root">
      <div className="sf-sidebar-wrap">
        <Sidebar pathname={pathname} />
        <StatusRail online />
      </div>

      <section className="sf-stage">
        <TopCommandBar activeLabel={activeLabel} />
        <main className="sf-content">{children}</main>
      </section>
    </div>
  );
}
