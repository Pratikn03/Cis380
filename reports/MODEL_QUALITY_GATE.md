# Model Quality Gate

- Status: **fail**

- Failed metric gates: brand, cyber, fraud, rag, recommender, vision_deepfake, vision_face_emotion, vision_temporal, voice
- Failed manifest checks: brand, cyber, fraud, fusion, rag, recommender, vision_deepfake, vision_face_emotion, vision_temporal, voice

## fraud
- Gate status: **fail**
- Artifact: `models/fraud/supervised/fraud_model.pkl`
- Metrics: `experiments/fraud/metrics/metrics.json`
- Failures: `[{"domain": "fraud", "metric": "test.roc_auc", "operator": ">=", "expected": 0.8214741065580803, "actual": 0.7682327735437844, "baseline": "test.roc_auc", "passed": false}, {"domain": "fraud", "metric": "test.f1", "operator": ">=", "expected": 0.65, "actual": 0.5506072874493927, "baseline": null, "passed": false}, {"domain": "fraud", "metric": "test.roc_auc", "baseline": 0.8053667711353728, "actual": 0.7682327735437844, "max_regression_pct": 2.0, "actual_regression_pct": 4.610818, "passed": false}, {"domain": "fraud", "metric": "test.f1", "baseline": 0.6903553299492385, "actual": 0.5506072874493927, "max_regression_pct": 2.0, "actual_regression_pct": 20.242915, "passed": false}]`

## cyber
- Gate status: **fail**
- Artifact: `models/cyber/supervised/cyber_model.pkl`
- Metrics: `experiments/cyber/metrics/metrics.json`
- Failures: `[{"domain": "cyber", "metric": "test.f1", "operator": ">=", "expected": 0.9822347667275445, "actual": 0.9785536159600997, "baseline": "test.f1", "passed": false}]`

## behavior
- Gate status: **pass**
- Artifact: `models/behavior/behavior_lof.pkl`
- Metrics: `experiments/behavior/metrics/metrics.json`

## vision_deepfake
- Gate status: **fail**
- Artifact: `models/vision/yolo_cls/best.pt`
- Metrics: `experiments/vision/metrics/metrics.json`
- Failures: `[{"domain": "vision_deepfake", "metric": "roc_auc", "operator": ">=", "expected": 0.85, "actual": null, "baseline": null, "passed": false}, {"domain": "vision_deepfake", "metric": "f1", "operator": ">=", "expected": 0.8, "actual": null, "baseline": null, "passed": false}, {"domain": "vision_deepfake", "metric": "accuracy", "operator": ">=", "expected": 0.85, "actual": null, "baseline": null, "passed": false}, {"domain": "vision_deepfake", "metric": "artifact_exists", "operator": "exists", "expected": true, "actual": false, "path": "models/vision/yolo_cls/best.pt", "passed": false}]`

## vision_face_emotion
- Gate status: **fail**
- Artifact: `models/vision/face_emotion/model.pt`
- Metrics: `models/vision/face_emotion/metrics.json`
- Failures: `[{"domain": "vision_face_emotion", "metric": "best_val_acc", "operator": ">=", "expected": 0.014571428571428572, "actual": 0.014285714285714285, "baseline": "best_val_acc", "passed": false}]`

## vision_temporal
- Gate status: **fail**
- Artifact: `models/vision/video_temporal_model.pkl`
- Metrics: `experiments/vision/video_temporal/metrics.json`
- Failures: `[{"domain": "vision_temporal", "metric": "accuracy", "operator": ">=", "expected": 0.75, "actual": 0.64, "baseline": null, "passed": false}]`

## brand
- Gate status: **fail**
- Artifact: `artifacts/brand/yolo_logo_det.pt`
- Metrics: `models/brand/full/results.csv`
- Failures: `[{"domain": "brand", "metric": "metrics_map50_b", "operator": ">=", "expected": 0.85, "actual": 0.0, "baseline": null, "passed": false}]`

## voice
- Gate status: **fail**
- Artifact: `models/voice_emotion_ssl`
- Metrics: `reports/voice_emotion_eval.json`
- Failures: `[{"domain": "voice", "metric": "macro_f1", "operator": ">=", "expected": 0.6, "actual": 0.14299586547850726, "baseline": null, "passed": false}, {"domain": "voice", "metric": "uar", "operator": ">=", "expected": 0.6, "actual": 0.2219047619047619, "baseline": null, "passed": false}]`

## recommender
- Gate status: **fail**
- Artifact: `models/recommender/recommender_model.pkl`
- Metrics: `experiments/recommender/metrics/metrics.json`
- Failures: `[{"domain": "recommender", "metric": "recall_at_10", "operator": ">=", "expected": 0.1, "actual": 0.004, "baseline": null, "passed": false}, {"domain": "recommender", "metric": "ndcg_at_10", "operator": ">=", "expected": 0.05, "actual": 0.0018572106393741415, "baseline": null, "passed": false}]`

## fusion
- Gate status: **pass**
- Artifact: `models/fusion/fusion_meta_model.pkl`
- Metrics: `experiments/fusion/metrics/metrics.json`

## rag
- Gate status: **fail**
- Artifact: `data/processed/rag`
- Metrics: `metrics/rag_eval.json`
- Failures: `[{"domain": "rag", "metric": "mrr", "operator": ">=", "expected": 0.7, "actual": 0.0, "baseline": null, "passed": false}, {"domain": "rag", "metric": "recall_at_k.10", "operator": ">=", "expected": 0.7, "actual": 0.0, "baseline": null, "passed": false}]`
