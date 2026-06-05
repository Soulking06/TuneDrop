import subprocess
import socket
import re
import threading
import os
import qrcode
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# --- AppleScript Commands ---
def run_applescript(script):
    try:
        subprocess.run(['osascript', '-e', script], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running AppleScript: {e}")
        return False

# --- Endpoints ---
@app.route('/api/next', methods=['POST'])
def next_slide():
    run_applescript('tell application "Keynote" to show next')
    return jsonify({"status": "success", "action": "next"})

@app.route('/api/prev', methods=['POST'])
def prev_slide():
    run_applescript('tell application "Keynote" to show previous')
    return jsonify({"status": "success", "action": "prev"})

@app.route('/api/start', methods=['POST'])
def start_presentation():
    run_applescript('tell application "Keynote" to start front document')
    return jsonify({"status": "success", "action": "start"})

@app.route('/api/stop', methods=['POST'])
def stop_presentation():
    # If "stop" fails, we fall back to simulating the Escape key
    success = run_applescript('tell application "Keynote" to stop')
    if not success:
        run_applescript('tell application "System Events" to key code 53')
    return jsonify({"status": "success", "action": "stop"})

# --- Frontend Web App ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <title>Keynote Remote</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        
        * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
        
        body {
            margin: 0;
            padding: 0;
            font-family: 'Inter', -apple-system, sans-serif;
            background: linear-gradient(-45deg, #ff416c, #ff4b2b, #4158d0, #c850c0);
            background-size: 400% 400%;
            animation: gradientBG 15s ease infinite;
            color: #ffffff;
            display: flex;
            flex-direction: column;
            height: 100vh;
            overflow: hidden;
            user-select: none;
        }

        @keyframes gradientBG {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        .header {
            padding: 25px 20px;
            text-align: center;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        }

        .header h1 {
            margin: 0;
            font-size: 1.8rem;
            font-weight: 800;
            letter-spacing: 1px;
            text-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }

        .container {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
            padding: 25px;
            gap: 20px;
        }

        .row {
            display: flex;
            gap: 20px;
            justify-content: center;
        }

        .btn {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.4);
            border-top: 1px solid rgba(255, 255, 255, 0.8);
            border-radius: 25px;
            color: white;
            font-family: 'Inter', sans-serif;
            font-size: 1.2rem;
            font-weight: 600;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 12px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2), inset 0 2px 5px rgba(255,255,255,0.3);
            transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
            cursor: pointer;
            flex: 1;
        }

        .btn:active {
            transform: scale(0.92);
            background: rgba(255, 255, 255, 0.25);
            box-shadow: 0 4px 15px 0 rgba(0, 0, 0, 0.1), inset 0 2px 10px rgba(0,0,0,0.1);
        }

        .btn-large {
            height: 180px;
            font-size: 1.6rem;
            border-radius: 35px;
        }

        .btn-primary { 
            background: rgba(255, 255, 255, 0.25);
            border: 2px solid rgba(255, 255, 255, 0.6);
            border-top: 2px solid rgba(255, 255, 255, 1);
            box-shadow: 0 10px 40px 0 rgba(255, 255, 255, 0.3), inset 0 2px 10px rgba(255,255,255,0.5);
            text-shadow: 0 2px 5px rgba(0,0,0,0.2);
            position: relative;
            overflow: hidden;
        }
        
        .btn-primary::after {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.3) 0%, transparent 60%);
            opacity: 0;
            transition: opacity 0.3s;
        }
        
        .btn-primary:active::after {
            opacity: 1;
        }

        .btn-danger { 
            background: rgba(255, 59, 48, 0.4);
            border-color: rgba(255, 59, 48, 0.6);
        }

        .btn-success { 
            background: rgba(52, 199, 89, 0.4);
            border-color: rgba(52, 199, 89, 0.6);
        }

        .icon {
            font-size: 2.8rem;
            filter: drop-shadow(0 4px 6px rgba(0,0,0,0.2));
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>✨ Keynote Remote</h1>
    </div>
    <div class="container">
        <div class="row">
            <button class="btn btn-success" onclick="sendCommand('start')">
                <span class="icon">▶️</span>
                Play
            </button>
            <button class="btn btn-danger" onclick="sendCommand('stop')">
                <span class="icon">⏹️</span>
                Exit
            </button>
        </div>
        <button class="btn btn-large" onclick="sendCommand('prev')">
            <span class="icon">⏮️</span>
            Previous Slide
        </button>
        <button class="btn btn-large btn-primary" onclick="sendCommand('next')">
            <span class="icon">⏭️</span>
            Next Slide
        </button>
    </div>

    <script>
        function sendCommand(action) {
            fetch(`/api/${action}`, { method: 'POST' })
                .then(res => res.json())
                .then(data => console.log(data))
                .catch(err => console.error(err));
            
            if (navigator.vibrate) {
                navigator.vibrate(50);
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def start_tunnel(port):
    import time
    print("Waiting for local server to start before launching tunnel...", flush=True)
    time.sleep(2)
    os.system("killall ssh 2>/dev/null")
    process = subprocess.Popen(
        ['ssh', '-tt', '-p', '443', '-R0:localhost:' + str(port), '-o', 'StrictHostKeyChecking=no', 'a.pinggy.io'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=0
    )
    
    url_pattern = re.compile(r'(https://[a-zA-Z0-9-]+\.run\.pinggy-free\.link)')
    
    qr_generated = False
    
    def test_tunnel(url):
        import time
        print(f"\n🧪 Waiting for Cloudflare to register {url}...", flush=True)
        for attempt in range(5):
            time.sleep(3)
            res = subprocess.run(['curl', '-I', '-s', url], capture_output=True, text=True)
            if '200 OK' in res.stdout:
                print(f"\n✅ Tunnel is UP and publicly accessible!", flush=True)
                return
            elif attempt == 4:
                print(f"\n⚠️ Tunnel is still returning errors. Cloudflare might be slow right now.", flush=True)
                print("--- Latest Status ---", flush=True)
                for line in res.stdout.splitlines():
                    if line.startswith('HTTP'):
                        print(line, flush=True)
                print("---------------------\n", flush=True)

    for line_bytes in iter(process.stdout.readline, b''):
        line = line_bytes.decode('utf-8', errors='ignore')
        print(f"Tunnel Log: {line.strip()}", flush=True)
        match = url_pattern.search(line)
        if match and not qr_generated:
            public_url = match.group(1)
            print(f"\n🌐 Cloudflare Tunnel created! URL: {public_url}")
            
            # Generate QR Code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(public_url)
            qr.make(fit=True)
            img = qr.make_image(fill='black', back_color='white')
            
            # Save to Desktop
            desktop_path = os.path.expanduser('~/Desktop/Keynote_Remote_QR.png')
            img.save(desktop_path)
            print(f"📷 QR Code saved to your Desktop: {desktop_path}\\n")
            qr_generated = True
            
            # Trigger curl test without blocking cloudflared logs
            threading.Thread(target=test_tunnel, args=(public_url,), daemon=True).start()

if __name__ == '__main__':
    ip = get_local_ip()
    port = 8080
    
    # Start the tunnel in a background thread
    tunnel_thread = threading.Thread(target=start_tunnel, args=(port,), daemon=True)
    tunnel_thread.start()
    
    print("="*50)
    print("📱 KEYNOTE REMOTE SERVER RUNNING!")
    print(f"👉 Local link: http://{ip}:{port}")
    print("="*50)
    app.run(host='0.0.0.0', port=port)
