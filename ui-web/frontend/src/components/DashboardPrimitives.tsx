import clsx from "clsx";
import { type ReactNode } from "react";

export function PageShell({
  title,
  eyebrow,
  children,
  actions,
}: {
  title: string;
  eyebrow?: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <main className="min-h-screen bg-sand px-5 py-6 text-ink md:px-8">
      <header className="mb-6 flex flex-col gap-3 border-b border-line pb-5 md:flex-row md:items-end md:justify-between">
        <div>
          {eyebrow && (
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-moss">
              {eyebrow}
            </p>
          )}
          <h1 className="mt-1 text-3xl font-semibold tracking-normal text-ink">{title}</h1>
        </div>
        {actions}
      </header>
      {children}
    </main>
  );
}

export function Panel({
  title,
  children,
  className,
}: {
  title?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={clsx("rounded-lg border border-line bg-panel p-4 shadow-card", className)}>
      {title && <h2 className="mb-3 text-base font-semibold text-ink">{title}</h2>}
      {children}
    </section>
  );
}

export function StatusPill({ status }: { status?: string }) {
  const value = (status || "unknown").toLowerCase();
  const tone =
    value.includes("healthy") || value.includes("pass") || value.includes("ready")
      ? "border-emerald-200 bg-emerald-50 text-emerald-700"
      : value.includes("degraded") || value.includes("pending")
        ? "border-amber-200 bg-amber-50 text-amber-700"
        : "border-rose-200 bg-rose-50 text-rose-700";
  return (
    <span className={clsx("inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold", tone)}>
      {status || "unknown"}
    </span>
  );
}

export function ConfidencePill({ value }: { value?: number }) {
  const score = typeof value === "number" ? Math.round((value <= 1 ? value * 100 : value)) : 0;
  return (
    <span className="inline-flex rounded-full border border-moss/20 bg-moss/10 px-2.5 py-1 text-xs font-semibold text-moss">
      Confidence {score}%
    </span>
  );
}

export function ErrorState({ message }: { message?: string | null }) {
  if (!message) return null;
  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
      {message}
    </div>
  );
}

export function TextInput(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={clsx(
        "w-full rounded-md border border-line bg-white px-3 py-2 text-sm text-ink outline-none focus:border-moss",
        props.className,
      )}
    />
  );
}

export function TextArea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      {...props}
      className={clsx(
        "w-full rounded-md border border-line bg-white px-3 py-2 text-sm text-ink outline-none focus:border-moss",
        props.className,
      )}
    />
  );
}

export function PrimaryButton(props: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...props}
      className={clsx(
        "rounded-md bg-moss px-3 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50",
        props.className,
      )}
    />
  );
}

export function SecondaryButton(props: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...props}
      className={clsx(
        "rounded-md border border-line bg-white px-3 py-2 text-sm font-semibold text-ink disabled:cursor-not-allowed disabled:opacity-50",
        props.className,
      )}
    />
  );
}

export function MiniBarChart({ data }: { data: Array<{ label: string; value: number }> }) {
  const max = Math.max(...data.map((item) => item.value), 1);
  return (
    <div className="space-y-2">
      {data.map((item) => (
        <div key={item.label} className="grid grid-cols-[7rem_1fr_3rem] items-center gap-2 text-xs">
          <span className="truncate text-fog">{item.label}</span>
          <div className="h-2 rounded-full bg-slate-100">
            <div
              className="h-2 rounded-full bg-moss"
              style={{ width: `${Math.max(4, (item.value / max) * 100)}%` }}
            />
          </div>
          <span className="text-right tabular-nums text-fog">{item.value.toFixed(2)}</span>
        </div>
      ))}
    </div>
  );
}

export function JsonBlock({ value }: { value: unknown }) {
  return (
    <pre className="max-h-72 overflow-auto rounded-md bg-slate-950 p-3 text-xs text-slate-100">
      {JSON.stringify(value, null, 2)}
    </pre>
  );
}

export function ToolSteps({ steps }: { steps: Array<Record<string, unknown>> }) {
  return (
    <div className="space-y-2">
      {steps.map((step, index) => (
        <details key={`${step.label || step.tool || index}`} className="rounded-md border border-line bg-white p-3">
          <summary className="cursor-pointer text-sm font-semibold text-ink">
            {String(step.label || step.tool || `Step ${index + 1}`)}
          </summary>
          <JsonBlock value={step} />
        </details>
      ))}
    </div>
  );
}

export function CitationPanel({ citations }: { citations: unknown[] }) {
  return (
    <div className="space-y-2">
      {citations.length === 0 && <p className="text-sm text-fog">No citations returned.</p>}
      {citations.map((citation, index) => (
        <div key={index} className="rounded-md border border-line bg-white p-3 text-sm text-fog">
          <JsonBlock value={citation} />
        </div>
      ))}
    </div>
  );
}
