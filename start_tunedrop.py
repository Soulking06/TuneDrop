import os
import time
import webbrowser
import threading
import socket

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def start_server():
    # Run the Flask app quietly
    os.system("python3 app.py")

def main():
    print("====================================")
    print("🎵 TuneDrop Server 🎵")
    print("Starting up the local environment...")
    print("====================================\n")
    
    # Start the Flask server in the background
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Wait a brief moment for the server to spin up
    time.sleep(1.5)
    
    local_ip = get_local_ip()
    local_url = "http://127.0.0.1:5001"
    mobile_url = f"http://{local_ip}:5001"
    
    print("✅ TuneDrop is running!")
    print(f"🌐 Local Address (this Mac): {local_url}")
    
    if local_ip != "127.0.0.1":
        print(f"📱 Mobile Network Address:    {mobile_url}")
        print(f"💡 Tip: Make sure your phone is on the same Wi-Fi network.")
        print(f"👉 When the phone app opens, enter this IP in Settings: {local_ip}\n")
    else:
        print("⚠️ Warning: Could not detect local Wi-Fi IP address. Mobile connection may require manual lookup.")
        
    print("Opening automatically in your default browser...\n")
    
    # Automatically open the user's default web browser to the page
    webbrowser.open(local_url)
    
    print("Press Ctrl+C to stop the server and exit.")
    
    try:
        # Keep the main thread alive so the daemon server thread keeps running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down TuneDrop... Goodbye!")

if __name__ == "__main__":
    main()
