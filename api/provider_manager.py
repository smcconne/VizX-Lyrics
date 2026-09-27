from typing import List, Dict, Optional, Any
from api.providers.base import BaseLyricProvider, LyricResult, SyncType
from api.providers.applemusic_provider import AppleMusicProvider
from api.providers.betterlyrics_provider import BetterLyricsProvider
from api.providers.unison_provider import UnisonProvider
from api.providers.lrclib_provider import LRCLibProvider
from api.providers.youtube_provider import YouTubeProvider
from api.providers.genius_provider import GeniusProvider
from api.providers.netease_provider import NeteaseProvider
from api.providers.sync_detector import detect_sync_type

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

        # BetterLyrics / Cubey Providers.
        for key in [
            "bLyrics-richsynced", "musixmatch-richsync",
            "portato-richsynced", "legato-synced", "binimum-richsynced"
        ]:
            self.providers[key] = BetterLyricsProvider(key)

        # Unison Providers
        for key in ["unison-richsynced"]:
            self.providers[key] = UnisonProvider(key)

        # LRCLib Providers
        for key in ["lrclib-synced"]:
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
        Always returns providers in the strict user priority order from preferred_keys.
        When use_sync_hierarchy is True, tier-aware targeting (the moving target tier
        and demotion tracking) lives in fetch_lyrics; ordering stays strictly by rank.
        """
        active_list = [self.providers[k] for k in preferred_keys if k in self.providers]
        return active_list

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
        force_precision: int = 2,
        applemusic_track: Optional[dict] = None
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
                        force_precision=force_precision,
                        applemusic_track=applemusic_track
                    )
                    if res and res.has_content():
                        res.sync_type = detect_sync_type(res)
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

        SYNC_HIERARCHY_IDX = {"syllable": 0, "word": 1, "line": 2, "unsynced": 3}

        demoted_by_tier: Dict[int, LyricResult] = {}

        # cutoffs[T] = last rank index at which tier T appears (only for tiers present).
        cutoffs: Dict[str, int] = {}
        for i, provider in enumerate(ordered_providers):
            cutoffs[provider.sync_type] = i

        def _current_target_idx(i: int) -> int:
            # Highest tier (in SYNC_HIERARCHY order) whose last rank index is >= i.
            for tier in SYNC_HIERARCHY:
                if tier in cutoffs and cutoffs[tier] >= i:
                    return SYNC_HIERARCHY_IDX[tier]
            return 3

        # Sequential fallback mode: strict rank order with a moving target tier.
        # The target tier only drops once the last provider of the current target
        # tier (by rank index) has been tried.
        for i, provider in enumerate(ordered_providers):
            target_idx = _current_target_idx(i)

            logger.info(f"Trying lyric source: {provider.name} ({provider.key}) [{provider.sync_type}]...")
            try:
                res = provider.fetch_lyrics(
                    song=song,
                    artist=artist,
                    duration=duration,
                    album=album,
                    isrc=isrc,
                    url=url,
                    force_precision=force_precision,
                    applemusic_track=applemusic_track
                )
                if not (res and res.has_content()):
                    continue

                actual = detect_sync_type(res)
                res.sync_type = actual
                actual_idx = SYNC_HIERARCHY_IDX[actual]

                if use_sync_hierarchy:
                    if actual_idx <= target_idx:
                        # Same-or-better than the tier we're searching for: accept and stop.
                        logger.info(f"Lyrics found via {provider.name} ({actual})!")
                        return [res]

                    # Demoted: track the first (highest-rank) candidate at this actual tier.
                    if actual_idx not in demoted_by_tier:
                        demoted_by_tier[actual_idx] = res
                        target_tier_name = SYNC_HIERARCHY[target_idx]
                        logger.warning(
                            f"[{provider.name}] returning {actual} while target tier is "
                            f"{target_tier_name}; demoting."
                        )
                    # Otherwise keep iterating in rank order.
                else:
                    # Strict priority mode: first non-empty result wins (original behavior).
                    logger.info(f"Lyrics found via {provider.name} ({actual})!")
                    return [res]

            except Exception as e:
                logger.warning(f"Failed to fetch from {provider.name}: {e}")
                continue

        if use_sync_hierarchy and demoted_by_tier:
            # End of loop: return best remaining demoted (lowest actual tier index wins).
            demoted = demoted_by_tier[min(demoted_by_tier)]
            logger.info(
                f"No true-tier hits; using best demoted result "
                f"({demoted.provider_name}, {demoted.sync_type})."
            )
            return [demoted]
        return results
