from typing import List, Dict, Optional, Any
from api.providers.base import BaseLyricProvider, LyricResult, SyncType
from api.providers.applemusic_provider import AppleMusicProvider
from api.providers.betterlyrics_provider import BetterLyricsProvider
from api.providers.unison_provider import UnisonProvider
from api.providers.lrclib_provider import LRCLibProvider
from api.providers.youtube_provider import YouTubeProvider
from api.providers.genius_provider import GeniusProvider
from api.providers.netease_provider import NeteaseProvider

SYNC_HIERARCHY: List[SyncType] = ["syllable", "word", "line", "unsynced"]

class ProviderManager:
    def __init__(self, cache_dir: str, config_dir: str):
        self.cache_dir = cache_dir
        self.config_dir = config_dir
        self.providers: Dict[str, BaseLyricProvider] = {}
        self._init_providers()

    def _init_providers(self):
        # Register all available provider instances
        self.providers["applemusic"] = AppleMusicProvider(self.cache_dir, self.config_dir)

        # BetterLyrics / Cubey Providers
        for key in [
            "bLyrics-richsynced", "bLyrics-synced", "musixmatch-richsync", "musixmatch-synced",
            "portato-richsynced", "legato-synced", "binimum-richsynced", "binimum-synced"
        ]:
            self.providers[key] = BetterLyricsProvider(key)

        # Unison Providers
        for key in ["unison-richsynced", "unison-synced", "unison-plain"]:
            self.providers[key] = UnisonProvider(key)

        # LRCLib Providers
        for key in ["lrclib-synced", "lrclib-plain"]:
            self.providers[key] = LRCLibProvider(key)

        # YouTube Providers
        for key in ["yt-captions", "yt-lyrics"]:
            self.providers[key] = YouTubeProvider(key)

        # Extra Providers
        self.providers["genius-plain"] = GeniusProvider()
        self.providers["netease-synced"] = NeteaseProvider()

    def get_provider(self, key: str) -> Optional[BaseLyricProvider]:
        return self.providers.get(key)

    def get_ordered_providers(
        self,
        preferred_keys: List[str],
        use_sync_hierarchy: bool = True
    ) -> List[BaseLyricProvider]:
        """
        Orders requested active providers.
        If use_sync_hierarchy is True:
          Groups active providers by SyncType hierarchy (syllable -> word -> line -> unsynced),
          preserving relative user priority order within each level.
        Else:
          Strictly follows the preferred_keys order.
        """
        active_list = [self.providers[k] for k in preferred_keys if k in self.providers]

        if not use_sync_hierarchy:
            return active_list

        # Group by sync hierarchy
        grouped: Dict[SyncType, List[BaseLyricProvider]] = {
            "syllable": [],
            "word": [],
            "line": [],
            "unsynced": []
        }

        for provider in active_list:
            grouped[provider.sync_type].append(provider)

        ordered: List[BaseLyricProvider] = []
        for sync_level in SYNC_HIERARCHY:
            ordered.extend(grouped[sync_level])

        return ordered

    def fetch_lyrics(
        self,
        song: str,
        artist: str,
        duration: Optional[float] = None,
        album: Optional[str] = None,
        isrc: Optional[str] = None,
        url: Optional[str] = None,
        preferred_keys: Optional[List[str]] = None,
        provider_mode: str = "fallback",
        use_sync_hierarchy: bool = True,
        sync_precision: int = 2
    ) -> List[LyricResult]:
        """
        Executes lyric retrieval across configured providers.
        Returns a list of successful LyricResults.
        In 'fallback' mode, returns a list with 1 item (the highest priority match).
        In 'multi' mode, returns all successful LyricResults across enabled providers.
        """
        if not preferred_keys:
            preferred_keys = list(self.providers.keys())

        ordered_providers = self.get_ordered_providers(preferred_keys, use_sync_hierarchy)
        results: List[LyricResult] = []

        from utils import logger

        if provider_mode == "multi":
            from concurrent.futures import ThreadPoolExecutor, as_completed

            def _task(provider: BaseLyricProvider):
                logger.info(f"Trying lyric source: {provider.name} ({provider.key}) [{provider.sync_type}]...")
                try:
                    res = provider.fetch_lyrics(
                        song=song,
                        artist=artist,
                        duration=duration,
                        album=album,
                        isrc=isrc,
                        url=url,
                        sync_precision=sync_precision
                    )
                    if res and res.has_content():
                        logger.info(f"Lyrics found via {provider.name}!")
                        return (ordered_providers.index(provider), res)
                except Exception as e:
                    logger.warning(f"Failed to fetch from {provider.name}: {e}")
                return None

            indexed_results = []
            with ThreadPoolExecutor(max_workers=min(len(ordered_providers), 10)) as executor:
                futures = [executor.submit(_task, p) for p in ordered_providers]
                for future in as_completed(futures):
                    item = future.result()
                    if item:
                        indexed_results.append(item)

            # Preserve priority order
            indexed_results.sort(key=lambda x: x[0])
            return [r for idx, r in indexed_results]

        # Sequential fallback mode
        for provider in ordered_providers:
            logger.info(f"Trying lyric source: {provider.name} ({provider.key}) [{provider.sync_type}]...")
            try:
                res = provider.fetch_lyrics(
                    song=song,
                    artist=artist,
                    duration=duration,
                    album=album,
                    isrc=isrc,
                    url=url,
                    sync_precision=sync_precision
                )
                if res and res.has_content():
                    logger.info(f"Lyrics found via {provider.name}!")
                    results.append(res)
                    break
            except Exception as e:
                logger.warning(f"Failed to fetch from {provider.name}: {e}")
                continue

        return results
