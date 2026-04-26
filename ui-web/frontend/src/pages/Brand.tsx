import { useMemo, useState, type ChangeEvent } from "react";
import {
  ErrorState,
  JsonBlock,
  PageShell,
  Panel,
  PrimaryButton,
  SecondaryButton,
} from "../components/DashboardPrimitives";
import { brandPredict } from "../services/endpoints";

type BrandDetection = {
  brand?: string;
  confidence?: number;
  bbox?: number[];
  bbox_xyxy?: number[];
  bbox_percent?: number[];
};

const toPercentBox = (
  detection: BrandDetection,
  image: { width: number; height: number } | null,
) => {
  const percent = detection.bbox_percent;
  if (Array.isArray(percent) && percent.length >= 4) {
    return percent.map(Number);
  }

  const xyxy = detection.bbox_xyxy || detection.bbox;
  if (Array.isArray(xyxy) && xyxy.length >= 4 && image?.width && image?.height) {
    const [x1, y1, x2, y2] = xyxy.map(Number);
    return [
      (x1 / image.width) * 100,
      (y1 / image.height) * 100,
      ((x2 - x1) / image.width) * 100,
      ((y2 - y1) / image.height) * 100,
    ];
  }

  if (Array.isArray(detection.bbox) && detection.bbox.length >= 4) {
    return detection.bbox.map(Number);
  }

  return null;
};

export default function Brand() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [result, setResult] = useState<Record<string, any> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [kind, setKind] = useState("logo");
  const [confidence, setConfidence] = useState(0.25);
  const [imageSize, setImageSize] = useState<{ width: number; height: number } | null>(null);
  const detections = useMemo<BrandDetection[]>(
    () => (Array.isArray(result?.detections) ? result.detections : []),
    [result],
  );
  const resultImage = result?.image || imageSize;

  const onFile = (event: ChangeEvent<HTMLInputElement>) => {
    const next = event.target.files?.[0] || null;
    setFile(next);
    setResult(null);
    setError(null);
    setImageSize(null);
    setPreview(next ? URL.createObjectURL(next) : null);
  };

  const run = async () => {
    if (!file) return;
    setError(null);
    setResult(null);
    setIsLoading(true);
    const form = new FormData();
    form.append("file", file);
    try {
      const { data } = await brandPredict(form, kind, confidence);
      setResult(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <PageShell title="Brand" eyebrow="Detection Gallery">
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_24rem]">
        <Panel title="Image">
          <div className="flex flex-wrap items-end gap-3">
            <label className="block">
              <span className="mb-1 block text-xs font-semibold uppercase tracking-normal text-fog">
                Upload
              </span>
              <input
                type="file"
                accept="image/*"
                aria-label="Upload brand image"
                onChange={onFile}
                className="block w-72 max-w-full rounded-md border border-line bg-white px-3 py-2 text-sm text-ink"
              />
            </label>
            <label className="block">
              <span className="mb-1 block text-xs font-semibold uppercase tracking-normal text-fog">
                Model
              </span>
              <select
                value={kind}
                onChange={(event) => setKind(event.target.value)}
                className="rounded-md border border-line bg-white px-3 py-2 text-sm text-ink outline-none focus:border-moss"
              >
                <option value="logo">Logo</option>
                <option value="car">Car</option>
                <option value="fashion">Fashion</option>
              </select>
            </label>
            <label className="block">
              <span className="mb-1 block text-xs font-semibold uppercase tracking-normal text-fog">
                Confidence
              </span>
              <input
                type="number"
                min={0.01}
                max={0.95}
                step={0.05}
                value={confidence}
                onChange={(event) => setConfidence(Number(event.target.value))}
                className="w-28 rounded-md border border-line bg-white px-3 py-2 text-sm text-ink outline-none focus:border-moss"
              />
            </label>
            <PrimaryButton onClick={run} disabled={!file || isLoading}>
              {isLoading ? "Detecting..." : "Detect Brands"}
            </PrimaryButton>
            {file && (
              <SecondaryButton type="button" onClick={() => {
                setFile(null);
                setPreview(null);
                setResult(null);
                setError(null);
                setImageSize(null);
              }}>
                Clear
              </SecondaryButton>
            )}
          </div>
          {file && <p className="mt-3 text-sm text-fog">Selected: {file.name}</p>}
          <ErrorState message={error} />
          {result && detections.length === 0 && (
            <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
              No brand detections returned for this image at confidence {confidence.toFixed(2)}.
            </div>
          )}
          <div className="relative mt-4 inline-block max-w-full overflow-hidden rounded-lg border border-line bg-white">
            {preview ? (
              <img
                src={preview}
                alt="Brand preview"
                className="max-h-[34rem] max-w-full"
                onLoad={(event) => {
                  setImageSize({
                    width: event.currentTarget.naturalWidth,
                    height: event.currentTarget.naturalHeight,
                  });
                }}
              />
            ) : (
              <p className="p-6 text-sm text-fog">Upload an image.</p>
            )}
            {detections.map((det, index) => {
              const box = toPercentBox(det, resultImage);
              if (!box) return null;
              const [x, y, w, h] = box;
              return (
                <div
                  key={index}
                  className="absolute border-2 border-emerald-500 bg-emerald-500/10"
                  style={{ left: `${x}%`, top: `${y}%`, width: `${w}%`, height: `${h}%` }}
                  title={det.brand || `Detection ${index + 1}`}
                >
                  <span className="absolute left-0 top-0 -translate-y-full rounded-t bg-emerald-600 px-1.5 py-0.5 text-xs font-semibold text-white">
                    {det.brand || `Detection ${index + 1}`}
                  </span>
                </div>
              );
            })}
          </div>
        </Panel>
        <Panel title="Detections">
          <div className="mb-3 grid grid-cols-2 gap-2 text-sm">
            <div className="rounded-md border border-line bg-white p-3">
              <p className="text-xs uppercase tracking-normal text-fog">Count</p>
              <p className="text-xl font-semibold text-ink">{result?.count ?? 0}</p>
            </div>
            <div className="rounded-md border border-line bg-white p-3">
              <p className="text-xs uppercase tracking-normal text-fog">Kind</p>
              <p className="text-xl font-semibold text-ink">{result?.kind || kind}</p>
            </div>
          </div>
          {detections.length > 0 ? (
            <div className="mb-3 space-y-2">
              {detections.map((det, index) => (
                <div key={index} className="rounded-md border border-line bg-white p-3 text-sm">
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-semibold text-ink">
                      {det.brand || `Detection ${index + 1}`}
                    </span>
                    <span className="text-fog">
                      {typeof det.confidence === "number"
                        ? `${Math.round(det.confidence * 100)}%`
                        : "confidence n/a"}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="mb-3 text-sm text-fog">
              Run detection to populate this panel. If count is zero, the backend processed the image but the selected model did not detect a trained brand class.
            </p>
          )}
          <JsonBlock value={result || { detections: [] }} />
        </Panel>
      </div>
    </PageShell>
  );
}
