import os
from typing import Dict, List, Optional

try:
    import google.generativeai as genai
except ImportError:
    genai = None


class GeminiClient:
    """Wrapper for Google's Gemini API."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-1.5-flash"):
        if not genai:
            raise ImportError(
                "google-generativeai package is not installed. Run `pip install google-generativeai`."
            )

        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)

    def generate(self, prompt: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        """Generate text response."""
        try:
            # Construct chat history for context if provided
            chat_history = []
            if history:
                for turn in history:
                    user_text = turn.get("user")
                    assistant_text = turn.get("assistant")
                    if user_text:
                        chat_history.append({"role": "user", "parts": [user_text]})
                    if assistant_text:
                        chat_history.append({"role": "model", "parts": [assistant_text]})

            # Start chat session with history
            chat = self.model.start_chat(history=chat_history)
            response = chat.send_message(prompt)
            return response.text
        except Exception as e:
            return f"Gemini API Error: {str(e)}"
