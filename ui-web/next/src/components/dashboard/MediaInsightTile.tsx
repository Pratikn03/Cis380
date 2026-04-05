export type MediaInsight = {
  title: string;
  tag: string;
  tone: "video" | "deepfake" | "brand" | "voice";
};

export function MediaInsightTile({ item }: { item: MediaInsight }) {
  return (
    <div className={`dash-media-card media-card-${item.tone}`}>
      <div className="dash-media-title">{item.title}</div>
      <div className="dash-media-tag">{item.tag}</div>
    </div>
  );
}
