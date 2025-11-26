```mermaid
flowchart TD
    UI[OmniChatX-UI<br/>(Chat Interface + UX)]
    API[OmniChatX API Gateway<br/>(FastAPI Backend)]

    UI --> API

    API --> LLM[LLM Engine<br/>(OpenAI / Groq / Mistral)]
    API --> RAG[RAG Retriever<br/>(Chroma / Pinecone)]
    API --> ML[ML Models Layer<br/>(Fraud / Cyber / Behavior / Rec)]

    RAG --> VDB[Document Embeddings DB<br/>(Vector DB Storage)]
    VDB --> RAG

    LLM --> ORCH[Chat Orchestration]
    RAG --> ORCH
    ML --> ORCH

    ORCH --> FINAL[Final Response<br/>(LLM + Facts + Explanations + ML Recommendations)]
```

**Legend:**
- **OmniChatX-UI**: your chat frontend (Streamlit or custom)
- **API Gateway**: FastAPI (or similar) that routes requests
- **LLM Engine**: GPT/Groq/Mistral, etc.
- **RAG Retriever**: pulls context from your documents via vector DB
- **ML Models Layer**: fraud/cyber/behavior/recommender models (`fraud_model.pkl`, `cyber_model.pkl`, `behavior_model.pkl`, `recommender.pkl`)
- **Chat Orchestration**: fuses outputs from LLM + RAG + ML into the final reply
