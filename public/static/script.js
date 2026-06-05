document.addEventListener('DOMContentLoaded', () => {
    const songInput = document.getElementById('song-input');
    const downloadBtn = document.getElementById('download-btn');
    const statusArea = document.getElementById('status-area');
    const statusText = document.getElementById('status-text');
    const resultArea = document.getElementById('result-area');
    const resultTitle = document.getElementById('result-title');
    const audioPlayer = document.getElementById('audio-player');
    const downloadLink = document.getElementById('download-link');
    const errorArea = document.getElementById('error-area');
    const errorText = document.getElementById('error-text');

    // Handle Enter key
    songInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            downloadBtn.click();
        }
    });

    downloadBtn.addEventListener('click', async () => {
        const songName = songInput.value.trim();
        
        if (!songName) {
            songInput.focus();
            return;
        }

        // UI Reset
        resultArea.classList.add('hidden');
        errorArea.classList.add('hidden');
        statusArea.classList.remove('hidden');
        
        // Button state
        downloadBtn.disabled = true;
        const btnText = downloadBtn.querySelector('.btn-text');
        btnText.textContent = 'Processing...';

        try {
            const response = await fetch('/api/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ song_name: songName })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                // Success UI update
                statusArea.classList.add('hidden');
                resultArea.classList.remove('hidden');
                
                resultTitle.textContent = data.title || songName;
                
                // Update audio player
                audioPlayer.src = data.file_path;
                audioPlayer.load();
                
                // Update download link
                downloadLink.href = data.file_path;
                
                // Keep the extension if the backend provides it, or default to mp3
                const ext = data.file_path.includes('.webm') ? 'webm' : (data.file_path.includes('.m4a') ? 'm4a' : 'mp3');
                downloadLink.download = `${data.title || songName}.${ext}`;
                
                // Optional: Auto-play
                // audioPlayer.play().catch(e => console.log('Autoplay prevented', e));
                
            } else {
                throw new Error(data.error || 'Failed to download the song');
            }
            
        } catch (error) {
            statusArea.classList.add('hidden');
            errorArea.classList.remove('hidden');
            errorText.textContent = error.message;
        } finally {
            downloadBtn.disabled = false;
            btnText.textContent = 'Grab Track';
            songInput.value = '';
        }
    });
});
