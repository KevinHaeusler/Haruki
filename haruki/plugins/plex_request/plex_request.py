__all__ = ()

from haruki.bots import Kiruha
from haruki.plugins.plex_request.overseer_search import get_search_results

CUSTOM_ID_REQUEST = 'request'
CUSTOM_ID_ABORT = 'abort'
PLEX_REQUEST_ID = 'plex_request'

MEDIA_TYPES = [
    'tv',
    'movie',
]


@Kiruha.interactions(is_global=True)
async def plex_request(media_type: ('str', 'Pick Media Type'), media: ('str', 'Enter the media to search for')):
    media_data = await get_search_results(media_type, media)
    return media_data


@plex_request.autocomplete('media_type')
async def autocomplete_media_type(value):
    if value is None:
        return MEDIA_TYPES[:25]

    value = value.casefold()
    return [media_type for media_type in MEDIA_TYPES if (value in media_type)]
