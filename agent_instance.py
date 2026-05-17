"""
AegisRoute — Mock AI Agent Server v2.0
Simulates a running LLM agent container with rich telemetry.
"""

import argparse
import asyncio
import random
import time
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

app = FastAPI(title="AegisRoute AI Agent Node")

# ---------------------------------------------------------------------------
# Global State
# ---------------------------------------------------------------------------
is_healthy = True
port = 8000
start_time = time.time()

# Simulated hardware metrics (randomised each health cycle)
simulated_cpu = 0.0
simulated_memory = 0.0

# Agent metadata
AGENT_META = {
    "model": "aegis-llm-7b",
    "version": "2.0.1",
    "region": "local-cluster",
}


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------
class QueryRequest(BaseModel):
    query: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.post("/query")
async def process_query(req: QueryRequest):
    """Simulate heavy LLM token generation / reasoning."""
    global is_healthy
    if not is_healthy:
        raise HTTPException(status_code=500, detail="Node crashed.")

    # Random processing delay to mimic real inference latency
    delay = random.uniform(0.5, 2.0)
    t0 = time.time()
    await asyncio.sleep(delay)
    latency_ms = round((time.time() - t0) * 1000, 1)

    return {
        "instance_port": port,
        "response": f"Processed: [{req.query}]",
        "latency_ms": latency_ms,
    }


@app.get("/health")
async def health_check():
    """Health probe endpoint used by the router daemon."""
    global is_healthy
    if not is_healthy:
        raise HTTPException(status_code=500, detail="Simulated failure.")
    return {"status": "healthy", "port": port}


@app.get("/metrics")
async def get_metrics():
    """Return simulated hardware telemetry for the dashboard."""
    global simulated_cpu, simulated_memory
    # Drift metrics slightly each call for realism
    simulated_cpu = max(5.0, min(95.0, simulated_cpu + random.uniform(-8, 8)))
    simulated_memory = max(10.0, min(90.0, simulated_memory + random.uniform(-5, 5)))

    return {
        "port": port,
        "cpu_percent": round(simulated_cpu, 1),
        "memory_percent": round(simulated_memory, 1),
        "uptime_seconds": round(time.time() - start_time, 1),
        "model": AGENT_META["model"],
        "version": AGENT_META["version"],
        "region": AGENT_META["region"],
    }


@app.post("/simulate_failure")
async def simulate_failure(status: bool = Query(...)):
    """Toggle the health status of this agent for chaos engineering."""
    global is_healthy
    is_healthy = status
    return {"is_healthy": is_healthy, "port": port}


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AegisRoute AI Agent Node")
    parser.add_argument("--port", type=int, required=True, help="Port to run on")
    args = parser.parse_args()

    port = args.port
    # Randomise starting metrics per instance
    simulated_cpu = random.uniform(15, 45)
    simulated_memory = random.uniform(20, 50)
    uvicorn.run(app, host="0.0.0.0", port=port)
