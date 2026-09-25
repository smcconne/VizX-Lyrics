# VizX-Lyrics

A powerful, menu-driven Python application and CLI engine to search and download time-synced lyrics (`.lrc`), plain text lyrics (`.txt`), and rich TTML lyrics (`.ttml`) from **12 Lyric Providers** with multi-provider fallback pipelines, sync hierarchy filtering, and customizable format export.

---

## 🌟 Features

- **🌐 12 Lyric Providers Integrated**:
  - **Syllable-Synced (RichSync / TTML)**: Better Lyrics (`bLyrics-richsynced`), Unison (`unison-richsynced`), BiniLyrics (`binimum-richsynced`)
  - **Word-Synced**: QQ Music (`portato-richsynced`), Musixmatch (`musixmatch-richsync`)
  - **Line-Synced**: Apple Music (`applemusic`), LRCLib (`lrclib-synced`), NetEase Cloud Music (`netease-synced`), KuGou (`legato-synced`), YouTube Captions (`yt-captions`)
  - **Plain Text / Unsynced**: Genius (`genius-plain`), YouTube Lyrics (`yt-lyrics`)
- **🎯 Dynamic Sync Hierarchy**: Automatic fallback prioritizing **Syllable-Synced** → **Word-Synced** → **Line-Synced** → **Plain Text**.
- **⚡ Dual Execution Modes**:
  - **Fallback Mode (First Hit)**: Returns highest-quality synced lyrics from the first matching provider in your priority order.
  - **Multi-Provider Mode (Save All)**: Queries all active providers simultaneously and exports `.lrc`, `.txt`, and `.ttml` files from every provider.
- **📱 Interactive Terminal UI**: Rich-powered menu for provider priority ordering, single custom provider search, format presets, output folder config, and JWT token management.
- **⚙️ Selective Format Presets**: Flexible format selection for `.lrc`, `.txt`, `.ttml`, or any custom combination (e.g. ONLY LRC, ONLY TTML, or ALL).
- **⏱️ Configurable Timestamp Precision**: Toggle between 2-digit (`00:00.00`) and 3-digit (`00:00.000`) millisecond timestamps.
- **🔑 Cubey JWT Token Support**: Built-in configuration to store Cloudflare Turnstile JWT tokens for Cubey / Better Lyrics backend API requests.

---

## 🚀 Installation & Requirements

1. **Clone Repository**:
   ```bash
   git clone https://github.com/VizXtreme/VizX-Lyrics.git
   cd VizX-Lyrics
   ```

2. **Install Required Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 📖 Usage Guides & Documentation

- 🖥️ **[Interactive Menu User Guide](MENU_GUIDE.md)**: Detailed walkthrough of screens, provider ranking, format presets, Cubey JWT tokens, and storage options.
- 💻 **[CLI Command-Line Guide](CLI_GUIDE.md)**: Complete argument reference (`-q`, `-p`, `-a`, `-s`, `-o`, `--no-lrc`, etc.) with example commands.

---

### 1. Interactive Menu Mode (Recommended)

Run `vizx_lyrics.py` without arguments to launch the interactive UI:

```bash
python vizx_lyrics.py
```

#### Main Menu Options:
* **`[1]` Search & Download Lyrics (Priority Pipeline)**: Search catalog (Apple Music with LRCLib & YouTube fallback) and download lyrics using your configured priority order & sync hierarchy.
* **`[2]` Search & Download via Custom Provider**: Choose a specific provider from the list of 12 providers to fetch lyrics directly.
* **`[3]` Search & Download from ALL Providers (Save All)**: Fetch and save lyrics simultaneously from every active provider.
* **`[4]` Download via Apple Music URL**: Input an Apple Music song or album URL.
* **`[5]` Configure Lyrics Formats & Precision**: Toggle `.lrc`, `.txt`, `.ttml` formats or pick quick presets (ONLY LRC, ONLY TTML, ALL, etc.).
* **`[6]` Configure Lyric Providers & Priority**: Re-order provider priority, enable/disable individual sources, toggle Sync Hierarchy, and set Cubey JWT tokens.
* **`[7]` Configure Download Output Folder**: Set custom download directory and toggle provider subfolders.

---

### 2. Command Line Interface (CLI)

#### Download via Search Query
```bash
python vizx_lyrics.py -q "Legends Never Die League of Legends"
```

#### Download from ALL Providers Simultaneously
```bash
python vizx_lyrics.py -q "Legends Never Die" -a
```

#### Use Specific Custom Provider(s) in Priority Order
```bash
python vizx_lyrics.py -q "Blinding Lights" -p lrclib-synced,bLyrics-richsynced
```

#### Export ONLY LRC or ONLY TTML
```bash
python vizx_lyrics.py -q "Fortnight Taylor Swift" --no-txt --no-ttml
```

#### Download via Apple Music Song/Album URL with 3-digit Millisecond Sync
```bash
python vizx_lyrics.py -s "https://music.apple.com/us/album/song-title/123456789?i=123456790"
```

#### List All 12 Available Providers & Active Priority Ranks
```bash
python vizx_lyrics.py --list-providers
```

---

## ⚙️ CLI Flags Reference

```text
usage: vizx_lyrics.py [-h] [-v] [-q QUERY] [-s] [--no-txt] [--no-lrc]
                      [--no-ttml] [-o OUTPUT] [-p PROVIDERS] [-a]
                      [--provider-mode {fallback,multi}] [--list-providers]
                      [url]

options:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -q, --query QUERY     Search query to search Apple Music catalog
  -s, --sync            Save timecodes in 00:00.000 format (3 millisecond digits)
  --no-txt              Don't save lyrics as a .txt file
  --no-lrc              Don't save time-synced lyrics as a .lrc file
  --no-ttml             Don't save raw lyrics as a .ttml file
  -o, --output OUTPUT   Custom output directory path
  -p, --providers PROVIDERS
                        Comma-separated list of active provider keys in priority order
  -a, --all-providers   Download lyrics from ALL active providers simultaneously
  --provider-mode {fallback,multi}
                        Provider selection mode: fallback (first hit) or multi (save all)
  --list-providers      List all available lyric providers and exit
  url                   Apple Music URL for an album or a song
```

---

## 📄 License
This project is licensed under the [MIT License](LICENSE).
