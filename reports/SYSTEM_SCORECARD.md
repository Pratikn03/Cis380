# System Scorecard (Tier-6)

## DSA Seed
- status: **200**
- sample: `{'status': 'ok', 'documents': 4, 'pages': 4, 'chunks': 4}`

## Latency (p50/p95) + Status
### Health
- status: **200**
- p50: **6.06 ms**, p95: **7.35 ms**
- sample: `{'status': 'ok', 'service': 'Sentifargo', 'version': '0.2', 'python': {'version': '3.13.5', 'implementation': 'CPython'}, 'platform': {'system': 'Darwin', 'release': '25.1.0', 'machine': 'arm64'}, 'optional_features': {'webrtc': False, 'stt': False, 'clip': False, 'faiss': False}}`

### Chat
- status: **200**
- p50: **6.38 ms**, p95: **7.02 ms**
- sample: `{'route': 'chat', 'answer': 'Welcome! I\'m Sentifargo - built by Pratik Niroula! 👋\n\n**Quick Actions:**\n→ Say "recommend action movies" for suggestions\n→ Ask "what is anomaly detection?" to learn\n→ Say "help" to see all my capabilities\n\nI specialize in security analytics, machine learning, and intelligent recommendations. How can I assist you?', 'meta': {'intent': 'llm', 'offline': True, 'hi`

### Fraud
- status: **200**
- p50: **4.97 ms**, p95: **7.09 ms**
- sample: `{'score': 0.0008704798205042115, 'input_features': 30, 'expected_features': 34, 'feature_names': ['Time', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'V7', 'V8', 'V9', 'V10', 'V11', 'V12', 'V13', 'V14', 'V15', 'V16', 'V17', 'V18', 'V19', 'V20', 'V21', 'V22', 'V23', 'V24', 'V25', 'V26', 'V27', 'V28', 'Amount', 'amount_log', 'time_hours', 'time_seconds_mod_day', 'hour_of_day']}`

### Risk
- status: **200**
- p50: **31.59 ms**, p95: **31.72 ms**
- sample: `{'cyber_risk': 0.9985989823852061, 'behavior_risk': 0.26514217775131327, 'fraud_risk': 0.0012, 'fusion_risk': 0.4160443932983708, 'decision': 'ALLOW', 'reason_code': 'LOW_RISK', 'fusion_meta': {'available': True, 'path': 'models/fusion/fusion_meta_model.pkl', 'decision': 'ALLOW', 'threshold': 0.8, 'feature_order': ['behavior', 'cyber', 'fraud'], 'inputs': {'behavior': 0.26514217775131327, 'cyber':`

### Voice Emotion
- status: **200**
- p50: **14.22 ms**, p95: **15.12 ms**
- sample: `{'emotion': 'angry', 'confidence': 0.3333, 'signals': {'sample_rate': 22050.0, 'duration_sec': 0.5, 'zcr_mean': 0.0, 'rms_mean': 0.0, 'rms_std': 0.0, 'pitch_mean_hz': 400.9091, 'pitch_std_hz': 0.0, 'spectral_contrast_mean': 0.0, 'stress_score_heuristic': 0.0, 'stress_note': 'Heuristic only; not clinically validated.'}, 'segments': {'segments': 1, 'emotion_shift_count': 0, 'predictions': [{'segment`

### Brand Vision
- status: **200**
- p50: **27.73 ms**, p95: **28.83 ms**
- sample: `{'filename': 'test_logo.png', 'detections': [], 'count': 0}`

### Face Emotion
- status: **200**
- p50: **12.54 ms**, p95: **13.95 ms**
- sample: `{'filename': 'face.png', 'emotion': 'neutral', 'confidence': 0.577486, 'top_k': [{'emotion': 'neutral', 'prob': 0.577486}, {'emotion': 'angry', 'prob': 0.263202}, {'emotion': 'surprise', 'prob': 0.095323}], 'num_classes': 7, 'classes': ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral'], 'model_path': 'models/vision/face_emotion/model.pt', 'model_meta': {'arch': 'resnet18', 'image_`

### DSA Docs
- status: **200**
- p50: **3.37 ms**, p95: **3.9 ms**
- sample: `{'answer': 'Effective anomaly detection requires understanding normal behavior patterns first, then flagging deviations that exceed defined thresholds.\n\nSources: [1], [2], [3], [4]', 'citations': [{'doc_id': '48e169add6c32dec', 'filename': 'e2e_doc.txt', 'source': '/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/data/raw/docs/e2e_doc.txt', 'page': None, 'chunk_id': '48e169ad`

### Monitor Summary
- status: **200**
- p50: **2.54 ms**, p95: **3.59 ms**
- sample: `{'count': 119, 'avg_latency': 20.0, 'avg_score': 0.2, 'label_dist': {'low': 119}, 'risk': {'total_events': 92, 'decision_counts': {'ALLOW': 91, 'BLOCK': 1}, 'avg_risks': {'cyber_risk': 0.6504192877841577, 'behavior_risk': 0.2795856626926386, 'fraud_risk': 0.010373388996004314, 'fusion_risk': 0.4457293389843852}}, 'paths': {'fraud_log': 'data/monitoring/logs/fraud_events.jsonl', 'risk_log': 'data/m`

### Monitor Drift
- status: **200**
- p50: **2.83 ms**, p95: **3.15 ms**
- sample: `{'window': 'last_1000', 'drift_score': 27.63099348490743, 'per_feature': {'amount': {'psi': 27.63099348490743}, 'hour': {'psi': 27.63099348490743}}, 'status': 'critical'}`

### Risk Summary
- status: **500**
- p50: **8.53 ms**, p95: **8.69 ms**
- sample: `{'detail': 'An internal error occurred', 'success': False, 'error': {'code': 'INTERNAL_SERVER_ERROR', 'message': 'An internal error occurred', 'details': {}, 'path': '/api/monitor/risk_summary', 'request_id': 'ed6a3b0f-8436-4df3-b448-751bccd4ad95', 'timestamp': '2026-01-22T03:52:27.731006Z'}}`
