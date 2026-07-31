import os
import pickle

DEFAULT_PROVIDERS = [
    "applemusic",
    "bLyrics-richsynced",
    "unison-richsynced",
    "binimum-richsynced",
    "portato-richsynced",
    "musixmatch-richsync",
    "bLyrics-synced",
    "unison-synced",
    "yt-captions",
    "binimum-synced",
    "lrclib-synced",
    "legato-synced",
    "musixmatch-synced",
    "netease-synced",
    "yt-lyrics",
    "unison-plain",
    "lrclib-plain",
    "genius-plain",
]

class Configure(object):
    def __init__(self, config: str):
        if not os.path.exists(config):
            os.makedirs(config)
        
        self.__config = os.path.join(config, "config.bin")

        if not os.path.exists(self.__config):
            __mediaUserToken = input("\n\tmedia-user-token: ")
            print()

            __config = {
                "content-type": "configuration",
                "mediaUserToken": __mediaUserToken,
                "output_dir": "downloads",
                "save_lrc": True,
                "save_txt": True,
                "save_ttml": True,
                "sync_precision": 2,
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
            "sync_precision": cfg.get("sync_precision", 2),
            "provider_mode": cfg.get("provider_mode", "fallback"),
            "use_sync_hierarchy": cfg.get("use_sync_hierarchy", True),
            "preferred_providers": cfg.get("preferred_providers", list(DEFAULT_PROVIDERS)),
            "cubey_jwt_token": cfg.get("cubey_jwt_token", None),
            "organize_by_provider": cfg.get("organize_by_provider", False),
        }