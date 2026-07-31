import requests
from urllib.parse import quote
from rich import box
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.align import Align
from utils import logger

console = Console()

def search_lrclib_catalog(query: str) -> list:
    """Fallback catalog search via LRCLib API."""
    try:
        resp = requests.get("https://lrclib.net/api/search", params={"q": query}, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            results = []
            for item in data[:15]:
                track_name = item.get("trackName", "Unknown Title")
                artist_name = item.get("artistName", "Unknown Artist")
                album_name = item.get("albumName", "Unknown Album")
                duration = item.get("duration", 0)
                dummy_url = f"fallback://track?name={quote(track_name)}&artist={quote(artist_name)}&duration={duration}"
                results.append({
                    "name": track_name,
                    "artist": artist_name,
                    "album": album_name,
                    "duration": duration,
                    "url": dummy_url,
                    "source": "LRCLib Catalog"
                })
            return results
    except Exception:
        pass
    return []

def search_ytmusic_catalog(query: str) -> list:
    """Fallback catalog search via YouTube Music search API."""
    try:
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
            "query": query
        }
        resp = requests.post(search_url, json=body, headers=headers, timeout=6)
        if resp.status_code == 200:
            text = resp.text
            import re
            # Extract videoId, title, and artist matches
            matches = re.findall(r'"videoId"\s*:\s*"([a-zA-Z0-9_-]{11})".*?"text"\s*:\s*"([^"]+)"', text)
            results = []
            seen = set()
            for vid, title in matches:
                if vid in seen or len(title) < 2 or title.lower() in ("song", "video", "album", "artist"):
                    continue
                seen.add(vid)
                dummy_url = f"fallback://track?name={quote(title)}&artist={quote(query)}&duration=0&video_id={vid}"
                results.append({
                    "name": title,
                    "artist": query,
                    "album": "YouTube Music Search",
                    "duration": 0,
                    "url": dummy_url,
                    "source": "YouTube Music"
                })
                if len(results) >= 10:
                    break
            return results
    except Exception:
        pass
    return []

def search_and_select(applemusic, query: str = None) -> str:
    """
    Search catalog (Apple Music with LRCLib/YouTube fallback),
    display formatted results table, allow track selection, and return track URL.
    """
    if not query:
        query = Prompt.ask("\n[bold green]❯ Enter song/artist name to search[/bold green]")
        query = query.strip()

    if not query:
        logger.error("No search query provided. Returning to menu...")
        return None

    # Primary search: Apple Music Catalog
    search_resp = None
    try:
        search_resp = applemusic.search(query, types="songs", limit=20)
    except Exception as e:
        logger.warning(f"Apple Music catalog search error: {e}")

    songs_data = []
    is_fallback = False

    if search_resp and "results" in search_resp and "songs" in search_resp["results"]:
        songs_data = search_resp["results"]["songs"].get("data", [])

    # If Apple Music returned no items, trigger Multi-Catalog Search Fallback
    if not songs_data:
        logger.info("Apple Music catalog returned no results. Searching fallback catalogs (LRCLib & YouTube Music)...")
        fallback_items = search_lrclib_catalog(query)
        if not fallback_items:
            fallback_items = search_ytmusic_catalog(query)
        
        if not fallback_items:
            logger.error("No songs found matching that search query across all catalog providers.")
            return None

        is_fallback = True
        songs_data = fallback_items

    table = Table(
        title=f"VIZX-LYRICS SEARCH RESULTS: '{query}'",
        title_style="bold cyan",
        show_header=True,
        header_style="bold bright_blue",
        border_style="bright_blue",
        box=box.ROUNDED
    )
    table.add_column("#", style="yellow", width=4, justify="right")
    table.add_column("TITLE", style="bold white", width=30)
    table.add_column("ARTIST", style="green", width=22)
    table.add_column("ALBUM / SOURCE", style="dim white", width=22)

    if not is_fallback:
        for idx, song_item in enumerate(songs_data, 1):
            attr = song_item.get("attributes", {})
            title = attr.get("name", "Unknown Title")
            artist = attr.get("artistName", "Unknown Artist")
            album = attr.get("albumName", "Unknown Album")
            table.add_row(f"[{idx}]", title, artist, album)
    else:
        for idx, item in enumerate(songs_data, 1):
            table.add_row(f"[{idx}]", item["name"], item["artist"], f"{item['album']} ({item['source']})")

    console.print()
    console.print(Align.center(table))
    console.print()

    # Prompt user for selection
    selected_song = None
    while True:
        choice = Prompt.ask(f"[bold green]❯ Select a song number (1-{len(songs_data)}) or 'c' to cancel[/bold green]")
        choice_str = choice.strip().lower()
        if choice_str == 'c':
            logger.info("Search cancelled.")
            return None
        if choice_str.isdigit():
            idx = int(choice_str)
            if 1 <= idx <= len(songs_data):
                selected_song = songs_data[idx - 1]
                break
        console.print("[bold red]❌ Invalid selection. Please enter a valid number.[/bold red]")

    if is_fallback:
        return selected_song["url"]

    attr = selected_song.get("attributes", {})
    song_url = attr.get("url", "")
    relationships = selected_song.get("relationships", {})
    albums_rel = relationships.get("albums", {}).get("data", [])

    album_id = albums_rel[0].get("id") if albums_rel else None
    if not album_id:
        return song_url

    try:
        album_resp = applemusic.getAlbumDetails(album_id)
        if not album_resp or "data" not in album_resp or not album_resp["data"]:
            return song_url

        album_data = album_resp["data"][0]
        album_attr = album_data.get("attributes", {})
        tracks = album_data.get("relationships", {}).get("tracks", {}).get("data", [])

        if len(tracks) > 1:
            console.print()
            console.print(f"[bold cyan]===============================================================================[/bold cyan]")
            console.print(f"[bold cyan] ALBUM:  {album_attr.get('name')}[/bold cyan]")
            console.print(f"[bold cyan] ARTIST: {album_attr.get('artistName')} ({len(tracks)} tracks)[/bold cyan]")
            console.print(f"[bold cyan]===============================================================================[/bold cyan]")
            console.print()

            for t_idx, track in enumerate(tracks, 1):
                t_attr = track.get("attributes", {})
                console.print(f"   [yellow]{t_idx:2d}.[/yellow] [white]{t_attr.get('name')}[/white]")

            console.print()
            console.print("   [yellow][A] Download Whole Album[/yellow]")
            console.print()

            while True:
                choice = Prompt.ask("[bold green]❯ Enter track number to download, or 'A' to download whole album[/bold green]")
                choice_lower = choice.strip().lower()
                if choice_lower == 'a':
                    album_url = album_attr.get("url", song_url)
                    logger.info(f"Downloading whole album: {album_attr.get('name')}")
                    return album_url
                elif choice_lower.isdigit():
                    t_idx = int(choice_lower)
                    if 1 <= t_idx <= len(tracks):
                        selected_track = tracks[t_idx - 1]
                        track_url = selected_track.get("attributes", {}).get("url", "")
                        if track_url:
                            return track_url
                        return f"{album_attr.get('url')}?i={selected_track.get('id')}"
                console.print("[bold red]❌ Invalid choice. Enter a track number or 'A'.[/bold red]")
    except Exception:
        pass

    return song_url
