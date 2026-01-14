from __future__ import annotations

from typing import Any, Callable

import os
import requests
import streamlit as st

COUNTRY_OPTIONS = [
    "US",
    "CA",
    "UK",
    "DE",
    "FR",
    "ES",
    "IT",
    "NL",
    "SE",
    "IN",
    "SG",
    "JP",
    "KR",
    "AU",
    "NZ",
    "BR",
    "MX",
    "AE",
    "ZA",
    "NG",
]

PRESETS: dict[str, dict[str, Any]] = {
    "Normal login (low risk)": {
        "login_country": "US",
        "device_known": True,
        "login_time": 12,
        "clicks_per_minute": 15,
        "files_accessed": 2,
        "transaction_amount": 50.0,
    },
    "Suspicious login (step-up demo)": {
        "login_country": "BR",
        "device_known": False,
        "login_time": 2,
        "clicks_per_minute": 180,
        "files_accessed": 120,
        "transaction_amount": 250.0,
    },
    "High fraud (block demo)": {
        "login_country": "NG",
        "device_known": False,
        "login_time": 1,
        "clicks_per_minute": 220,
        "files_accessed": 200,
        "transaction_amount": 20000.0,
    },
}

FIELD_KEYS = {
    "login_country": "risk_login_country",
    "device_known": "risk_device_known",
    "login_time": "risk_login_time",
    "clicks_per_minute": "risk_clicks_per_minute",
    "files_accessed": "risk_files_accessed",
    "transaction_amount": "risk_transaction_amount",
}


def _backend_base(backend_url: str | None = None) -> str:
    base = (
        backend_url
        or os.getenv("Sentifargo_BACKEND")
        or os.getenv("OMNICHATX_BACKEND")
        or "http://localhost:8000"
    ).strip()
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

    preset = st.selectbox("Scenario preset", list(PRESETS.keys()), index=0, key="risk_preset")
    if st.button("Apply preset", key="risk_apply_preset"):
        chosen = PRESETS.get(preset, {})
        for field, value in chosen.items():
            st.session_state[FIELD_KEYS[field]] = value
        st.rerun()

    with st.form("risk_simulator"):
        c1, c2, c3 = st.columns(3)
        with c1:
            login_country = st.selectbox(
                "Login Country",
                COUNTRY_OPTIONS,
                index=0,
                key=FIELD_KEYS["login_country"],
            )
        with c2:
            device_known = st.checkbox(
                "Device Known", value=True, key=FIELD_KEYS["device_known"]
            )
        with c3:
            login_time = st.slider(
                "Login Time (hour)",
                min_value=0,
                max_value=23,
                value=12,
                key=FIELD_KEYS["login_time"],
            )

        c4, c5, c6 = st.columns(3)
        with c4:
            clicks_per_minute = st.slider(
                "Clicks / min",
                min_value=0,
                max_value=500,
                value=10,
                key=FIELD_KEYS["clicks_per_minute"],
            )
        with c5:
            files_accessed = st.slider(
                "Files Accessed",
                min_value=0,
                max_value=500,
                value=0,
                key=FIELD_KEYS["files_accessed"],
            )
        with c6:
            transaction_amount = st.slider(
                "Transaction Amount ($)",
                min_value=0.0,
                max_value=25000.0,
                value=0.0,
                step=50.0,
                key=FIELD_KEYS["transaction_amount"],
            )

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
    st.json(
        {
            "event": payload,
            "risks": {k: data.get(k) for k in ["cyber_risk", "behavior_risk", "fraud_risk"]},
            "decision": data.get("decision"),
        }
    )

    if data.get("explanation"):
        st.subheader("Explain decision")
        st.write(data["explanation"])
