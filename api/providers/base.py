from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Literal

SyncType = Literal["syllable", "word", "line", "unsynced"]

class LyricResult:
    def __init__(
        self,
        provider_key: str,
        provider_name: str,
        sync_type: SyncType,
        lrc_lines: Optional[List[str]] = None,
        txt_lines: Optional[List[str]] = None,
        ttml_content: Optional[str] = None,
        language: Optional[str] = None,
        source_href: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.provider_key = provider_key
        self.provider_name = provider_name
        self.sync_type = sync_type
        self.lrc_lines = lrc_lines or []
        self.txt_lines = txt_lines or []
        self.ttml_content = ttml_content or ""
        self.language = language
        self.source_href = source_href or ""
        self.metadata = metadata or {}

    def has_content(self) -> bool:
        return bool(self.lrc_lines or self.txt_lines or self.ttml_content)

    def __repr__(self):
        return f"<LyricResult provider={self.provider_key} sync={self.sync_type} lrc_lines={len(self.lrc_lines)} txt_lines={len(self.txt_lines)} ttml={bool(self.ttml_content)}>"


class BaseLyricProvider(ABC):
    def __init__(self, key: str, name: str, sync_type: SyncType):
        self.key = key
        self.name = name
        self.sync_type = sync_type

    @abstractmethod
    def fetch_lyrics(
        self,
        song: str,
        artist: str,
        duration: Optional[float] = None,
        album: Optional[str] = None,
        isrc: Optional[str] = None,
        url: Optional[str] = None,
        video_id: Optional[str] = None,
        force_precision: int = 2,
        applemusic_track: Optional[dict] = None
    ) -> Optional[LyricResult]:
        """
        Fetches lyrics from the provider.
        Returns a LyricResult if found, or None if not found/error.
        """
        pass
