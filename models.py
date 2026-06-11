from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class TrackData(BaseModel):
    name: str
    artist: str
    preview_url: Optional[str] = None
    url: str  
    duration: Optional[int] = Field(None, description="Продолжительность в секундах")
    is_local: bool = False  
    metadata: Dict[str, Any] = Field(default_factory=dict)