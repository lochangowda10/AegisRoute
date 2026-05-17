import asyncio
import httpx
import logging
import random
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Literal

from health_checker import HealthCheckerDaemon

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AegisRoute Router")

# Pre-defined mock agent instances (We expect them to be started separately)
REGISTERED_PORTS = [8001, 8002, 8003]

# Core engine state
daemon = HealthCheckerDaemon(REGISTERED_PORTS)

# Router statistics
request_counts: Dict[int, int] = {p: 0 for p in REGISTERED_PORTS}
active_connections: Dict[int, int] = {p: 0 for p in REGISTERED_PORTS}
active_connections_lock = asyncio.Lock()

# Load balancing state
round_robin_index = 0

class QueryRequest(BaseModel):
    query: str

@app.on_event("startup")
async def startup_event():
    # Start the background daemon
    asyncio.create_task(daemon.run())

@app.on_event("shutdown")
async def shutdown_event():
    daemon.stop()

async def select_node(strategy: str) -> int:
    healthy_nodes = list(daemon.healthy_pool)
    if not healthy_nodes:
        raise HTTPException(status_code=503, detail="No healthy nodes available")

    # Sort healthy nodes so load balancing is deterministic regardless of set order
    healthy_nodes.sort()

    if strategy == "round-robin":
        global round_robin_index
        node = healthy_nodes[round_robin_index % len(healthy_nodes)]
        round_robin_index = (round_robin_index + 1) % len(healthy_nodes)
        return node
    
    elif strategy == "least-connections":
        async with active_connections_lock:
            # Sort healthy nodes by active connections
            node = min(healthy_nodes, key=lambda p: active_connections[p])
        return node
    
    elif strategy == "random":
        return random.choice(healthy_nodes)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown strategy: {strategy}")

@app.post("/router/route")
async def route_query(
    request: QueryRequest, 
    strategy: Literal["round-robin", "least-connections", "random"] = Query("round-robin")
):
    target_port = await select_node(strategy)
    
    async with active_connections_lock:
        active_connections[target_port] += 1
    
    try:
        async with httpx.AsyncClient() as client:
            # Forward the request to the target agent
            url = f"http://127.0.0.1:{target_port}/query"
            response = await client.post(url, json={"query": request.query}, timeout=10.0)
            
            if response.status_code == 200:
                request_counts[target_port] += 1
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail="Error from agent node")
    except httpx.RequestError as e:
        logger.error(f"Routing error to port {target_port}: {str(e)}")
        raise HTTPException(status_code=502, detail="Bad Gateway: Target node unreachable")
    finally:
        async with active_connections_lock:
            active_connections[target_port] -= 1

@app.get("/api/v1/balancer/stats")
async def get_stats():
    return {
        "registered_instances": REGISTERED_PORTS,
        "healthy_instances": list(daemon.healthy_pool),
        "dead_instances": list(daemon.dead_pool),
        "total_requests": request_counts,
        "active_connections": active_connections
    }

if __name__ == "__main__":
    import uvicorn
    import os
    # Bind to 0.0.0.0 and use the PORT env var for cloud environments like Render/Railway
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("router:app", host="0.0.0.0", port=port, reload=False)
