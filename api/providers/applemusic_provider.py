import os
from typing import Optional
from api.providers.base import BaseLyricProvider, LyricResult
from api.api import AppleMusic
from api.lyrics import getLyrics

class AppleMusicProvider(BaseLyricProvider):
    def __init__(self, cache_dir: str, config_dir: str):
        super().__init__(
            key="applemusic",
            name="Apple Music",
            sync_type="syllable"
        )
        self.cache_dir = cache_dir
        self.config_dir = config_dir

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
        # Fast path: reuse the per-track dict already fetched by
        # handler.download_lyrics, avoiding a second Apple Music API call.
        if applemusic_track is not None:
            return self._build_result_from_track(applemusic_track, song)

        if not url:
            # Apple Music provider currently requires a direct Apple Music URL or search selection URL
            return None

        try:
            applemusic = AppleMusic(self.cache_dir, self.config_dir, force_precision)
            data = applemusic.getInfo(url)

            if not data or "tracks" not in data or not data["tracks"]:
                return None

            # Return lyrics for the target track (first track if single song)
            return self._build_result_from_track(data["tracks"][0], song, all_tracks=data["tracks"])

        except Exception as e:
            from utils import logger
            logger.warning(f"[AppleMusicProvider] Error fetching lyrics for {url}: {e}")
            return None

    def _build_result_from_track(
        self,
        track: dict,
        song: str,
        all_tracks=None
    ) -> Optional[LyricResult]:
        ttml_raw = track.get("ttml", "")
        time_synced = track.get("timeSyncedLyrics", [])
        plain_lyrics = track.get("lyrics", [])

        # Check if we have word/syllable timing in TTML
        sync_type = "syllable" if ttml_raw and ("<span" in ttml_raw or "itunes:timing" in ttml_raw) else ("line" if time_synced else "unsynced")

        if not ttml_raw and not time_synced and not plain_lyrics:
            return None

        metadata = {"title": track.get("file", song)}
        if all_tracks is not None:
            metadata["all_tracks"] = all_tracks

        return LyricResult(
            provider_key=self.key,
            provider_name=self.name,
            sync_type=sync_type,
            lrc_lines=time_synced,
            txt_lines=plain_lyrics,
            ttml_content=ttml_raw,
            metadata=metadata
        )
