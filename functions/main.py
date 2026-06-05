from firebase_functions import https_fn
from firebase_admin import initialize_app, storage
import os
import yt_dlp
import uuid
import json

# Initialize Firebase Admin SDK
initialize_app()

@https_fn.on_request()
def download(req: https_fn.Request) -> https_fn.Response:
    """
    Firebase Cloud Function to handle searching, downloading, and hosting music.
    It takes a JSON body with a 'song_name' and returns a Firebase Storage public URL.
    """
    # Handle CORS preflight requests
    if req.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return https_fn.Response('', status=204, headers=headers)

    # Set CORS headers for actual requests
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type'
    }

    if req.method != 'POST':
        return https_fn.Response('Method Not Allowed', status=405, headers=headers)

    # Parse request JSON body
    try:
        data = req.get_json()
    except Exception:
        return https_fn.Response('Invalid JSON body', status=400, headers=headers)

    song_name = data.get('song_name')
    if not song_name:
        return https_fn.Response(json.dumps({"error": "No song name provided"}), status=400, headers={**headers, 'Content-Type': 'application/json'})

    # Cloud Function writeable temporary folder
    download_dir = "/tmp"
    
    # Configure yt-dlp to download best audio directly to /tmp.
    # Native download (.m4a/.webm) is serverless friendly as it doesn't require ffmpeg conversion.
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{download_dir}/%(title)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch1',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Search and extract information
            info = ydl.extract_info(song_name, download=True)
            
            # Handle search playlist structure (take first item)
            if 'entries' in info:
                info = info['entries'][0]
            
            title = info.get('title', song_name)
            filename = ydl.prepare_filename(info)
            
            # Verify file exists, or locate the most recent file in /tmp as fallback
            if not os.path.exists(filename):
                files = [os.path.join(download_dir, f) for f in os.listdir(download_dir) if os.path.isfile(os.path.join(download_dir, f))]
                if not files:
                    raise Exception("Downloaded file could not be found in local directory.")
                filename = max(files, key=os.path.getctime)

            basename = os.path.basename(filename)
            _, ext = os.path.splitext(basename)
            ext = ext.lower()
            
            # Upload downloaded song to Firebase Storage Bucket
            bucket = storage.bucket()
            blob_name = f"downloads/{uuid.uuid4()}{ext}"
            blob = bucket.blob(blob_name)
            
            # Map extensions to correct audio MIME types for streaming compatibility
            content_type = "audio/mpeg"
            if ext == ".m4a":
                content_type = "audio/x-m4a"
            elif ext == ".webm":
                content_type = "audio/webm"
            elif ext == ".ogg":
                content_type = "audio/ogg"
            elif ext == ".wav":
                content_type = "audio/wav"

            # Set content-type metadata and upload
            blob.content_type = content_type
            blob.upload_from_filename(filename)
            
            # Make blob public for browser direct playing and download
            blob.make_public()
            public_url = blob.public_url

            # Delete the file from local /tmp folder to conserve server resources
            try:
                os.remove(filename)
            except Exception as e:
                print(f"Error removing temp file: {e}")

            # Return success JSON with public streaming link
            response_data = {
                "success": True,
                "title": title,
                "file_path": public_url
            }
            return https_fn.Response(json.dumps(response_data), status=200, headers={**headers, 'Content-Type': 'application/json'})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return https_fn.Response(json.dumps({"error": str(e)}), status=500, headers={**headers, 'Content-Type': 'application/json'})
