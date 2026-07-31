import requests
import re
from typing import Optional
from api.providers.base import BaseLyricProvider, LyricResult
from api.providers.betterlyrics_provider import parse_lrc_string

LRCLIB_API_URL = "https://lrclib.net/api/get"
LRCLIB_SEARCH_URL = "https://lrclib.net/api/search"

class LRCLibProvider(BaseLyricProvider):
    def __init__(self, key: str):
        sync_type = "line" if key == "lrclib-synced" else "unsynced"
        name = "LRCLib (Synced)" if key == "lrclib-synced" else "LRCLib (Plain)"
        super().__init__(key=key, name=name, sync_type=sync_type)

    def fetch_lyrics(
        self,
        song: str,
        artist: str,
        duration: Optional[float] = None,
        album: Optional[str] = None,
        isrc: Optional[str] = None,
        url: Optional[str] = None,
        sync_precision: int = 2
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

            if self.key == "lrclib-synced":
                if not synced_lyrics:
                    return None
                lrc_lines = parse_lrc_string(synced_lyrics)
                txt_lines = [re.sub(r"\[.*?\]", "", line).strip() for line in lrc_lines if line.strip()]
                return LyricResult(
                    provider_key=self.key,
                    provider_name=self.name,
                    sync_type="line",
                    lrc_lines=lrc_lines,
                    txt_lines=txt_lines,
                    source_href="https://lrclib.net"
                )

            elif self.key == "lrclib-plain":
                if not plain_lyrics and not synced_lyrics:
                    return None
                if plain_lyrics:
                    txt_lines = [line.strip() for line in plain_lyrics.splitlines() if line.strip()]
                else:
                    txt_lines = [re.sub(r"\[.*?\]", "", line).strip() for line in synced_lyrics.splitlines() if line.strip()]

                return LyricResult(
                    provider_key=self.key,
                    provider_name=self.name,
                    sync_type="unsynced",
                    txt_lines=txt_lines,
                    source_href="https://lrclib.net"
                )

        except Exception as e:
            from utils import logger
            logger.warning(f"[{self.name}] Error fetching lyrics: {e}")
            return None
