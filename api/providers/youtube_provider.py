import requests
import json
import re
from typing import Optional
from api.providers.base import BaseLyricProvider, LyricResult
from api.providers.betterlyrics_provider import format_timestamp

class YouTubeProvider(BaseLyricProvider):
    def __init__(self, key: str):
        sync_type = "line" if key == "yt-captions" else "unsynced"
        name = "YouTube Captions" if key == "yt-captions" else "YouTube Lyrics"
        super().__init__(key=key, name=name, sync_type=sync_type)

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

        # Search YouTube Music video via innertube search API
        try:
            search_query = f"{artist} - {song}"
            search_url = "https://music.youtube.com/youtubei/v1/search"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Content-Type": "application/json"
            }
            body = {
                "context": {
                    "client": {
                        "clientName": "WEB_REMIX",
                        "clientVersion": "1.20240101.01.00"
                    }
                },
                "query": search_query
            }
            
            resp = requests.post(search_url, json=body, headers=headers, timeout=8)
            if resp.status_code != 200:
                return None

            data = resp.json()

            # Extract video ID from search results
            video_id = None
            str_data = json.dumps(data)
            match = re.search(r'"videoId"\s*:\s*"([a-zA-Z0-9_-]{11})"', str_data)
            if match:
                video_id = match.group(1)

            if not video_id:
                return None

            # Fetch player info to extract caption tracks / lyrics
            player_url = "https://music.youtube.com/youtubei/v1/player"
            player_body = {
                "context": {
                    "client": {
                        "clientName": "WEB_REMIX",
                        "clientVersion": "1.20240101.01.00"
                    }
                },
                "videoId": video_id
            }
            player_resp = requests.post(player_url, json=player_body, headers=headers, timeout=8)
            if player_resp.status_code != 200:
                return None

            player_data = player_resp.json()
            captions_data = player_data.get("captions", {}).get("playerCaptionsTracklistRenderer", {}).get("captionTracks", [])

            if self.key == "yt-captions" and captions_data:
                # Find caption track URL
                caption_url = captions_data[0].get("baseUrl")
                if caption_url:
                    cap_resp = requests.get(caption_url + "&fmt=json3", timeout=8)
                    if cap_resp.status_code == 200:
                        cap_json = cap_resp.json()
                        lrc_lines = []
                        txt_lines = []
                        for event in cap_json.get("events", []):
                            segs = event.get("segs", [])
                            start_ms = event.get("tStartMs", 0)
                            words = "".join([s.get("utf8", "") for s in segs]).replace("\n", " ").strip()
                            if words and words != "♪":
                                ts_str = format_timestamp(start_ms / 1000.0, force_precision)
                                lrc_lines.append(f"[{ts_str}] {words}")
                                txt_lines.append(words)

                        if lrc_lines:
                            return LyricResult(
                                provider_key=self.key,
                                provider_name=self.name,
                                sync_type="line",
                                lrc_lines=lrc_lines,
                                txt_lines=txt_lines,
                                source_href=f"https://music.youtube.com/watch?v={video_id}"
                            )

            elif self.key == "yt-lyrics":
                # Try getting lyrics tab from YouTube Music next endpoint
                next_url = "https://music.youtube.com/youtubei/v1/next"
                next_body = {
                    "context": body["context"],
                    "videoId": video_id
                }
                next_resp = requests.post(next_url, json=next_body, headers=headers, timeout=8)
                if next_resp.status_code == 200:
                    str_next = next_resp.text
                    lyrics_browse_id = re.search(r'"browseId"\s*:\s*"(MPLYt_[^"]+)"', str_next)
                    if lyrics_browse_id:
                        browse_url = "https://music.youtube.com/youtubei/v1/browse"
                        browse_body = {
                            "context": body["context"],
                            "browseId": lyrics_browse_id.group(1)
                        }
                        b_resp = requests.post(browse_url, json=browse_body, headers=headers, timeout=8)
                        if b_resp.status_code == 200:
                            b_str = b_resp.text
                            # Extract plain lyrics text
                            lyrics_match = re.search(r'"runs"\s*:\s*\[\s*\{\s*"text"\s*:\s*"([^"]+)"', b_str)
                            if lyrics_match:
                                txt = lyrics_match.group(1).replace("\\n", "\n")
                                txt_lines = [line.strip() for line in txt.splitlines() if line.strip()]
                                return LyricResult(
                                    provider_key=self.key,
                                    provider_name=self.name,
                                    sync_type="unsynced",
                                    txt_lines=txt_lines,
                                    source_href=f"https://music.youtube.com/watch?v={video_id}"
                                )

        except Exception as e:
            from utils import logger
            logger.warning(f"[{self.name}] Error fetching YouTube lyrics: {e}")

        return None
