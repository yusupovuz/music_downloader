import asyncio
import multiprocessing
from music_service import MusicDownload

async def main():
    downloader = MusicDownload()
    
    print("Поиск музыки: Eminem - Mockingbird...")
    results = await downloader.search(name="Mockingbird", author="Eminem")
    
    if not results:
        print("Ничего не найдено.")
        
    for item in results:
        print("\n" + "="*40)
        print(f"Песня: {item.name}")
        print(f"Автор: {item.author}")
        print(f"Жанр: {item.genre}")
        print(f"Продолжительность: {item.duration_ms} мс")
        print(f"Preview URL: {item.preview_url}")
        print(f"Основной URL / Статус: {item.url}")
        print("="*40)

    await downloader.close()
    print("\nГлавный поток завершен. Фоновые процессы скачивания продолжают работу...")

if __name__ == "__main__":
    multiprocessing.freeze_support() 
    asyncio.run(main())