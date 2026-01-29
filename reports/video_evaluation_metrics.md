# Video Model Evaluation Metrics

**Last Updated:** 2026-01-28
**Model:** `video_lstm.py`

---

## ⚠️ Placeholder Metrics

**NOTE:** The following metrics are placeholders. A full evaluation has not yet been run on the video model. To generate real metrics, a dedicated evaluation script needs to be created and run against a labeled test dataset.

The evaluation script should:
1. Load the trained `video_temporal_model.pkl` artifact.
2. Iterate through a test set of videos with known labels (e.g., "real", "fake").
3. For each video, call the `/api/vision/video/predict` endpoint.
4. Compare the model's prediction with the true label to calculate accuracy.
5. Record the `latency_ms` from the API response to analyze performance.
6. (Advanced) Implement calibration analysis (e.g., using a reliability diagram) to check if predicted probabilities are well-calibrated.

---

## 📊 Placeholder Performance Metrics

| Metric | Value | Notes |
|---|---|---|
| **Accuracy** | `~88.5%` | *(Placeholder)* Estimated based on similar image models. |
| **P95 Latency** | `~1200 ms` | *(Placeholder)* Estimated latency for processing a 30-frame video. |
| **Calibration** | `N/A` | *(Placeholder)* Calibration analysis has not been performed. |

### Per-Class Accuracy (Placeholder)

| Class | Accuracy |
|---|---|
| Real | `~92%` |
| Fake | `~85%` |

---

This report should be updated once a formal evaluation is complete.
