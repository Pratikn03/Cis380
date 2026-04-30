# Model Quality Gate

- Status: **fail**

- Failed metric gates: brand, vision_temporal, voice
- Failed manifest checks: brand, cyber, fraud, fusion, rag, recommender, vision_deepfake, vision_face_emotion, vision_temporal, voice

## fraud
- Gate status: **pass**
- Artifact: `models/fraud/supervised/fraud_model.pkl`
- Metrics: `experiments/fraud/metrics/metrics.json`
- Manifest failures: `[{"metric": "thresholdResult", "actual": "fail", "passed": false}, {"metric": "smokeInference", "actual": "pending", "passed": false}, {"metric": "artifactSha256", "passed": false}]`

## cyber
- Gate status: **pass**
- Artifact: `models/cyber/supervised/cyber_model.pkl`
- Metrics: `experiments/cyber/metrics/metrics.json`
- Manifest failures: `[{"metric": "thresholdResult", "actual": "fail", "passed": false}, {"metric": "smokeInference", "actual": "pending", "passed": false}, {"metric": "artifactSha256", "passed": false}]`

## behavior
- Gate status: **pass**
- Artifact: `models/behavior/behavior_lof.pkl`
- Metrics: `experiments/behavior/metrics/metrics.json`

## vision_deepfake
- Gate status: **pass**
- Artifact: `models/vision/yolo_cls/best.pt`
- Metrics: `experiments/vision/metrics/metrics.json`
- Manifest failures: `[{"metric": "thresholdResult", "actual": "fail", "passed": false}, {"metric": "smokeInference", "actual": "pending", "passed": false}]`

## vision_face_emotion
- Gate status: **pass**
- Artifact: `models/vision/face_emotion/model.pt`
- Metrics: `models/vision/face_emotion/metrics.json`
- Manifest failures: `[{"metric": "thresholdResult", "actual": "fail", "passed": false}, {"metric": "smokeInference", "actual": "pending", "passed": false}, {"metric": "artifactSha256", "passed": false}]`

## vision_temporal
- Gate status: **fail**
- Artifact: `models/vision/video_temporal_model.pkl`
- Metrics: `experiments/vision/video_temporal/metrics.json`
- Failures: `[{"domain": "vision_temporal", "metric": "roc_auc", "baseline": 0.6612, "actual": 0.5816766286604048, "max_regression_pct": 2.0, "actual_regression_pct": 12.027128, "passed": false}]`
- Manifest failures: `[{"metric": "thresholdResult", "actual": "fail", "passed": false}, {"metric": "smokeInference", "actual": "pending", "passed": false}, {"metric": "artifactSha256", "passed": false}]`

## brand
- Gate status: **fail**
- Artifact: `artifacts/brand/yolo_logo_det.pt`
- Metrics: `models/brand/full/results.csv`
- Failures: `[{"domain": "brand", "metric": "metrics_map50_b", "operator": ">=", "expected": 0.85, "actual": 0.81549, "baseline": null, "passed": false}]`
- Manifest failures: `[{"metric": "thresholdResult", "actual": "fail", "passed": false}, {"metric": "smokeInference", "actual": "pending", "passed": false}, {"metric": "artifactSha256", "passed": false}]`

## voice
- Gate status: **fail**
- Artifact: `models/voice_emotion_ssl_6class`
- Metrics: `reports/voice_emotion_eval.json`
- Failures: `[{"domain": "voice", "metric": "macro_f1", "operator": ">=", "expected": 0.6, "actual": 0.44273946985265744, "baseline": null, "passed": false}, {"domain": "voice", "metric": "uar", "operator": ">=", "expected": 0.6, "actual": 0.43809523809523815, "baseline": null, "passed": false}, {"domain": "voice", "metric": "artifact_exists", "operator": "exists", "expected": true, "actual": false, "path": "models/voice_emotion_ssl_6class", "passed": false}]`
- Manifest failures: `[{"metric": "thresholdResult", "actual": "fail", "passed": false}, {"metric": "smokeInference", "actual": "pending", "passed": false}, {"metric": "artifactSha256", "passed": false}]`

## recommender
- Gate status: **pass**
- Artifact: `models/recommender/recommender_model.pkl`
- Metrics: `experiments/recommender/metrics/metrics.json`
- Manifest failures: `[{"metric": "thresholdResult", "actual": "fail", "passed": false}, {"metric": "smokeInference", "actual": "pending", "passed": false}, {"metric": "artifactSha256", "passed": false}]`

## fusion
- Gate status: **pass**
- Artifact: `models/fusion/fusion_meta_model.pkl`
- Metrics: `experiments/fusion/metrics/metrics.json`
- Manifest failures: `[{"metric": "thresholdResult", "actual": "fail", "passed": false}, {"metric": "smokeInference", "actual": "pending", "passed": false}]`

## rag
- Gate status: **pass**
- Artifact: `data/processed/rag`
- Metrics: `metrics/rag_eval.json`
- Manifest failures: `[{"metric": "thresholdResult", "actual": "fail", "passed": false}, {"metric": "smokeInference", "actual": "pending", "passed": false}]`
