const stats = [
  { label: "Images Processed", value: "154K+" },
  { label: "ML Models", value: "6" },
  { label: "Detection Accuracy", value: "99.2%" },
  { label: "API Endpoints", value: "15+" },
];

const capabilities = [
  {
    title: "Fraud Detection",
    details: "Transaction scoring with real-time anomaly signals and explainable outputs.",
  },
  {
    title: "Cybersecurity",
    details: "Network intrusion detection and pattern-based threat analysis.",
  },
  {
    title: "Behavior Analytics",
    details: "User behavior modeling for insider threat detection and anomaly scoring.",
  },
  {
    title: "Vision Intelligence",
    details: "Image authenticity checks, face emotion inference, and brand/logo detection.",
  },
  {
    title: "Voice Emotion",
    details: "Audio emotion recognition with offline-first inference.",
  },
  {
    title: "RAG + Recommendations",
    details: "Document Q&A and personalized recommendations with local embeddings.",
  },
];

const quickStart = [
  {
    label: "Run the API",
    command: "uvicorn app.main:app --reload --port 8000",
  },
  {
    label: "Run the Web UI",
    command: "cd ui-web/frontend && npm install && npm run dev",
  },
  {
    label: "Run Streamlit Command Center",
    command: "streamlit run app/streamlit_chatbot/app.py",
  },
];

const projectSummary = `Sentifargo: Sentifargo

Project Overview
Sentifargo is a comprehensive AI-powered anomaly detection and intelligent recommendation platform built by Pratik Niroula as part of the CIS 380 course project. The system demonstrates practical applications of machine learning in security, fraud detection, and personalized recommendations.

Key highlights:
- 154,000+ images processed for vision analysis
- 60,000+ movies in the recommendation database
- 99.2% accuracy in fraud detection
- 6 ML models integrated (fraud, cyber, behavior, vision, NLP, fusion)
- 100% offline capable - works without external APIs

Architecture
Frontend Layer
- React/TypeScript UI (Command Center)
- Streamlit app (Chat/Demo)
- GitHub Pages (Portfolio)

FastAPI Backend
- API routes: /api/chat, /api/risk, /api/vision, /api/voice
- Orchestrator: intent detection, route selection, response fusion

ML Models Layer
- Fraud, Cyber, Behavior, Vision
- NLP, Fusion, Recommender

Data Layer
- RAG store (docs and Q&A)
- Catalogs (items and recommendations)
- Training datasets (fraud, cyber, vision)

Core Features
1) Fraud Detection System
   - Model: XGBoost/Random Forest ensemble
   - Accuracy: 99.2% on test data
   - Features: Transaction amount, velocity, location, device fingerprinting
   - Real-time: Sub-second prediction latency
   - Explainability: SHAP values for feature importance

2) Cybersecurity Threat Analysis
   - Detection types: Network intrusion, anomalous patterns
   - Methods: Isolation Forest, LSTM for sequence analysis
   - Metrics: Precision, recall, F1-score tracking
   - Alerts: Configurable threshold-based alerting

3) Behavioral Anomaly Detection
   - Use case: Insider threat detection, account compromise
   - Features: User activity patterns, access times, resource usage
   - Model: Autoencoder for anomaly scoring
   - Baseline: Dynamic baseline learning

4) Intelligent Recommendations
   - Movie database: 60,000+ titles from MovieLens
   - Methods: Content-based filtering, TF-IDF similarity
   - Categories: Movies, products, courses, cars, places
   - Randomization: Varied results each query

5) Vision Analysis
   - Dataset: 154,000+ images (Real/Fake classification)
   - Models: CNN, ResNet, custom architectures
   - Use cases: Deepfake detection, image authenticity
   - Integration: Upload via chat or API

6) Natural Language Processing
   - RAG system: Document retrieval and Q&A
   - Intent detection: Keyword and semantic matching
   - Responses: 50+ varied intelligent responses
   - Offline: Works without OpenAI API

Technology Stack
Backend:
- Python 3.13
- FastAPI
- Uvicorn
- Pydantic

Machine Learning:
- PyTorch
- scikit-learn
- XGBoost
- FAISS
- Transformers

Frontend:
- React 18
- TypeScript
- Tailwind CSS
- Vite
- Streamlit

Data and Storage:
- Pandas
- NumPy
- SQLite
- YAML/JSON

DevOps:
- Docker
- GitHub Actions
- GitHub Pages

Project Statistics
- Total Python files: 352
- Total lines of code: ~50,000+
- ML models: 6
- API endpoints: 15+
- Training images: 154,000+
- Movie database: 60,000+
- Fraud detection accuracy: 99.2%
- Response variations: 50+ unique responses

Key Innovations
1) Offline-First AI
   - Local ML models for all predictions
   - Pre-computed embeddings for recommendations
   - Intelligent response generation without LLM API
   - Fallback responses with variety

2) Multi-Modal Orchestration
   - Single entry point handles multiple AI tasks

3) Randomized Intelligent Responses
   - 4 greeting variations
   - 3 help response formats
   - 45+ movie recommendations (random selection)
   - Topic-specific knowledge base with multiple answers

4) Production-Ready Architecture
   - Modular design with clear separation of concerns
   - Comprehensive error handling
   - Configurable via YAML files
   - Docker-ready deployment
`;

export default function CommandCenter() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-6xl mx-auto space-y-10">
        <section className="space-y-4">
          <p className="text-sm uppercase tracking-[0.3em] text-emerald-400">
            Sentifargo
          </p>
          <h1 className="text-4xl md:text-5xl font-bold text-white">Sentifargo</h1>
          <p className="text-slate-300 max-w-3xl">
            A multimodal AI platform for fraud detection, cybersecurity monitoring, behavioral
            analytics, and vision intelligence. Built to run fully offline with a unified FastAPI
            gateway and a production-ready orchestration layer.
          </p>
          <div className="flex flex-wrap gap-3">
            <a
              href="https://pratikn03.github.io/Cis380/"
              target="_blank"
              rel="noreferrer"
              className="px-5 py-2 bg-emerald-500 text-slate-900 font-semibold rounded-lg hover:bg-emerald-400 transition-colors"
            >
              Live Demo
            </a>
            <a
              href="https://github.com/Pratikn03/Cis380"
              target="_blank"
              rel="noreferrer"
              className="px-5 py-2 border border-slate-600 text-slate-200 rounded-lg hover:border-emerald-400 transition-colors"
            >
              GitHub Repo
            </a>
          </div>
        </section>

        <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {stats.map((stat) => (
            <div
              key={stat.label}
              className="rounded-xl border border-slate-700 bg-slate-800/50 p-4"
            >
              <p className="text-xs text-slate-400">{stat.label}</p>
              <p className="text-2xl font-semibold text-emerald-300">{stat.value}</p>
            </div>
          ))}
        </section>

        <section className="space-y-4">
          <div>
            <h2 className="text-2xl font-semibold text-white">Core Capabilities</h2>
            <p className="text-slate-400">
              Sentifargo combines multiple intelligence engines behind a single interface.
            </p>
          </div>
          <div className="grid md:grid-cols-2 gap-4">
            {capabilities.map((capability) => (
              <div
                key={capability.title}
                className="rounded-xl border border-slate-700 bg-slate-800/50 p-5"
              >
                <p className="text-lg font-semibold text-white">{capability.title}</p>
                <p className="text-sm text-slate-400 mt-2">{capability.details}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="space-y-4">
          <div>
            <h2 className="text-2xl font-semibold text-white">Quick Start</h2>
            <p className="text-slate-400">
              Run the backend and UI locally, then explore the AI chat integrations.
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-4">
            {quickStart.map((item) => (
              <div
                key={item.label}
                className="rounded-xl border border-slate-700 bg-slate-900/70 p-4"
              >
                <p className="text-sm font-semibold text-emerald-300">{item.label}</p>
                <pre className="mt-3 text-xs text-slate-300 whitespace-pre-wrap break-words">
                  {item.command}
                </pre>
              </div>
            ))}
          </div>
        </section>

        <section className="space-y-4">
          <div>
            <h2 className="text-2xl font-semibold text-white">Project Summary</h2>
            <p className="text-slate-400">
              Full project overview based on the documentation summary.
            </p>
          </div>
          <div className="rounded-2xl border border-slate-700 bg-slate-900/60 p-6">
            <pre className="text-xs text-slate-300 whitespace-pre-wrap">
              {projectSummary}
            </pre>
          </div>
        </section>
      </div>
    </main>
  );
}
