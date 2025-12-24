# Streamlit OmniChat Error & Bug Analysis

**Date:** December 17, 2025  
**File:** `app/streamlit_chatbot/omnichat_unified.py`  
**Status:** Active Streamlit instance running on port 8502

> Note: This document is a historical debugging log from the UI hardening phase.

---

## 🔴 CRITICAL ERRORS

### 1. Type Error in `call_get` function (Line 971)
**Severity:** HIGH  
**Location:** Line 971  
**Error Type:** Type mismatch in `requests.get()` params argument

```python
# Current problematic code:
def call_get(
    path: str,
    *,
    params: dict[str, object] | None = None,  # ❌ Wrong type
    timeout: float = 15.0
) -> dict:
    try:
        resp = requests.get(
            f"{backend_url}{path}",
            params=params,  # ❌ Type error here
            headers=_auth_headers(),
            timeout=timeout
        )
```

**Issue:** The `params` type is declared as `dict[str, object]` but `requests.get()` expects `_Params` type which requires specific value types (str, bytes, int, float, Iterable).

**Impact:**
- Type checker warnings
- Potential runtime errors with certain parameter values
- IDE/linting errors

**Fix Required:**
```python
def call_get(
    path: str,
    *,
    params: dict[str, str | int | float] | None = None,  # ✅ Correct type
    timeout: float = 15.0
) -> dict:
```

---

## ⚠️ HIGH PRIORITY ISSUES

### 2. Session State Race Conditions
**Severity:** HIGH  
**Location:** Multiple locations throughout chat flow

**Issue:** Session state variables are modified and immediately used, which can cause race conditions with Streamlit's rerun mechanism.

**Affected Variables:**
- `st.session_state.omni_messages`
- `st.session_state.omni_attached_image`
- `st.session_state.omni_attached_audio`
- `st.session_state.omni_attached_video`

**Scenarios:**
1. User uploads image → clicks send before state fully updates
2. Multiple reruns triggered in quick succession
3. Clear attachments button pressed during API call

**Impact:**
- Lost messages
- Duplicate messages
- Attachments not cleared properly
- UI inconsistencies

**Recommended Fix:**
```python
# Add state locks or use callbacks
if 'processing' not in st.session_state:
    st.session_state.processing = False

if not st.session_state.processing:
    st.session_state.processing = True
    # Process message
    st.session_state.processing = False
```

---

### 3. File Upload Memory Leaks
**Severity:** HIGH  
**Location:** Lines 450-550 (media upload sections)

**Issue:** File contents are stored in session state as bytes without size limits.

**Problems:**
- Large video files (>100MB) can crash Streamlit
- Session state grows unbounded
- No cleanup of old attachments
- Multiple file uploads accumulate in memory

**Current Code:**
```python
if uploaded_video:
    st.session_state.omni_attached_video = uploaded_video.getvalue()  # ❌ No size check
```

**Recommended Fix:**
```python
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB
MAX_AUDIO_SIZE = 20 * 1024 * 1024  # 20MB

if uploaded_video:
    video_bytes = uploaded_video.getvalue()
    if len(video_bytes) > MAX_VIDEO_SIZE:
        st.error(f"❌ Video too large! Max size: {MAX_VIDEO_SIZE / (1024*1024):.0f}MB")
    else:
        st.session_state.omni_attached_video = video_bytes
```

---

### 4. API Timeout Issues
**Severity:** HIGH  
**Location:** Lines 730-750 (API calls)

**Issue:** Fixed timeout values don't account for large media files or slow backends.

**Current Timeouts:**
- Text-only: 15 seconds
- Multimodal: 120 seconds (2 minutes)

**Problems:**
- Large video analysis may take >2 minutes
- No retry mechanism
- User sees spinner indefinitely if timeout occurs
- No progress indication

**Recommended Fix:**
```python
# Dynamic timeout based on file size
def calculate_timeout(files: dict) -> float:
    base_timeout = 15.0
    for file_tuple in files.values():
        file_size = len(file_tuple[1])
        # Add 10 seconds per MB
        base_timeout += (file_size / (1024 * 1024)) * 10
    return min(base_timeout, 300.0)  # Max 5 minutes

timeout = calculate_timeout(files) if files else 15.0

# Add retry logic with exponential backoff
for attempt in range(3):
    try:
        res = call_multipart(..., timeout=timeout)
        break
    except requests.Timeout:
        if attempt < 2:
            time.sleep(2 ** attempt)
        else:
            raise
```

---

## 🟡 MEDIUM PRIORITY ISSUES

### 5. Unsafe HTML Rendering
**Severity:** MEDIUM  
**Location:** Multiple locations using `unsafe_allow_html=True`

**Issue:** User input is directly inserted into HTML without sanitization.

**Vulnerable Code:**
```python
st.markdown(f"""
<div class="message-content">
    <div style="margin-top: 6px;">{content}</div>  # ❌ XSS vulnerability
</div>
""", unsafe_allow_html=True)
```

**Attack Vector:**
User could input: `<script>alert('XSS')</script>` or `<img src=x onerror=alert(1)>`

**Recommended Fix:**
```python
import html

# Escape all user content
safe_content = html.escape(content)

st.markdown(f"""
<div class="message-content">
    <div style="margin-top: 6px;">{safe_content}</div>  # ✅ Safe
</div>
""", unsafe_allow_html=True)
```

---

### 6. Missing Error Handling for Backend Failures
**Severity:** MEDIUM  
**Location:** Lines 915-925 (exception handling)

**Current Code:**
```python
except Exception as e:
    reply = f"❌ **Exception:** {str(e)}"
```

**Problems:**
- Generic error messages don't help users
- No logging of errors
- No differentiation between error types
- Stack traces not captured

**Recommended Fix:**
```python
import logging
import traceback

logger = logging.getLogger(__name__)

try:
    res = call_multipart(...)
except requests.ConnectionError:
    reply = "❌ **Connection Error:** Cannot reach backend server. Please check if the API is running."
    logger.error(f"Backend connection failed: {backend_url}")
except requests.Timeout:
    reply = "⏱️ **Timeout:** Request took too long. Try with smaller files or simpler queries."
    logger.warning(f"Request timeout after {timeout}s")
except requests.HTTPError as e:
    status_code = e.response.status_code
    if status_code == 413:
        reply = "❌ **File Too Large:** Your upload exceeds the maximum size."
    elif status_code == 500:
        reply = "❌ **Server Error:** Backend encountered an error. Please try again."
    else:
        reply = f"❌ **HTTP Error {status_code}:** {e.response.text[:200]}"
    logger.error(f"HTTP error: {e}", exc_info=True)
except Exception as e:
    reply = f"❌ **Unexpected Error:** {str(e)}"
    logger.error(f"Unexpected error: {traceback.format_exc()}")
```

---

### 7. Response Parsing Fragility
**Severity:** MEDIUM  
**Location:** Lines 760-850 (response processing)

**Issue:** Complex nested dictionary access without proper validation.

**Problematic Pattern:**
```python
# This can fail at any level
emotion = res.get("meta", {}).get("voice", {}).get("emotion")
```

**Problems:**
- Silent failures if API response structure changes
- No validation of expected response format
- Difficult to debug when parsing fails

**Recommended Fix:**
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

# Usage
emotion = safe_get_nested(res, "meta", "voice", "emotion")
if emotion:
    # Process emotion
    pass
```

---

### 8. Camera Input State Management
**Severity:** MEDIUM  
**Location:** Lines 470-480

**Issue:** Camera input doesn't clear after use.

**Current Behavior:**
1. User takes photo
2. Photo captured
3. Send message
4. Camera still shows captured photo
5. Confusing for next message

**Recommended Fix:**
```python
# Add a flag to track if camera image was used
if 'camera_used' not in st.session_state:
    st.session_state.camera_used = False

# After sending message with camera image:
if st.session_state.omni_image_name == "camera_photo.jpg":
    st.session_state.camera_used = True
    # Force camera widget to reset by changing key
    st.rerun()
```

---

## 🟢 LOW PRIORITY ISSUES

### 9. Performance: Redundant Reruns
**Severity:** LOW  
**Location:** Multiple `st.rerun()` calls

**Issue:** Unnecessary full page reruns after every action.

**Impact:**
- Slower UI response
- Flickering
- Higher CPU usage

**Optimization:**
```python
# Use st.experimental_rerun() or callbacks instead
# Batch state updates before rerun
# Use st.fragment for partial updates (Streamlit 1.33+)
```

---

### 10. Missing Input Validation
**Severity:** LOW  
**Location:** Chat input processing

**Issues:**
- No check for empty messages (only whitespace)
- No maximum message length
- No sanitization of special characters

**Recommended Validation:**
```python
if prompt:
    user_text = prompt.strip()
    
    if not user_text:
        st.warning("⚠️ Please enter a non-empty message!")
        st.stop()
    
    if len(user_text) > 5000:
        st.error("❌ Message too long! Maximum 5000 characters.")
        st.stop()
    
    # Sanitize
    user_text = user_text.replace('\0', '')  # Remove null bytes
```

---

### 11. Hardcoded Styling
**Severity:** LOW  
**Location:** Lines 50-350 (CSS)

**Issue:** All styling is inline, making customization difficult.

**Recommendation:**
- Move CSS to separate file
- Add theme configuration
- Use CSS variables for colors

---

### 12. Missing Accessibility Features
**Severity:** LOW  
**Location:** Throughout UI

**Missing Features:**
- No ARIA labels
- No keyboard navigation hints
- No screen reader support
- No high contrast mode

---

## 🔧 CONFIGURATION ISSUES

### 13. Environment Variable Handling
**Severity:** MEDIUM  
**Location:** Lines 905-910

**Issues:**
```python
backend_url = os.environ.get("OMNICHATX_BACKEND", "http://localhost:8000")
```

**Problems:**
- No validation of URL format
- No check if backend is reachable
- Default might not work in all environments

**Recommended Fix:**
```python
import validators

backend_url = os.environ.get("OMNICHATX_BACKEND", "http://localhost:8000").strip().rstrip("/")

if not validators.url(backend_url):
    st.error(f"❌ Invalid backend URL: {backend_url}")
    st.stop()

# Health check
try:
    health_check = requests.get(f"{backend_url}/health", timeout=5)
    if health_check.status_code != 200:
        st.warning("⚠️ Backend is not responding correctly")
except:
    st.error("❌ Cannot connect to backend. Please check the server.")
    st.stop()
```

---

## 📊 POTENTIAL RUNTIME ERRORS

### Error Scenarios by Frequency (Estimated)

1. **Type Error in params** (100% - always present in type checking)
2. **Timeout errors** (30% - with large files)
3. **Memory errors** (20% - with multiple large files)
4. **Connection errors** (15% - network issues)
5. **Response parsing errors** (10% - API changes)
6. **Session state race conditions** (5% - rapid user actions)
7. **XSS attempts** (1% - malicious input)

---

## 🛠️ RECOMMENDED FIXES PRIORITY

### Immediate (Deploy Today):
1. ✅ Fix type error in `call_get()` function
2. ✅ Add file size validation
3. ✅ Improve error handling with specific messages
4. ✅ Add HTML escaping for user content

### This Week:
5. Add retry logic for API calls
6. Implement proper logging
7. Add response validation
8. Fix session state race conditions

### This Month:
9. Refactor CSS to external file
10. Add comprehensive input validation
11. Implement health checks
12. Add accessibility features

---

## 🧪 TESTING RECOMMENDATIONS

### Unit Tests Needed:
- `call_model()` error handling
- `call_multipart()` with various file types
- `call_get()` parameter types
- Response parsing functions

### Integration Tests:
- Full chat flow with attachments
- Multiple rapid messages
- Large file uploads
- Backend timeout scenarios
- Session state persistence

### Load Tests:
- Concurrent users
- Large file uploads
- Extended sessions
- Memory usage over time

---

## 📝 CODE QUALITY METRICS

- **Total Lines:** 991
- **Functions:** 4 main functions
- **Type Errors:** 1 confirmed
- **Exception Handlers:** 3 (need improvement)
- **Input Validation:** Minimal
- **Logging:** None
- **Security Issues:** 2 (XSS, unlimited uploads)

---

## 🎯 QUICK WIN FIXES

Here are the 5 fastest fixes with highest impact:

```python
# 1. Fix type error (30 seconds)
params: dict[str, str | int | float] | None = None

# 2. Add file size check (2 minutes)
if len(video_bytes) > MAX_SIZE:
    st.error("File too large")
    
# 3. Escape HTML (1 minute)
import html
safe_content = html.escape(content)

# 4. Better error messages (5 minutes)
except requests.ConnectionError:
    reply = "Cannot reach server"
except requests.Timeout:
    reply = "Request timed out"

# 5. Add logging (3 minutes)
import logging
logger = logging.getLogger(__name__)
logger.error(f"Error: {e}")
```

---

## 📞 MONITORING RECOMMENDATIONS

### Add Metrics:
- Message count per session
- API response times
- Error rates by type
- File upload sizes
- Session duration

### Add Alerts:
- Error rate > 10%
- Response time > 5s
- Memory usage > 1GB
- Backend unreachable

---

## ✅ CONCLUSION

The Streamlit app is **functional but has several critical bugs** that should be addressed:

**Must Fix:**
- Type error causing linting/IDE errors
- File size validation missing
- Poor error handling

**Should Fix:**
- Session state race conditions
- Response parsing fragility
- XSS vulnerabilities

**Nice to Have:**
- Better performance
- Accessibility
- Code organization

**Overall Risk Level:** 🟡 **MEDIUM-HIGH**

The app will work for most users but may fail unexpectedly with:
- Large files
- Slow networks
- Malicious input
- API changes

**Estimated Fix Time:** 4-6 hours for critical issues
