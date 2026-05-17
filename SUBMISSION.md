# AegisRoute — AI-Native Agent Orchestration Infrastructure 🛡️

> **A production-grade, self-healing API gateway and intelligent routing engine for scalable multi-agent AI systems.**

AegisRoute is not a simple load balancer. It is an **AI-native orchestration platform** that provides intelligent traffic distribution, autonomous failover, predictive routing, and enterprise-grade observability — all operating in real-time with zero-downtime guarantees.

---

## 🌟 Value Proposition

| Capability | What It Does |
|---|---|
| **Intelligent Routing** | 6 hot-swappable strategies including latency-aware and adaptive routing |
| **Self-Healing Architecture** | Automatic quarantine on failure, automatic re-injection on recovery |
| **Full Observability** | Real-time metrics, request tracing, event logging, traffic analytics |
| **Chaos Engineering** | Built-in fault injection to prove resilience under pressure |
| **Demo Engine** | One-click automated demonstration of the entire resilience lifecycle |

---

## 🏗️ System Architecture

```
                    ┌──────────────────────────────────┐
                    │       Client / Stress Tester      │
                    └──────────────┬───────────────────┘
                                   │ POST /router/route?strategy=...
                    ┌──────────────▼───────────────────┐
                    │   AegisRoute Gateway (Port 8000)  │
                    │                                   │
                    │  ┌─────────────────────────────┐  │
                    │  │   Load Balancing Engine      │  │
                    │  │  ┌─────────┐ ┌───────────┐  │  │
                    │  │  │Round    │ │Least      │  │  │
                    │  │  │Robin    │ │Connections│  │  │
                    │  │  ├─────────┤ ├───────────┤  │  │
                    │  │  │Latency  │ │Weighted   │  │  │
                    │  │  │Aware    │ │           │  │  │
                    │  │  ├─────────┤ ├───────────┤  │  │
                    │  │  │Random   │ │Adaptive   │  │  │
                    │  │  └─────────┘ └───────────┘  │  │
                    │  └─────────────────────────────┘  │
                    │                                   │
                    │  ┌──────────┐ ┌───────────────┐  │
                    │  │ Health   │ │ Request       │  │
                    │  │ Daemon   │ │ Tracer        │  │
                    │  └──────────┘ └───────────────┘  │
                    │  ┌──────────┐ ┌───────────────┐  │
                    │  │ Metrics  │ │ Demo          │  │
                    │  │Collector │ │ Engine        │  │
                    │  └──────────┘ └───────────────┘  │
                    └───────┬──────────┬──────────┬────┘
                            │          │          │
                    ┌───────▼──┐ ┌─────▼────┐ ┌──▼───────┐
                    │Agent 8001│ │Agent 8002│ │Agent 8003│
                    │ LLM Node │ │ LLM Node │ │ LLM Node │
                    └──────────┘ └──────────┘ └──────────┘
```

---

## 🧠 Core Routing Logic

### Round-Robin
```python
node = healthy[round_robin_index % len(healthy)]
round_robin_index = (round_robin_index + 1) % len(healthy)
return node, f"Round-robin index {round_robin_index} → port {node}"
```

### Least-Connections
```python
async with active_connections_lock:
    node = min(healthy, key=lambda p: active_connections[p])
return node, f"Lowest active connections ({conns}) → port {node}"
```

### Latency-Aware
```python
node = min(healthy, key=lambda p: daemon.telemetry[p].latency_ms)
return node, f"Lowest latency ({lat}ms) → port {node}"
```

### Adaptive (Context-Aware)
```python
if dead_count > 0:
    # Failover-first: route to healthiest node
    node = max(healthy, key=lambda p: daemon.telemetry[p].health_score)
    return node, f"Adaptive (failover-first) → healthiest port {node}"
else:
    # All healthy: use least-connections
    node = min(healthy, key=lambda p: active_connections[p])
    return node, f"Adaptive (least-connections) → port {node}"
```

---

## 🧪 Test the API Gateway

**1. Check System Status**
```bash
curl -X GET https://YOUR_RENDER_URL/api/v1/balancer/stats
```

**2. Route a Request (Adaptive Strategy)**
```bash
curl -X POST "https://YOUR_RENDER_URL/router/route?strategy=adaptive" \
     -H "Content-Type: application/json" \
     -d '{"query":"Solve differential equations"}'
```

**3. View the Dashboard**
Visit the deployed Streamlit URL and click the **🎬 Demo Mode** tab for an automated showcase.

---

## 🔗 Live Links
- **Dashboard**: https://aegisroute.streamlit.app/
- **Source Code**: https://github.com/lochangowda10/AegisRoute
