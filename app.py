from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import yt_dlp
import traceback

app = Flask(__name__)
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
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch1',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info and download
            info = ydl.extract_info(song_name, download=True)
            
            # Handle if it returns a playlist (search results)
            if 'entries' in info:
                info = info['entries'][0]
            
            title = info.get('title')
            
            # Determine the final mp3 filename
            filename = ydl.prepare_filename(info)
            base, _ = os.path.splitext(filename)
            mp3_filename = base + ".mp3"
            mp3_basename = os.path.basename(mp3_filename)
            
            return jsonify({
                "success": True, 
                "title": title,
                "file_path": f"/downloads/{mp3_basename}"
            })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/downloads/<path:filename>')
def serve_file(filename):
    return send_from_directory(DOWNLOAD_DIR, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001)
