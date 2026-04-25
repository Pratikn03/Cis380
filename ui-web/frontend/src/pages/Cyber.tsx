import { useEffect, useMemo, useState } from "react";
import { ErrorState, JsonBlock, MiniBarChart, PageShell, Panel, StatusPill } from "../components/DashboardPrimitives";
import { cyberTimeline, cyberTimelineEvents, cyberTimelineSummary } from "../services/endpoints";

export default function Cyber() {
  const [timeline, setTimeline] = useState<any[]>([]);
  const [events, setEvents] = useState<any[]>([]);
  const [summary, setSummary] = useState<Record<string, any> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const severity = useMemo(
    () => Object.entries(summary?.by_severity || {}).map(([label, value]) => ({ label, value: Number(value) })),
    [summary],
  );

  useEffect(() => {
    Promise.all([cyberTimeline({ window: 120, limit: 18 }), cyberTimelineEvents({ limit: 12 }), cyberTimelineSummary()])
      .then(([tl, ev, sum]) => {
        setTimeline(tl.data.timeline || []);
        setEvents(ev.data.events || []);
        setSummary(sum.data);
      })
      .catch((err) => setError(err.response?.data?.detail || err.message));
  }, []);

  return (
    <PageShell title="Cyber" eyebrow="Timeline + Severity">
      <ErrorState message={error} />
      <div className="grid gap-4 lg:grid-cols-3">
        <Panel title="Summary">
          <StatusPill status={summary ? "ready" : "pending"} />
          <JsonBlock value={summary || {}} />
        </Panel>
        <Panel title="Severity Histogram">
          <MiniBarChart data={severity} />
        </Panel>
        <Panel title="Recent Events">
          <div className="space-y-2">
            {events.map((event, index) => (
              <div key={index} className="rounded-md border border-line bg-white p-3 text-sm">
                <div className="flex justify-between gap-2">
                  <strong>{event.event_type}</strong>
                  <StatusPill status={event.severity} />
                </div>
                <p className="mt-1 text-fog">{event.description}</p>
              </div>
            ))}
          </div>
        </Panel>
      </div>
      <Panel title="Timeline Buckets" className="mt-4">
        <JsonBlock value={timeline.slice(0, 12)} />
      </Panel>
    </PageShell>
  );
}
