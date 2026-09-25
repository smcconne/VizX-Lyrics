import re
from api.providers.base import LyricResult, SyncType

_WORD_TS = re.compile(r'<\d{2}:\d{2}[.:]\d')

def detect_sync_type(result: LyricResult) -> SyncType:
    """Inspect a LyricResult's actual content and return the true sync tier.

    Returns one of 'syllable' | 'word' | 'line' | 'unsynced'.

    Precedence:
      1. TTML inspection (most accurate):
         - {itunes,lrc}:timing="Syllable" on root <tt> -> 'syllable'
         - {itunes,lrc}:timing="Word" on root <tt>     -> 'word'
         - {itunes,lrc}:timing="Line" on root <tt>     -> 'line'
         - any <span ... begin=...> child             -> 'syllable'
         - otherwise with LRC lines extracted       -> 'line'
         - otherwise without LRC lines              -> 'unsynced'
      2. LRC inspection fallback (no TTML shipped):
         - any lrc_line containing inline '<mm:ss.xx>' timestamps -> 'word'
         - any [mm:ss.xx] line timestamps without inline word marks -> 'line'
      3. Plain text only -> 'unsynced'
    """
    if result.ttml_content:
        # Explicit timing declarations from known providers (Apple Music 'itunes',
        # Better Lyrics / lrc.red 'lrc'). Checked before the generic <span> heuristic
        # because the heuristic cannot distinguish syllable from word spans.
        for tier_value, tier_name in (("Syllable", "syllable"), ("Word", "word"), ("Line", "line")):
            for ns in ("itunes", "lrc"):
                if f'{ns}:timing="{tier_value}"' in result.ttml_content:
                    return tier_name
        if re.search(r'<span[^>]*\bbegin=', result.ttml_content):
            return "syllable"
        # TTML with no timing declaration: only "line" if getLyrics can extract LRC lines.
        # Otherwise with itunes:timing="None" or missing attribute the lyrics are unsynced.
        if result.lrc_lines:
            return "line"
        return "unsynced"

    if result.lrc_lines:
        for line in result.lrc_lines:
            if _WORD_TS.search(line):
                return "word"
        return "line"

    return "unsynced"