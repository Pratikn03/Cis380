from __future__ import annotations


import requests
import streamlit as st

API_BASE = st.secrets.get("backend_url", "http://localhost:8000")


def render_risk_dashboard() -> None:
    st.set_page_config(page_title="Risk Command Center", layout="wide")
    st.title("OmniChatX Risk Command Center")

    with st.form("risk_form"):
        st.subheader("Simulate a user event")
        login_country = st.selectbox("Login country", ["US", "BR", "IN", "DE", "CN"])
        device_known = st.selectbox("Device known", [True, False])
        login_time = st.time_input("Login time")
        clicks_per_minute = st.slider("Clicks per minute", 0, 500, 75)
        files_accessed = st.slider("Files accessed", 0, 200, 12)
        transaction_amount = st.number_input("Transaction amount", min_value=0.0, max_value=50000.0, value=1200.0)
        submitted = st.form_submit_button("Analyze risk")

    if submitted:
        payload = {
            "login_country": login_country,
            "device_known": device_known,
            "login_time": login_time.strftime("%H:%M"),
            "clicks_per_minute": clicks_per_minute,
            "files_accessed": files_accessed,
            "transaction_amount": transaction_amount,
        }
        response = requests.post(f"{API_BASE}/api/risk/analyze", json=payload, timeout=15)
        st.session_state.latest_payload = payload
        st.session_state.latest_response = response.json()

    if "latest_response" not in st.session_state:
        st.session_state.latest_response = {}
        st.session_state.latest_payload = {}

    if "risk_summary" not in st.session_state:
        st.session_state.risk_summary = {}

    try:
        summary_resp = requests.get(f"{API_BASE}/api/monitor/risk_summary", timeout=5)
        st.session_state.risk_summary = summary_resp.json()
    except Exception:
        summary_resp = None

    col1, col2 = st.columns([3, 1])

    with col1:
        st.subheader("Risk Scores & Decision")
        risks = st.session_state.latest_response.get("risk_scores", {})
        if risks:
            st.metric("Cyber risk", f"{risks.get('cyber_risk', 0):.3f}")
            st.metric("Behavior risk", f"{risks.get('behavior_risk', 0):.3f}")
            st.metric("Fraud risk", f"{risks.get('fraud_risk', 0):.3f}")
            st.markdown(f"**Decision:** {st.session_state.latest_response.get('decision', '—')}")
            with st.expander("Explanation"):
                st.write(st.session_state.latest_response.get("explanation", "—"))
            if st.button("Explain decision again", key="reexplain"):
                explain_resp = requests.post(
                    f"{API_BASE}/api/risk/analyze",
                    json=st.session_state.latest_payload,
                    timeout=15,
                )
                st.session_state.latest_response["explanation"] = explain_resp.json().get("explanation", "—")
                st.experimental_rerun()
        else:
            st.info("Submit the simulator to see risk scores, decision, and explanation.")

    with col2:
        st.subheader("Payload & Timeline")
        st.json(st.session_state.latest_payload)
        st.caption("Timeline: capture sequence of events here in future iterations.")

    with st.expander("Live risk summary"):
        summary = st.session_state.risk_summary
        if summary:
            st.metric("Total events logged", summary.get("total_events", 0))
            st.write("Decision counts")
            st.write(summary.get("decision_counts", {}))
            st.write("Average risks")
            st.write(summary.get("avg_risks", {}))
        else:
            st.info("Risk summary currently unavailable.")

    if submitted:
        st.sidebar.success("Payload sent. Check results on the left.")
        st.sidebar.json(st.session_state.latest_payload)


if __name__ == "__main__":
    render_risk_dashboard()

with st.form("risk_form"):
    st.subheader("Simulate a user event")
    login_country = st.selectbox("Login country", ["US", "BR", "IN", "DE", "CN"])
    device_known = st.selectbox("Device known", [True, False])
    login_time = st.time_input("Login time")
    clicks_per_minute = st.slider("Clicks per minute", 0, 500, 75)
    files_accessed = st.slider("Files accessed", 0, 200, 12)
    transaction_amount = st.number_input("Transaction amount", min_value=0.0, max_value=50000.0, value=1200.0)
    submitted = st.form_submit_button("Analyze risk")

if submitted:
    payload = {
        "login_country": login_country,
        "device_known": device_known,
        "login_time": login_time.strftime("%H:%M"),
        "clicks_per_minute": clicks_per_minute,
        "files_accessed": files_accessed,
        "transaction_amount": transaction_amount,
    }
    response = requests.post(f"{API_BASE}/api/risk/analyze", json=payload, timeout=15)
    st.session_state.latest_payload = payload
    st.session_state.latest_response = response.json()

if "latest_response" not in st.session_state:
    st.session_state.latest_response = {}
    st.session_state.latest_payload = {}

col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("Risk Scores & Decision")
    risks = st.session_state.latest_response.get("risk_scores", {})
    if risks:
        st.metric("Cyber risk", f"{risks.get('cyber_risk', 0):.3f}")
        st.metric("Behavior risk", f"{risks.get('behavior_risk', 0):.3f}")
        st.metric("Fraud risk", f"{risks.get('fraud_risk', 0):.3f}")
        st.markdown(f"**Decision:** {st.session_state.latest_response.get('decision', '—')}" )
        st.markdown("**Explanation:**")
        st.write(st.session_state.latest_response.get("explanation", "—"))
    else:
        st.info("Submit the simulator to see risk scores, decision, and explanation.")

with col2:
    st.subheader("Payload & Timeline")
    st.json(st.session_state.latest_payload)
    st.caption("Timeline: capture sequence of events here in future iterations.")
