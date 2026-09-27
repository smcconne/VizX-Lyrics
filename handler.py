import os
import sys

from sanitize_filename import sanitize

from api import AppleMusic
from api.provider_manager import ProviderManager
from config import Configure
from utils import logger

def __get_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

CACHE = os.path.join(__get_path(), "cache")
CONFIG = os.path.join(__get_path(), "config")

def __sanitize(path):
    if path != "":
        return sanitize(path)
    return path

def get_applemusic_instance(force_precision=2):
    return AppleMusic(CACHE, CONFIG, force_precision)

def download_lyrics(
    url: str,
    save_lrc: bool = True,
    save_txt: bool = True,
    save_ttml: bool = True,
    force_precision: int = 2,
    output_dir: str = "downloads",
    preferred_providers: list = None,
    provider_mode: str = None,
    use_sync_hierarchy: bool = None
):
    if not save_lrc and not save_txt and not save_ttml:
        logger.warning("Nothing to save! All file output formats are disabled.")
        return

    if not url:
        logger.error("No valid URL or query provided for lyrics download.")
        return

    config = Configure(CONFIG)
    settings = config.get_settings()

    if preferred_providers is None:
        preferred_providers = settings["preferred_providers"]
    if provider_mode is None:
        provider_mode = settings["provider_mode"]
    if use_sync_hierarchy is None:
        use_sync_hierarchy = settings["use_sync_hierarchy"]

    provider_manager = ProviderManager(CACHE, CONFIG)

    organize_by_provider = settings.get("organize_by_provider", False)

    if url.startswith("fallback://"):
        from urllib.parse import parse_qs, urlparse, unquote
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        name = unquote(params.get("name", ["Unknown"])[0])
        artist = unquote(params.get("artist", ["Unknown"])[0])
        duration_raw = params.get("duration", [0])[0]
        try:
            duration = float(duration_raw) if duration_raw else None
        except Exception:
            duration = None
        
        folder_name = __sanitize(f"{artist} - {name}")
        data = {
            "dir": folder_name,
            "album_name": "Single",
            "tracks": [{
                "file": f"01 - {name}",
                "name": name,
                "artist": artist,
                "duration": duration
            }]
        }
    else:
        applemusic = AppleMusic(CACHE, CONFIG, force_precision)
        data = applemusic.getInfo(url)

    if not data or "tracks" not in data:
        logger.error("Could not fetch song/album metadata from source.")
        return

    target_folder_name = __sanitize(data.get("dir", "Lyrics"))
    
    # Resolve storage path
    if not os.path.isabs(output_dir):
        base_storage = os.path.join(__get_path(), output_dir)
    else:
        base_storage = output_dir

    final_dir = os.path.join(base_storage, target_folder_name)
    any_saved = False
    created_dirs = set()

    for track in data["tracks"]:
        __file = track.get("file")
        if not __file:
            continue

        sanitized_filename = __sanitize(__file)
        song_title = track.get("name", __file)
        artist_name = track.get("artist", "")
        duration = track.get("duration", None)
        album_name = data.get("album_name", None)

        logger.info(f"\nProcessing: {artist_name} - {song_title}")

        # Fetch lyrics through provider manager pipeline
        results = provider_manager.fetch_lyrics(
            song=song_title,
            artist=artist_name,
            duration=duration,
            album=album_name,
            url=url if ("applemusic" in preferred_providers and not url.startswith("fallback://")) else None,
            preferred_keys=preferred_providers,
            provider_mode=provider_mode,
            use_sync_hierarchy=use_sync_hierarchy,
            force_precision=force_precision,
            applemusic_track=track
        )

        if not results:
            logger.warning(f'No lyrics found for "{__file}" across selected providers.')
            continue

        for res in results:
            if organize_by_provider and provider_mode == "multi":
                target_dir = os.path.join(final_dir, __sanitize(res.provider_name))
                file_base = sanitized_filename
            else:
                target_dir = final_dir
                prefix_suffix = f" ({res.provider_key})" if provider_mode == "multi" else ""
                file_base = f"{sanitized_filename}{prefix_suffix}"

            if save_lrc and res.lrc_lines:
                path = os.path.join(target_dir, f"{file_base}.lrc")
                if os.path.exists(path):
                    logger.warning(f'"{file_base}.lrc" already exists!')
                else:
                    logger.info(f'Saving [{res.provider_name}] "{file_base}.lrc"...')
                    if target_dir not in created_dirs:
                        os.makedirs(target_dir, exist_ok=True)
                        created_dirs.add(target_dir)
                    with open(path, "w", encoding="utf-8") as l:
                        l.write('\n'.join(res.lrc_lines))
                    any_saved = True

            if save_txt and res.txt_lines:
                path = os.path.join(target_dir, f"{file_base}.txt")
                if os.path.exists(path):
                    logger.warning(f'"{file_base}.txt" already exists!')
                else:
                    logger.info(f'Saving [{res.provider_name}] "{file_base}.txt"...')
                    if target_dir not in created_dirs:
                        os.makedirs(target_dir, exist_ok=True)
                        created_dirs.add(target_dir)
                    with open(path, "w", encoding="utf-8") as l:
                        l.write('\n'.join(res.txt_lines))
                    any_saved = True

            if save_ttml and res.ttml_content:
                path = os.path.join(target_dir, f"{file_base}.ttml")
                if os.path.exists(path):
                    logger.warning(f'"{file_base}.ttml" already exists!')
                else:
                    logger.info(f'Saving [{res.provider_name}] "{file_base}.ttml"...')
                    if target_dir not in created_dirs:
                        os.makedirs(target_dir, exist_ok=True)
                        created_dirs.add(target_dir)
                    with open(path, "w", encoding="utf-8") as l:
                        l.write(res.ttml_content)
                    any_saved = True

    if any_saved:
        logger.info(f"\nDone. Files saved in: {final_dir}")

def arguments(args):
    config = Configure(CONFIG)
    settings = config.get_settings()

    save_lrc = not args.no_lrc if getattr(args, 'no_lrc', False) else settings["save_lrc"]
    save_txt = not args.no_txt if getattr(args, 'no_txt', False) else settings["save_txt"]
    save_ttml = not args.no_ttml if getattr(args, 'no_ttml', False) else settings["save_ttml"]
    
    force_precision = 3 if getattr(args, 'sync', False) else settings["force_timestamp_precision_lrc"]
    output_dir = getattr(args, 'output', None) or settings["output_dir"]

    providers = None
    if getattr(args, 'providers', None):
        providers = [p.strip() for p in args.providers.split(",") if p.strip()]

    provider_mode = getattr(args, 'provider_mode', None)

    download_lyrics(
        url=args.url,
        save_lrc=save_lrc,
        save_txt=save_txt,
        save_ttml=save_ttml,
        force_precision=force_precision,
        output_dir=output_dir,
        preferred_providers=providers,
        provider_mode=provider_mode
    )
