__all__ = ()

from icecream import ic

from ...bots import Kiruha
from ..api_helpers.sonarr_api import check_indexers


@Kiruha.interactions(is_global=True)
async def plex_fix(client, event):
    ic(event)
    await check_indexers(client)
    return "Fix"
