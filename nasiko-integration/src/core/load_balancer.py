"""
AegisRoute Load Balancer and Health Checker Daemon for Nasiko
"""
import asyncio
import time
import httpx
import logging
from typing import Set, Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import random

logger = logging.getLogger(__name__)


@dataclass
class NodeTelemetry:
    url: str
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
    url: str
    message: str


class HealthCheckerDaemon:
    def __init__(self, registered_urls: Optional[List[str]] = None):
        self.registered_urls: Set[str] = set(registered_urls) if registered_urls else set()
        self.healthy_pool: Set[str] = set(registered_urls) if registered_urls else set()
        self.dead_pool: Set[str] = set()
        self.consecutive_failures: Dict[str, int] = defaultdict(int)
        self.consecutive_successes: Dict[str, int] = defaultdict(int)
        self.telemetry: Dict[str, NodeTelemetry] = {}
        if registered_urls:
            for url in registered_urls:
                self.telemetry[url] = NodeTelemetry(url=url)
        self.event_log: List[EventLogEntry] = []
        self._max_events = 200
        self.running = False

    def register_url(self, url: str):
        """Register a new agent URL for health checking."""
        self.registered_urls.add(url)
        if url not in self.healthy_pool and url not in self.dead_pool:
            self.healthy_pool.add(url)
        if url not in self.telemetry:
            self.telemetry[url] = NodeTelemetry(url=url)

    def unregister_url(self, url: str):
        """Unregister an agent URL."""
        self.registered_urls.discard(url)
        self.healthy_pool.discard(url)
        self.dead_pool.discard(url)
        self.telemetry.pop(url, None)

    def _emit(self, level: str, url: str, msg: str):
        self.event_log.append(EventLogEntry(time.time(), level, url, msg))
        if len(self.event_log) > self._max_events:
            self.event_log = self.event_log[-self._max_events:]

    def _score(self, url: str):
        s = 100 - min(self.consecutive_failures[url] * 30, 90)
        if url in self.telemetry and self.telemetry[url].latency_ms > 1000:
            s -= 20
        elif url in self.telemetry and self.telemetry[url].latency_ms > 500:
            s -= 10
        if url in self.telemetry:
            self.telemetry[url].health_score = max(0, min(100, s))

    async def check_url(self, url: str, client: httpx.AsyncClient):
        try:
            t0 = time.time()
            r = await client.get(f"{url}/health", timeout=0.5)
            lat = round((time.time() - t0) * 1000, 1)
            if r.status_code == 200:
                if url not in self.telemetry:
                    self.telemetry[url] = NodeTelemetry(url=url)
                self.telemetry[url].latency_ms = lat
                self.consecutive_successes[url] += 1
                self.consecutive_failures[url] = 0
                if url in self.dead_pool and self.consecutive_successes[url] >= 2:
                    self.dead_pool.remove(url)
                    self.healthy_pool.add(url)
                    self._emit("RECOVERY", url, "Node recovered - re-injected into healthy rotation")
            else:
                raise httpx.RequestError("Non-200 status code")
        except Exception:
            self.consecutive_failures[url] += 1
            self.consecutive_successes[url] = 0
            if url not in self.telemetry:
                self.telemetry[url] = NodeTelemetry(url=url)
            self.telemetry[url].latency_ms = 9999.0
            if url in self.healthy_pool and self.consecutive_failures[url] >= 2:
                self.healthy_pool.remove(url)
                self.dead_pool.add(url)
                self._emit("CRITICAL", url, "Node failed checks - quarantined")
        self._score(url)

    async def fetch_metrics(self, url: str, client: httpx.AsyncClient):
        if url not in self.healthy_pool or url not in self.telemetry:
            return
        try:
            r = await client.get(f"{url}/metrics", timeout=0.5)
            if r.status_code == 200:
                d = r.json()
                t = self.telemetry[url]
                t.cpu_percent = d.get("cpu_percent", 0)
                t.memory_percent = d.get("memory_percent", 0)
                t.uptime_seconds = d.get("uptime_seconds", 0)
                t.model = d.get("model", "unknown")
                t.version = d.get("version", "0.0")
                t.region = d.get("region", "unknown")
        except Exception:
            pass

    async def run(self):
        self.running = True
        self._emit("INFO", "", "Health Checker Daemon started")
        async with httpx.AsyncClient() as client:
            while self.running:
                if self.registered_urls:
                    await asyncio.gather(
                        *[self.check_url(url, client) for url in self.registered_urls],
                        *[self.fetch_metrics(url, client) for url in self.registered_urls],
                        return_exceptions=True
                    )
                await asyncio.sleep(3)

    def stop(self):
        self.running = False


class LoadBalancer:
    def __init__(self, health_daemon: HealthCheckerDaemon):
        self.health_daemon = health_daemon
        self.round_robin_index: Dict[str, int] = defaultdict(int)  # key: agent_name, value: index
        self.active_connections: Dict[str, int] = defaultdict(int)  # key: agent_url, value: count
        self.active_connections_lock = asyncio.Lock()
        self.request_counts: Dict[str, int] = defaultdict(int)  # key: agent_url, value: count
        self.error_counts: Dict[str, int] = defaultdict(int)  # key: agent_url, value: count
        self.total_requests: int = 0
        self.start_time = time.time()

    async def select_instance(
        self,
        agent_name: str,
        agent_urls: List[str],
        strategy: str = "round-robin"
    ) -> Tuple[str, str]:
        """
        Select an agent instance URL based on the specified strategy.
        
        Args:
            agent_name: Name of the agent
            agent_urls: List of URLs for the agent instances
            strategy: Load balancing strategy (round-robin, least-connections, random)
        
        Returns:
            Tuple of (selected_url, routing_reason)
        """
        # Filter to only healthy URLs
        healthy_urls = [url for url in agent_urls if url in self.health_daemon.healthy_pool]
        
        if not healthy_urls:
            # Fall back to all registered URLs if no healthy ones
            healthy_urls = agent_urls
            if not healthy_urls:
                raise ValueError(f"No URLs available for agent {agent_name}")
        
        if strategy == "round-robin":
            index = self.round_robin_index[agent_name] % len(healthy_urls)
            selected_url = healthy_urls[index]
            self.round_robin_index[agent_name] += 1
            reason = f"Round-robin index {index} → {selected_url}"
            return selected_url, reason
        
        elif strategy == "least-connections":
            async with self.active_connections_lock:
                # Select URL with minimum active connections
                selected_url = min(healthy_urls, key=lambda url: self.active_connections.get(url, 0))
            conns = self.active_connections.get(selected_url, 0)
            return selected_url, f"Lowest active connections ({conns}) → {selected_url}"
        
        elif strategy == "random":
            selected_url = random.choice(healthy_urls)
            return selected_url, f"Random selection from {len(healthy_urls)} healthy nodes → {selected_url}"
        
        else:
            # Default to round-robin
            index = self.round_robin_index[agent_name] % len(healthy_urls)
            selected_url = healthy_urls[index]
            self.round_robin_index[agent_name] += 1
            reason = f"Default round-robin index {index} → {selected_url}"
            return selected_url, reason

    async def increment_connections(self, url: str):
        async with self.active_connections_lock:
            self.active_connections[url] += 1

    async def decrement_connections(self, url: str):
        async with self.active_connections_lock:
            if self.active_connections[url] > 0:
                self.active_connections[url] -= 1

    def increment_request_count(self, url: str):
        self.request_counts[url] += 1
        self.total_requests += 1

    def increment_error_count(self, url: str):
        self.error_counts[url] += 1

    def get_stats(self) -> Dict:
        """Get load balancer statistics for the /api/v1/balancer/stats endpoint."""
        uptime = round(time.time() - self.start_time, 1)
        telemetry_data = {}
        for url, t in self.health_daemon.telemetry.items():
            telemetry_data[url] = {
                "latency_ms": t.latency_ms,
                "cpu_percent": t.cpu_percent,
                "memory_percent": t.memory_percent,
                "health_score": t.health_score,
                "uptime_seconds": t.uptime_seconds,
                "model": t.model,
                "version": t.version,
                "region": t.region,
            }
        return {
            "registered_urls": list(self.health_daemon.registered_urls),
            "healthy_urls": sorted(self.health_daemon.healthy_pool),
            "dead_urls": sorted(self.health_daemon.dead_pool),
            "total_requests": dict(self.request_counts),
            "error_counts": dict(self.error_counts),
            "active_connections": dict(self.active_connections),
            "total_processed": self.total_requests,
            "uptime_seconds": uptime,
            "telemetry": telemetry_data,
            "event_log": [
                {"timestamp": e.timestamp, "level": e.level, "url": e.url, "message": e.message}
                for e in self.health_daemon.event_log[-30:]
            ],
        }
