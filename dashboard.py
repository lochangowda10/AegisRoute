"""
AegisRoute — NOC Terminal Dashboard v2.0
Enterprise-grade, 4-tab Datadog/Grafana-inspired observability platform.
"""
import streamlit as st
import httpx, os, time, json
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="AegisRoute NOC Terminal", layout="wide", page_icon="🛡️")

ROUTER_URL = os.environ.get("ROUTER_URL", "http://127.0.0.1:8000")

# ═══════════════════════════════════════════════════════════════════════════
# GLOBAL CSS — Dark Futuristic NOC Terminal Theme
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
        return r.json() if r.status_code == 200 else None
    except Exception: return None

def send_burst(strategy, count=20):
    results = []
    for i in range(count):
        r = send_query(strategy, f"Burst #{i+1}")
        if r: results.append(r)
    return results

def get_val(d, key, port, default=0):
    """Safely get a value from a dict that may have string or int keys."""
    return d.get(str(port), d.get(port, default))

# ═══════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 🛡️ AegisRoute")
    st.markdown("*AI Orchestration Engine*")
    st.markdown("---")

    st.markdown("#### ⚡ Quick Actions")
    strategy = st.selectbox("Routing Strategy", ["round-robin","least-connections","random","latency-aware","weighted","adaptive"])
    query_text = st.text_input("Test Query", "Inference request")
    if st.button("🚀 Send Query", use_container_width=True):
        r = send_query(strategy, query_text)
        if r: st.success(f"Port {r.get('instance_port')} | {r.get('routing_reason','')[:50]}")
        else: st.error("Request failed")

    if st.button("💥 Send Traffic Burst (20)", use_container_width=True):
        with st.spinner("Sending 20 requests..."): send_burst(strategy, 20)
        st.success("Burst complete!")

    st.markdown("---")
    st.markdown("#### 🔧 Chaos Engineering")
    sidebar_stats = fetch_stats()
    if sidebar_stats:
        for p in sidebar_stats.get("registered_instances", []):
            is_h = p in sidebar_stats.get("healthy_instances", [])
            c1, c2 = st.columns(2)
            with c1: st.markdown(f"**:{('green' if is_h else 'red')}[Node {p}]**")
            with c2:
                if is_h:
                    if st.button(f"Kill", key=f"k{p}", use_container_width=True): api_post(f"/api/v1/agents/{p}/kill")
                else:
                    if st.button(f"Heal", key=f"r{p}", use_container_width=True): api_post(f"/api/v1/agents/{p}/restore")

    st.markdown("---")
    st.markdown("#### 🎬 Demo Engine")
    demo_sidebar_stats = fetch_stats()
    if demo_sidebar_stats:
        if demo_sidebar_stats.get("demo_active", False):
            st.warning("🔴 Demo is currently LIVE")
            if st.button("⏹️ Stop Demo", use_container_width=True): api_post("/api/v1/demo/stop")
        else:
            if st.button("🚀 Start Demo", use_container_width=True, type="primary"): api_post("/api/v1/demo/start")

# ═══════════════════════════════════════════════════════════════════════════
# MAIN CONTENT — TAB LAYOUT
# ═══════════════════════════════════════════════════════════════════════════
placeholder = st.empty()

while True:
    stats = fetch_stats()

    with placeholder.container():
        tab1, tab2, tab3, tab4 = st.tabs(["🖥️ Command Center", "📈 Traffic Analytics", "🔍 Traces & Logs", "🎬 Demo Mode"])
        if not stats:
            st.error(f"⚠️ Cannot connect to AegisRoute Router at `{ROUTER_URL}`")
            st.info("Make sure the backend is running. If deployed on Render, set `ROUTER_URL` in Streamlit secrets.")
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
        err_rate = round((total_errs / max(total_proc, 1)) * 100, 1)
        current_rps = rps_data[-1]["rps"] if rps_data else 0

        # ───────────────────────────────────────────────────────────
        # TAB 1: COMMAND CENTER
        # ───────────────────────────────────────────────────────────
        with tab1:
            # Hero Banner
            sys_status = "OPERATIONAL" if len(dead) == 0 else ("DEGRADED" if len(healthy) > 0 else "OFFLINE")
            scls = {"OPERATIONAL":"status-online","DEGRADED":"status-degraded","OFFLINE":"status-offline"}[sys_status]
            sym = {"OPERATIONAL":"●","DEGRADED":"◐","OFFLINE":"✕"}[sys_status]
            hours = int(uptime // 3600); mins = int((uptime % 3600) // 60); secs = int(uptime % 60)
            st.markdown(f"""<div class="hero-banner">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div><div class="hero-title">AegisRoute Orchestration Engine</div>
                    <div class="hero-sub">AI-Native Agent Load Balancing & Resilience Infrastructure</div></div>
                    <div style="text-align:right;"><span class="hero-status {scls}">{sym} {sys_status}</span>
                    <div style="color:#8b949e;font-size:0.8rem;margin-top:6px;">Uptime: {hours}h {mins}m {secs}s</div></div>
                </div></div>""", unsafe_allow_html=True)

            # Metric Cards
            c1,c2,c3,c4,c5,c6 = st.columns(6)
            cards = [
                (c1, str(len(registered)), "Managed Nodes", "val-cyan"),
                (c2, str(len(healthy)), "Healthy", "val-green"),
                (c3, str(len(dead)), "Quarantined", "val-red"),
                (c4, str(total_proc), "Total Requests", "val-cyan"),
                (c5, str(current_rps), "Req/Sec", "val-amber"),
                (c6, f"{err_rate}%", "Error Rate", "val-red" if err_rate > 5 else "val-green"),
            ]
            for col, val, label, vcls in cards:
                with col:
                    st.markdown(f'<div class="glass-card"><div class="card-value {vcls}">{val}</div><div class="card-label">{label}</div></div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Agent Topology Grid
            st.markdown("#### 🌐 Agent Topology")
            node_cols = st.columns(len(registered))
            for i, p in enumerate(registered):
                with node_cols[i]:
                    is_h = p in healthy
                    cls = "node-card-healthy" if is_h else "node-card-dead"
                    badge = '<span class="badge-on">● Operational</span>' if is_h else '<span class="badge-off">▲ Quarantined</span>'
                    t = telemetry.get(str(p), {})
                    cpu = t.get("cpu_percent", 0); mem = t.get("memory_percent", 0)
                    hs = t.get("health_score", 0); lat = t.get("latency_ms", 0)
                    model = t.get("model", "—"); ver = t.get("version", "—")
                    cpu_cls = "fill-green" if cpu < 60 else ("fill-amber" if cpu < 80 else "fill-red")
                    mem_cls = "fill-green" if mem < 60 else ("fill-amber" if mem < 80 else "fill-red")
                    hs_cls = "fill-green" if hs > 60 else ("fill-amber" if hs > 30 else "fill-red")
                    reqs = get_val(req_counts, "total_requests", p)
                    conns = get_val(act_conn, "active_connections", p)

                    st.markdown(f"""<div class="node-card {cls}">
                        <div class="node-port">:{p}</div>
                        {badge}
                        <div style="margin-top:10px;font-size:0.8rem;color:#8b949e;">{model} v{ver}</div>
                        <div style="margin-top:10px;">
                            <div style="display:flex;justify-content:space-between;font-size:0.75rem;color:#8b949e;"><span>Health</span><span>{hs}/100</span></div>
                            <div class="progress-wrap"><div class="progress-fill {hs_cls}" style="width:{hs}%"></div></div>
                            <div style="display:flex;justify-content:space-between;font-size:0.75rem;color:#8b949e;margin-top:6px;"><span>CPU</span><span>{cpu}%</span></div>
                            <div class="progress-wrap"><div class="progress-fill {cpu_cls}" style="width:{cpu}%"></div></div>
                            <div style="display:flex;justify-content:space-between;font-size:0.75rem;color:#8b949e;margin-top:6px;"><span>Memory</span><span>{mem}%</span></div>
                            <div class="progress-wrap"><div class="progress-fill {mem_cls}" style="width:{mem}%"></div></div>
                        </div>
                        <div style="margin-top:10px;font-size:0.8rem;">
                            <span style="color:#8b949e;">Latency:</span> <span style="color:#00d4ff;">{lat}ms</span><br>
                            <span style="color:#8b949e;">Requests:</span> <span style="color:#e6edf3;">{reqs}</span> |
                            <span style="color:#8b949e;">Active:</span> <span style="color:#ffaa00;">{conns}</span>
                        </div></div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Traffic Distribution Bar Chart
            st.markdown("#### 📊 Traffic Distribution")
            chart_df = pd.DataFrame({
                "Port": [f":{p}" for p in registered],
                "Requests": [get_val(req_counts, "r", p) for p in registered]
            })
            if chart_df["Requests"].sum() > 0:
                st.bar_chart(chart_df.set_index("Port"), color="#00d4ff", height=250)
            else:
                st.info("No traffic yet. Send requests using the sidebar controls.")

        # ───────────────────────────────────────────────────────────
        # TAB 2: TRAFFIC ANALYTICS
        # ───────────────────────────────────────────────────────────
        with tab2:
            st.markdown("#### 📈 Requests Per Second (Rolling)")
            if rps_data:
                rps_df = pd.DataFrame(rps_data)
                rps_df["time"] = pd.to_datetime(rps_df["time"], unit="s")
                st.line_chart(rps_df.set_index("time")["rps"], color="#00d4ff", height=200)
            else:
                st.info("Waiting for RPS data...")

            st.markdown("---")
            ac1, ac2 = st.columns(2)
            with ac1:
                st.markdown("#### ⏱️ Latency per Node")
                lat_df = pd.DataFrame({
                    "Port": [f":{p}" for p in registered],
                    "Latency (ms)": [telemetry.get(str(p), {}).get("latency_ms", 0) for p in registered]
                })
                st.bar_chart(lat_df.set_index("Port"), color="#ffaa00", height=200)
            with ac2:
                st.markdown("#### 🔴 Error Distribution")
                err_df = pd.DataFrame({
                    "Port": [f":{p}" for p in registered],
                    "Errors": [err_counts.get(str(p), err_counts.get(p, 0)) for p in registered]
                })
                st.bar_chart(err_df.set_index("Port"), color="#ff4444", height=200)

            st.markdown("---")
            st.markdown("#### 🔥 Load Heatmap (CPU & Memory)")
            heat_data = []
            for p in registered:
                t = telemetry.get(str(p), {})
                heat_data.append({"Node": f":{p}", "CPU %": t.get("cpu_percent", 0), "Memory %": t.get("memory_percent", 0), "Health Score": t.get("health_score", 0)})
            st.dataframe(pd.DataFrame(heat_data), use_container_width=True, hide_index=True)

        # ───────────────────────────────────────────────────────────
        # TAB 3: TRACES & LOGS
        # ───────────────────────────────────────────────────────────
        with tab3:
            log_col, trace_col = st.columns([1, 2])

            with log_col:
                st.markdown("#### 📋 Event Log")
                if events:
                    for e in reversed(events[-15:]):
                        ts = datetime.fromtimestamp(e["timestamp"]).strftime("%H:%M:%S")
                        lvl = e["level"]
                        lcls = {"INFO":"log-info","WARN":"log-warn","CRITICAL":"log-critical","RECOVERY":"log-recovery"}.get(lvl,"log-info")
                        st.markdown(f'<div class="log-entry {lcls}"><span style="color:#8b949e;">{ts}</span> [{lvl}] Port {e["port"]} — {e["message"]}</div>', unsafe_allow_html=True)
                else:
                    st.info("No events yet.")

            with trace_col:
                st.markdown("#### 🔍 Request Traces")
                if traces_data:
                    trace_rows = []
                    for t in reversed(traces_data[-15:]):
                        trace_rows.append({
                            "Trace ID": t.get("trace_id", ""),
                            "Time": datetime.fromtimestamp(t.get("timestamp", 0)).strftime("%H:%M:%S"),
                            "Strategy": t.get("strategy", ""),
                            "Node": f":{t.get('target_port', '')}",
                            "Total (ms)": t.get("total_ms", 0),
                            "Status": t.get("status", ""),
                            "Reason": (t.get("routing_reason", ""))[:60],
                        })
                    st.dataframe(pd.DataFrame(trace_rows), use_container_width=True, hide_index=True)
                else:
                    st.info("No traces yet. Send some requests!")

        # ───────────────────────────────────────────────────────────
        # TAB 4: DEMO MODE
        # ───────────────────────────────────────────────────────────
        with tab4:
            st.markdown("""<div class="hero-banner" style="text-align:center;">
                <div class="hero-title">🎬 Hackathon Demo Mode</div>
                <div class="hero-sub">One-click automated demonstration of AegisRoute's orchestration & self-healing capabilities</div></div>""", unsafe_allow_html=True)

            st.markdown("")
            dc1, dc2, dc3 = st.columns([1,2,1])
            with dc2:
                if demo_active:
                    st.warning("🔴 Demo is LIVE — watch the Command Center and Analytics tabs!")
                    st.info("To stop the demo, use the 🎬 Demo Engine controls in the left sidebar.")
                else:
                    st.success("Ready to launch demo.")
                    st.info("Click **🚀 Start Demo** in the left sidebar to begin.")

            st.markdown("---")
            st.markdown("#### 📋 Demo Sequence")
            st.markdown("""
| Phase | Duration | What Happens |
|-------|----------|--------------|
| **1. Steady Traffic** | ~15s | Sends requests across all 6 strategies to build baseline metrics |
| **2. Node Crash** | Instant | Randomly kills one agent node to simulate infrastructure failure |
| **3. Pressure Test** | ~15s | Continues traffic — demonstrates automatic failover & rerouting |
| **4. Self-Healing** | Instant | Restores the crashed node — watch it re-enter the healthy pool |
| **5. Recovery Traffic** | ~10s | Final burst proves zero-downtime recovery with balanced distribution |
""")
            st.markdown("""
> **💡 Tip for Judges:** Open the **Command Center** tab in another browser window while the demo runs.
> Watch the node cards update in real-time: health scores drop, badges flash red, traffic reroutes,
> and then the recovered node glows green again — all automatically.
""")

    time.sleep(1.5)
