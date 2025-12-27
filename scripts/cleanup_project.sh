#!/bin/bash
# cleanup_project.sh - Comprehensive project cleanup
# Safe operations that won't break the project

set -e

echo "🧹 Starting Safe Project Cleanup..."
echo ""

# 1. Remove Python cache files
echo "📦 Cleaning Python cache files..."
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type d -name "__pycache__" -not -path "./.venv*/*" -not -path "./venv/*" -exec rm -rf {} + 2>/dev/null || true
echo "✅ Removed Python cache files"
echo ""

# 2. Remove macOS system files
echo "🍎 Removing macOS system files..."
find . -name ".DS_Store" -delete 2>/dev/null || true
echo "✅ Removed .DS_Store files"
echo ""

# 3. Remove untitled notebooks
echo "📓 Removing untitled notebooks..."
find . -name "Untitled*.ipynb" -not -path "./.venv*/*" -delete 2>/dev/null || true
find . -name "*-checkpoint.ipynb" -delete 2>/dev/null || true
echo "✅ Removed temporary notebooks"
echo ""

# 4. Organize documentation (safe moves)
echo "📚 Organizing documentation..."
mkdir -p docs/fixes docs/guides

# Only move if files exist
[ -f "EMOTION_DETECTION_FIX.md" ] && mv EMOTION_DETECTION_FIX.md docs/fixes/
[ -f "FIXES_APPLIED_SUMMARY.md" ] && mv FIXES_APPLIED_SUMMARY.md docs/fixes/
[ -f "STREAMLIT_CRITICAL_FIXES.md" ] && mv STREAMLIT_CRITICAL_FIXES.md docs/fixes/
[ -f "STREAMLIT_ERROR_ANALYSIS.md" ] && mv STREAMLIT_ERROR_ANALYSIS.md docs/fixes/
[ -f "STREAMLIT_RUNTIME_ERRORS.md" ] && mv STREAMLIT_RUNTIME_ERRORS.md docs/fixes/
[ -f "STREAMLIT_COMPLETE.md" ] && mv STREAMLIT_COMPLETE.md docs/guides/
[ -f "STREAMLIT_INSTALLATION.md" ] && mv STREAMLIT_INSTALLATION.md docs/guides/
[ -f "project_summary.md" ] && mv project_summary.md docs/
[ -f "PROJECT_STATUS.md" ] && mv PROJECT_STATUS.md docs/

echo "✅ Organized documentation into docs/"
echo ""

# 5. Add .gitkeep to important empty directories
echo "📂 Preserving important directory structure..."
mkdir -p logs artifacts data/interim data/monitoring/live
touch logs/.gitkeep
touch artifacts/.gitkeep
touch data/interim/.gitkeep
touch data/monitoring/live/.gitkeep
echo "✅ Added .gitkeep files"
echo ""

# 6. Show disk space saved
echo "💾 Calculating space saved..."
echo ""

# 7. Summary
echo "🎉 Safe Cleanup Complete!"
echo ""
echo "📊 What was cleaned:"
echo "  ✅ Python cache files (__pycache__, *.pyc)"
echo "  ✅ macOS system files (.DS_Store)"
echo "  ✅ Temporary Jupyter notebooks"
echo "  ✅ Organized documentation into docs/"
echo "  ✅ Preserved directory structure with .gitkeep"
echo ""
echo "⚠️  Manual Actions Required:"
echo "  1. Review extra virtual environments:"
echo "     - .venv/"
echo "     - .venv-full/"
echo "     - .venv-sentinelforge/"
echo "     - venv/"
echo "     Consider removing all except .venv/"
echo ""
echo "  2. Review duplicate directories:"
echo "     - backend/ (re-exports app/main.py)"
echo "     - api/ (duplicates app/api/)"
echo "     - agent/ (duplicates app/agent/)"
echo "     - rag/ (duplicates app/rag/)"
echo ""
echo "  3. Update .gitignore with enhanced version"
echo "     (See PROJECT_CLEANUP_ANALYSIS.md)"
echo ""
echo "  4. Commit changes:"
echo "     git add ."
echo "     git commit -m 'chore: organize project structure and cleanup artifacts'"
echo ""
echo "📖 For detailed analysis, see: PROJECT_CLEANUP_ANALYSIS.md"
