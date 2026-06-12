import yt_dlp

def download_audio_process(query_or_url: str, output_path: str):
    """
    Работает в отдельном процессе, чтобы не блокировать основной поток.
    Запускает фоновое скачивание аудио через yt-dlp.
    """
    print(f"[Process] Запуск скачивания: {query_or_url}")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_path}/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if not query_or_url.startswith("http"):
                query_or_url = f"ytsearch1:{query_or_url}"
            ydl.download([query_or_url])
        print(f"[Process] Успешно скачано и сохранено: {query_or_url}")
    except Exception as e:
        print(f"[Process] Ошибка при скачивании: {e}")