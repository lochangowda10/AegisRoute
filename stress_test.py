import asyncio
import httpx
import time
import argparse
from collections import Counter

async def send_request(client, router_url, strategy, request_id):
    try:
        response = await client.post(
            f"{router_url}/router/route?strategy={strategy}",
            json={"query": f"Stress test query #{request_id}"},
            timeout=10.0
        )
        if response.status_code == 200:
            data = response.json()
            print(f"Request {request_id:02d} -> Success | Handled by Port {data.get('instance_port')}")
            return data.get('instance_port')
        else:
            print(f"Request {request_id:02d} -> Failed | Status {response.status_code}")
            return None
    except Exception as e:
        print(f"Request {request_id:02d} -> Error | {str(e)}")
        return None

async def main():
    parser = argparse.ArgumentParser(description="AegisRoute Stress Tester")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="Router URL")
    parser.add_argument("--strategy", default="round-robin", choices=["round-robin", "least-connections", "random"])
    parser.add_argument("--requests", type=int, default=50, help="Number of concurrent requests")
    args = parser.parse_args()

    print(f"🚀 Starting Stress Test: {args.requests} concurrent requests to {args.url} using {args.strategy} strategy")
    start_time = time.time()

    async with httpx.AsyncClient() as client:
        tasks = [send_request(client, args.url, args.strategy, i+1) for i in range(args.requests)]
        results = await asyncio.gather(*tasks)

    end_time = time.time()
    
    # Filter out None results
    handled_ports = [r for r in results if r is not None]
    counts = Counter(handled_ports)
    
    print("\n" + "="*40)
    print("📊 Stress Test Results")
    print("="*40)
    print(f"Total Time: {end_time - start_time:.2f} seconds")
    print(f"Successful Requests: {len(handled_ports)}/{args.requests}")
    print("Distribution:")
    for port, count in counts.items():
        print(f"  Port {port}: {count} requests handled")
    print("="*40)

if __name__ == "__main__":
    asyncio.run(main())
