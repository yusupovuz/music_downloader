import os
import yt_dlp

def download_via_ytdlp(url: str, output_dir: str = "downloads") -> str:
    """Отдельная функция для скачивания аудио."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_dir}/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'extract_audio': True,
        'audio_format': 'mp3'
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        base, _ = os.path.splitext(filename)
        return os.path.abspath(f"{base}.mp3")

def search_via_ytdlp(query: str, limit: int = 5) -> list:
    """Отдельная функция для поиска. yt_dlp больше не внутри класса."""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True 
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
        return info.get('entries', [])