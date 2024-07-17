__all__ = ()

from hata import ClientWrapper
from haruki.bots import Kiruha
from .helper import get_session_info, make_api_call  # import the helper function

ALL = ClientWrapper(Kiruha)


@ALL.interactions(is_global=True)
async def plex_activity(client):
    data = await make_api_call(client, 'get_activity')
    sessions = data.get('response', {}).get('data', {}).get('sessions', [])
    if sessions is None:
        return "Invalid request."
    if not sessions:
        return "No active sessions."
    result = ["**Active Plex Sessions:**"]
    for session in sessions:
        result.append(get_session_info(session))
        # TODO refactor to use embeds instead
    return "\n".join(result)
