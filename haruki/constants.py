__all__ = (
    "HARUKI_TOKEN", "KIRUHA_TOKEN", "TAUTULLI_TOKEN", "TAUTULLI_URL", "TAUTULLI_IMAGE",
    "OVERSEER_TOKEN", "OVERSEER_URL", "SONARR_URL", "SONARR_TOKEN",
    "RADARR_URL", "RADARR_TOKEN",
    "TMDB_IMAGE_URL", "MISSING_POSTER_URL", "UPTIME_KUMA_URL",
)
from hata.env import EnvGetter

with EnvGetter() as env:
    HARUKI_TOKEN = env.get_str("HARUKI_TOKEN", raise_if_missing_or_empty=True)
    KIRUHA_TOKEN = env.get_str("KIRUHA_TOKEN", raise_if_missing_or_empty=True)
    TAUTULLI_URL = env.get_str("TAUTULLI_URL", raise_if_missing_or_empty=True)
    TAUTULLI_TOKEN = env.get_str("TAUTULLI_TOKEN", raise_if_missing_or_empty=True)
    TAUTULLI_IMAGE = env.get_str("TAUTULLI_IMAGE", raise_if_missing_or_empty=True)
    OVERSEER_URL = env.get_str("OVERSEER_URL", raise_if_missing_or_empty=True)
    OVERSEER_TOKEN = env.get_str("OVERSEER_TOKEN", raise_if_missing_or_empty=True)
    SONARR_URL = env.get_str("SONARR_URL", raise_if_missing_or_empty=True)
    SONARR_TOKEN = env.get_str("SONARR_TOKEN", raise_if_missing_or_empty=True)
    RADARR_URL = env.get_str("RADARR_URL", raise_if_missing_or_empty=True)
    RADARR_TOKEN = env.get_str("RADARR_TOKEN", raise_if_missing_or_empty=True)
    TMDB_IMAGE_URL = env.get_str("TMDB_IMAGE_URL", raise_if_missing_or_empty=True)
    MISSING_POSTER_URL = env.get_str("MISSING_POSTER_URL", raise_if_missing_or_empty=True)
    UPTIME_KUMA_URL = env.get_str("UPTIME_KUMA_URL", raise_if_missing_or_empty=True)