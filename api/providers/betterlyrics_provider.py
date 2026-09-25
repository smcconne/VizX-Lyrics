import json
import re
import requests
from typing import Optional, Dict, Any, List
from bs4 import BeautifulSoup
from api.providers.base import BaseLyricProvider, LyricResult, SyncType

CUBEY_LYRICS_API_URL = "https://lyrics.api.dacubeking.com/"

PROVIDER_METADATA: Dict[str, Dict[str, Any]] = {
    "bLyrics-richsynced": {"name": "Better Lyrics (Syllable)", "sync_type": "syllable"},
    "musixmatch-richsync": {"name": "Musixmatch (Word)", "sync_type": "word"},
    "portato-richsynced": {"name": "QQ Music (Word)", "sync_type": "word"},
    "legato-synced": {"name": "KuGou (Line)", "sync_type": "line"},
    "binimum-richsynced": {"name": "BiniLyrics (Syllable)", "sync_type": "syllable"},
}

def parse_ttml_to_lrc(ttml_text: str, force_precision: int = 2) -> List[str]:
    """Parses raw TTML string into LRC format lines."""
    lrc_lines = []
    try:
        soup = BeautifulSoup(ttml_text, "lxml-xml")
        for line in soup.find_all("p"):
            begin = line.get("begin")
            if not begin:
                continue
            
            # Format begin timestamp
            ts_str = format_timestamp(begin, force_precision)
            
            spans = line.find_all("span", attrs={"begin": True})
            if spans:
                word_parts = []
                for span in spans:
                    s_begin = span.get("begin")
                    w_text = span.text.strip()
                    if s_begin and w_text:
                        w_ts = format_timestamp(s_begin, force_precision)
                        word_parts.append(f"<{w_ts}> {w_text}")
                lrc_lines.append(f"[{ts_str}] " + " ".join(word_parts))
            else:
                line_text = line.text.strip()
                lrc_lines.append(f"[{ts_str}] {line_text}")
    except Exception:
        pass
    return lrc_lines

def parse_lrc_string(lrc_text: str) -> List[str]:
    """Splits raw LRC text into clean non-empty lines."""
    return [line.strip() for line in lrc_text.splitlines() if line.strip()]

def parse_qrc_to_lrc(qrc_text: str, force_precision: int = 2) -> List[str]:
    """Parses QQ Music QRC format ([ms,dur]word(ms,dur)...) into LRC format lines."""
    lrc_lines = []
    for line in qrc_text.splitlines():
        line = line.strip()
        if not line:
            continue
        
        match = re.match(r"^\[(\d+),(\d+)\](.*)", line)
        if match:
            line_start_ms = int(match.group(1))
            line_ts = format_timestamp(line_start_ms / 1000.0, force_precision)
            content = match.group(3)
            
            words = re.findall(r"(.*?)\((\d+),(\d+)\)", content)
            if words:
                word_parts = []
                for w_text, w_start_ms, w_dur in words:
                    w_ts = format_timestamp(int(w_start_ms) / 1000.0, force_precision)
                    w_clean = w_text.strip()
                    if w_clean:
                        word_parts.append(f"<{w_ts}> {w_clean}")
                if word_parts:
                    lrc_lines.append(f"[{line_ts}] " + " ".join(word_parts))
            else:
                lrc_lines.append(f"[{line_ts}] {content.strip()}")
        elif line.startswith("[") and "]" in line:
            lrc_lines.append(line)
            
    return lrc_lines

def format_timestamp(ts: str, force_precision: int = 2) -> str:
    """Normalizes time string into mm:ss.xx format."""
    ts = str(ts).replace("s", "").strip()
    if ":" in ts:
        parts = ts.split(":")
        mins = int(parts[-2])
        secs = float(parts[-1])
    else:
        total_secs = float(ts) if ts else 0.0
        mins = int(total_secs // 60)
        secs = total_secs % 60
    
    if force_precision == 3:
        return f"{mins:02d}:{secs:06.3f}"
    return f"{mins:02d}:{secs:05.2f}"


def get_youtube_video_id(song: str, artist: str) -> Optional[str]:
    """Helper to resolve a 11-char YouTube video ID for Cubey API."""
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
        resp = requests.post(search_url, json=body, headers=headers, timeout=6)
        if resp.status_code == 200:
            match = re.search(r'"videoId"\s*:\s*"([a-zA-Z0-9_-]{11})"', resp.text)
            if match:
                return match.group(1)
    except Exception:
        pass
    return None


class BetterLyricsProvider(BaseLyricProvider):
    def __init__(self, key: str):
        meta = PROVIDER_METADATA.get(key, {"name": key, "sync_type": "line"})
        super().__init__(
            key=key,
            name=meta["name"],
            sync_type=meta["sync_type"]
        )

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
        if not song and not artist:
            return None

        if not video_id:
            video_id = get_youtube_video_id(song, artist)

        body = {
            "song": song,
            "artist": artist,
        }
        if video_id:
            body["videoId"] = video_id
        if duration:
            body["duration"] = str(int(duration))
        if album:
            body["album"] = album
        if isrc:
            body["isrc"] = isrc

        try:
            try:
                from config import Configure
                from handler import CONFIG
                cfg = Configure(CONFIG)
                jwt = cfg.get_setting("cubey_jwt_token", None)
                if jwt:
                    body["token"] = jwt
            except Exception:
                pass
            resp = requests.post(
                CUBEY_LYRICS_API_URL + "v2/lyrics",
                data=body,
                timeout=10,
                headers={"User-Agent": "VizX-Lyrics/2.0"}
            )
            if resp.status_code == 403:
                from utils import logger
                logger.warning(f"[{self.name}] Cubey API requires extension authorization token (HTTP 403). Skipping to next provider...")
                return None
            elif resp.status_code != 200:
                return None

            # Process Server-Sent Event stream
            events = resp.text.split("\n\n")
            target_event = None

            for event in events:
                if not event.strip():
                    continue
                
                event_name = ""
                data_buf = ""
                for line in event.splitlines():
                    if line.startswith("event:"):
                        event_name = line.split(":", 1)[1].strip()
                    elif line.startswith("data:"):
                        data_buf += line.split(":", 1)[1].strip()

                if event_name == "provider" and data_buf:
                    try:
                        data = json.loads(data_buf)
                        provider_id = data.get("provider")
                        results = data.get("results", {})

                        # Match target provider key
                        if self.key == "bLyrics-richsynced" and provider_id == "golyrics":
                            ttml = results.get("lyrics")
                            if ttml:
                                if isinstance(ttml, str) and ttml.startswith("{"):
                                    ttml = json.loads(ttml).get("ttml", ttml)
                                lrc_lines = parse_ttml_to_lrc(ttml, force_precision)
                                txt_lines = [BeautifulSoup(ttml, "lxml-xml").text.strip()]
                                return LyricResult(
                                    provider_key=self.key,
                                    provider_name=self.name,
                                    sync_type=self.sync_type,
                                    lrc_lines=lrc_lines,
                                    txt_lines=txt_lines,
                                    ttml_content=ttml
                                )

                        elif self.key == "musixmatch-richsync" and provider_id == "musixmatch":
                            if results.get("wordByWord"):
                                lrc_lines = parse_lrc_string(results["wordByWord"])
                                sync = "word"
                            elif results.get("synced"):
                                lrc_lines = parse_lrc_string(results["synced"])
                                sync = "line"
                            else:
                                continue  # nothing to return
                            return LyricResult(
                                provider_key=self.key,
                                provider_name=self.name,
                                sync_type=sync,
                                lrc_lines=lrc_lines,
                                txt_lines=[re.sub(r"\[.*?\]|<.*?>", "", line).strip() for line in lrc_lines]
                            )

                        elif self.key == "portato-richsynced" and provider_id == "qq" and results.get("lyrics"):
                            raw_lyrics = json.loads(results["lyrics"]).get("lyrics", "") if isinstance(results["lyrics"], str) and results["lyrics"].startswith("{") else str(results["lyrics"])
                            lrc_lines = parse_qrc_to_lrc(raw_lyrics, force_precision)
                            if not lrc_lines:
                                lrc_lines = parse_lrc_string(raw_lyrics)
                            return LyricResult(
                                provider_key=self.key,
                                provider_name=self.name,
                                sync_type="word",
                                lrc_lines=lrc_lines,
                                txt_lines=[re.sub(r"\[.*?\]|<.*?>", "", line).strip() for line in lrc_lines]
                            )

                        elif self.key == "legato-synced" and provider_id == "kugou" and results.get("lyrics"):
                            raw_lyrics = json.loads(results["lyrics"]).get("lyrics", "") if isinstance(results["lyrics"], str) else str(results["lyrics"])
                            lrc_lines = parse_lrc_string(raw_lyrics)
                            return LyricResult(
                                provider_key=self.key,
                                provider_name=self.name,
                                sync_type="line",
                                lrc_lines=lrc_lines,
                                txt_lines=[re.sub(r"\[.*?\]", "", line).strip() for line in lrc_lines]
                            )

                        elif provider_id == "binimum" and self.key == "binimum-richsynced":
                            ttml = results.get("lyrics")
                            if ttml:
                                lrc_lines = parse_ttml_to_lrc(ttml, force_precision)
                                return LyricResult(
                                    provider_key=self.key,
                                    provider_name=self.name,
                                    sync_type=self.sync_type,
                                    lrc_lines=lrc_lines,
                                    ttml_content=ttml
                                )

                    except Exception:
                        continue

        except Exception as e:
            from utils import logger
            logger.warning(f"[{self.name}] Error fetching lyrics: {e}")

        return None
