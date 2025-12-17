from __future__ import annotations

from typing import Any, Callable

import os
import requests
import streamlit as st


def _backend_base(backend_url: str | None = None) -> str:
    base = (backend_url or os.getenv("OMNICHATX_BACKEND") or "http://localhost:8000").strip()
    return base.rstrip("/")


def _env_auth_headers() -> dict[str, str]:
    token = os.getenv("AUTH_TOKEN")
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def render_risk_command_center(
    *,
    backend_url: str | None = None,
    auth_headers: Callable[[], dict[str, str]] | None = None,
) -> None:
    st.header("Risk Command Center")
    st.caption("Simulate a live session event and get Cyber + Behavior + Fraud risk + decision.")

    with st.form("risk_simulator"):
        c1, c2, c3 = st.columns(3)
        with c1:
            login_country = st.selectbox("Login Country", ["US", "CA", "UK", "DE", "IN", "BR", "NG"], index=0)
        with c2:
            device_known = st.checkbox("Device Known", value=True)
        with c3:
            login_time = st.slider("Login Time (hour)", min_value=0, max_value=23, value=12)

        c4, c5, c6 = st.columns(3)
        with c4:
            clicks_per_minute = st.slider("Clicks / min", min_value=0, max_value=500, value=10)
        with c5:
            files_accessed = st.slider("Files Accessed", min_value=0, max_value=500, value=0)
        with c6:
            transaction_amount = st.slider("Transaction Amount ($)", min_value=0.0, max_value=25000.0, value=0.0, step=50.0)

        explain = st.checkbox("Explain decision", value=True)
        submitted = st.form_submit_button("Analyze Risk")

    if not submitted:
        st.info("Adjust the sliders and click **Analyze Risk**.")
        return

    payload: dict[str, Any] = {
        "login_country": login_country,
        "device_known": device_known,
        "login_time": float(login_time),
        "clicks_per_minute": float(clicks_per_minute),
        "files_accessed": int(files_accessed),
        "transaction_amount": float(transaction_amount),
    }

    url = f"{_backend_base(backend_url)}/api/risk/analyze"
    try:
        headers = auth_headers() if auth_headers is not None else _env_auth_headers()
        res = requests.post(
            url,
            params={"explain": str(explain).lower()},
            json=payload,
            headers=headers or None,
            timeout=15,
        )
        res.raise_for_status()
        data = res.json()
    except Exception as e:
        st.error(f"Risk API call failed: {e}")
        st.code({"url": url, "payload": payload})
        return

    st.subheader("Risk gauges")
    g1, g2, g3 = st.columns(3)
    g1.metric("Cyber", f"{data.get('cyber_risk', 0):.2f}")
    g2.metric("Behavior", f"{data.get('behavior_risk', 0):.2f}")
    g3.metric("Fraud", f"{data.get('fraud_risk', 0):.2f}")

    st.subheader("System decision")
    st.write(f"**{data.get('decision', 'UNKNOWN')}**  (`{data.get('reason_code', '')}`)")

    monitoring = data.get("monitoring")
    if isinstance(monitoring, dict):
        log_path = monitoring.get("log_path") or "data/monitoring/logs/risk_events.jsonl"
        if monitoring.get("logged") is True:
            st.caption(f"Monitoring: logged to `{log_path}`")
        else:
            st.caption(f"Monitoring: not logged (expected path `{log_path}`)")

    st.subheader("Event timeline")
    st.json({"event": payload, "risks": {k: data.get(k) for k in ["cyber_risk", "behavior_risk", "fraud_risk"]}, "decision": data.get("decision")})

    if data.get("explanation"):
        st.subheader("Explain decision")
        st.write(data["explanation"])
