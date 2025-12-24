"""Legacy wrapper for the Streamlit Command Center.

This repo accumulated multiple Streamlit entrypoints over time. The canonical UI
is `app/streamlit_chatbot/app.py`.

Keep this file so older docs/bookmarks still work:
  streamlit run dashboard/unified_app.py
"""

from __future__ import annotations

from app.streamlit_chatbot.app import main as command_center_main


command_center_main()

