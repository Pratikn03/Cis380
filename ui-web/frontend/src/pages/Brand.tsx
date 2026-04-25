import { useMemo, useState, type ChangeEvent } from "react";
import { ErrorState, JsonBlock, PageShell, Panel, PrimaryButton } from "../components/DashboardPrimitives";
import { brandPredict } from "../services/endpoints";

export default function Brand() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [result, setResult] = useState<Record<string, any> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const detections = useMemo(() => result?.detections || [], [result]);

  const onFile = (event: ChangeEvent<HTMLInputElement>) => {
    const next = event.target.files?.[0] || null;
    setFile(next);
    setResult(null);
    setPreview(next ? URL.createObjectURL(next) : null);
    event.target.value = "";
  };

  const run = async () => {
    if (!file) return;
    setError(null);
    const form = new FormData();
    form.append("file", file);
    try {
      const { data } = await brandPredict(form, "logo");
      setResult(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message);
    }
  };

  return (
    <PageShell title="Brand" eyebrow="Detection Gallery">
      <div className="grid gap-4 lg:grid-cols-[1fr_22rem]">
        <Panel title="Image">
          <input
            type="file"
            accept="image/*"
            aria-label="Upload brand image"
            onChange={onFile}
            className="mb-3 text-sm"
          />
          <PrimaryButton onClick={run} disabled={!file}>
            Detect Brands
          </PrimaryButton>
          <ErrorState message={error} />
          <div className="relative mt-4 inline-block max-w-full overflow-hidden rounded-lg border border-line bg-white">
            {preview ? <img src={preview} alt="Brand preview" className="max-h-[34rem] max-w-full" /> : <p className="p-6 text-sm text-fog">Upload an image.</p>}
            {detections.map((det: any, index: number) => {
              const box = det.bbox || det.box || [];
              if (box.length < 4) return null;
              const [x, y, w, h] = box.map(Number);
              return (
                <div
                  key={index}
                  className="absolute border-2 border-emerald-500 bg-emerald-500/10"
                  style={{ left: `${x}%`, top: `${y}%`, width: `${w}%`, height: `${h}%` }}
                  title={det.brand}
                />
              );
            })}
          </div>
        </Panel>
        <Panel title="Detections">
          <JsonBlock value={result || { detections: [] }} />
        </Panel>
      </div>
    </PageShell>
  );
}
