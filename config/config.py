import os
import pickle

DEFAULT_PROVIDERS = [
    "applemusic",
    "bLyrics-richsynced",
    "unison-richsynced",
    "binimum-richsynced",
    "portato-richsynced",
    "musixmatch-richsync",
    "yt-captions",
    "lrclib-synced",
    "legato-synced",
    "netease-synced",
    "yt-lyrics",
    "genius-plain",
]

APPLE_MUSIC_TOKEN_INSTRUCTIONS = """How to get your media-user-token:
  1. Sign in to music.apple.com in a desktop browser (a free Apple ID works for searching)
  2. Open DevTools (F12 or Ctrl+Shift+I) -> Application tab -> Cookies -> https://music.apple.com
  3. Copy the value of the "media-user-token" cookie and paste it below
Note: A free Apple ID is sufficient for searching. Apple's lyrics are rehosted
by other providers (Musixmatch, etc.), so synced lyrics will still be available
via fallback providers even if Apple's own lyrics aren't returned."""
# Note: pickled configs from older versions may still contain removed provider keys;
# ProviderManager.get_ordered_providers drops them silently via `if k in self.providers`.

class Configure(object):
    def __init__(self, config: str):
        if not os.path.exists(config):
            os.makedirs(config)
        
        self.__config = os.path.join(config, "config.bin")

        if not os.path.exists(self.__config):
            print(APPLE_MUSIC_TOKEN_INSTRUCTIONS)
            __mediaUserToken = input("\n\tmedia-user-token: ")
            print()

            __config = {
                "content-type": "configuration",
                "mediaUserToken": __mediaUserToken,
                "output_dir": "downloads",
                "save_lrc": True,
                "save_txt": True,
                "save_ttml": True,
                "force_timestamp_precision_lrc": 2,
                "provider_mode": "fallback",
                "use_sync_hierarchy": True,
                "preferred_providers": list(DEFAULT_PROVIDERS)
            }

            with open(self.__config, 'wb') as c:
                pickle.dump(__config, c)

    def _read_config(self):
        with open(self.__config, 'rb') as c:
            return pickle.load(c)

    def _write_config(self, data):
        with open(self.__config, 'wb') as c:
            pickle.dump(data, c)

    def get(self):
        cfg = self._read_config()
        return cfg.get("mediaUserToken")

    def set(self):
        print(APPLE_MUSIC_TOKEN_INSTRUCTIONS)
        __mediaUserToken = input("\n\tmedia-user-token: ")
        print()
        cfg = self._read_config()
        cfg["mediaUserToken"] = __mediaUserToken
        self._write_config(cfg)

    def delete(self):
        cfg = self._read_config()
        if "mediaUserToken" in cfg:
            del cfg["mediaUserToken"]
        self._write_config(cfg)

    def get_setting(self, key, default=None):
        cfg = self._read_config()
        return cfg.get(key, default)

    def set_setting(self, key, value):
        cfg = self._read_config()
        cfg[key] = value
        self._write_config(cfg)

    def get_settings(self):
        cfg = self._read_config()
        return {
            "output_dir": cfg.get("output_dir", "downloads"),
            "save_lrc": cfg.get("save_lrc", True),
            "save_txt": cfg.get("save_txt", True),
            "save_ttml": cfg.get("save_ttml", True),
            # Backward-compat: fall back to legacy "sync_precision" key for existing configs
            "force_timestamp_precision_lrc": cfg.get("force_timestamp_precision_lrc", cfg.get("sync_precision", 2)),
            "provider_mode": cfg.get("provider_mode", "fallback"),
            "use_sync_hierarchy": cfg.get("use_sync_hierarchy", True),
            "preferred_providers": cfg.get("preferred_providers", list(DEFAULT_PROVIDERS)),
            "cubey_jwt_token": cfg.get("cubey_jwt_token", None),
            "organize_by_provider": cfg.get("organize_by_provider", False),
        }