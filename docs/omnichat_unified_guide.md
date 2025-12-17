# 🧠 OmniChat Pratik - Unified AI Assistant

A comprehensive ChatGPT-style interface that integrates all UAIS-V capabilities into one seamless experience.

## 🎯 Features

### Core Capabilities
- **💳 Fraud Detection** - Real-time transaction fraud scoring
- **🔐 Cyber Security** - Network threat and intrusion detection
- **🎭 Behavior Analysis** - User behavior profiling and anomaly detection
- **📸 Vision Analysis** - Image classification and object detection
- **🎥 Video Analysis** - Video content analysis and frame extraction
- **🗣️ Voice Emotion AI** - Emotion detection from audio/speech
- **🎬 Recommendations** - Personalized movie, product, and content suggestions
- **📚 Document Q&A** - RAG-powered document chat
- **🤖 AI Agent** - Intelligent conversational assistant

### Interface Features
- **ChatGPT-like Layout** - Familiar and intuitive chat interface
- **Bluish-Gray Theme** - Modern, professional color scheme
- **Multi-modal Input** - Text, image, audio, and video support
- **Real-time Analysis** - Instant results with streaming responses
- **Session Management** - Persistent conversation history
- **Attachment Preview** - Visual feedback for uploaded media
- **Responsive Design** - Works on desktop and mobile devices

## 🚀 Quick Start

### Option 1: Launch Script (Recommended)
```bash
# From project root
./launch_omnichat.sh
```

### Option 2: Direct Streamlit Run
```bash
# Activate virtual environment
source .venv-macos/bin/activate

# Set backend URL (optional)
export OMNICHATX_BACKEND="http://localhost:8000"

# Launch the app
streamlit run app/streamlit_chatbot/omnichat_unified.py
```

### Option 3: Via Main App
```bash
streamlit run app/streamlit_chatbot/app.py
# Then select "🧠 OmniChat Pratik (All-in-One)" tab
```

## 📋 Prerequisites

### Backend Server
Make sure the UAIS-V backend is running:
```bash
# Terminal 1: Start backend
uvicorn app.main:app --reload --port 8000
```

### Environment Variables
```bash
# Backend URL (default: http://localhost:8000)
export OMNICHATX_BACKEND="http://localhost:8000"

# Optional: Authentication token
export AUTH_TOKEN="your-token-here"
```

## 🎨 Interface Overview

### Header
- **OmniChat Pratik** branding with gradient effect
- Feature indicators showing all capabilities

### Sidebar
- **⚙️ Settings**
  - Toggle RAG (Retrieval-Augmented Generation)
  - Enable/disable vision analysis
  - Enable/disable voice emotion detection
  - Enable/disable risk detection
  - Enable/disable recommendations

- **📊 Statistics**
  - Total messages count
  - User queries count

- **🎨 Features**
  - Complete list of available capabilities

- **🗑️ Actions**
  - Clear chat history
  - Start new session
  - Session ID display

### Main Chat Area
- **Welcome Screen** - Shown when no messages exist
- **Message Bubbles** - ChatGPT-style user/assistant messages
- **Typing Indicator** - Animated dots while processing
- **Attachment Badges** - Visual indicators for media attachments

### Input Section
- **📎 Attach Media** - Expandable section with tabs:
  - **📷 Camera/Image** - Take photo or upload image
  - **🎤 Audio/Voice** - Record or upload audio
  - **🎥 Video** - Upload video files

- **📌 Current Attachments** - Preview of attached media with remove buttons
- **💬 Message Input** - Chat input field with send button

## 🔧 Usage Examples

### Text Chat
```
You: What's the fraud risk for this transaction amount of $5000?
OmniChat: Analyzing... [Returns fraud score and risk level]
```

### Image Analysis
1. Click "📎 Attach Media"
2. Upload an image or take a photo
3. Type your question: "What objects are in this image?"
4. Send message

### Voice Emotion Detection
1. Click "📎 Attach Media"
2. Record audio or upload an audio file
3. Type: "Analyze the emotion in this voice"
4. Send message

### Multi-modal Query
1. Attach both image and audio
2. Type: "Analyze both the image and voice emotion"
3. Receive comprehensive analysis

### Get Recommendations
```
You: Recommend me some sci-fi movies
OmniChat: [Returns personalized movie recommendations]

You: Show me laptops under $1000
OmniChat: [Returns product recommendations]
```

## 📊 Response Format

The assistant provides structured responses including:

### Risk Analysis
```
Fraud Risk: 🟢 LOW (12%)
Cyber Threat: 🟡 MEDIUM (45%)
Behavior: ✅ NORMAL (18%)
```

### Emotion Detection
```
Voice Emotion: Happy (87.5% confidence)
```

### Vision Analysis
```
Vision: Cat (94.2%)
Objects Detected: cat, sofa, plant, window
```

### Recommendations
```
🎯 Recommendations:
1. Inception (2010) - Mind-bending thriller
2. The Matrix (1999) - Cyberpunk classic
3. Interstellar (2014) - Space epic
```

## 🎨 Theme Customization

The interface uses a bluish-gray color scheme:
- **Primary Blue**: `#3b82f6`
- **Dark Background**: `#1a252f`
- **Secondary Background**: `#1e3a5f`
- **Accent Colors**: Blue gradients

### Color Variables
- Backgrounds: Dark gradients (navy to black)
- User messages: Blue gradient bubble
- Assistant messages: Gray translucent bubble
- Buttons: Blue gradient with hover effects
- Borders: Semi-transparent blue

## 🔍 Technical Details

### Architecture
- **Frontend**: Streamlit with custom CSS
- **Backend**: FastAPI (UAIS-V backend)
- **Communication**: REST API with multipart/form-data support
- **State Management**: Streamlit session state

### API Endpoints Used
- `/api/chat` - Text-only chat
- `/api/chat/multimodal` - Multi-modal (image/audio/video + text)
- `/api/fraud` - Fraud detection
- `/api/cyber` - Cyber threat analysis
- `/api/behavior` - Behavior scoring
- `/api/vision/*` - Vision analysis
- `/api/audio/*` - Audio emotion detection
- `/api/recommend/*` - Recommendation engine

### File Structure
```
app/streamlit_chatbot/
├── omnichat_unified.py      # Main unified interface
├── app.py                    # Multi-tab launcher
├── chatgpt_style.py          # Original ChatGPT-style tab
├── ui/
│   └── theme.py              # Shared theme utilities
└── pages/
    ├── command_center.py     # Recommendations
    ├── live.py               # Live camera/mic
    └── voice_chat.py         # Voice chat
```

## 🐛 Troubleshooting

### Backend Connection Issues
```bash
# Check if backend is running
curl http://localhost:8000/health

# Set correct backend URL
export OMNICHATX_BACKEND="http://localhost:8000"
```

### Port Already in Use
```bash
# Use a different port
streamlit run app/streamlit_chatbot/omnichat_unified.py --server.port=8502
```

### Media Upload Errors
- Ensure file formats are supported:
  - Images: PNG, JPG, JPEG, WebP
  - Audio: WAV, MP3, M4A, OGG, AAC
  - Video: MP4, MOV, AVI, MKV

### Performance Issues
- Reduce video resolution before uploading
- Use smaller audio files
- Clear chat history if it gets too long

## 📝 Development

### Adding New Features
1. Add toggle in sidebar settings
2. Add corresponding API call in message processing
3. Add result formatting in response handler

### Customizing Styling
Edit the CSS in `render_omnichat_unified()` function:
```python
st.markdown("""
<style>
/* Your custom CSS here */
</style>
""", unsafe_allow_html=True)
```

## 🤝 Integration with Other Components

The unified interface integrates with:
- **Fraud Detection Models** - Transaction scoring
- **Cyber Threat Models** - Network analysis
- **Behavior Analysis** - User profiling
- **Vision Models** - YOLOv8, ResNet, etc.
- **Audio Emotion** - Librosa + ML models
- **RAG System** - Document embedding and retrieval
- **Recommender Systems** - Collaborative filtering

## 📚 Related Documentation

- [API Documentation](../../docs/api_streamlit_notes.md)
- [Architecture Overview](../../docs/architecture.md)
- [Component Orchestrator](../../docs/component_orchestrator.md)
- [Technical Brief](../../docs/UAISV_technical_brief.md)

## 🎯 Roadmap

- [ ] Dark/light theme toggle
- [ ] Export chat to PDF/Markdown
- [ ] Voice input/output (STT/TTS)
- [ ] Real-time collaboration
- [ ] Custom model selection
- [ ] Advanced filters and search
- [ ] Mobile app version
- [ ] Browser extension

## 📄 License

Part of the Universal Anomaly Intelligence System V2 (UAIS-V)

---

**Built with ❤️ by Pratik**

For issues or feature requests, please contact the development team.
