# SentinelForge User Guide (RAG Corpus)

This document is part of the local knowledge base under `data/docs/` and is indexed by the RAG pipeline.

## Overview
SentinelForge is a multimodal AI agent platform that integrates:
- chat + routing,
- local document Q&A (RAG),
- risk scoring (fraud/cyber/behavior + fused decision),
- recommendations (text + multimodal similarity),
- voice emotion recognition,
- vision inference (image/video) + optional face emotion + brand/logo YOLO.

## Common API Endpoints
- Chat: `POST /api/chat`
- Multimodal chat: `POST /api/chat/multimodal`
- RAG query: `POST /api/rag/query`
- RAG ingest/upload: `POST /api/rag/ingest`, `POST /api/rag/upload`
- Risk scoring: `POST /api/risk/analyze`
- Recommendations: `POST /api/recommend`, `POST /api/recommend/multimodal`
- Voice emotion: `POST /api/voice/emotion`
- Vision: `POST /api/vision/predict`, `POST /api/vision/video/predict`
- Brand/logo YOLO: `POST /api/vision/brand/predict`

## Tips for Best Results
- Be specific in your question (what, where, which constraints).
- If a feature returns `503`, it usually means the required local model artifact was not trained yet.
- To add knowledge for RAG, drop `.md`/`.txt` files into `data/docs/` and call `/api/rag/ingest` (or `/api/rag/upload`).

