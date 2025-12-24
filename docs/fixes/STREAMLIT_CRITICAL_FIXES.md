# Streamlit Critical Fixes (Applied & Pending)

**Date:** December 17, 2025  
**File:** `app/streamlit_chatbot/omnichat_unified.py`

---

> Note: This document is a historical checklist. Some items may already be resolved in the current codebase.

## ✅ FIXED (Applied)

### 1. Type Error in `call_get()` - FIXED ✅
**Status:** Applied  
**Line:** 962  
**Change:**
```python
# Before:
params: dict[str, object] | None = None

# After:
params: dict[str, str | int | float] | None = None
```
**Result:** Type error resolved, no more linting errors

---

## 🔴 CRITICAL - APPLY IMMEDIATELY

### 2. File Size Validation - PENDING ⚠️
**Risk:** HIGH - App crashes with large files  
**Location:** Lines 470-550

**Add this code before storing files:**

```python
# Add at top of file with imports
MAX_IMAGE_SIZE = 10 * 1024 * 1024   # 10MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB
MAX_AUDIO_SIZE = 20 * 1024 * 1024   # 20MB

# In camera input section (line ~475)
if camera_input:
    photo_bytes = camera_input.getvalue()
    if len(photo_bytes) > MAX_IMAGE_SIZE:
        st.error(f"❌ Photo too large! Max: {MAX_IMAGE_SIZE/(1024*1024):.0f}MB")
    else:
        st.session_state.omni_attached_image = photo_bytes
        st.session_state.omni_image_name = "camera_photo.jpg"
        st.success("✅ Photo captured!")

# In image upload section (line ~485)
if uploaded_image:
    img_bytes = uploaded_image.getvalue()
    if len(img_bytes) > MAX_IMAGE_SIZE:
        st.error(f"❌ Image too large! Max: {MAX_IMAGE_SIZE/(1024*1024):.0f}MB")
    else:
        st.session_state.omni_attached_image = img_bytes
        st.session_state.omni_image_name = uploaded_image.name
        st.success(f"✅ {uploaded_image.name} uploaded!")

# In video upload section (line ~530)
if uploaded_video:
    video_bytes = uploaded_video.getvalue()
    if len(video_bytes) > MAX_VIDEO_SIZE:
        st.error(f"❌ Video too large! Max: {MAX_VIDEO_SIZE/(1024*1024):.0f}MB")
    else:
        st.session_state.omni_attached_video = video_bytes
        st.session_state.omni_video_name = uploaded_video.name
        st.success(f"✅ {uploaded_video.name} uploaded!")

# In audio upload section (line ~510)
if uploaded_audio:
    audio_bytes = uploaded_audio.getvalue()
    if len(audio_bytes) > MAX_AUDIO_SIZE:
        st.error(f"❌ Audio too large! Max: {MAX_AUDIO_SIZE/(1024*1024):.0f}MB")
    else:
        st.session_state.omni_attached_audio = audio_bytes
        st.session_state.omni_audio_name = uploaded_audio.name
        st.success(f"✅ {uploaded_audio.name} uploaded!")
```

---

### 3. HTML Injection (XSS) - PENDING ⚠️
**Risk:** MEDIUM - Security vulnerability  
**Location:** Lines 280-290, 305-315

**Add this import at top:**
```python
import html
```

**Replace message display code (line ~285):**
```python
# Before:
<div style="margin-top: 6px;">{content}</div>

# After:
<div style="margin-top: 6px;">{html.escape(content)}</div>
```

**Apply to both user and assistant message rendering**

---

### 4. Better Error Handling - PENDING ⚠️
**Risk:** HIGH - Poor user experience, hard to debug  
**Location:** Lines 915-925

**Add logging import:**
```python
import logging
import traceback

logger = logging.getLogger(__name__)
```

**Replace exception handling (line ~915):**
```python
# Replace this:
except Exception as e:
    reply = f"❌ **Exception:** {str(e)}"

# With this:
except requests.ConnectionError as e:
    reply = "❌ **Connection Error:** Cannot reach the backend server. Please ensure the API is running."
    logger.error(f"Backend connection failed to {backend_url}: {e}")
except requests.Timeout as e:
    reply = "⏱️ **Timeout:** The request took too long. Try with smaller files or simpler queries."
    logger.warning(f"Request timeout after {timeout}s: {e}")
except requests.HTTPError as e:
    status_code = e.response.status_code
    if status_code == 413:
        reply = "❌ **File Too Large:** Your upload exceeds the server's maximum size limit."
    elif status_code == 500:
        reply = "❌ **Server Error:** The backend encountered an internal error. Please try again later."
    elif status_code == 404:
        reply = "❌ **Not Found:** The requested endpoint doesn't exist. Check your backend URL."
    else:
        reply = f"❌ **HTTP Error {status_code}:** {e.response.text[:200]}"
    logger.error(f"HTTP error {status_code}: {e}", exc_info=True)
except ValueError as e:
    reply = "❌ **Invalid Response:** The server returned unexpected data format."
    logger.error(f"Response parsing error: {e}", exc_info=True)
except Exception as e:
    reply = f"❌ **Unexpected Error:** {str(e)[:200]}"
    logger.error(f"Unexpected error in chat handler: {traceback.format_exc()}")
```

---

## 🟡 IMPORTANT - APPLY SOON

### 5. Input Validation - PENDING
**Risk:** MEDIUM  
**Location:** Line ~650

**Add before processing message:**
```python
if prompt or send_button:
    if not prompt:
        st.warning("⚠️ Please type a message first!")
        st.stop()
    
    user_text = prompt.strip()
    
    # Validate message
    if not user_text:
        st.warning("⚠️ Please enter a non-empty message!")
        st.stop()
    
    if len(user_text) > 5000:
        st.error("❌ Message too long! Maximum 5000 characters.")
        st.stop()
    
    # Remove potentially harmful characters
    user_text = user_text.replace('\0', '')  # Null bytes
```

---

### 6. Dynamic Timeout - PENDING
**Risk:** MEDIUM  
**Location:** Line ~730

**Add function at module level:**
```python
def calculate_timeout(files: dict) -> float:
    """Calculate timeout based on total file size."""
    base_timeout = 15.0
    
    if not files:
        return base_timeout
    
    total_size = 0
    for file_tuple in files.values():
        if len(file_tuple) >= 2:
            total_size += len(file_tuple[1])
    
    # Add 10 seconds per MB
    size_mb = total_size / (1024 * 1024)
    dynamic_timeout = base_timeout + (size_mb * 10)
    
    # Cap at 5 minutes
    return min(dynamic_timeout, 300.0)
```

**Use it in API calls:**
```python
# Replace:
res = call_multipart(..., timeout=120.0)

# With:
timeout = calculate_timeout(files)
res = call_multipart(..., timeout=timeout)
```

---

### 7. Health Check on Startup - PENDING
**Risk:** MEDIUM  
**Location:** Line ~905 (in main())

**Add after backend_url definition:**
```python
backend_url = os.environ.get("OMNICHATX_BACKEND", "http://localhost:8000").strip().rstrip("/")

# Health check
try:
    health_resp = requests.get(f"{backend_url}/health", timeout=5)
    if health_resp.status_code == 200:
        st.success(f"✅ Connected to backend: {backend_url}")
    else:
        st.warning(f"⚠️ Backend returned status {health_resp.status_code}")
except requests.ConnectionError:
    st.error(f"❌ Cannot connect to backend at {backend_url}")
    st.info("💡 Make sure the backend server is running")
    st.stop()
except requests.Timeout:
    st.warning("⏱️ Backend is slow to respond")
except Exception as e:
    st.warning(f"⚠️ Backend health check failed: {e}")
```

---

## 🟢 NICE TO HAVE - LOW PRIORITY

### 8. Session State Lock
**Location:** Throughout

```python
# Add at initialization
if 'processing_lock' not in st.session_state:
    st.session_state.processing_lock = False

# Use before processing
if st.session_state.processing_lock:
    st.warning("⏳ Please wait for current request to complete...")
    st.stop()

st.session_state.processing_lock = True
try:
    # Process message
    pass
finally:
    st.session_state.processing_lock = False
```

---

### 9. Response Validation Helper
**Location:** Add new function

```python
def safe_get_nested(data: dict, *keys, default=None):
    """Safely navigate nested dictionaries."""
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
        if current is None:
            return default
    return current

# Usage in response parsing (line ~780):
emotion = safe_get_nested(res, "meta", "voice", "emotion")
vision_label = safe_get_nested(res, "meta", "vision_image", "label")
```

---

### 10. Add Retry Logic
**Location:** In API call functions

```python
import time

def call_with_retry(func, *args, max_retries=3, **kwargs):
    """Retry API calls with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except requests.Timeout:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.warning(f"Timeout on attempt {attempt+1}, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
        except requests.ConnectionError:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.warning(f"Connection error on attempt {attempt+1}, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise

# Usage:
res = call_with_retry(call_multipart, "/api/chat/multimodal", data=data, files=files)
```

---

## 📋 TESTING CHECKLIST

After applying fixes, test these scenarios:

### Critical Tests:
- [ ] Upload image >10MB (should show error)
- [ ] Upload video >100MB (should show error)
- [ ] Send message with XSS payload: `<script>alert('test')</script>`
- [ ] Stop backend and send message (should show connection error)
- [ ] Send very long message (>5000 chars)
- [ ] Upload large file and wait for timeout

### Normal Tests:
- [ ] Send text-only message
- [ ] Upload and send with image
- [ ] Upload and send with audio
- [ ] Upload and send with video
- [ ] Clear attachments
- [ ] Start new session
- [ ] Multiple rapid messages

---

## 🎯 RECOMMENDED ORDER

1. **Apply immediately** (5 minutes):
   - ✅ Type error (DONE)
   - ⚠️ File size validation
   - ⚠️ HTML escaping

2. **Apply today** (15 minutes):
   - ⚠️ Better error handling
   - ⚠️ Input validation
   - ⚠️ Health check

3. **Apply this week** (30 minutes):
   - Dynamic timeout
   - Session lock
   - Response validation
   - Retry logic

---

## 📊 IMPACT SUMMARY

| Fix | Risk Reduced | User Impact | Dev Time |
|-----|--------------|-------------|----------|
| Type error | Low | None | 1 min ✅ |
| File size | HIGH | Crashes prevented | 5 min |
| XSS escape | MEDIUM | Security | 2 min |
| Error handling | HIGH | UX improved | 10 min |
| Input validation | MEDIUM | Edge cases | 5 min |
| Health check | MEDIUM | Startup clarity | 5 min |
| Dynamic timeout | MEDIUM | Large files work | 10 min |
| Retry logic | MEDIUM | Reliability | 15 min |

**Total time for critical fixes:** ~40 minutes  
**Total time for all fixes:** ~1.5 hours

---

## 🚀 DEPLOYMENT NOTES

1. **No restart needed** for type fix (already applied)
2. **Restart Streamlit** after applying other fixes
3. **Test in dev** before production
4. **Monitor logs** for new error patterns
5. **Set up alerts** for error rates

---

## 📞 SUPPORT

If issues persist after applying fixes:

1. Check backend logs: `/var/log/backend.log`
2. Check Streamlit logs: `streamlit run --log_level=debug`
3. Enable debug mode: `export DEBUG_MODE=true`
4. Test backend directly: `curl http://localhost:8000/health`

---

**Status:** 1/10 fixes applied, 9 pending  
**Overall Health:** 🟡 IMPROVING (was 🔴 CRITICAL)
