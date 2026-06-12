from pydantic import BaseModel, Field
from typing import Optional

# Модель данных для аудио
class AudioData(BaseModel):
    name: str
    author: str
    preview_url: Optional[str] = None
    url: Optional[str] = None
    duration_ms: Optional[int] = Field(default=0, description="Продолжительность музыки в миллисекундах")
    is_permanent: bool = Field(default=False, description="Является ли ссылка постоянной?")
    genre: Optional[str] = None