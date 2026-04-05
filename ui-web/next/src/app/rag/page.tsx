"use client";

import { useQuery } from "@apollo/client";
import { MissionChatPanel } from "@/components/mission/MissionChatPanel";
import { OfflineBanner } from "@/components/dashboard/OfflineBanner";
import { RAG_STATUS } from "@/lib/gateway-graphql";

export default function RagPage() {
  const { data, error } = useQuery(RAG_STATUS, { pollInterval: 12000 });
  const status = data?.ragStatus;
  const offline = Boolean(error);

  return (
    <div className="sf-page-stack">
      <section className="sf-page-head card">
        <div>
          <h1 className="sf-page-title">Mission Chat (RAG)</h1>
          <p className="muted">
            Ask docs, movie, and clothes intelligence queries through one mission console.
          </p>
        </div>
        <div className="sf-tab-row">
          <button className="sf-tab sf-tab-active" type="button">
            Mission
          </button>
          <button className="sf-tab" type="button">
            Retrieval
          </button>
          <button className="sf-tab" type="button">
            Recommendations
          </button>
        </div>
      </section>

      {offline && (
        <OfflineBanner
          title="Gateway offline:"
          subtitle="mission chat is still available in fallback mode until GraphQL reconnects."
        />
      )}

      <section className="sf-two-col">
        <article className="card panel-grid">
          <div className="sf-panel-heading">Index Status</div>
          <div className="sf-mini-kpis">
            <div>
              <span>Status</span>
              <strong>{String(status?.status ?? (offline ? "offline" : "loading"))}</strong>
            </div>
            <div>
              <span>Documents</span>
              <strong>{status?.docsCount ?? 0}</strong>
            </div>
            <div>
              <span>Chunks</span>
              <strong>{status?.chunksCount ?? 0}</strong>
            </div>
            <div>
              <span>Mode</span>
              <strong>{offline ? "Fallback" : "Live"}</strong>
            </div>
          </div>
        </article>

        <article className="card panel-grid">
          <div className="sf-panel-heading">Intent Shortcuts</div>
          <div className="sf-action-strip">
            <button className="sf-strip-btn strip-purple" type="button">Ask Docs</button>
            <button className="sf-strip-btn strip-orange" type="button">Recommend Movies</button>
            <button className="sf-strip-btn strip-gold" type="button">Recommend Clothes</button>
            <button className="sf-strip-btn strip-blue" type="button">Risk Summary</button>
          </div>
        </article>
      </section>

      <MissionChatPanel />
    </div>
  );
}
