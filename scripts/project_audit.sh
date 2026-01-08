#!/usr/bin/env bash
set -e

OUT=PROJECT_AUDIT_REPORT.md
echo "# 📊 PROJECT AUDIT REPORT" > $OUT
echo "" >> $OUT

CODE_DIRS=()
for candidate in app src scripts configs docs tests deploy dashboard ui-web; do
  if [ -d "$candidate" ]; then
    CODE_DIRS+=("$candidate")
  fi
done

echo "## 📁 Repository Structure" >> $OUT
tree -L 4 >> $OUT 2>/dev/null || find . -maxdepth 4 -type d >> $OUT
echo "" >> $OUT

echo "## 🧠 Backend (FastAPI / APIs)" >> $OUT
rg -n "FastAPI" app 2>/dev/null >> $OUT || echo "FastAPI not detected" >> $OUT
rg -n "@router" app/api app/legacy/api 2>/dev/null >> $OUT || true
echo "" >> $OUT

echo "## 🤖 Models Detected" >> $OUT
find models artifacts runs -type f \( -name "*.pkl" -o -name "*.pt" -o -name "*.onnx" \) 2>/dev/null >> $OUT || echo "No models found" >> $OUT
echo "" >> $OUT

echo "## 📊 ML Training Scripts" >> $OUT
find src scripts notebooks -type f -name "train*.py" 2>/dev/null >> $OUT || echo "No training scripts found" >> $OUT
echo "" >> $OUT

echo "## 🧪 Evaluation Scripts" >> $OUT
find src scripts notebooks -type f -name "*eval*.py" 2>/dev/null >> $OUT || echo "No evaluation scripts found" >> $OUT
echo "" >> $OUT

echo "## 📦 Datasets" >> $OUT
find data -maxdepth 3 -type d 2>/dev/null >> $OUT || echo "No data directory found" >> $OUT
echo "" >> $OUT

echo "## 🔁 MLOps Components" >> $OUT
[ -d .dvc ] && echo "✔ DVC initialized" >> $OUT || echo "✘ DVC missing" >> $OUT
[ -f mlflow.db ] && echo "✔ MLflow DB found" >> $OUT || echo "✘ MLflow DB missing" >> $OUT
rg -n "mlflow" "${CODE_DIRS[@]}" 2>/dev/null >> $OUT || true
echo "" >> $OUT

echo "## ⚙️ Async / Workers" >> $OUT
rg -n "celery" "${CODE_DIRS[@]}" 2>/dev/null >> $OUT || echo "Celery not detected" >> $OUT
rg -n "BackgroundTasks" "${CODE_DIRS[@]}" 2>/dev/null >> $OUT || true
echo "" >> $OUT

echo "## 🧩 Multimodal / Fusion" >> $OUT
[ -d app/fusion ] && echo "✔ Fusion module exists" >> $OUT || echo "✘ Fusion module missing" >> $OUT
[ -d app/models/fusion ] && echo "✔ Fusion models exist" >> $OUT || echo "✘ Fusion models missing" >> $OUT
rg -n "fusion" app 2>/dev/null >> $OUT || true
echo "" >> $OUT

echo "## 🔍 Monitoring & Drift" >> $OUT
[ -d monitoring ] && echo "✔ Monitoring directory exists" >> $OUT || echo "✘ Monitoring missing" >> $OUT
[ -d app/monitoring ] && echo "✔ app/monitoring exists" >> $OUT || echo "✘ app/monitoring missing" >> $OUT
rg -n "drift" app/monitoring monitoring 2>/dev/null >> $OUT || true
echo "" >> $OUT

echo "## 🔐 Security & Auth" >> $OUT
rg -n "JWT" "${CODE_DIRS[@]}" 2>/dev/null >> $OUT || true
rg -n "auth" app 2>/dev/null >> $OUT || true
echo "" >> $OUT

echo "## 🐳 Docker & Deployment" >> $OUT
ls Dockerfile* >> $OUT 2>/dev/null || echo "No Dockerfile found" >> $OUT
ls docker-compose*.yml >> $OUT 2>/dev/null
echo "" >> $OUT

echo "## 🧠 TODO / FIXME Markers" >> $OUT
rg -n "TODO|FIXME" "${CODE_DIRS[@]}" 2>/dev/null >> $OUT || echo "No TODOs found" >> $OUT
echo "" >> $OUT

echo "## ✅ SUMMARY" >> $OUT
echo "- Backend:" >> $OUT
[ -d app/api ] && echo "  ✔ API layer present" >> $OUT || echo "  ✘ API layer missing" >> $OUT
[ -d app/agent ] && echo "  ✔ Agent/orchestrator present" >> $OUT || echo "  ✘ Agent missing" >> $OUT
[ -d models ] && echo "  ✔ Models directory present" >> $OUT || echo "  ✘ Models missing" >> $OUT

echo "" >> $OUT
echo "📌 End of report." >> $OUT

echo "✅ PROJECT AUDIT COMPLETE"
echo "📄 Output saved to: $OUT"
