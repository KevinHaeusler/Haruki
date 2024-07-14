__all__ = ('HARUKI_TOKEN', 'KIRUHA_TOKEN', 'TAUTULLI_TOKEN', 'TAUTULLI_API')

from hata.env import EnvGetter


with EnvGetter() as env:
    HARUKI_TOKEN = env.get_str('HARUKI_TOKEN', raise_if_missing_or_empty = True)
    KIRUHA_TOKEN = env.get_str('KIRUHA_TOKEN', raise_if_missing_or_empty = True)
    TAUTULLI_TOKEN = env.get_str('TAUTULLI_TOKEN', raise_if_missing_or_empty = True)
    TAUTULLI_API = env.get_str('TAUTULLI_API', raise_if_missing_or_empty = True)

