"""
Plotting utilities for model evaluation.
"""

from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
from sklearn import metrics


def plot_roc_curve(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    title: str = "ROC Curve",
    show: bool = True,
    save_path: Optional[str] = None,
) -> None:
    """
    Plot ROC curve and optionally save to file.
    """
    fpr, tpr, _ = metrics.roc_curve(y_true, y_prob)
    auc_val = metrics.roc_auc_score(y_true, y_prob)

    plt.figure()
    plt.plot(fpr, tpr, label=f"ROC AUC = {auc_val:.3f}")
    plt.plot([0, 1], [0, 1], linestyle="--")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title(title)
    plt.legend(loc="lower right")

    if save_path is not None:
        plt.savefig(save_path, bbox_inches="tight")

    if show:
        plt.show()
    else:
        plt.close()


def plot_pr_curve(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    title: str = "Precision-Recall Curve",
    show: bool = True,
    save_path: Optional[str] = None,
) -> None:
    """
    Plot Precision-Recall curve and optionally save to file.
    """
    precision, recall, _ = metrics.precision_recall_curve(y_true, y_prob)
    ap = metrics.average_precision_score(y_true, y_prob)

    plt.figure()
    plt.step(recall, precision, where="post")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title(f"{title} (AP = {ap:.3f})")

    if save_path is not None:
        plt.savefig(save_path, bbox_inches="tight")

    if show:
        plt.show()
    else:
        plt.close()
