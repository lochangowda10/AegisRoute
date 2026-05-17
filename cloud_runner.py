import subprocess, time, sys

def start():
    print("🚀 Starting AegisRoute Cloud System...")
    procs = []
    for port in [8001, 8002, 8003]:
        print(f"  Starting agent on port {port}...")
        procs.append(subprocess.Popen([sys.executable, "agent_instance.py", "--port", str(port)]))
    time.sleep(2)
    print("  Starting Router...")
    try:
        subprocess.run([sys.executable, "router.py"], check=True)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        for p in procs: p.terminate()

if __name__ == "__main__":
    start()
