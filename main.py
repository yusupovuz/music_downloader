import asyncio
from music_service import MusicDownload
from yt_tools import search_via_ytdlp, download_via_ytdlp

async def main():
    # Мы передаем и поиск, и скачивание снаружи. 
    # Теперь класс MusicDownload полностью независим от внешних библиотек!
    downloader = MusicDownload(
        search_fn=search_via_ytdlp,
        download_fn=download_via_ytdlp
    )
    
    user_query = input("Какую песню вы хотите найти?: ")
    if user_query:
        print(f"\n'{user_query}' ищется и скачивается... (Подождите немного)")
        
        search_results = await downloader.search_by_name(user_query, limit=1)
        
        for track in search_results:
            print(f"\nРезультат: {track.artist} - {track.name}")
            print(f"Продолжительность: {track.duration} сек.")
            print(f"Локальный путь к файлу: {track.url}")
            print(f"Скачан локально?: {track.is_local}")

if __name__ == "__main__":
    asyncio.run(main())