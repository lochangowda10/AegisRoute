import streamlit as st
import httpx
import time
import pandas as pd

st.set_page_config(page_title="AegisRoute NOC Terminal", layout="wide", page_icon="🛡️")

# NOC Terminal Dark Theme Styling via st.markdown
st.markdown("""
<style>
    /* Global Background */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    
    /* Glowing Metric Cards */
    .metric-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 0 10px rgba(0,0,0,0.5);
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #58a6ff;
        text-shadow: 0 0 8px rgba(88, 166, 255, 0.4);
    }
    .metric-title {
        font-size: 1rem;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Node Status Badges */
    .badge-healthy {
        color: #3fb950;
        font-weight: bold;
        border: 1px solid #3fb950;
        padding: 5px 10px;
        border-radius: 20px;
        background: rgba(63, 185, 80, 0.1);
        text-shadow: 0 0 5px #3fb950;
        animation: pulse 2s infinite;
        display: inline-block;
    }
    .badge-dead {
        color: #f85149;
        font-weight: bold;
        border: 1px solid #f85149;
        padding: 5px 10px;
        border-radius: 20px;
        background: rgba(248, 81, 73, 0.1);
        text-shadow: 0 0 5px #f85149;
        animation: flash 1s infinite;
        display: inline-block;
    }

    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(63, 185, 80, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(63, 185, 80, 0); }
        100% { box-shadow: 0 0 0 0 rgba(63, 185, 80, 0); }
    }
    
    @keyframes flash {
        0%, 50%, 100% { opacity: 1; }
        25%, 75% { opacity: 0.5; }
    }
    
    /* Tables */
    .dataframe {
        background: #161b22;
        color: #c9d1d9;
    }
</style>
""", unsafe_allow_html=True)

import os

ROUTER_URL = os.environ.get("ROUTER_URL", "http://127.0.0.1:8000")

def fetch_stats():
    try:
        response = httpx.get(f"{ROUTER_URL}/api/v1/balancer/stats", timeout=2.0)
        if response.status_code == 200:
            return response.json()
    except Exception:
        return None

def trigger_failure(port, healthy):
    try:
        base_host = os.environ.get("AGENT_HOST", "http://127.0.0.1")
        httpx.post(f"{base_host}:{port}/simulate_failure?status={str(healthy).lower()}", timeout=1.0)
    except Exception as e:
        st.sidebar.error(f"Error toggling port {port}: {e}")

st.title("🛡️ AegisRoute NOC Terminal")
st.markdown("Real-time Agent Load Balancing & Resiliency Engine")

# --- SIDEBAR CONTROLS ---
st.sidebar.header("🛠️ Control Panel")
strategy = st.sidebar.selectbox("Test Query Strategy", ["round-robin", "least-connections", "random"])
test_query = st.sidebar.text_input("Test Query", value="Ping test")
if st.sidebar.button("Send Test Query"):
    try:
        resp = httpx.post(f"{ROUTER_URL}/router/route?strategy={strategy}", json={"query": test_query})
        if resp.status_code == 200:
            st.sidebar.success(f"Success! Handled by Port {resp.json().get('instance_port')}")
        else:
            st.sidebar.error(f"Error: {resp.status_code}")
    except Exception as e:
        st.sidebar.error(f"Request failed: {e}")

st.sidebar.markdown("---")
st.sidebar.subheader("Chaos Engineering (Simulate Failure)")
stats = fetch_stats()
if stats:
    for port in stats.get("registered_instances", []):
        is_healthy = port in stats.get("healthy_instances", [])
        if st.sidebar.button(f"{'KILL' if is_healthy else 'RESTORE'} Node {port}"):
            trigger_failure(port, not is_healthy)
else:
    st.sidebar.warning("Router offline. Cannot fetch nodes.")

# --- LIVE DASHBOARD ---
placeholder = st.empty()

while True:
    stats = fetch_stats()
    
    with placeholder.container():
        if not stats:
            st.error("⚠️ Cannot connect to AegisRoute Router at 127.0.0.1:8000")
        else:
            registered = stats.get("registered_instances", [])
            healthy = stats.get("healthy_instances", [])
            dead = stats.get("dead_instances", [])
            req_counts = stats.get("total_requests", {})
            act_conn = stats.get("active_connections", {})
            
            # Metric Cards
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f'<div class="metric-card"><div class="metric-title">Total Nodes</div><div class="metric-value">{len(registered)}</div></div>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<div class="metric-card"><div class="metric-title">Healthy Nodes</div><div class="metric-value" style="color:#3fb950;">{len(healthy)}</div></div>', unsafe_allow_html=True)
            with col3:
                st.markdown(f'<div class="metric-card"><div class="metric-title">Dead Nodes</div><div class="metric-value" style="color:#f85149;">{len(dead)}</div></div>', unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Node Status Table
            st.subheader("🌐 Node Status")
            node_cols = st.columns(len(registered))
            for i, port in enumerate(registered):
                with node_cols[i]:
                    st.markdown(f"**Port {port}**")
                    if port in healthy:
                        st.markdown('<div class="badge-healthy">● Operational</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="badge-dead">▲ Quarantined</div>', unsafe_allow_html=True)
                    st.markdown(f"Active Conns: `{act_conn.get(str(port), act_conn.get(port, 0))}`")
                    st.markdown(f"Total Reqs: `{req_counts.get(str(port), req_counts.get(port, 0))}`")
            
            st.markdown("---")
            
            # Traffic Distribution Chart
            st.subheader("📊 Traffic Distribution (Total Requests)")
            # Standardize keys to string to avoid mismatch in Streamlit
            chart_data = pd.DataFrame({
                "Port": [str(p) for p in registered],
                "Requests": [req_counts.get(str(p), req_counts.get(p, 0)) for p in registered]
            })
            if chart_data["Requests"].sum() > 0:
                st.bar_chart(chart_data.set_index("Port"), color="#58a6ff", height=300)
            else:
                st.info("No requests routed yet. Send some traffic to see the distribution!")

    time.sleep(1.0)
