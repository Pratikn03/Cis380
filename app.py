import streamlit as st
import requests
from PIL import Image, ImageDraw
import io
import librosa
import numpy as np
import os

DEFAULT_BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001")

def analyze_uploaded_file(uploaded_file, backend_url):
    """Sends the uploaded file to the appropriate backend endpoint."""
    # Reset pointer to beginning of file
    uploaded_file.seek(0)
    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
    
    if uploaded_file.type == "application/pdf":
        file_type = "pdf"
    else:
        file_type = uploaded_file.type.split("/")[0]
        
    try:
        response = None
        if file_type == "image":
            response = requests.post(f"{backend_url}/detect-anomalies", files=files)
        elif file_type == "audio":
            response = requests.post(f"{backend_url}/analyze-audio", files=files)
        elif file_type == "pdf":
            response = requests.post(f"{backend_url}/analyze-text", files=files)
        
        if response and response.status_code == 200:
            return response.json(), None, file_type
        else:
            error_msg = f"I encountered an error connecting to the brain. Status: {response.status_code if response else 'Unknown'}"
            if response:
                error_msg += f"\nDetail: {response.text}"
            return None, error_msg, file_type
            
    except Exception as e:
        return None, f"Connection failed: {str(e)}. Is the backend running on {backend_url}?", file_type

def get_recommendation(context, backend_url):
    """Fetches recommendation from the backend."""
    try:
        rec_res = requests.post(f"{backend_url}/recommend", json={"context": context})
        if rec_res.status_code == 200:
            return rec_res.json().get("recommendation", "")
    except Exception:
        pass
    return ""

def check_backend_status(url):
    """Checks if the backend is reachable."""
    try:
        response = requests.get(f"{url}/docs", timeout=1)
        return response.status_code == 200
    except:
        return False

# Page Config
st.set_page_config(
    page_title="Universal Anomaly Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Gemini-like styling
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #FFFFFF;
        color: #1F1F1F;
    }
    
    /* Chat messages container */
    .stChatMessage {
        background-color: transparent;
        border: none;
    }
    
    /* User message bubble */
    div[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #F0F4F9;
        border-radius: 20px;
        padding: 15px;
        margin-bottom: 10px;
    }

    /* Assistant message bubble */
    div[data-testid="stChatMessage"]:nth-child(even) {
        background-color: #FFFFFF;
        padding: 15px;
        margin-bottom: 10px;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #F0F4F9;
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 20px;
        background-color: #1a73e8;
        color: white;
        border: none;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Backend URL in Session State
if "backend_url" not in st.session_state:
    st.session_state.backend_url = DEFAULT_BACKEND_URL
backend_url = st.session_state.backend_url

# Sidebar Configuration
with st.sidebar:
    st.title("PN Pratik Niroula")
    st.caption("ML Engineer")
    
    st.markdown("**Core Skills**")
    st.caption("Python | React | ML/AI | FastAPI | Docker")
    
    st.markdown("---")
    
    # Navigation
    st.subheader("AI Chat")
    nav_options = ["AI Chat", "Docs (DSA)", "Vision", "Brand (YOLO)", "Outfits", "Audio", "Video", "Fraud", "Cyber", "Behavior"]
    active_tool = st.radio("Select Tool", nav_options, label_visibility="collapsed")
    
    st.markdown("---")
    
    # Connection Settings
    st.caption("Backend URL")
    url_input = st.text_input("Backend URL", value=st.session_state.get("backend_url", DEFAULT_BACKEND_URL), label_visibility="collapsed")
    
    if url_input != st.session_state.get("backend_url"):
        st.session_state.backend_url = url_input.rstrip("/")
        st.rerun()

    if check_backend_status(st.session_state.backend_url):
        st.success("Connected")
    else:
        st.error("Disconnected")
    
    st.markdown("---")
    rag_on = st.toggle("RAG On", value=True)
    dsa_mode = st.toggle("DSA Mode On", value=False)
    
    st.markdown("---")
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# Main Chat Interface
st.title(active_tool)
st.caption("Unified chat with built-in tools plus offline-first DSA RAG when enabled.")

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Handle Recommendation Trigger from Tags
if "recommend_trigger" in st.session_state:
    tag = st.session_state.pop("recommend_trigger")
    st.session_state.messages.append({"role": "user", "content": f"Give me recommendations for: {tag}"})
    
    try:
        with st.spinner(f"Generating recommendations for {tag}..."):
            rec_res = requests.post(f"{backend_url}/recommend", json={"context": tag})
            if rec_res.status_code == 200:
                rec_text = rec_res.json().get("recommendation", "")
                st.session_state.messages.append({"role": "assistant", "content": f"💡 **Recommendations for {tag}:**\n\n{rec_text}"})
            else:
                st.session_state.messages.append({"role": "assistant", "content": "Sorry, I couldn't fetch recommendations."})
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")

# Display Chat History
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "image" in message and message["image"] is not None:
            st.image(message["image"], caption="Analyzed Image", width=400)
        if "json" in message:
            with st.expander("View Raw Analysis Data"):
                st.json(message["json"])
        
        # Display Tags
        if "tags" in message and message["tags"]:
            st.markdown("**Select an object for specific recommendations:**")
            tags = message["tags"]
            cols = st.columns(min(len(tags), 4)) if len(tags) > 0 else []
            for idx, tag in enumerate(tags):
                if cols and cols[idx % len(cols)].button(f"🏷️ {tag}", key=f"tag_{i}_{idx}"):
                    st.session_state["recommend_trigger"] = tag
                    st.rerun()
        
        # Copy to Clipboard
        if message["role"] == "assistant":
            with st.expander("Copy Response"):
                st.code(message["content"], language=None)
    
    # Regenerate Button for the last assistant message
    if i == len(st.session_state.messages) - 1 and message["role"] == "assistant":
        if st.button("🔄 Regenerate", key="regenerate_last"):
            # Determine context from the previous user message
            if i > 0:
                last_user_msg = st.session_state.messages[i-1]
                user_content = last_user_msg["content"]
                
                if user_content.startswith("Analyze this file:"):
                    st.session_state["trigger_analysis"] = True
                    st.session_state.messages.pop() # Remove last assistant response
                    st.rerun()
                elif user_content.startswith("Give me recommendations for:"):
                    tag = user_content.split(": ")[1]
                    st.session_state["recommend_trigger"] = tag
                    st.session_state.messages.pop() # Remove last assistant response
                    st.rerun()

# Input Area
uploaded_file = None

if active_tool in ["Vision", "Brand (YOLO)", "Outfits"]:
    uploaded_file = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])
elif active_tool == "Audio":
    tab1, tab2 = st.tabs(["📁 Upload File", "🎙️ Record Audio"])
    with tab1:
        uploaded_file = st.file_uploader("Upload Audio", type=["wav", "mp3"])
    with tab2:
        uploaded_file = st.audio_input("Record voice note")
elif active_tool == "Docs (DSA)":
    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

# File Analysis Logic
if uploaded_file:
    # Action Button
    analyze_clicked = st.button("Analyze Content", type="primary")
    if analyze_clicked or st.session_state.get("trigger_analysis", False):
        st.session_state["trigger_analysis"] = False

        if uploaded_file.type == "application/pdf":
            file_type = "pdf"
        else:
            file_type = uploaded_file.type.split("/")[0]
        
        # 1. Display User Message immediately
        with st.chat_message("user"):
            st.write(f"Analyze this file: `{uploaded_file.name}`")
            if file_type == "image":
                image = Image.open(uploaded_file)
                st.image(image, width=300)
            elif file_type == "audio":
                st.audio(uploaded_file)
            elif file_type == "pdf":
                st.markdown("📄 **PDF Document**")
        
        # Add to history
        st.session_state.messages.append({
            "role": "user",
            "content": f"Analyze this file: `{uploaded_file.name}`",
            "image": image if file_type == "image" else None
        })

        # 2. Process with Backend
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("Thinking...")
            
            data, error_msg, file_type = analyze_uploaded_file(uploaded_file, backend_url)
            
            if data:
                try:
                    
                    tags = []
                    # Formulate a natural language response
                    if file_type == "image":
                        anomalies = data.get("anomalies", [])
                        emotions = data.get("emotions", [])
                        tags = list(set([a['type'] for a in anomalies]))
                        
                        summary = f"I analyzed **{data.get('filename', 'the image')}**.\n\n"
                        
                        if anomalies:
                            summary += f"**Detected Objects:** {', '.join([a['type'] for a in anomalies])}.\n"
                            # Draw bounding boxes
                            img_copy = image.copy()
                            draw = ImageDraw.Draw(img_copy)
                            for a in anomalies:
                                bbox = a["bbox"]
                                # Draw rectangle
                                draw.rectangle(bbox, outline="red", width=3)
                                # Draw text background
                                text_pos = (bbox[0], max(0, bbox[1] - 20))
                                draw.text(text_pos, f"{a['type']} {a['confidence']}", fill="red")
                            
                            st.image(img_copy, caption="Detected Anomalies", width=400)
                        else:
                            summary += "No specific anomalies or objects detected.\n"
                            
                        if emotions:
                            top_emotion = emotions[0]
                            summary += f"\n**Dominant Emotion:** {top_emotion['label']} ({top_emotion['confidence']*100:.1f}%)."
                        
                    elif file_type == "audio":
                        transcription = data.get("transcription", "")
                        lang = data.get("language", "unknown")
                        emotions = data.get("emotions", [])
                        
                        summary = f"I listened to the audio. It appears to be in **{lang}**.\n\n**Transcription:**\n> {transcription}"
                        
                        if emotions:
                            top_emotion = emotions[0]
                            summary += f"\n\n**Dominant Emotion:** {top_emotion['label']} ({top_emotion['score']*100:.1f}%)"
                            st.bar_chart({e['label']: e['score'] for e in emotions})
                        
                        # Visualize Waveform
                        try:
                            uploaded_file.seek(0)
                            y, sr = librosa.load(uploaded_file, sr=16000)
                            st.markdown("**Audio Waveform:**")
                            st.line_chart(y[::50])
                        except Exception as e:
                            st.error(f"Error visualizing waveform: {e}")
                        
                        # Download Transcription
                        st.download_button(
                            label="Download Transcription",
                            data=transcription,
                            file_name=f"{data.get('filename')}_transcription.txt",
                            mime="text/plain"
                        )

                    elif file_type == "pdf":
                        content = data.get("content", "")
                        st.session_state["active_pdf"] = data.get("filename")
                        summary_text = data.get("summary", "")
                        
                        if summary_text:
                            summary = f"I analyzed the PDF **{data.get('filename')}**.\n\n**Summary:**\n> {summary_text}\n\n**Extracted Content Preview:**\n> {content[:500]}..."
                        else:
                            preview = content[:1000] + "..." if len(content) > 1000 else content
                            summary = f"I analyzed the PDF **{data.get('filename')}**.\n\n**Extracted Content:**\n> {preview}"
                        
                        # Download Extracted Text
                        st.download_button(
                            label="Download Extracted Text",
                            data=content,
                            file_name=f"{data.get('filename')}.txt",
                            mime="text/plain"
                        )
                    
                    # Generate Recommendation
                    try:
                        context_str = "General situation"
                        if file_type == "image":
                            if anomalies:
                                context_str = f"{anomalies[0]['type']} detected"
                            elif emotions:
                                context_str = f"{emotions[0]['label']} expression"
                        elif file_type == "audio":
                            context_str = "Audio recording analyzed"
                            if 'emotions' in data and data['emotions']:
                                context_str += f" with {data['emotions'][0]['label']} tone"
                        elif file_type == "pdf":
                            context_str = "Document content analyzed"
                            
                        rec_text = get_recommendation(context_str, backend_url)
                        if rec_text:
                            summary += f"\n\n💡 **Recommendation:** {rec_text}"
                    except Exception as e:
                        print(f"Recommendation error: {e}")

                    message_placeholder.markdown(summary)
                    
                    # Add to history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": summary,
                        "json": data,
                        "tags": tags
                    })
                    
                except Exception as e:
                    message_placeholder.error(f"Error processing response: {str(e)}")
            else:
                message_placeholder.error(error_msg)

# Chat Input (Text)
if prompt := st.chat_input("Type your message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        
        response_text = ""
        try:
            # Context-aware routing
            if active_tool == "Docs (DSA)" and "active_pdf" in st.session_state:
                # Use PDF QA if in Docs mode and PDF is loaded
                payload = {"filename": st.session_state["active_pdf"], "question": prompt}
                res = requests.post(f"{backend_url}/ask-pdf", json=payload)
                if res.status_code == 200:
                    response_text = res.json().get("answer", "No answer found.")
                else:
                    response_text = f"Error: {res.text}"
            else:
                # General Chat / Recommendation
                res = requests.post(f"{backend_url}/recommend", json={"context": prompt})
                if res.status_code == 200:
                    response_text = res.json().get("recommendation", "")
                else:
                    response_text = "I couldn't generate a response."
        except Exception as e:
            response_text = f"Connection error: {e}"
            
        message_placeholder.markdown(response_text)
        st.session_state.messages.append({"role": "assistant", "content": response_text})

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: grey;">
    © 2026 Pratik Niroula. All rights reserved.
</div>
""", unsafe_allow_html=True)