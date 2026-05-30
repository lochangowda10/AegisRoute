"""
AegisRoute — AI Agent Orchestration & Intelligent Routing Infrastructure
Enterprise-grade observability platform for hackathon demos.
"""
import streamlit as st
import httpx, os, time, json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="AegisRoute Orchestration", layout="wide", page_icon="🛡️")

# Initialize session state
if "recent_requests" not in st.session_state:
    st.session_state.recent_requests = []  # Keep last 100 requests
if "last_failover" not in st.session_state:
    st.session_state.last_failover = None

ROUTER_URL = os.environ.get("ROUTER_URL", "http://127.0.0.1:8000")

# ═══════════════════════════════════════════════════════════════════════════
# GLOBAL CSS — Dark Cloud Infrastructure Theme
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
* { font-family: 'Inter', sans-serif; }
.stApp { background: #0a0e17; color: #c9d1d9; }
[data-testid="stSidebar"] { background: #0d1117 !important; border-right: 1px solid #1a2332; }
[data-testid="stHeader"] { background: transparent; }
.stTabs [data-baseweb="tab-list"] { gap: 4px; background: #0d1117; border-radius: 8px; padding: 4px; }
.stTabs [data-baseweb="tab"] { background: transparent; color: #8b949e; border-radius: 6px; padding: 8px 16px; font-weight: 500; }
.stTabs [aria-selected="true"] { background: #161b22 !important; color: #00d4ff !important; border-bottom: 2px solid #00d4ff; }

/* Hero Banner */
.hero-banner { background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #1a1f2e 100%); border: 1px solid #1a2332; border-radius: 12px; padding: 24px 32px; margin-bottom: 20px; position: relative; overflow: hidden; }
.hero-banner::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; background: linear-gradient(90deg, #00d4ff, #00ff88, #00d4ff); }
.hero-title { font-size: 1.8rem; font-weight: 700; color: #e6edf3; margin: 0; letter-spacing: -0.5px; }
.hero-sub { color: #8b949e; font-size: 0.9rem; margin-top: 4px; }
.hero-status { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; }
.status-online { background: rgba(0,255,136,0.1); color: #00ff88; border: 1px solid rgba(0,255,136,0.3); animation: glow-green 2s infinite; }
.status-degraded { background: rgba(255,170,0,0.1); color: #ffaa00; border: 1px solid rgba(255,170,0,0.3); }
.status-offline { background: rgba(255,68,68,0.1); color: #ff4444; border: 1px solid rgba(255,68,68,0.3); }

/* Glassmorphism Metric Cards */
.glass-card { background: rgba(22,27,34,0.8); backdrop-filter: blur(10px); border: 1px solid rgba(48,54,61,0.6); border-radius: 12px; padding: 20px; text-align: center; transition: all 0.3s ease; }
.glass-card:hover { border-color: rgba(0,212,255,0.3); box-shadow: 0 0 20px rgba(0,212,255,0.1); }
.card-value { font-size: 2.2rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
.card-label { font-size: 0.75rem; color: #8b949e; text-transform: uppercase; letter-spacing: 1.5px; margin-top: 4px; }
.val-cyan { color: #00d4ff; text-shadow: 0 0 10px rgba(0,212,255,0.3); }
.val-green { color: #00ff88; text-shadow: 0 0 10px rgba(0,255,136,0.3); }
.val-red { color: #ff4444; text-shadow: 0 0 10px rgba(255,68,68,0.3); }
.val-amber { color: #ffaa00; text-shadow: 0 0 10px rgba(255,170,0,0.3); }

/* Node Server Cards */
.node-card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 16px; margin-bottom: 8px; }
.node-card-healthy { border-left: 3px solid #00ff88; }
.node-card-dead { border-left: 3px solid #ff4444; }
.node-port { font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; font-weight: 600; color: #e6edf3; }
.badge-on { display:inline-block; padding:3px 10px; border-radius:12px; font-size:0.75rem; font-weight:600; background:rgba(0,255,136,0.1); color:#00ff88; border:1px solid rgba(0,255,136,0.3); animation: pulse 2s infinite; }
.badge-off { display:inline-block; padding:3px 10px; border-radius:12px; font-size:0.75rem; font-weight:600; background:rgba(255,68,68,0.15); color:#ff4444; border:1px solid rgba(255,68,68,0.4); animation: flash 0.8s infinite; }

/* Progress Bars */
.progress-wrap { background: #21262d; border-radius: 4px; height: 8px; margin: 4px 0; overflow: hidden; }
.progress-fill { height: 100%; border-radius: 4px; transition: width 0.5s ease; }
.fill-green { background: linear-gradient(90deg, #00ff88, #00d4ff); }
.fill-amber { background: linear-gradient(90deg, #ffaa00, #ff6600); }
.fill-red { background: linear-gradient(90deg, #ff4444, #ff0066); }

/* Event Log */
.log-entry { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; padding: 6px 10px; border-left: 3px solid #30363d; margin-bottom: 4px; background: #0d1117; border-radius: 0 4px 4px 0; }
.log-info { border-left-color: #00d4ff; }
.log-warn { border-left-color: #ffaa00; }
.log-critical { border-left-color: #ff4444; }
.log-recovery { border-left-color: #00ff88; }

/* Animations */
@keyframes pulse { 0%{box-shadow:0 0 0 0 rgba(0,255,136,0.4)} 70%{box-shadow:0 0 0 8px rgba(0,255,136,0)} 100%{box-shadow:0 0 0 0 rgba(0,255,136,0)} }
@keyframes flash { 0%,100%{opacity:1} 50%{opacity:0.4} }
@keyframes glow-green { 0%,100%{box-shadow:0 0 5px rgba(0,255,136,0.3)} 50%{box-shadow:0 0 15px rgba(0,255,136,0.5)} }

/* Streamlit overrides */
.stMarkdown { color: #c9d1d9; }
div[data-testid="stMetricValue"] { color: #00d4ff; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# DATA FETCHING
# ═══════════════════════════════════════════════════════════════════════════
def fetch_stats():
    try:
        r = httpx.get(f"{ROUTER_URL}/api/v1/balancer/stats", timeout=3.0)
        if r.status_code == 200: return r.json()
    except Exception: pass
    return None

def api_post(path):
    try: httpx.post(f"{ROUTER_URL}{path}", timeout=3.0)
    except Exception: pass

def send_query(strategy, query):
    try:
        r = httpx.post(f"{ROUTER_URL}/router/route", params={"strategy": strategy}, json={"query": query}, timeout=5.0)
        if r.status_code == 200:
            data = r.json()
            st.session_state.recent_requests.insert(0, {
                "Request ID": data.get("trace_id", f"req-{int(time.time() * 1000)}"),
                "Agent": data.get("instance_port", "unknown"),
                "Strategy": strategy,
                "Latency (ms)": data.get("latency_ms", 0),
                "Status": "Success",
                "Timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
                "Reason": data.get("routing_reason", ""),
            })
            if len(st.session_state.recent_requests) > 100:
                st.session_state.recent_requests = st.session_state.recent_requests[:100]
            return data
        else:
            return None
    except Exception: 
        st.session_state.recent_requests.insert(0, {
            "Request ID": f"req-{int(time.time() * 1000)}",
            "Agent": "unknown",
            "Strategy": strategy,
            "Latency (ms)": 0,
            "Status": "Failed",
            "Timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "Reason": "Request failed",
        })
        return None

def send_burst(strategy, count=20):
    from concurrent.futures import ThreadPoolExecutor
    import random
    strategies = ["round-robin", "least-connections", "random", "latency-aware", "weighted", "adaptive"]
    def _fire(i):
        strat = random.choice(strategies)
        return send_query(strat, f"Burst-{i+1}")
    with ThreadPoolExecutor(max_workers=5) as executor:
        list(executor.map(_fire, range(count)))

def get_val(d, key, port, default=0):
    return d.get(str(port), d.get(port, default))

# ═══════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 🛡️ AegisRoute")
    st.markdown("**AI Agent Orchestration & Intelligent Routing Infrastructure**")
    st.markdown("---")

    st.markdown("#### ⚡ Routing Engine")
    strategy = st.selectbox("Select Strategy", ["round-robin","least-connections","random","latency-aware","weighted","adaptive"])
    query_text = st.text_input("Test Query", "Hello, Agent!")
    if st.button("🚀 Send Query", use_container_width=True):
        r = send_query(strategy, query_text)
        if r: st.success(f"Success! Agent-{r.get('instance_port')}")
        else: st.error("Request failed")

    st.markdown("#### 🚀 Traffic Generator")
    tg1, tg2, tg3 = st.columns(3)
    with tg1:
        if st.button("50 Requests", use_container_width=True):
            with st.spinner("Sending 50 requests..."): send_burst(strategy, 50)
            st.success("50 requests sent!")
    with tg2:
        if st.button("100 Requests", use_container_width=True):
            with st.spinner("Sending 100 requests..."): send_burst(strategy, 100)
            st.success("100 requests sent!")
    with tg3:
        if st.button("500 Requests", use_container_width=True):
            with st.spinner("Sending 500 requests..."): send_burst(strategy, 500)
            st.success("500 requests sent!")

    st.markdown("---")
    st.markdown("#### 🔧 Failover Manager")
    sidebar_stats = fetch_stats()
    if sidebar_stats:
        for p in sidebar_stats.get("registered_instances", []):
            is_h = p in sidebar_stats.get("healthy_instances", [])
            c1, c2 = st.columns([1, 1])
            with c1:
                status_emoji = "🟢" if is_h else "🔴"
                st.markdown(f"**{status_emoji} Agent-{p}**")
            with c2:
                if is_h:
                    if st.button("Kill", key=f"k{p}", use_container_width=True):
                        api_post(f"/api/v1/agents/{p}/kill")
                else:
                    if st.button("Restore", key=f"r{p}", use_container_width=True):
                        api_post(f"/api/v1/agents/{p}/restore")

    st.markdown("---")
    st.markdown("#### 🎬 Demo Mode")
    demo_sidebar_stats = fetch_stats()
    if demo_sidebar_stats:
        if demo_sidebar_stats.get("demo_active", False):
            st.warning("🔴 Demo is LIVE!")
            if st.button("⏹️ Stop Demo", use_container_width=True):
                api_post("/api/v1/demo/stop")
        else:
            if st.button("🚀 Launch Demo", use_container_width=True, type="primary"):
                api_post("/api/v1/demo/start")

# ═══════════════════════════════════════════════════════════════════════════
# MAIN CONTENT — TAB LAYOUT
# ═══════════════════════════════════════════════════════════════════════════
placeholder = st.empty()
loop_count = 0

while True:
    loop_count += 1
    stats = fetch_stats()

    with placeholder.container():
        tab1, tab2, tab3, tab4 = st.tabs(["🏠 Infrastructure Overview", "📊 Traffic Analytics", "📝 Request Logs & Traces", "🎬 Demo Mode"])
        if not stats:
            st.error(f"⚠️ Cannot connect to AegisRoute Router at `{ROUTER_URL}`")
            st.info("Make sure the backend is running (cloud_runner.py) and set ROUTER_URL in secrets if deployed.")
            time.sleep(2); continue

        registered = stats.get("registered_instances", [])
        healthy = stats.get("healthy_instances", [])
        dead = stats.get("dead_instances", [])
        req_counts = stats.get("total_requests", {})
        err_counts = stats.get("error_counts", {})
        act_conn = stats.get("active_connections", {})
        telemetry = stats.get("telemetry", {})
        traces_data = stats.get("recent_traces", [])
        events = stats.get("event_log", [])
        rps_data = stats.get("rps_history", [])
        total_proc = stats.get("total_processed", 0)
        uptime = stats.get("uptime_seconds", 0)
        demo_active = stats.get("demo_active", False)
        total_errs = sum(err_counts.get(str(p), err_counts.get(p, 0)) for p in registered)
        err_rate = round((total_errs / max(total_proc, 1)) * 100, 1) if total_proc > 0 else 0
        current_rps = rps_data[-1]["rps"] if rps_data else 0
        failovers = stats.get("failovers_triggered", 0)
        avg_latency = stats.get("average_latency", 0)
        success_rate = 100 - err_rate if total_proc > 0 else 100

        # ───────────────────────────────────────────────────────────
        # TAB 1: INFRASTRUCTURE OVERVIEW
        # ───────────────────────────────────────────────────────────
        with tab1:
            # Hero Banner
            sys_status = "OPERATIONAL" if len(dead) == 0 else ("DEGRADED" if len(healthy) > 0 else "OFFLINE")
            scls = {"OPERATIONAL":"status-online","DEGRADED":"status-degraded","OFFLINE":"status-offline"}[sys_status]
            sym = {"OPERATIONAL":"🟢","DEGRADED":"🟡","OFFLINE":"🔴"}[sys_status]
            hours = int(uptime // 3600); mins = int((uptime % 3600) // 60); secs = int(uptime % 60)
            st.markdown(f"""<div class="hero-banner">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <div class="hero-title">AegisRoute Orchestration Engine</div>
                        <div class="hero-sub">AI Agent Orchestration & Intelligent Routing Infrastructure</div>
                    </div>
                    <div style="text-align:right;">
                        <span class="hero-status {scls}">{sym} {sys_status}</span>
                        <div style="color:#8b949e;font-size:0.8rem;margin-top:6px;">Uptime: {hours}h {mins}m {secs}s</div>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

            # Metric Cards
            m1, m2, m3, m4, m5, m6 = st.columns(6)
            metrics = [
                (m1, str(total_proc), "Total Requests", "val-cyan"),
                (m2, str(len(healthy)), "Healthy Agents", "val-green"),
                (m3, str(len(dead)), "Quarantined", "val-red"),
                (m4, str(failovers), "Failovers Triggered", "val-amber"),
                (m5, str(avg_latency), "Avg Latency (ms)", "val-cyan"),
                (m6, f"{success_rate}%", "Success Rate", "val-green" if success_rate > 95 else "val-amber"),
            ]
            for col, val, label, vcls in metrics:
                with col:
                    st.markdown(f'<div class="glass-card"><div class="card-value {vcls}">{val}</div><div class="card-label">{label}</div></div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Agent Registry
            st.markdown("#### 📋 Agent Registry")
            agent_cols = st.columns(len(registered))
            for i, p in enumerate(registered):
                with agent_cols[i]:
                    is_h = p in healthy
                    cls = "node-card-healthy" if is_h else "node-card-dead"
                    badge = '<span class="badge-on">🟢 Healthy</span>' if is_h else '<span class="badge-off">🔴 Quarantined</span>'
                    t = telemetry.get(str(p), {})
                    cpu = t.get("cpu_percent", 0); mem = t.get("memory_percent", 0)
                    hs = t.get("health_score", 0); lat = t.get("latency_ms", 0)
                    reqs = get_val(req_counts, "r", p)
                    conns = get_val(act_conn, "active_connections", p)
                    cpu_cls = "fill-green" if cpu < 60 else ("fill-amber" if cpu < 80 else "fill-red")
                    mem_cls = "fill-green" if mem < 60 else ("fill-amber" if mem < 80 else "fill-red")

                    st.markdown(f"""
                    <div class="node-card {cls}">
                        <div class="node-port">Agent-{p}</div>
                        {badge}
                        <div style="margin-top:12px;">
                            <div style="display:flex;justify-content:space-between;font-size:0.75rem;color:#8b949e;">
                                <span>Health Score</span><span>{hs}/100</span>
                            </div>
                            <div class="progress-wrap"><div class="progress-fill fill-green" style="width:{hs}%"></div></div>
                        </div>
                        <div style="margin-top:10px;">
                            <div style="display:flex;justify-content:space-between;font-size:0.75rem;color:#8b949e;">
                                <span>CPU</span><span>{cpu}%</span>
                            </div>
                            <div class="progress-wrap"><div class="progress-fill {cpu_cls}" style="width:{cpu}%"></div></div>
                        </div>
                        <div style="margin-top:10px;">
                            <div style="display:flex;justify-content:space-between;font-size:0.75rem;color:#8b949e;">
                                <span>Memory</span><span>{mem}%</span>
                            </div>
                            <div class="progress-wrap"><div class="progress-fill {mem_cls}" style="width:{mem}%"></div></div>
                        </div>
                        <div style="margin-top:12px;font-size:0.85rem;">
                            <div>⏱️ Latency: <span style="color:#00d4ff;font-family:JetBrains Mono">{lat}ms</span></div>
                            <div>📨 Requests: <span style="color:#00ff88;font-family:JetBrains Mono">{reqs}</span></div>
                            <div>🔗 Active: <span style="color:#ffaa00;font-family:JetBrains Mono">{conns}</span></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Request Flow & Routing Decision
            flow_col, decision_col = st.columns([1, 1])
            with flow_col:
                st.markdown("#### 🔄 Request Flow Visualization")
                if st.session_state.recent_requests:
                    for req in st.session_state.recent_requests[:8]:
                        st.markdown(f"""
                        <div style="border-left:3px solid #00d4ff;padding-left:12px;margin-bottom:8px;background:#0d1117;border-radius:8px;">
                            <div style="font-family:JetBrains Mono;font-size:0.9rem;font-weight:600;color:#00d4ff;">Request #{req['Request ID']}</div>
                            <div style="display:flex;align-items:center;gap:8px;margin-top:4px;">
                                <span style="color:#8b949e;">→</span>
                                <span style="background:rgba(0,255,136,0.1);color:#00ff88;padding:2px 8px;border-radius:4px;font-family:JetBrains Mono">Agent-{req['Agent']}</span>
                            </div>
                            <div style="display:flex;gap:16px;margin-top:4px;font-size:0.8rem;color:#8b949e;">
                                <span>Strategy: {req['Strategy']}</span>
                                <span>Latency: {req['Latency (ms)']}ms</span>
                                <span>{req['Timestamp']}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("Send requests using the sidebar to see live flow!")

            with decision_col:
                st.markdown("#### 🧠 Routing Decision Explainer")
                if st.session_state.recent_requests:
                    latest_req = st.session_state.recent_requests[0]
                    conn_list = []
                    for p in registered:
                        conn_list.append(f"Agent-{p} = {get_val(act_conn, 'active_connections', p)}")
                    st.markdown(f"""
                    <div class="node-card" style="border-left:3px solid #00d4ff;">
                        <div style="font-weight:600;color:#00ff88;margin-bottom:8px;">Selected Agent</div>
                        <div style="font-family:JetBrains Mono;font-size:1.3rem;color:#e6edf3;">Agent-{latest_req['Agent']}</div>
                        <div style="margin-top:12px;">
                            <div style="color:#8b949e;margin-bottom:4px;">Decision Reason:</div>
                            <div style="background:#0d1117;padding:10px 14px;border-radius:6px;font-family:JetBrains Mono;font-size:0.9rem;">
                                {latest_req['Reason']}
                            </div>
                        </div>
                        <div style="margin-top:12px;">
                            <div style="color:#8b949e;margin-bottom:4px;">Current Connections:</div>
                            <div style="background:#0d1117;padding:10px 14px;border-radius:6px;">
                                {'<br>'.join(conn_list)}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("Send a request to see the decision explainer!")

            st.markdown("<br>", unsafe_allow_html=True)

            # Failover Alert Banner
            if len(dead) > 0:
                st.session_state.last_failover = time.time()
            if st.session_state.last_failover and time.time() - st.session_state.last_failover < 12:
                st.markdown("""
                <div style="background:rgba(255,68,68,0.1);border:1px solid rgba(255,68,68,0.3);border-radius:12px;padding:16px 24px;text-align:center;margin-bottom:20px;">
                    <div style="font-size:1.6rem;font-weight:700;color:#ff4444;animation:flash 0.8s infinite;">⚠️ FAILOVER ACTIVATED</div>
                    <div style="color:#8b949e;margin-top:6px;">Traffic automatically rerouted to healthy agents — zero downtime!</div>
                </div>
                """, unsafe_allow_html=True)

        # ───────────────────────────────────────────────────────────
        # TAB 2: TRAFFIC ANALYTICS
        # ───────────────────────────────────────────────────────────
        with tab2:
            st.markdown("#### 📈 Requests Per Second (RPS)")
            if rps_data:
                rps_df = pd.DataFrame(rps_data)
                rps_df["time"] = pd.to_datetime(rps_df["time"], unit="s")
                st.line_chart(rps_df.set_index("time")["rps"], color="#00d4ff", height=250)
            else:
                st.info("Waiting for RPS data...")

            st.markdown("---")

            a1, a2 = st.columns(2)
            with a1:
                st.markdown("#### 📊 Request Distribution by Agent")
                dist_df = pd.DataFrame({
                    "Agent": [f"Agent-{p}" for p in registered],
                    "Requests": [get_val(req_counts, "r", p) for p in registered]
                })
                if dist_df["Requests"].sum() > 0:
                    st.bar_chart(dist_df.set_index("Agent"), color="#00d4ff", height=250)
                else:
                    st.info("No requests yet!")
            with a2:
                st.markdown("#### 🎯 Strategy Usage")
                if st.session_state.recent_requests:
                    strat_counts = {}
                    for req in st.session_state.recent_requests:
                        s = req["Strategy"]
                        strat_counts[s] = strat_counts.get(s, 0) + 1
                    strat_df = pd.DataFrame({
                        "Strategy": list(strat_counts.keys()),
                        "Count": list(strat_counts.values())
                    })
                    st.bar_chart(strat_df.set_index("Strategy"), color="#00ff88", height=250)
                else:
                    st.info("Send requests to see strategy distribution!")

            st.markdown("---")

            b1, b2 = st.columns(2)
            with b1:
                st.markdown("#### ⏱️ Latency per Agent")
                lat_df = pd.DataFrame({
                    "Agent": [f"Agent-{p}" for p in registered],
                    "Latency (ms)": [telemetry.get(str(p), {}).get("latency_ms", 0) for p in registered]
                })
                st.bar_chart(lat_df.set_index("Agent"), color="#ffaa00", height=250)
            with b2:
                st.markdown("#### 🔥 Load Heatmap")
                heat_data = []
                for p in registered:
                    t = telemetry.get(str(p), {})
                    heat_data.append({
                        "Agent": f"Agent-{p}",
                        "CPU %": t.get("cpu_percent", 0),
                        "Memory %": t.get("memory_percent", 0),
                        "Health Score": t.get("health_score", 0)
                    })
                st.dataframe(pd.DataFrame(heat_data), use_container_width=True, hide_index=True)

        # ───────────────────────────────────────────────────────────
        # TAB 3: REQUEST LOGS & TRACES
        # ───────────────────────────────────────────────────────────
        with tab3:
            log_col, trace_col = st.columns([1, 2])
            with log_col:
                st.markdown("#### 📋 Health Monitor Events")
                if events:
                    for e in reversed(events[-20:]):
                        ts = datetime.fromtimestamp(e["timestamp"]).strftime("%H:%M:%S")
                        lvl = e["level"]
                        lcls_map = {
                            "INFO": "log-info",
                            "WARN": "log-warn",
                            "CRITICAL": "log-critical",
                            "RECOVERY": "log-recovery"
                        }
                        lcls = lcls_map.get(lvl, "log-info")
                        st.markdown(f'<div class="log-entry {lcls}"><span style="color:#8b949e;">{ts}</span> [{lvl}] Port {e["port"]} — {e["message"]}</div>', unsafe_allow_html=True)
                else:
                    st.info("No events yet!")
            with trace_col:
                st.markdown("#### 📝 Request Logs")
                if st.session_state.recent_requests:
                    log_df = pd.DataFrame(st.session_state.recent_requests)
                    st.dataframe(log_df, use_container_width=True, hide_index=True)
                else:
                    st.info("Send requests to see logs!")

        # ───────────────────────────────────────────────────────────
        # TAB 4: DEMO MODE
        # ───────────────────────────────────────────────────────────
        with tab4:
            st.markdown("""
            <div class="hero-banner" style="text-align:center;">
                <div class="hero-title">🎬 Hackathon Demo Mode</div>
                <div class="hero-sub">One-click automated demonstration of AegisRoute's orchestration & self-healing capabilities</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("")

            d1, d2, d3 = st.columns([1,3,1])
            with d2:
                if demo_active:
                    st.warning("🔴 Demo is LIVE! Watch the Infrastructure Overview tab!")
                    st.info("To stop the demo, use the controls in the left sidebar.")
                else:
                    st.success("Ready to launch!")
                    st.info("Click **🚀 Launch Demo** in the left sidebar to start the automated sequence.")

            st.markdown("---")
            st.markdown("#### 📋 Demo Sequence")
            st.markdown("""
            | Phase | Duration | What Happens |
            |-------|----------|--------------|
            | 1. Steady Traffic | ~15s | Generates traffic across all 6 routing strategies to build baseline metrics |
            | 2. Simulate Failure | Instant | Randomly kills one agent node to demonstrate infrastructure failure |
            | 3. Failover & Reroute | ~15s | Continues traffic to show automatic failover to healthy agents |
            | 4. Self-Heal | Instant | Restores the failed agent — watch it rejoin the healthy pool! |
            | 5. Recovery Traffic | ~10s | Final traffic burst to prove zero-downtime recovery & balanced distribution |
            """)
            st.markdown("""
            > 💡 **Pro Tip for Judges:** Open the **Infrastructure Overview** tab in another browser window while the demo runs.
            > Watch the agent cards update in real-time!
            """)

    time.sleep(1.5)
