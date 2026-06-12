import asyncio
import multiprocessing
import os
from urllib.parse import urlparse, parse_qs
from pydantic import BaseModel, Field
from typing import Optional, List
from shazamio import Shazam
import aiohttp
import yt_dlp

# ---------------------------------------------------------
# 1. Модель данных (Pydantic Dataclass)
# ---------------------------------------------------------
class AudioData(BaseModel):
    name: str
    author: str
    preview_url: Optional[str] = None
    url: Optional[str] = None
    duration_ms: Optional[int] = Field(default=0, description="Продолжительность музыки в миллисекундах")
    is_permanent: bool = Field(default=False, description="Является ли ссылка постоянной?")
    genre: Optional[str] = None

# ---------------------------------------------------------
# 2. ОТДЕЛЬНАЯ ФУНКЦИЯ для скачивания (yt-dlp)
# ---------------------------------------------------------
def download_audio_process(query_or_url: str, output_path: str):
    """
    Работает в отдельном процессе, чтобы не блокировать основной поток (thread).
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
            # Если переданный текст не является ссылкой, ищем аудио на YouTube
            if not query_or_url.startswith("http"):
                query_or_url = f"ytsearch1:{query_or_url}"
            ydl.download([query_or_url])
        print(f"[Process] Успешно скачано и сохранено: {query_or_url}")
    except Exception as e:
        print(f"[Process] Ошибка при скачивании: {e}")

# ---------------------------------------------------------
# 3. Основной класс MusicDownload
# ---------------------------------------------------------
class MusicDownload:
    def __init__(self):
        # Shazamio используется для получения популярных чартов
        self.shazam = Shazam()
        
        # Заголовки браузера для обхода защиты (Cloudflare bypass) через aiohttp
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }
        self.session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(headers=self.headers)
        return self.session

    async def _check_link_permanent(self, url: str) -> bool:
        """Проверяет, является ли ссылка постоянной (отсутствие временных токенов)"""
        if not url:
            return False
            
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        
        temporary_keys = ['expire', 'expires', 'token', 'sig', 'signature', 'Policy']
        for key in temporary_keys:
            if key in query_params or key.lower() in url.lower():
                return False
                
        try:
            session = await self._get_session()
            async with session.head(url, timeout=5) as response:
                if response.status >= 400:
                    return False
        except Exception:
            return False

        return True

    def _trigger_background_download(self, search_query: str):
        """Запускает отдельный процесс для фонового скачивания музыки"""
        if not os.path.exists("./downloads"):
            os.makedirs("./downloads")
            
        process = multiprocessing.Process(
            target=download_audio_process,
            args=(search_query, "./downloads")
        )
        process.start()

    async def search(self, name: str = "", author: str = "", genre: str = "", popular: bool = False) -> List[AudioData]:
        results = []
        
        if popular:
            # Способ 1: Получение топ-чартов через Shazamio
            try:
                top_tracks = await self.shazam.top_world_tracks(limit=5)
                tracks_data = top_tracks.get('tracks', [])
                
                for track in tracks_data:
                    track_name = track.get('title', 'Неизвестно')
                    track_author = track.get('subtitle', 'Неизвестно')
                    
                    preview_url = None
                    for action in track.get('hub', {}).get('actions', []):
                        if action.get('type') == 'uri':
                            preview_url = action.get('uri')
                            break

                    is_perm = await self._check_link_permanent(preview_url) if preview_url else False
                    final_url = preview_url if is_perm else "Скачивается локально..."
                    
                    if not is_perm:
                        self._trigger_background_download(f"{track_author} - {track_name}")

                    results.append(AudioData(
                        name=track_name,
                        author=track_author,
                        preview_url=preview_url,
                        url=final_url,
                        is_permanent=is_perm,
                        genre=track.get('genres', {}).get('primary', 'Неизвестно')
                    ))
            except Exception as e:
                print(f"Ошибка в чартах Shazam: {e}")
                
        else:
            # Способ 2: Текстовый поиск через Apple/iTunes API (основной бэкенд Shazam)
            query_parts = [name, author, genre]
            query = " ".join([p for p in query_parts if p]).strip()
            
            if not query:
                return results

            session = await self._get_session()
            url_search = "https://itunes.apple.com/search"
            params = {
                "term": query,
                "entity": "song",
                "limit": 5
            }
            
            try:
                async with session.get(url_search, params=params) as response:
                    if response.status == 200:
                        # content_type=None игнорирует mimetype (например, text/javascript)
                        data = await response.json(content_type=None) 
                        
                        for item in data.get('results', []):
                            track_name = item.get('trackName', 'Неизвестно')
                            track_author = item.get('artistName', 'Неизвестно')
                            preview_url = item.get('previewUrl') # 30-секундное демо
                            duration_ms = item.get('trackTimeMillis', 0)
                            genre_name = item.get('primaryGenreName', 'Неизвестно')
                            
                            # Принудительно запускаем скачивание полной версии через yt-dlp
                            self._trigger_background_download(f"{track_author} - {track_name}")

                            results.append(AudioData(
                                name=track_name,
                                author=track_author,
                                preview_url=preview_url,
                                url="Скачивается в фоновом режиме (yt-dlp)...",
                                duration_ms=int(duration_ms),
                                is_permanent=False, 
                                genre=genre_name
                            ))
                    else:
                        print(f"[Ошибка] iTunes API вернул статус {response.status}")
            except Exception as e:
                print(f"[Ошибка] Проблема при поиске: {e}")

        return results

    async def close(self):
        """Безопасное закрытие HTTP-сессии"""
        if self.session and not self.session.closed:
            await self.session.close()

# ---------------------------------------------------------
# 4. Запуск программы (Блок тестирования)
# ---------------------------------------------------------
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
    # Обязательно для корректной работы multiprocessing в Windows
    multiprocessing.freeze_support() 
    asyncio.run(main())