import argparse
import asyncio
import random
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="AegisRoute Mock Agent")

# Global flag to simulate crashes
is_healthy = True
port = 8000

class QueryRequest(BaseModel):
    query: str

@app.post("/query")
async def process_query(req: QueryRequest):
    global is_healthy
    if not is_healthy:
        raise HTTPException(status_code=500, detail="Internal Server Error: Node crashed.")
    
    # Simulate heavy LLM token generation/reasoning
    delay = random.uniform(0.5, 2.0)
    await asyncio.sleep(delay)
    
    return {
        "instance_port": port,
        "response": f"Processed: [{req.query}]"
    }

@app.get("/health")
async def health_check():
    global is_healthy
    if not is_healthy:
        raise HTTPException(status_code=500, detail="Simulated failure.")
    return {"status": "healthy", "port": port}

@app.post("/simulate_failure")
async def simulate_failure(status: bool):
    """Toggle the health status of this agent."""
    global is_healthy
    is_healthy = status
    return {"is_healthy": is_healthy}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mock AI Agent Server")
    parser.add_argument("--port", type=int, required=True, help="Port to run the instance on")
    args = parser.parse_args()
    
    port = args.port
    uvicorn.run(app, host="127.0.0.1", port=port)
