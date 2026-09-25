import requests
import re
from typing import Optional
from api.providers.base import BaseLyricProvider, LyricResult
from api.providers.betterlyrics_provider import parse_lrc_string

NETEASE_SEARCH_URL = "https://music.163.com/api/search/get/web"
NETEASE_LYRIC_URL = "https://music.163.com/api/song/lyric"

class NeteaseProvider(BaseLyricProvider):
    def __init__(self, key: str = "netease-synced"):
        super().__init__(key="netease-synced", name="NetEase Cloud Music", sync_type="line")

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

        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            search_params = {
                "s": f"{artist} {song}",
                "type": 1,
                "limit": 5
            }
            resp = requests.get(NETEASE_SEARCH_URL, params=search_params, headers=headers, timeout=8)
            if resp.status_code != 200:
                return None

            data = resp.json()
            if not isinstance(data, dict):
                return None

            result = data.get("result")
            if not isinstance(result, dict):
                return None

            songs = result.get("songs")
            if not isinstance(songs, list) or not songs:
                return None

            song_id = songs[0].get("id")
            if not song_id:
                return None

            # Fetch lyrics for song_id
            lyric_params = {"id": song_id, "lv": -1, "kv": -1, "tv": -1}
            l_resp = requests.get(NETEASE_LYRIC_URL, params=lyric_params, headers=headers, timeout=8)
            if l_resp.status_code != 200:
                return None

            l_data = l_resp.json()
            if not isinstance(l_data, dict):
                return None

            lrc_dict = l_data.get("lrc")
            if not isinstance(lrc_dict, dict):
                return None

            lrc_raw = lrc_dict.get("lyric", "")
            if not lrc_raw:
                return None

            lrc_lines = parse_lrc_string(lrc_raw)
            txt_lines = [re.sub(r"\[.*?\]", "", line).strip() for line in lrc_lines if line.strip()]

            return LyricResult(
                provider_key=self.key,
                provider_name=self.name,
                sync_type="line",
                lrc_lines=lrc_lines,
                txt_lines=txt_lines,
                source_href=f"https://music.163.com/#/song?id={song_id}"
            )

        except Exception as e:
            from utils import logger
            logger.warning(f"[{self.name}] Error fetching NetEase lyrics: {e}")

        return None
