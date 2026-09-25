import requests
from typing import Optional
from api.providers.base import BaseLyricProvider, LyricResult, SyncType
from api.providers.betterlyrics_provider import parse_ttml_to_lrc, parse_lrc_string

UNISON_API_URL = "https://unison.boidu.dev/lyrics"

UNISON_CONFIGS = {
    "unison-richsynced": {"name": "Unison (Syllable)", "sync_type": "syllable"},
}

class UnisonProvider(BaseLyricProvider):
    def __init__(self, key: str):
        meta = UNISON_CONFIGS.get(key, {"name": "Unison (Syllable)", "sync_type": "syllable"})
        super().__init__(key=key, name=meta["name"], sync_type=meta["sync_type"])

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
            "song": song,
            "artist": artist,
        }
        if duration:
            params["duration"] = str(int(duration))
        if album:
            params["album"] = album

        try:
            resp = requests.get(
                UNISON_API_URL,
                params=params,
                timeout=8,
                headers={
                    "x-key-id": "VizX-Lyrics-Client-V2",
                    "User-Agent": "VizX-Lyrics/2.0"
                }
            )
            if resp.status_code != 200:
                return None

            data = resp.json().get("data", {})
            raw_lyrics = data.get("lyrics")
            lyric_fmt = data.get("format")
            sync_type_field = data.get("syncType")

            if not raw_lyrics:
                return None

            lrc_lines = []
            txt_lines = []
            ttml_content = ""

            if lyric_fmt == "ttml":
                ttml_content = raw_lyrics
                lrc_lines = parse_ttml_to_lrc(ttml_content, force_precision)
                txt_lines = [line.split("]", 1)[-1].strip() for line in lrc_lines if "]" in line]
            elif lyric_fmt == "lrc":
                lrc_lines = parse_lrc_string(raw_lyrics)
                txt_lines = [line.split("]", 1)[-1].strip() for line in lrc_lines if "]" in line]
            elif lyric_fmt == "plain":
                txt_lines = [line.strip() for line in raw_lyrics.splitlines() if line.strip()]

            # Determine actual sync level
            actual_sync: SyncType = "syllable" if lyric_fmt == "ttml" else ("line" if lrc_lines else "unsynced")

            return LyricResult(
                provider_key=self.key,
                provider_name=self.name,
                sync_type=actual_sync,
                lrc_lines=lrc_lines,
                txt_lines=txt_lines,
                ttml_content=ttml_content,
                source_href="https://unison.boidu.dev"
            )

        except Exception as e:
            from utils import logger
            logger.warning(f"[{self.name}] Error fetching lyrics: {e}")
            return None
