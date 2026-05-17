# AegisRoute 🛡️
**Real-time Agent Load Balancing & Resiliency Engine**

AegisRoute is a prototype distributed systems infrastructure designed to efficiently load balance traffic across multiple AI agent nodes, actively monitor their health, and automatically quarantine and recover nodes upon failure.

## 🚀 Features
- **3 Hot-Swappable Load Balancing Strategies**: Round-Robin, Least-Connections, Random.
- **Active Health Checking**: Background async daemon probing nodes every 3s.
- **Self-Healing Architecture**: Automatic failover (quarantine) on 2 consecutive failures, and auto-recovery on 2 successes.
- **NOC Terminal Dashboard**: Beautiful, glowing dark-themed Streamlit UI for real-time telemetry.
- **Concurrency Blaster**: Stress test script to validate traffic distribution.

## 🛠️ Setup Instructions

1. **Install Requirements:**
   Make sure you are running Python 3.12.
   ```bash
   pip install -r requirements.txt
   ```

2. **Launch Mock Agent Instances:**
   Open 3 separate terminal windows and start the agents:
   ```bash
   python agent_instance.py --port 8001
   python agent_instance.py --port 8002
   python agent_instance.py --port 8003
   ```

3. **Launch the AegisRoute Router:**
   Open a 4th terminal window to run the core engine on port 8000:
   ```bash
   python router.py
   ```

4. **Launch the NOC Terminal Dashboard:**
   Open a 5th terminal window to run the visualizer:
   ```bash
   streamlit run dashboard.py
   ```
   *The dashboard will be available at http://localhost:8501*

5. **Run the Stress Test:**
   Open a 6th terminal window and fire concurrent requests:
   ```bash
   python stress_test.py --strategy round-robin --requests 50
   ```
   You can also test other strategies:
   ```bash
   python stress_test.py --strategy least-connections --requests 40
   ```

## 🧪 Chaos Engineering
Use the left sidebar in the Streamlit Dashboard to click **"KILL Node"** on a healthy node.
Watch the dashboard update as the node is moved to the "Dead Nodes" pool and observe how the traffic is seamlessly re-routed to the remaining healthy instances during the stress test. Click **"RESTORE Node"** to watch the self-healing daemon inject it back into rotation.
