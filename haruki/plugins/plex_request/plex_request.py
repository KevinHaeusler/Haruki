__all__ = ()

from haruki.bots import Kiruha

PLEX_REQUEST = Kiruha.interactions(None, name='plex-request', description='Plex request', is_global=True)


@PLEX_REQUEST.interactions(name='tv-show')
async def tv_show():
    yield
    yield f'TV-Show'

@PLEX_REQUEST.interactions(name='tv-movie')
async def tv_movie():
    yield
    yield f'TV-Movie'


@PLEX_REQUEST.interactions(name='anime-show')
async def anime_show():
    yield
    yield f'anime-Show'

@PLEX_REQUEST.interactions(name='anime-movie')
async def anime_movie():
    yield
    yield f'anime-Movie'

@PLEX_REQUEST.interactions(name='foreign-show')
async def foreign_show():
    yield
    yield f'foreign-Show'

@PLEX_REQUEST.interactions(name='foreign-movie')
async def foreign_movie():
    yield
    yield f'foreign-Movie'