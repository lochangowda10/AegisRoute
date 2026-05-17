import asyncio
import httpx
from typing import Set, Dict
import logging

logger = logging.getLogger(__name__)

class HealthCheckerDaemon:
    def __init__(self, registered_ports: list[int]):
        self.registered_ports = set(registered_ports)
        self.healthy_pool: Set[int] = set(registered_ports)
        self.dead_pool: Set[int] = set()
        
        # Track consecutive failures/successes
        self.consecutive_failures: Dict[int, int] = {p: 0 for p in registered_ports}
        self.consecutive_successes: Dict[int, int] = {p: 0 for p in registered_ports}
        
        self.running = False

    async def check_port(self, port: int, client: httpx.AsyncClient):
        try:
            response = await client.get(f"http://127.0.0.1:{port}/health", timeout=0.5)
            if response.status_code == 200:
                self.consecutive_successes[port] += 1
                self.consecutive_failures[port] = 0
                
                if port in self.dead_pool and self.consecutive_successes[port] >= 2:
                    self.dead_pool.remove(port)
                    self.healthy_pool.add(port)
                    logger.info(f"[Health] Port {port} recovered and moved to healthy pool.")
            else:
                raise httpx.RequestError("Non-200 status code")
        except httpx.RequestError:
            self.consecutive_failures[port] += 1
            self.consecutive_successes[port] = 0
            
            if port in self.healthy_pool and self.consecutive_failures[port] >= 2:
                self.healthy_pool.remove(port)
                self.dead_pool.add(port)
                logger.warning(f"[Health] Port {port} failed checks and moved to dead pool.")

    async def run(self):
        self.running = True
        logger.info("[Health] Health Checker Daemon Started.")
        async with httpx.AsyncClient() as client:
            while self.running:
                tasks = [self.check_port(p, client) for p in self.registered_ports]
                await asyncio.gather(*tasks, return_exceptions=True)
                await asyncio.sleep(3)

    def stop(self):
        self.running = False
