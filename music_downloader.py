import os
import sys
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
import yt_dlp

console = Console()

class MusicDownloader:
    def __init__(self, download_dir="downloads"):
        self.download_dir = download_dir
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)

    def download_song(self, song_name: str):
        console.print(Panel.fit(f"[bold cyan]Searching and Downloading:[/bold cyan] [yellow]{song_name}[/yellow]", border_style="cyan"))

        # yt-dlp options for downloading best audio and converting to mp3
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{self.download_dir}/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'ytsearch1', # Search youtube and pick the first result
        }

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("[cyan]Downloading...", total=None)

            class MyLogger:
                def debug(self, msg):
                    # Could parse progress here, but yt_dlp's internal progress hook is better
                    pass
                def warning(self, msg):
                    pass
                def error(self, msg):
                    console.print(f"[red]Error: {msg}[/red]")

            def progress_hook(d):
                if d['status'] == 'downloading':
                    # Update progress bar if total bytes are known
                    total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                    downloaded_bytes = d.get('downloaded_bytes', 0)
                    if total_bytes:
                        progress.update(task, total=total_bytes, completed=downloaded_bytes)
                elif d['status'] == 'finished':
                    progress.update(task, completed=progress.tasks[task].total, description="[green]Converting to MP3...")

            ydl_opts['logger'] = MyLogger()
            ydl_opts['progress_hooks'] = [progress_hook]

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([song_name])
                console.print(f"\n[bold green]✅ Successfully downloaded to [cyan]{self.download_dir}/[/cyan][/bold green]")
            except Exception as e:
                console.print(f"\n[bold red]❌ Failed to download: {e}[/bold red]")


def main():
    console.print(Panel.fit("[bold magenta]🎵 TunesDrop 🎵[/bold magenta]\n[dim]Downloads MP3s by simply searching the song name[/dim]", border_style="magenta"))
    
    downloader = MusicDownloader()
    
    while True:
        try:
            song_name = Prompt.ask("\n[bold green]Enter the exact name of the song (or 'q' to quit)[/bold green]")
            
            if song_name.lower() in ['q', 'quit', 'exit']:
                console.print("[yellow]Goodbye![/yellow]")
                break
                
            if not song_name.strip():
                continue
                
            downloader.download_song(song_name)
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Goodbye![/yellow]")
            sys.exit(0)

if __name__ == "__main__":
    main()
