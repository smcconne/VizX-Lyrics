from bs4 import BeautifulSoup

def __getTs(ts, syncpoints: int):
    """Convert a TTML timestamp (e.g., '1:23.456s', '83.456s', '01:23.456') to LRC format."""
    ts = str(ts).replace('s', '')

    if ":" in ts:
        parts = ts.split(':')
        mins = int(parts[-2])
        secs = float(parts[-1])
    else:
        total_secs = float(ts)
        mins = int(total_secs // 60)
        secs = total_secs % 60

    if syncpoints == 3:
        return f'{mins:02d}:{secs:06.3f}'
    elif syncpoints == 2:
        return f'{mins:02d}:{secs:05.2f}'

def getLyrics(ttml, syncpoints: int):
    ttml_raw = ttml
    ttml = BeautifulSoup(ttml_raw, "lxml")

    info = {}

    lyrics = []
    songwriters = []
    timeSyncedLyrics = []

    songwriter = ttml.find_all("songwriter")
    if len(songwriter) > 0:
        for sw in songwriter:
            songwriters.append(sw.text)
        info["songwriter"] = ', '.join(songwriters)

    tt_tag = ttml.find("tt")
    timing = None
    if tt_tag:
        timing = tt_tag.get("itunes:timing")

    for line in ttml.find_all("p"):
        line_text = line.text.strip()
        if line_text:
            lyrics.append(line_text)
        else:
            lyrics.append("")

        if timing and timing != "None":
            if "span" in str(line):
                span = BeautifulSoup(str(line), "lxml")
                spans = span.find_all("span", attrs={'begin': True, 'end': True})

                if spans:
                    # Get line-level timestamp
                    p_begin = line.get("begin")
                    if p_begin:
                        line_ts = __getTs(p_begin, syncpoints)
                    else:
                        line_ts = __getTs(spans[0].get("begin"), syncpoints)

                    # Build word-synced Enhanced LRC line
                    # Format: [mm:ss.xx] <mm:ss.xx> word1 <mm:ss.xx> word2 ...
                    lrc_parts = [f"[{line_ts}]"]
                    for s in spans:
                        word_text = s.text.strip()
                        if word_text:
                            word_begin = __getTs(s.get("begin"), syncpoints)
                            lrc_parts.append(f"<{word_begin}> {word_text}")

                    timeSyncedLyrics.append(" ".join(lrc_parts))
                else:
                    # Spans present but no begin/end attributes — fall back to line-level
                    begin = line.get("begin")
                    if begin:
                        timeSyncedLyrics.append(f"[{__getTs(begin, syncpoints)}] {line_text}")
            else:
                begin = line.get("begin")
                if begin:
                    timeSyncedLyrics.append(f"[{__getTs(begin, syncpoints)}] {line_text}")
                else:
                    # Line without timing (e.g., instrumental break or empty line)
                    timeSyncedLyrics.append("")
    
    info["lyrics"] = lyrics
    if timeSyncedLyrics: info["timeSyncedLyrics"] = timeSyncedLyrics
    
    return info