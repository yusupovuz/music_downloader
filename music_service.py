import asyncio
from typing import List, Callable, Optional
from models import TrackData

class MusicDownload:
    def __init__(self, 
                 search_fn: Callable[[str, int], list],
                 download_fn: Optional[Callable[[str], str]] = None):
        """
        :param search_fn: Функция для поиска аудио (передается извне).
        :param download_fn: Функция для скачивания (передается извне).
        """
        self.search_fn = search_fn
        self.download_fn = download_fn

    async def search_by_name(self, query: str, limit: int = 5) -> List[TrackData]:
        entries = await asyncio.to_thread(self.search_fn, query, limit)
        return await self._parse_results(entries)

    async def search_by_artist(self, artist_name: str, limit: int = 5) -> List[TrackData]:
        entries = await asyncio.to_thread(self.search_fn, f"{artist_name} songs", limit)
        return await self._parse_results(entries)

    async def search_by_genre(self, genre: str, limit: int = 5) -> List[TrackData]:
        entries = await asyncio.to_thread(self.search_fn, f"Top {genre} music hits", limit)
        return await self._parse_results(entries)

    async def _parse_results(self, entries: list) -> List[TrackData]:
        tracks_data = []
        
        for entry in entries:
            if not entry:
                continue
                
            title = entry.get('title', 'Unknown')
            artist = entry.get('uploader', 'Unknown')
            duration = int(entry.get('duration', 0)) if entry.get('duration') else None
            
            webpage_url = entry.get('url')
            if not webpage_url and entry.get('id'):
                webpage_url = f"https://www.youtube.com/watch?v={entry.get('id')}"

            final_url = webpage_url or ""
            is_local = False
            
            if self.download_fn and webpage_url:
                try:
                    final_url = await asyncio.to_thread(self.download_fn, webpage_url)
                    is_local = True
                except Exception as e:
                    print(f"Ошибка при скачивании: {e}")

            track_obj = TrackData(
                name=title,
                artist=artist,
                preview_url=webpage_url,
                url=final_url,
                duration=duration,
                is_local=is_local,
                metadata={
                    "youtube_id": entry.get('id'),
                    "view_count": entry.get('view_count', 0)
                }
            )
            tracks_data.append(track_obj)
            
        return tracks_data