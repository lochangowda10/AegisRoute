"""
AegisRoute — Async Resilience Daemon v2.0
Background health checker with latency tracking, health scores, and event logging.
"""
import asyncio, time, httpx, logging
from typing import Set, Dict, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class NodeTelemetry:
    port: int
    latency_ms: float = 0.0
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    health_score: int = 100
    uptime_seconds: float = 0.0
    model: str = "unknown"
    version: str = "0.0"
    region: str = "unknown"

@dataclass
class EventLogEntry:
    timestamp: float
    level: str
    port: int
    message: str

class HealthCheckerDaemon:
    def __init__(self, registered_ports: list[int]):
        self.registered_ports = set(registered_ports)
        self.healthy_pool: Set[int] = set(registered_ports)
        self.dead_pool: Set[int] = set()
        self.consecutive_failures: Dict[int, int] = {p: 0 for p in registered_ports}
        self.consecutive_successes: Dict[int, int] = {p: 0 for p in registered_ports}
        self.telemetry: Dict[int, NodeTelemetry] = {p: NodeTelemetry(port=p) for p in registered_ports}
        self.event_log: List[EventLogEntry] = []
        self._max_events = 200
        self.running = False

    def _emit(self, level, port, msg):
        self.event_log.append(EventLogEntry(time.time(), level, port, msg))
        if len(self.event_log) > self._max_events:
            self.event_log = self.event_log[-self._max_events:]

    def _score(self, port):
        s = 100 - min(self.consecutive_failures[port] * 30, 90)
        if self.telemetry[port].latency_ms > 1000: s -= 20
        elif self.telemetry[port].latency_ms > 500: s -= 10
        self.telemetry[port].health_score = max(0, min(100, s))

    async def check_port(self, port, client):
        try:
            t0 = time.time()
            r = await client.get(f"http://127.0.0.1:{port}/health", timeout=0.5)
            lat = round((time.time() - t0) * 1000, 1)
            if r.status_code == 200:
                self.telemetry[port].latency_ms = lat
                self.consecutive_successes[port] += 1
                self.consecutive_failures[port] = 0
                if port in self.dead_pool and self.consecutive_successes[port] >= 2:
                    self.dead_pool.remove(port); self.healthy_pool.add(port)
                    self._emit("RECOVERY", port, "Node recovered — re-injected into healthy rotation")
            else:
                raise httpx.RequestError("Non-200")
        except Exception:
            self.consecutive_failures[port] += 1
            self.consecutive_successes[port] = 0
            self.telemetry[port].latency_ms = 9999.0
            if port in self.healthy_pool and self.consecutive_failures[port] >= 2:
                self.healthy_pool.remove(port); self.dead_pool.add(port)
                self._emit("CRITICAL", port, "Node failed checks — quarantined")
        self._score(port)

    async def fetch_metrics(self, port, client):
        if port not in self.healthy_pool: return
        try:
            r = await client.get(f"http://127.0.0.1:{port}/metrics", timeout=0.5)
            if r.status_code == 200:
                d = r.json(); t = self.telemetry[port]
                t.cpu_percent = d.get("cpu_percent", 0)
                t.memory_percent = d.get("memory_percent", 0)
                t.uptime_seconds = d.get("uptime_seconds", 0)
                t.model = d.get("model", "unknown")
                t.version = d.get("version", "0.0")
                t.region = d.get("region", "unknown")
        except Exception: pass

    async def run(self):
        self.running = True
        self._emit("INFO", 0, "Health Checker Daemon started")
        async with httpx.AsyncClient() as client:
            while self.running:
                await asyncio.gather(
                    *[self.check_port(p, client) for p in self.registered_ports],
                    *[self.fetch_metrics(p, client) for p in self.registered_ports],
                    return_exceptions=True)
                await asyncio.sleep(3)

    def stop(self):
        self.running = False
