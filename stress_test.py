"""
AegisRoute — Concurrency Blaster v2.0
Stress testing with burst, chaos, and multi-strategy support.
"""
import asyncio, httpx, time, argparse, random
from collections import Counter

STRATEGIES = ["round-robin","least-connections","random","latency-aware","weighted","adaptive"]

async def send(client, url, strategy, rid):
    try:
        r = await client.post(f"{url}/router/route", params={"strategy": strategy},
            json={"query": f"Stress #{rid}"}, timeout=10.0)
        if r.status_code == 200:
            d = r.json()
            print(f"  #{rid:03d} | Port {d.get('instance_port')} | {strategy} | {d.get('routing_reason','')[:50]}")
            return d.get("instance_port")
        else:
            print(f"  #{rid:03d} | FAILED ({r.status_code})")
            return None
    except Exception as e:
        print(f"  #{rid:03d} | ERROR: {e}")
        return None

async def main():
    p = argparse.ArgumentParser(description="AegisRoute Stress Tester v2.0")
    p.add_argument("--url", default="http://127.0.0.1:8000")
    p.add_argument("--strategy", default="round-robin", choices=STRATEGIES)
    p.add_argument("--requests", type=int, default=50)
    p.add_argument("--burst", action="store_true", help="Spike pattern: 10 → 50 → 10")
    p.add_argument("--chaos", action="store_true", help="Kill a node mid-test, then restore")
    args = p.parse_args()

    print(f"\n🚀 AegisRoute Stress Tester v2.0")
    print(f"   Target: {args.url} | Strategy: {args.strategy}")
    print(f"   Mode: {'BURST' if args.burst else 'CHAOS' if args.chaos else 'STANDARD'}\n")

    t0 = time.time()
    all_results = []
    async with httpx.AsyncClient() as client:
        if args.burst:
            for phase, count in [("Warm-up", 10), ("SPIKE", 50), ("Cool-down", 10)]:
                print(f"── Phase: {phase} ({count} requests) ──")
                tasks = [send(client, args.url, args.strategy, i+1) for i in range(count)]
                results = await asyncio.gather(*tasks)
                all_results.extend(results)
                await asyncio.sleep(1)
        elif args.chaos:
            print("── Phase 1: Baseline (20 requests) ──")
            tasks = [send(client, args.url, args.strategy, i+1) for i in range(20)]
            all_results.extend(await asyncio.gather(*tasks))

            print("\n💀 Killing node 8002...")
            try: await client.post(f"{args.url}/api/v1/agents/8002/kill", timeout=2)
            except: pass
            await asyncio.sleep(2)

            print("\n── Phase 2: Under pressure (20 requests) ──")
            tasks = [send(client, args.url, args.strategy, i+21) for i in range(20)]
            all_results.extend(await asyncio.gather(*tasks))

            print("\n💚 Restoring node 8002...")
            try: await client.post(f"{args.url}/api/v1/agents/8002/restore", timeout=2)
            except: pass
            await asyncio.sleep(7)

            print("\n── Phase 3: Recovery (10 requests) ──")
            tasks = [send(client, args.url, args.strategy, i+41) for i in range(10)]
            all_results.extend(await asyncio.gather(*tasks))
        else:
            tasks = [send(client, args.url, args.strategy, i+1) for i in range(args.requests)]
            all_results = await asyncio.gather(*tasks)

    elapsed = time.time() - t0
    ports = [r for r in all_results if r is not None]
    counts = Counter(ports)

    print(f"\n{'='*50}")
    print(f"📊 Results | {len(ports)}/{len(all_results)} successful | {elapsed:.2f}s")
    print(f"{'='*50}")
    for port, cnt in sorted(counts.items()):
        bar = "█" * cnt
        print(f"  Port {port}: {cnt:3d} reqs  {bar}")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    asyncio.run(main())
