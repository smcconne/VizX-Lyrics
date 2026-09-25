# VizX-Lyrics: Interactive Menu User Guide

This guide provides a detailed walkthrough of the **VizX-Lyrics Interactive Rich Terminal Interface**, explaining all menu screens, settings, provider priority controls, format presets, and token configuration.

---

## 🚀 Launching the Main Menu

To open the interactive interface, launch `vizx_lyrics.py` without command-line arguments:

```bash
python vizx_lyrics.py
```

---

## 🖥️ Main Menu Overview

```text
  ██╗   ██╗██╗███████╗██╗  ██╗   ██╗  ██╗   ██╗██████╗ ██╗██████╗███████╗
  ██║   ██║██║╚══███╔╝╚██╗██╔╝   ██║  ╚██╗ ██╔╝██╔══██╗██║██╔════╝██╔════╝
  ██║   ██║██║  ███╔╝  ╚███╔╝    ██║   ╚████╔╝ ██████╔╝██║██║     ███████╗
  ╚██╗ ██╔╝██║ ███╔╝   ██╔██╗    ██║    ╚██╔╝  ██╔══██╗██║██║     ╚════██║
   ╚████╔╝ ██║███████╗██╔╝ ██╗   ███████╗██║   ██║  ██║██║╚██████╗███████║
    ╚═══╝  ╚═╝╚══════╝╚═╝  ╚═╝   ╚══════╝╚═╝   ╚═╝  ╚═╝╚═╝ ╚═════╝╚══════╝

               VIZX-LYRICS MAIN MENU
 [1] 🔍 Search & Download Lyrics (Priority Pipeline)
 [2] 🎯 Search & Download via Custom Provider
 [3] 🌐 Search & Download from ALL Providers (Save All)
 [4] 🔗 Download via Apple Music URL
 [5] ⚙️ Configure Lyrics Formats & Precision
 [6] 🎛️ Configure Lyric Providers & Priority
 [7] 📁 Configure Download Output Folder
 [0] 🚪 Exit
```

---

## 📖 Main Menu Options Explained

### `[1]` 🔍 Search & Download Lyrics (Priority Pipeline)
- **Description**: Search for any song or artist name across catalog engines (Apple Music with automatic fallback to LRCLib & YouTube Music).
- **Workflow**:
  1. Enter your search query.
  2. A formatted Rich table will display top 20 matches with **#**, **Title**, **Artist**, and **Album/Source**.
  3. Enter the song number (or select track/whole album).
  4. VizX-Lyrics will fetch and save lyrics using your active **Provider Priority Rank** and **Sync Hierarchy**.

---

### `[2]` 🎯 Search & Download via Custom Provider
- **Description**: Target a specific provider directly without altering your overall global settings.
- **Workflow**:
  1. Displays a numbered table of all 18 lyric providers.
  2. Select the provider number.
  3. Enter search query or Apple Music URL.
  4. VizX-Lyrics will fetch lyrics specifically from your chosen provider.

---

### `[3]` 🌐 Search & Download from ALL Providers (Save All)
- **Description**: Simultaneously query all 18 active lyric providers in parallel using `ThreadPoolExecutor` and save all returned `.lrc`, `.txt`, and `.ttml` files.
- **Workflow**:
  1. Enter song/artist search query and pick track.
  2. Queries all 18 providers concurrently in ~1–2 seconds.
  3. Exports files from every successful provider into your output folder.

---

### `[4]` 🔗 Download via Apple Music URL
- **Description**: Direct link download mode. Paste an Apple Music song or full album URL (`https://music.apple.com/...`).

---

### `[5]` ⚙️ Configure Lyrics Formats & Precision
- **Description**: Configure export formats and millisecond timecode precision.
- **Options**:
  - `[1] Toggle LRC (.lrc)`: Enable or disable `.lrc` time-synced export.
  - `[2] Toggle TXT (.txt)`: Enable or disable `.txt` plain text export.
  - `[3] Toggle TTML (.ttml)`: Enable or disable `.ttml` raw XML export.
  - `[4] Preset: Save ONLY LRC`: Quick preset for `.lrc` files only.
  - `[5] Preset: Save ONLY TTML`: Quick preset for `.ttml` files only.
  - `[6] Preset: Save ONLY TXT`: Quick preset for `.txt` files only.
  - `[7] Preset: Save ALL Formats`: Quick preset for `.lrc` + `.txt` + `.ttml`.
  - `[8] Force Timestamp Precision (.lrc)`: Toggle between 2-decimal (`00:00.00`) and 3-decimal (`00:00.000`) timestamps for saved `.lrc` files.

---

### `[6]` 🎛️ Configure Lyric Providers & Priority
- **Description**: Full management screen for provider ranking, sync hierarchy, and API keys.
- **Table View**: Displays all active providers in priority rank order (`1`, `2`, `3`...) along with their sync level (**Syllable**, **Word**, **Line**, **Unsynced**).
- **Options**:
  - `[1] Toggle Provider Mode`: Switch between `Fallback (First Hit)` and `Multi-Provider (Save All)`.
  - `[2] Toggle Sync Hierarchy Preference`:
    - **ENABLED**: Groups providers by sync precision (Syllable → Word → Line → Unsynced) before applying priority rank.
    - **DISABLED**: Follows priority rank order strictly regardless of sync precision.
  - `[3] Enable/Disable Provider Key`: Add or remove a provider key from active execution list.
  - `[4] Move Provider Priority Up`: Move provider key up in priority rank.
  - `[5] Move Provider Priority Down`: Move provider key down in priority rank.
  - `[6] Reset Providers to Default Priority`: Reset priority table to default factory order.
  - `[7] Set Cubey / Better Lyrics JWT Token`: Enter or update Cloudflare Turnstile JWT token (`cubey_jwt_token`) for direct Cubey API access. Type `clear` to remove token.

---

### `[7]` 📁 Configure Download Output Folder & Subfolders
- **Description**: Configure destination storage path and file organization.
- **Options**:
  - `[1] Change Download Output Folder`: Set custom storage path (e.g. `downloads` or `D:/Music/Lyrics`).
  - `[2] Toggle Provider Subfolder Organization`:
    - **ENABLED**: Saves multi-provider files into dedicated subfolders (`downloads/Artist - Title/Provider Name/01 - Song.lrc`).
    - **DISABLED**: Saves multi-provider files in single folder with provider key suffixes (`downloads/Artist - Title/01 - Song (lrclib-synced).lrc`).

---

### `[0]` 🚪 Exit
- Closes VizX-Lyrics cleanly.
