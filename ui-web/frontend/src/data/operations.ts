export const runbooks = [
  {
    title: "Local bootstrap",
    items: [
      "Backend: uvicorn app.main:app --reload",
      "Frontend: cd ui-web/frontend && npm install && npm run dev",
      "Streamlit fallback: streamlit run app/streamlit_chatbot/app.py",
    ],
  },
  {
    title: "GitHub Pages build",
    items: [
      "cd ui-web/frontend",
      "VITE_BASE_PATH=/REPO_NAME/ npm run build",
      "Deploy dist/ to the gh-pages branch",
    ],
  },
  {
    title: "Before demo",
    items: [
      "Confirm model artifacts are present for vision, voice, and fraud.",
      "Set VITE_API_BASE to your running FastAPI backend.",
      "Trigger a risk scenario and confirm JSONL logs update.",
    ],
  },
];
