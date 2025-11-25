"""Train a fusion meta-model from per-domain scores."""
from pathlib import Path
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

from uais.utils.metrics import compute_classification_metrics
from uais.utils.plotting import plot_roc_curve, plot_pr_curve

def load_fusion_scores():
    # expected CSVs with columns: entity_id, score, label (label optional)
    fraud = pd.read_csv("experiments/fraud/scores.csv")  # columns: entity_id, fraud_score, label?
    cyber = pd.read_csv("experiments/cyber/scores.csv")  # entity_id, cyber_score
    cert = pd.read_csv("experiments/cert/scores.csv")    # entity_id, cert_score

    df = fraud.merge(cyber, on="entity_id", how="inner").merge(cert, on="entity_id", how="inner")
    # adjust label column name if different
    label_col = "label" if "label" in df.columns else "fraud_label"
    return df, label_col

"""Train a fusion meta-model from per-domain scores."""
from pathlib import Path
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

from uais.utils.metrics import compute_classification_metrics
from uais.utils.plotting import plot_roc_curve, plot_pr_curve

def load_fusion_scores():
    fraud = pd.read_csv("experiments/fraud/scores.csv")   # entity_id, fraud_score, label?
    cyber = pd.read_csv("experiments/cyber/scores.csv")   # entity_id, cyber_score
    cert  = pd.read_csv("experiments/cert/scores.csv")    # entity_id, cert_score
    df = fraud.merge(cyber, on="entity_id", suffixes=("_fraud", "_cyber")).merge(cert, on="entity_id")
    label_col = "label" if "label" in df.columns else "fraud_label"
    return df, label_col

def train_fusion_meta():
    df, label_col = load_fusion_scores()
    score_cols = [c for c in df.columns if c.endswith("_score")]
    X = df[score_cols]
    y = df[label_col].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, stratify=y, random_state=42)

    model = LogisticRegression(class_weight="balanced", max_iter=1000)
    model.fit(X_train, y_train)
    y_prob = model.predict_proba(X_test)[:, 1]

    metrics = compute_classification_metrics(y_test.values, y_prob, threshold=0.5)
    print("Fusion meta-model metrics:")
    for k, v in metrics.items():
        print(f"{k}: {v:.4f}")

    plots_dir = Path("experiments/fusion/plots")
    plots_dir.mkdir(parents=True, exist_ok=True)
    plot_roc_curve(y_test.values, y_prob, title="Fusion ROC", output_dir=plots_dir)
    plot_pr_curve(y_test.values, y_prob, title="Fusion PR", output_dir=plots_dir)

    return model, metrics

if __name__ == "__main__":
    train_fusion_meta()
    df, label_col = load_fusion_scores()
    X = df[[c for c in df.columns if c.endswith("_score")]]
    y = df[label_col].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, stratify=y, random_state=42
    )

    model = LogisticRegression(class_weight="balanced", max_iter=1000)
    model.fit(X_train, y_train)
    y_prob = model.predict_proba(X_test)[:, 1]

    metrics = compute_classification_metrics(y_test.values, y_prob, threshold=0.5)
    print("Fusion meta-model metrics:")
    for k, v in metrics.items():
        print(f"{k}: {v:.4f}")

    plots_dir = Path("experiments/fusion/plots")
    plots_dir.mkdir(parents=True, exist_ok=True)
    plot_roc_curve(y_test.values, y_prob, title="Fusion ROC", output_dir=plots_dir)
    plot_pr_curve(y_test.values, y_prob, title="Fusion PR", output_dir=plots_dir)

    return model, metrics

if __name__ == "__main__":
    train_fusion_meta()
