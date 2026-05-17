import subprocess
import time
import os
import sys

def start_cloud_system():
    print("🚀 Starting AegisRoute Cloud System...")
    
    # Start agents as background subprocesses
    agent_ports = [8001, 8002, 8003]
    agent_processes = []
    
    for port in agent_ports:
        print(f"Starting agent on port {port}...")
        # Bind to localhost inside the container so the router can still reach them
        p = subprocess.Popen([sys.executable, "agent_instance.py", "--port", str(port)])
        agent_processes.append(p)
    
    # Give agents a second to spin up
    time.sleep(2)
    
    # Start the router in the foreground
    print("Starting Router...")
    try:
        subprocess.run([sys.executable, "router.py"], check=True)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        for p in agent_processes:
            p.terminate()

if __name__ == "__main__":
    start_cloud_system()
