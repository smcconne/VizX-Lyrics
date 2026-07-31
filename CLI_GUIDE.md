# VizX-Lyrics: CLI Command-Line Reference Guide

This guide provides a comprehensive breakdown of all command-line arguments, flags, options, and terminal usage patterns available in **VizX-Lyrics**.

---

## 📋 Quick Command Summary Table

| Flag / Option | Full Option Name | Description | Example Usage |
| :--- | :--- | :--- | :--- |
| `-q` | `--query` | Search query for track or artist | `python vizx_lyrics.py -q "Blinding Lights"` |
| `-p` | `--providers` | Comma-separated list of active provider keys in priority order | `python vizx_lyrics.py -q "Song" -p lrclib-synced,bLyrics-richsynced` |
| `-a` | `--all-providers` | Download lyrics from ALL active providers simultaneously | `python vizx_lyrics.py -q "Legends Never Die" -a` |
| `--provider-mode` | `--provider-mode` | Provider execution mode (`fallback` or `multi`) | `python vizx_lyrics.py -q "Song" --provider-mode multi` |
| `-s` | `--sync` | Format timestamps with 3 millisecond digits (`00:00.000`) | `python vizx_lyrics.py -s "https://music.apple.com/..."` |
| `--no-lrc` | `--no-lrc` | Disable saving `.lrc` files | `python vizx_lyrics.py -q "Song" --no-lrc` |
| `--no-txt` | `--no-txt` | Disable saving `.txt` files | `python vizx_lyrics.py -q "Song" --no-txt` |
| `--no-ttml` | `--no-ttml` | Disable saving `.ttml` files | `python vizx_lyrics.py -q "Song" --no-ttml` |
| `-o` | `--output` | Specify custom download output directory path | `python vizx_lyrics.py -o "D:/Music/Lyrics" -q "Song"` |
| `--list-providers` | `--list-providers` | List all 18 available lyric providers & current priority ranks | `python vizx_lyrics.py --list-providers` |
| `-v` | `--version` | Display VizX-Lyrics version number | `python vizx_lyrics.py -v` |
| `-h` | `--help` | Show command-line help message | `python vizx_lyrics.py --help` |

---

## 📖 Detailed Option Explanations

### 1. `url` (Positional Argument)
- **Syntax**: `python vizx_lyrics.py [url]`
- **Description**: Direct Apple Music URL to a song or full album.
- **Example**:
  ```bash
  python vizx_lyrics.py "https://music.apple.com/us/album/legends-never-die/1283307934?i=1283307949"
  ```

---

### 2. `-q`, `--query <SEARCH_STRING>`
- **Description**: Search Apple Music catalog (with automatic fallback to LRCLib and YouTube Music if Apple Music catalog search yields no items).
- **Example**:
  ```bash
  python vizx_lyrics.py -q "Against The Current Legends Never Die"
  ```

---

### 3. `-a`, `--all-providers`
- **Description**: Enables **Multi-Provider Mode** across all active providers simultaneously. VizX-Lyrics queries all 18 lyric providers concurrently in parallel using `ThreadPoolExecutor` and saves `.lrc`, `.txt`, and `.ttml` files from every provider that has lyrics.
- **Example**:
  ```bash
  python vizx_lyrics.py -q "Legends Never Die" -a
  ```

---

### 4. `-p`, `--providers <KEYS>`
- **Description**: Passes a custom comma-separated list of provider keys to specify exact provider execution order or search a single provider.
- **Available Provider Keys**:
  - `bLyrics-richsynced` (Better Lyrics Syllable)
  - `bLyrics-synced` (Better Lyrics Line)
  - `musixmatch-richsync` (Musixmatch Word)
  - `musixmatch-synced` (Musixmatch Line)
  - `portato-richsynced` (QQ Music Word)
  - `legato-synced` (KuGou Line)
  - `binimum-richsynced` (BiniLyrics Syllable)
  - `binimum-synced` (BiniLyrics Line)
  - `unison-richsynced` (Unison Syllable)
  - `unison-synced` (Unison Line)
  - `unison-plain` (Unison Unsynced)
  - `lrclib-synced` (LRCLib Synced)
  - `lrclib-plain` (LRCLib Unsynced)
  - `yt-captions` (YouTube Subtitles)
  - `yt-lyrics` (YouTube Lyrics)
  - `genius-plain` (Genius Unsynced)
  - `netease-synced` (NetEase Cloud Music)
  - `applemusic` (Apple Music Native)
- **Example**:
  ```bash
  python vizx_lyrics.py -q "Starboy" -p lrclib-synced,bLyrics-richsynced
  ```

---

### 5. `--provider-mode {fallback,multi}`
- **Description**:
  - `fallback`: Queries providers in priority order and stops at the first successful provider that returns lyrics.
  - `multi`: Queries all active providers simultaneously and exports files from all successful providers.
- **Example**:
  ```bash
  python vizx_lyrics.py -q "Flowers" --provider-mode multi
  ```

---

### 6. `-s`, `--sync`
- **Description**: Changes timestamp format precision from 2-decimal places (`[00:00.00]`) to 3-decimal places (`[00:00.000]`).
- **Example**:
  ```bash
  python vizx_lyrics.py -s -q "Fortnight Taylor Swift"
  ```

---

### 7. Format Suppression Flags (`--no-lrc`, `--no-txt`, `--no-ttml`)
- **Description**: Exclude specific format exports.
- **Examples**:
  - Download **ONLY LRC**:
    ```bash
    python vizx_lyrics.py -q "Song" --no-txt --no-ttml
    ```
  - Download **ONLY TTML**:
    ```bash
    python vizx_lyrics.py -q "Song" --no-lrc --no-txt
    ```

---

### 8. `-o`, `--output <DIRECTORY>`
- **Description**: Override the default output folder directory path.
- **Example**:
  ```bash
  python vizx_lyrics.py -o "C:/Music/Lyrics" -q "Blinding Lights"
  ```

---

### 9. `--list-providers`
- **Description**: Prints a formatted Rich table listing all 18 integrated lyric providers, their active priority ranks, and sync types.
- **Example**:
  ```bash
  python vizx_lyrics.py --list-providers
  ```
