from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import yt_dlp
import traceback

app = Flask(__name__)
CORS(app)  # Enable CORS for the Netlify frontend
DOWNLOAD_DIR = "downloads"

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/download', methods=['POST'])
def download():
    data = request.json
    song_name = data.get('song_name')
    if not song_name:
        return jsonify({"error": "No song name provided"}), 400
        
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch1',
    }
    
    # If a cookies.txt file exists (e.g., provided securely on the server), use it
    # This prevents YouTube from blocking the server as a bot.
    if os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info and download
            info = ydl.extract_info(song_name, download=True)
            
            # Handle if it returns a playlist (search results)
            if 'entries' in info:
                info = info['entries'][0]
            
            title = info.get('title')
            
            # Determine the final downloaded filename
            filename = ydl.prepare_filename(info)
            basename = os.path.basename(filename)
            
            return jsonify({
                "success": True, 
                "title": title,
                "file_path": f"/downloads/{basename}"
            })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/downloads/<path:filename>')
def serve_file(filename):
    return send_from_directory(DOWNLOAD_DIR, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001)
