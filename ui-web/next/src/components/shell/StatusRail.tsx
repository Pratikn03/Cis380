"use client";

export function StatusRail({ online }: { online: boolean }) {
  return (
    <div className="sf-sidebar-status">
      <span className={`sf-status-dot ${online ? "" : "sf-status-dot-offline"}`} />
      {online ? "Signal mesh online" : "Offline fallback mode"}
    </div>
  );
}
