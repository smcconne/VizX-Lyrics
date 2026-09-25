import requests
import re
from typing import Optional
from api.providers.base import BaseLyricProvider, LyricResult
from api.providers.betterlyrics_provider import parse_lrc_string

LRCLIB_API_URL = "https://lrclib.net/api/get"
LRCLIB_SEARCH_URL = "https://lrclib.net/api/search"

class LRCLibProvider(BaseLyricProvider):
    def __init__(self, key: str):
        super().__init__(key=key, name="LRCLib (Synced)", sync_type="line")

    def fetch_lyrics(
        self,
        song: str,
        artist: str,
        duration: Optional[float] = None,
        album: Optional[str] = None,
        isrc: Optional[str] = None,
        url: Optional[str] = None,
        force_precision: int = 2,
        applemusic_track: Optional[dict] = None
    ) -> Optional[LyricResult]:
        if not song and not artist:
            return None

        params = {
            "track_name": song,
            "artist_name": artist,
        }
        if album:
            params["album_name"] = album
        if duration:
            params["duration"] = int(duration)

        try:
            resp = requests.get(
                LRCLIB_API_URL,
                params=params,
                timeout=8,
                headers={"User-Agent": "VizX-Lyrics/2.0"}
            )

            data = None
            if resp.status_code == 200:
                data = resp.json()
            elif resp.status_code == 404:
                # Fallback to search endpoint if exact match fail
                search_resp = requests.get(
                    LRCLIB_SEARCH_URL,
                    params={"q": f"{artist} {song}"},
                    timeout=8,
                    headers={"User-Agent": "VizX-Lyrics/2.0"}
                )
                if search_resp.status_code == 200:
                    results = search_resp.json()
                    if results and isinstance(results, list):
                        data = results[0]

            if not data:
                return None

            synced_lyrics = data.get("syncedLyrics")
            plain_lyrics = data.get("plainLyrics")

            if not synced_lyrics and not plain_lyrics:
                return None

            if synced_lyrics:
                lrc_lines = parse_lrc_string(synced_lyrics)
                txt_lines = [re.sub(r"\[.*?\]", "", line).strip() for line in lrc_lines if line.strip()]
            else:
                lrc_lines = []
                txt_lines = [line.strip() for line in plain_lyrics.splitlines() if line.strip()]

            return LyricResult(
                provider_key=self.key,
                provider_name=self.name,
                sync_type=self.sync_type,  # let detect_sync_type recompute downstream; safe default is "line"
                lrc_lines=lrc_lines,
                txt_lines=txt_lines,
                source_href="https://lrclib.net"
            )

        except Exception as e:
            from utils import logger
            logger.warning(f"[{self.name}] Error fetching lyrics: {e}")
            return None
