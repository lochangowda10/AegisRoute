# AegisRoute 🛡️
### AI-Native Agent Orchestration & Intelligent Routing Infrastructure

AegisRoute is a production-grade, self-healing API gateway and orchestration engine purpose-built for scalable multi-agent AI systems. It delivers intelligent traffic distribution, autonomous failover, and enterprise-grade observability — all in real-time.

## 🌟 Core Capabilities
- **6 Intelligent Routing Strategies**: Round-Robin, Least-Connections, Random, Latency-Aware, Weighted, Adaptive
- **Autonomous Failover & Self-Healing**: Nodes are automatically quarantined on failure and re-injected upon recovery
- **NOC Terminal Dashboard**: Datadog-inspired dark-themed UI with glassmorphism cards, live charts, request tracing, and event logs
- **One-Click Demo Mode**: Automated traffic generation + chaos engineering to showcase the full resilience lifecycle
- **Request Tracing**: Every request gets a trace ID with full latency breakdown and routing explanation

## 🏗️ Architecture
```
Client → AegisRoute Gateway (Port 8000)
             ├── Round-Robin / Least-Connections / Random
             ├── Latency-Aware / Weighted / Adaptive
             ├── Health Checker Daemon (3s interval)
             ├── Metrics Collector (CPU, Memory, Latency)
             ├── Request Tracer (Trace ID, timing breakdown)
             └── Demo Engine (automated chaos + traffic)
                    ↓
         Agent Pool: [8001] [8002] [8003]
```

## 🚀 Quick Start

```bash
pip install -r requirements.txt

# Terminal 1-3: Start agent nodes
python agent_instance.py --port 8001
python agent_instance.py --port 8002
python agent_instance.py --port 8003

# Terminal 4: Start router
python router.py

# Terminal 5: Start dashboard
streamlit run dashboard.py

# Terminal 6: Run stress test
python stress_test.py --strategy adaptive --requests 50
python stress_test.py --burst
python stress_test.py --chaos
```

## ☁️ Cloud Deployment
- **Backend**: Deploy via Render.com with `python cloud_runner.py` as the start command
- **Dashboard**: Deploy via Streamlit Cloud, set `ROUTER_URL` to your Render URL in secrets

## 🧪 Demo Mode
Click the **🎬 Demo Mode** tab in the dashboard and press **Start Demo**.
It automatically generates traffic → crashes a node → reroutes traffic → restores the node → proves zero-downtime recovery.
