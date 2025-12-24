# Streamlit Runtime Errors (Common)

**App:** OmniChat Unified Streamlit Interface  
**File:** `app/streamlit_chatbot/omnichat_unified.py`  
**Last Updated:** December 17, 2025

> Note: This document is a historical troubleshooting list from the UI hardening phase.

---

## 🔥 MOST COMMON ERRORS

### 1. "Cannot connect to backend" / Connection Refused
**Frequency:** Very High  
**Error Message:**
```
❌ Connection Error: Cannot reach backend server
```

**Causes:**
- Backend server not running
- Wrong backend URL in environment variable
- Firewall blocking connection
- Backend crashed

**Solutions:**
```bash
# Check if backend is running
ps aux | grep python | grep main.py

# Start backend if not running
cd /path/to/project
python -m uvicorn backend.main:app --reload

# Check backend URL
echo $OMNICHATX_BACKEND

# Set correct URL
export OMNICHATX_BACKEND="http://localhost:8000"

# Test backend directly
curl http://localhost:8000/health
```

---

### 2. "Request timed out" / Timeout Error
**Frequency:** High  
**Error Message:**
```
⏱️ Timeout: Request took too long
```

**Causes:**
- Large file uploads (videos >50MB)
- Slow backend processing
- Network latency
- Backend overloaded

**Solutions:**
```bash
# Check file sizes before upload
ls -lh video.mp4

# Compress large files
ffmpeg -i input.mp4 -vcodec h264 -acodec aac output.mp4

# Increase timeout in code (temporary)
# In omnichat_unified.py line 730:
# timeout=240.0  # 4 minutes instead of 2

# Check backend performance
curl -w "@curl-format.txt" http://localhost:8000/api/chat
```

---

### 3. "File too large" / 413 Error
**Frequency:** Medium  
**Error Message:**
```
❌ File Too Large: Your upload exceeds maximum size
```

**Causes:**
- Video file >100MB
- Image file >10MB
- Backend has smaller limit than Streamlit

**Solutions:**
```bash
# Check file size
du -h myfile.mp4

# Compress video
ffmpeg -i input.mp4 -vcodec h264 -crf 28 output.mp4

# Compress image
convert input.jpg -quality 85 -resize 1920x1080 output.jpg

# Or use online tools:
# - https://tinypng.com/ (images)
# - https://www.videosmaller.com/ (videos)
```

---

### 4. Streamlit Won't Start / Port Already in Use
**Frequency:** Medium  
**Error Message:**
```
OSError: [Errno 48] Address already in use
```

**Causes:**
- Another Streamlit instance running
- Port 8502 occupied by another process

**Solutions:**
```bash
# Find process using port
lsof -i :8502

# Kill the process
kill -9 <PID>

# Or use different port
streamlit run app/streamlit_chatbot/omnichat_unified.py --server.port=8503

# Find all streamlit processes
ps aux | grep streamlit

# Kill all streamlit
pkill -f streamlit
```

---

### 5. "Module not found" / Import Error
**Frequency:** Medium  
**Error Message:**
```
ModuleNotFoundError: No module named 'streamlit'
```

**Causes:**
- Wrong Python environment
- Dependencies not installed
- Virtual environment not activated

**Solutions:**
```bash
# Check Python version
python --version  # Should be 3.11+

# Activate virtual environment
source .venv-macos/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep streamlit

# Install specific packages
pip install streamlit requests Pillow
```

---

### 6. Camera Not Working
**Frequency:** Medium  
**Error Message:**
```
Camera access denied
```

**Causes:**
- Browser doesn't have camera permission
- HTTPS required for camera (in some browsers)
- Camera in use by another app

**Solutions:**
```bash
# Check browser permissions (Chrome):
# chrome://settings/content/camera

# Use HTTPS (for production)
streamlit run app.py --server.enableCORS=false \
  --server.sslCertFile=cert.pem \
  --server.sslKeyFile=key.pem

# Check camera access on macOS
# System Preferences > Security & Privacy > Camera

# Close other apps using camera
# (Zoom, Teams, etc.)
```

---

### 7. Session State Not Persisting
**Frequency:** Low  
**Symptoms:**
- Messages disappear after reload
- Attachments lost
- Settings reset

**Causes:**
- Browser cookies disabled
- Incognito/Private mode
- Page hard refresh (Cmd+Shift+R)
- Streamlit cache cleared

**Solutions:**
```python
# Save to browser localStorage (add to app)
import streamlit.components.v1 as components

components.html(f"""
<script>
localStorage.setItem('omnichat_session', '{st.session_state.omni_session_id}');
</script>
""")

# Or use Streamlit's cache
@st.cache_data
def load_session():
    return {...}

# Or save to file
import json
with open('session.json', 'w') as f:
    json.dump(st.session_state.omni_messages, f)
```

---

### 8. "Invalid JSON response" / Parsing Error
**Frequency:** Low  
**Error Message:**
```
ValueError: Invalid response format
```

**Causes:**
- Backend returned HTML instead of JSON
- Backend error page
- Nginx/proxy returning error page
- Backend crashed mid-response

**Solutions:**
```python
# Add response validation
try:
    resp = requests.post(...)
    content_type = resp.headers.get('content-type', '')
    
    if 'application/json' not in content_type:
        st.error(f"Backend returned {content_type}, expected JSON")
        st.code(resp.text[:500])
        st.stop()
    
    return resp.json()
except ValueError as e:
    st.error(f"Invalid JSON: {e}")
    st.code(resp.text[:500])
```

---

### 9. Slow Performance / UI Freezing
**Frequency:** Low  
**Symptoms:**
- App becomes unresponsive
- Spinner runs forever
- High CPU usage

**Causes:**
- Large session state
- Too many messages in history
- Memory leak from attachments
- Inefficient reruns

**Solutions:**
```python
# Limit message history
MAX_MESSAGES = 100
if len(st.session_state.omni_messages) > MAX_MESSAGES:
    st.session_state.omni_messages = st.session_state.omni_messages[-MAX_MESSAGES:]

# Clear old attachments
def cleanup_attachments():
    if len(st.session_state.omni_messages) > 50:
        for msg in st.session_state.omni_messages[:-50]:
            if 'attachment_bytes' in msg:
                del msg['attachment_bytes']

# Use pagination
page = st.selectbox("Page", range(1, total_pages))
display_messages = messages[page*10:(page+1)*10]

# Profile performance
import cProfile
cProfile.run('st.rerun()')
```

---

### 10. XSS / Security Warning
**Frequency:** Very Low  
**Error Message:**
```
WARNING: Potential XSS detected
```

**Causes:**
- User input contains `<script>` tags
- Unsafe HTML rendering
- Malicious file upload

**Solutions:**
```python
import html
import re

# Sanitize user input
def sanitize_input(text: str) -> str:
    # Remove script tags
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove event handlers
    text = re.sub(r'\son\w+\s*=', '', text, flags=re.IGNORECASE)
    
    # Escape HTML
    text = html.escape(text)
    
    return text

# Use it
user_text = sanitize_input(prompt)
```

---

## 🔍 DEBUGGING GUIDE

### Step 1: Check Logs
```bash
# Streamlit logs
streamlit run app.py --log_level=debug 2>&1 | tee streamlit.log

# Backend logs
tail -f backend.log

# System logs (macOS)
log show --predicate 'process == "Python"' --last 5m
```

### Step 2: Test Backend Separately
```bash
# Health check
curl http://localhost:8000/health

# Test chat endpoint
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "user_id": "123"}'

# Test with file
curl -X POST http://localhost:8000/api/chat/multimodal \
  -F "message=test" \
  -F "image=@test.jpg"
```

### Step 3: Check Environment
```bash
# Python version
python --version

# Installed packages
pip list

# Environment variables
env | grep OMNICHAT

# Network connectivity
ping localhost
curl -v http://localhost:8000
```

### Step 4: Enable Debug Mode
```python
# Add to omnichat_unified.py
import os
os.environ['DEBUG_MODE'] = 'true'

# This will show:
# - Full API responses
# - Session state
# - Error tracebacks
```

### Step 5: Browser Console
```javascript
// Open browser console (F12)
// Check for errors
console.log('Streamlit loaded:', typeof Streamlit);

// Check WebSocket
console.log('WebSocket state:', Streamlit.WebSocket.readyState);

// Clear cache
localStorage.clear();
sessionStorage.clear();
location.reload();
```

---

## 📊 ERROR FREQUENCY TABLE

| Error | Frequency | Severity | Fix Time |
|-------|-----------|----------|----------|
| Connection refused | 40% | High | 2 min |
| Timeout | 25% | Medium | 5 min |
| File too large | 15% | Low | 1 min |
| Port in use | 10% | Low | 1 min |
| Module not found | 5% | Medium | 5 min |
| Camera issues | 3% | Low | Varies |
| Session state | 1% | Low | N/A |
| JSON parsing | 0.5% | Medium | 10 min |
| Performance | 0.4% | Low | Varies |
| XSS | 0.1% | Medium | 5 min |

---

## 🛠️ QUICK FIXES CHEATSHEET

```bash
# Restart everything
pkill -f streamlit
pkill -f uvicorn
source .venv-macos/bin/activate
python -m uvicorn backend.main:app --reload &
sleep 5
streamlit run app/streamlit_chatbot/omnichat_unified.py --server.port=8502

# Clear all caches
rm -rf ~/.streamlit/
rm -rf __pycache__/
find . -type d -name "__pycache__" -exec rm -r {} +

# Reset virtual environment
deactivate
rm -rf .venv-macos
python3 -m venv .venv-macos
source .venv-macos/bin/activate
pip install -r requirements.txt

# Check ports
lsof -i :8000  # Backend
lsof -i :8502  # Streamlit

# Test minimal setup
python -c "import streamlit; print(streamlit.__version__)"
python -c "import requests; print(requests.get('http://localhost:8000/health').json())"
```

---

## 📞 TROUBLESHOOTING FLOWCHART

```
Error occurs
    ↓
Is Streamlit running?
    NO → Start Streamlit
    YES ↓
        Is Backend running?
            NO → Start Backend
            YES ↓
                Can you reach backend?
                    NO → Check network/firewall
                    YES ↓
                        Is file too large?
                            YES → Compress file
                            NO ↓
                                Check logs
                                    ↓
                                Found error?
                                    YES → Apply fix from above
                                    NO → Enable debug mode
```

---

## 🎯 PREVENTION CHECKLIST

Before starting the app:
- [ ] Virtual environment activated
- [ ] Backend running and healthy
- [ ] Port 8502 available
- [ ] Environment variables set
- [ ] Dependencies installed
- [ ] Logs directory exists
- [ ] File size limits known
- [ ] Browser has camera permission (if needed)

---

## 📚 ADDITIONAL RESOURCES

- **Streamlit Docs:** https://docs.streamlit.io/
- **Debugging Guide:** https://docs.streamlit.io/knowledge-base/deploy/remote-start
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **Project Issues:** Check STREAMLIT_ERROR_ANALYSIS.md

---

**Last Updated:** December 17, 2025  
**Maintainer:** System Analysis
