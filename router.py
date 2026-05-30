"""
AegisRoute — Core Routing Engine v2.0
Central FastAPI proxy with 6 load-balancing strategies, request tracing,
routing explanations, and a built-in hackathon demo engine.
"""
import asyncio, httpx, logging, random, time, uuid
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
from collections import deque
from health_checker import HealthCheckerDaemon

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AegisRoute Orchestration Engine v2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ---------------------------------------------------------------------------
# Registry & State
# ---------------------------------------------------------------------------
REGISTERED_PORTS = [8001, 8002, 8003]  # Keep all 3 agents
daemon = HealthCheckerDaemon(REGISTERED_PORTS)

request_counts: Dict[int, int] = {p: 0 for p in REGISTERED_PORTS}
error_counts: Dict[int, int] = {p: 0 for p in REGISTERED_PORTS}
active_connections: Dict[int, int] = {p: 0 for p in REGISTERED_PORTS}
active_connections_lock = asyncio.Lock()
round_robin_index = 0
total_requests = 0
start_time = time.time()

# Request tracing (rolling buffer, reduced size for memory)
traces: deque = deque(maxlen=30)
# RPS tracking
rps_history: deque = deque(maxlen=30)  # last 30 seconds
_rps_counter = 0
_last_rps_time = time.time()

# Demo mode
demo_running = False
demo_task: Optional[asyncio.Task] = None

STRATEGY_NAMES = ["round-robin", "least-connections", "random", "latency-aware", "weighted", "adaptive"]

class QueryRequest(BaseModel):
    query: str

# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def startup():
    asyncio.create_task(daemon.run())
    asyncio.create_task(_rps_tracker())

@app.on_event("shutdown")
async def shutdown():
    daemon.stop()

async def _rps_tracker():
    """Track requests-per-second every second."""
    global _rps_counter, _last_rps_time
    while True:
        await asyncio.sleep(1)
        rps_history.append({"time": time.time(), "rps": _rps_counter})
        _rps_counter = 0

# ---------------------------------------------------------------------------
# Load Balancing Strategies
# ---------------------------------------------------------------------------
async def select_node(strategy: str) -> tuple[int, str]:
    """Returns (port, routing_reason)."""
    healthy = sorted(daemon.healthy_pool)
    if not healthy:
        raise HTTPException(status_code=503, detail="No healthy nodes available")

    global round_robin_index

    if strategy == "round-robin":
        node = healthy[round_robin_index % len(healthy)]
        reason = f"Round-robin index {round_robin_index} → port {node}"
        round_robin_index = (round_robin_index + 1) % len(healthy)
        return node, reason

    elif strategy == "least-connections":
        async with active_connections_lock:
            node = min(healthy, key=lambda p: active_connections[p])
        conns = active_connections[node]
        return node, f"Lowest active connections ({conns}) → port {node}"

    elif strategy == "random":
        node = random.choice(healthy)
        return node, f"Random selection from {len(healthy)} healthy nodes → port {node}"

    elif strategy == "latency-aware":
        node = min(healthy, key=lambda p: daemon.telemetry[p].latency_ms)
        lat = daemon.telemetry[node].latency_ms
        return node, f"Lowest latency ({lat}ms) → port {node}"

    elif strategy == "weighted":
        weights = [max(1, daemon.telemetry[p].health_score) for p in healthy]
        node = random.choices(healthy, weights=weights, k=1)[0]
        score = daemon.telemetry[node].health_score
        return node, f"Weighted by health score ({score}/100) → port {node}"

    elif strategy == "adaptive":
        dead_count = len(daemon.dead_pool)
        if dead_count > 0:
            # Failover-first: route to healthiest node
            node = max(healthy, key=lambda p: daemon.telemetry[p].health_score)
            return node, f"Adaptive (failover-first, {dead_count} dead) → healthiest port {node}"
        else:
            # All healthy: use least-connections
            async with active_connections_lock:
                node = min(healthy, key=lambda p: active_connections[p])
            return node, f"Adaptive (all healthy, least-connections) → port {node}"
    else:
        raise HTTPException(status_code=400, detail=f"Unknown strategy: {strategy}")

# ---------------------------------------------------------------------------
# Routing Endpoint
# ---------------------------------------------------------------------------
@app.post("/router/route")
async def route_query(request: QueryRequest, strategy: str = Query("round-robin")):
    global total_requests, _rps_counter
    trace_id = str(uuid.uuid4())[:8]
    t_start = time.time()

    target_port, reason = await select_node(strategy)

    async with active_connections_lock:
        active_connections[target_port] += 1
    try:
        async with httpx.AsyncClient() as client:
            t_fwd = time.time()
            resp = await client.post(
                f"http://127.0.0.1:{target_port}/query",
                json={"query": request.query}, timeout=10.0)
            t_resp = time.time()

            if resp.status_code == 200:
                request_counts[target_port] += 1
                total_requests += 1
                _rps_counter += 1
                data = resp.json()
                data["trace_id"] = trace_id
                data["strategy"] = strategy
                data["routing_reason"] = reason
                # Store trace
                traces.append({
                    "trace_id": trace_id,
                    "timestamp": t_start,
                    "strategy": strategy,
                    "target_port": target_port,
                    "routing_reason": reason,
                    "queue_ms": round((t_fwd - t_start) * 1000, 1),
                    "forward_ms": round((t_resp - t_fwd) * 1000, 1),
                    "total_ms": round((t_resp - t_start) * 1000, 1),
                    "status": "success",
                })
                return data
            else:
                error_counts[target_port] += 1
                raise HTTPException(status_code=resp.status_code, detail="Agent error")
    except httpx.RequestError as e:
        error_counts[target_port] += 1
        traces.append({
            "trace_id": trace_id, "timestamp": t_start, "strategy": strategy,
            "target_port": target_port, "routing_reason": reason,
            "queue_ms": 0, "forward_ms": 0, "total_ms": 0, "status": "error",
        })
        raise HTTPException(status_code=502, detail="Target node unreachable")
    finally:
        async with active_connections_lock:
            active_connections[target_port] -= 1

# ---------------------------------------------------------------------------
# Stats Endpoint (expanded)
# ---------------------------------------------------------------------------
@app.get("/api/v1/balancer/stats")
async def get_stats():
    uptime = round(time.time() - start_time, 1)
    telemetry_data = {}
    total_latency = 0.0
    healthy_count = 0
    for p in REGISTERED_PORTS:
        t = daemon.telemetry[p]
        telemetry_data[str(p)] = {
            "latency_ms": t.latency_ms, "cpu_percent": t.cpu_percent,
            "memory_percent": t.memory_percent, "health_score": t.health_score,
            "uptime_seconds": t.uptime_seconds, "model": t.model,
            "version": t.version, "region": t.region,
        }
        if p in daemon.healthy_pool:
            total_latency += t.latency_ms
            healthy_count += 1
    average_latency = round(total_latency / max(healthy_count, 1), 1) if healthy_count > 0 else 0
    return {
        "registered_instances": REGISTERED_PORTS,
        "healthy_instances": sorted(daemon.healthy_pool),
        "dead_instances": sorted(daemon.dead_pool),
        "total_requests": request_counts,
        "error_counts": error_counts,
        "active_connections": active_connections,
        "total_processed": total_requests,
        "uptime_seconds": uptime,
        "rps_history": list(rps_history)[-30:],
        "telemetry": telemetry_data,
        "recent_traces": list(traces)[-20:],
        "event_log": [
            {"timestamp": e.timestamp, "level": e.level, "port": e.port, "message": e.message}
            for e in daemon.event_log[-30:]
        ],
        "demo_active": demo_running,
        "strategies_available": STRATEGY_NAMES,
        "failovers_triggered": daemon.failovers_triggered,
        "average_latency": average_latency,
    }

@app.post("/api/v1/balancer/reset")
async def reset_stats():
    global total_requests, round_robin_index, start_time, _rps_counter
    total_requests = 0
    round_robin_index = 0
    start_time = time.time()
    _rps_counter = 0
    traces.clear()
    rps_history.clear()
    daemon.event_log.clear()
    daemon.failovers_triggered = 0
    for p in REGISTERED_PORTS:
        request_counts[p] = 0
        error_counts[p] = 0
        # Active connections are not cleared because they track currently inflight requests.
    daemon._emit("INFO", 0, "System metrics reset to zero")
    return {"status": "reset"}

# ---------------------------------------------------------------------------
# Chaos Engineering (cloud-safe — router proxies the kill/restore)
# ---------------------------------------------------------------------------
@app.post("/api/v1/agents/{port_num}/kill")
async def kill_agent(port_num: int):
    try:
        async with httpx.AsyncClient() as c:
            await c.post(f"http://127.0.0.1:{port_num}/simulate_failure?status=false", timeout=1)
        daemon._emit("WARN", port_num, "Manual kill triggered via dashboard")
        return {"status": "killed", "port": port_num}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/agents/{port_num}/restore")
async def restore_agent(port_num: int):
    try:
        async with httpx.AsyncClient() as c:
            await c.post(f"http://127.0.0.1:{port_num}/simulate_failure?status=true", timeout=1)
        daemon._emit("INFO", port_num, "Manual restore triggered via dashboard")
        return {"status": "restored", "port": port_num}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------------------------
# Demo Engine
# ---------------------------------------------------------------------------
async def _demo_loop():
    """Automated hackathon demo: generates traffic, crashes a node, recovers."""
    global demo_running
    daemon._emit("INFO", 0, "🎬 Demo Mode started — generating traffic")
    strategies = STRATEGY_NAMES
    async with httpx.AsyncClient() as client:
        # Phase 1: Steady traffic (15s)
        for i in range(30):
            if not demo_running: return
            s = random.choice(strategies)
            try:
                await client.post("http://127.0.0.1:8000/router/route",
                    params={"strategy": s}, json={"query": f"Demo query {i}"}, timeout=5)
            except Exception: pass
            await asyncio.sleep(0.5)

        # Phase 2: Kill a node
        if not demo_running: return
        victim = random.choice(sorted(daemon.healthy_pool)) if daemon.healthy_pool else 8002
        daemon._emit("WARN", victim, "🔥 Demo Mode — simulating node crash")
        try:
            await client.post(f"http://127.0.0.1:{victim}/simulate_failure?status=false", timeout=1)
        except Exception: pass

        # Phase 3: Traffic under pressure (15s)
        for i in range(30):
            if not demo_running: return
            s = random.choice(strategies)
            try:
                await client.post("http://127.0.0.1:8000/router/route",
                    params={"strategy": s}, json={"query": f"Pressure query {i}"}, timeout=5)
            except Exception: pass
            await asyncio.sleep(0.5)

        # Phase 4: Restore node
        if not demo_running: return
        daemon._emit("INFO", victim, "💚 Demo Mode — restoring crashed node")
        try:
            await client.post(f"http://127.0.0.1:{victim}/simulate_failure?status=true", timeout=1)
        except Exception: pass

        # Phase 5: Recovery traffic (10s)
        for i in range(20):
            if not demo_running: return
            s = random.choice(strategies)
            try:
                await client.post("http://127.0.0.1:8000/router/route",
                    params={"strategy": s}, json={"query": f"Recovery query {i}"}, timeout=5)
            except Exception: pass
            await asyncio.sleep(0.5)

    daemon._emit("INFO", 0, "✅ Demo Mode completed successfully")
    demo_running = False

@app.post("/api/v1/demo/start")
async def start_demo():
    global demo_running, demo_task
    if demo_running:
        return {"status": "already_running"}
    demo_running = True
    demo_task = asyncio.create_task(_demo_loop())
    return {"status": "started"}

@app.post("/api/v1/demo/stop")
async def stop_demo():
    global demo_running, demo_task
    demo_running = False
    if demo_task:
        demo_task.cancel()
    daemon._emit("INFO", 0, "Demo Mode stopped by user")
    return {"status": "stopped"}

# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn, os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("router:app", host="0.0.0.0", port=port, reload=False)
