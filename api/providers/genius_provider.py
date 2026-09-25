import requests
import re
from bs4 import BeautifulSoup
from typing import Optional
from api.providers.base import BaseLyricProvider, LyricResult

class GeniusProvider(BaseLyricProvider):
    def __init__(self, key: str = "genius-plain"):
        super().__init__(key="genius-plain", name="Genius (Plain)", sync_type="unsynced")

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
            search_query = f"{artist} {song}"
            search_url = f"https://genius.com/api/search/multi?q={requests.utils.quote(search_query)}"

            resp = requests.get(search_url, headers=headers, timeout=8)
            if resp.status_code != 200:
                return None

            data = resp.json()
            sections = data.get("response", {}).get("sections", [])
            hit_url = None

            for sec in sections:
                if sec.get("type") == "song":
                    hits = sec.get("hits", [])
                    if hits:
                        hit_url = hits[0].get("result", {}).get("url")
                        break

            if not hit_url:
                return None

            # Fetch Genius lyric page
            page_resp = requests.get(hit_url, headers=headers, timeout=8)
            if page_resp.status_code != 200:
                return None

            soup = BeautifulSoup(page_resp.text, "html.parser")
            containers = soup.select('div[class*="Lyrics__Container"], .lyrics')

            txt_lines = []
            for container in containers:
                for br in container.find_all("br"):
                    br.replace_with("\n")
                text = container.get_text()
                for line in text.splitlines():
                    clean_line = line.strip()
                    if clean_line and not (clean_line.startswith("[") and clean_line.endswith("]")):
                        txt_lines.append(clean_line)

            if txt_lines:
                return LyricResult(
                    provider_key=self.key,
                    provider_name=self.name,
                    sync_type="unsynced",
                    txt_lines=txt_lines,
                    source_href=hit_url
                )

        except Exception as e:
            from utils import logger
            logger.warning(f"[{self.name}] Error fetching Genius lyrics: {e}")

        return None
