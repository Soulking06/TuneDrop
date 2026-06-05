FROM python:3.10-slim

# Install NodeJS (for yt-dlp JavaScript challenges) and FFmpeg (for audio extraction)
RUN apt-get update && apt-get install -y nodejs ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Run Gunicorn
CMD sh -c "gunicorn app:app --bind 0.0.0.0:${PORT:-10000}"
