# System Scorecard (Tier-6)

## DSA Seed
- failed: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api/rag/ingest (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x1048ed940>: Failed to establish a new connection: [Errno 61] Connection refused'))

## Latency (p50/p95) + Status
### Health
- failed: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api/health (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x1048cee90>: Failed to establish a new connection: [Errno 61] Connection refused'))

### Chat
- failed: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api/chat (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x1048cf890>: Failed to establish a new connection: [Errno 61] Connection refused'))

### Fraud
- failed: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api/fraud (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x10485b820>: Failed to establish a new connection: [Errno 61] Connection refused'))

### Risk
- failed: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api/risk/analyze (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x1049482b0>: Failed to establish a new connection: [Errno 61] Connection refused'))

### Voice Emotion
- failed: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api/voice/emotion (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x104924dd0>: Failed to establish a new connection: [Errno 61] Connection refused'))

### Brand Vision
- failed: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api/vision/brand/predict?kind=logo (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x1048f16a0>: Failed to establish a new connection: [Errno 61] Connection refused'))

### Face Emotion
- failed: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api/vision/face_emotion/predict (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x1048f0e20>: Failed to establish a new connection: [Errno 61] Connection refused'))

### DSA Docs
- failed: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api/rag/ask (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x1048f0af0>: Failed to establish a new connection: [Errno 61] Connection refused'))

### Monitor Summary
- failed: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api/monitor/summary (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x1048f0c00>: Failed to establish a new connection: [Errno 61] Connection refused'))

### Monitor Drift
- failed: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api/monitor/drift (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x1048f08d0>: Failed to establish a new connection: [Errno 61] Connection refused'))

### Risk Summary
- failed: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api/monitor/risk_summary (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x1048f1d00>: Failed to establish a new connection: [Errno 61] Connection refused'))
