import subprocess
import time
import sys
import os

def run_tunnel():
    print("Installing pyngrok...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyngrok"], check=True)
    
    from pyngrok import ngrok
    
    # Try to load authtoken from env if it exists
    token = os.environ.get("NGROK_AUTHTOKEN")
    if token:
        ngrok.set_auth_token(token)
        print("Using provided ngrok authtoken.")
    else:
        print("No ngrok authtoken found. Tunnels will expire in 2 hours and may have strict limits.")
        print("To fix, set NGROK_AUTHTOKEN=your_token as an environment variable.")

    print("Opening tunnels...")
    try:
        # Open a tunnel to the FastAPI router
        router_tunnel = ngrok.connect(8000, "http")
        print(f"🌍 Public URL for AegisRoute Router: {router_tunnel.public_url}")
        
        # Open a tunnel to the Streamlit Dashboard
        dashboard_tunnel = ngrok.connect(8501, "http")
        print(f"📊 Public URL for NOC Dashboard:   {dashboard_tunnel.public_url}")
        
        print("\nPress Ctrl+C to close tunnels.")
        
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nClosing tunnels...")
        ngrok.kill()
    except Exception as e:
        print(f"An error occurred: {e}")
        ngrok.kill()

if __name__ == "__main__":
    run_tunnel()
