from ...constants import TAUTULLI_TOKEN, TAUTULLI_API


def get_session_info(session):
    """
    Reads session data and returns the formatted string. Used for the get_activity
    """
    user = session.get('user', 'Unknown User')
    show = session.get('grandparent_title', '')
    season = session.get('parent_title', '')
    title = session.get('title', 'Unknown Title')
    return f"User: {user}, Title: {show} - {season} - {title}"


async def make_api_call(client, api_call):
    """
    Makes API call and retrieves the JSON response.
    """
    url = f"{TAUTULLI_API}?apikey={TAUTULLI_TOKEN}&cmd={api_call}"
    async with client.http.get(url) as response:
        data = await response.json()
    return data
